"""
core.py — Vectorized Pandas computation engine.

TWO scoring columns are produced:

  smart_score  (capital-agnostic quality ranking)
  ─────────────────────────────────────────────────
  Answers: "Which item has the best intrinsic quality?"
  Stable regardless of your cash stack size.

    roi_decimal  = margin / buy_p
    vol_score    = log10(vol_use + 1)
    depth_score  = log10(ge_lim × margin + 1)
    smart_score  = roi_decimal × vol_score × depth_score × freshness

  Used by: Watchlist, background quality filter.


  action_score  (capital-aware action ranking)
  ─────────────────────────────────────────────────
  Answers: "What is the best trade I can do RIGHT NOW with my cash?"
  Deliberately capital-dependent — pot_profit reflects YOUR available qty.

    norm_profit  = pot_profit / max(pot_profit)   # 0..1 relative to the set
    norm_smart   = smart_score / max(smart_score)  # 0..1 normalised quality
    action_score = 0.55 × norm_profit + 0.45 × norm_smart

  Weights: profit-pull (55%) + quality-pull (45%).
  This ensures the Hero Card always surfaces the absolute best GP opportunity
  for the current cash, while quality keeps garbage-margin items out.

  Used by: Scanner Hero Card, Runner-up feed.
"""
import numpy as np
import pandas as pd

from src.engine.formulas import (
    GE_TAX_RATE,
    GE_TAX_THRESHOLD,
    GE_TAX_CAP,
    ge_tax_vectorized,
    cooldown_remaining_qty,
    data_freshness,
)


def compute_flips(
    mapping:      dict,
    latest:       dict,
    vol5m:        dict,
    vol1h:        dict,
    free_cash:    int,
    acc_type:     str,
    cooldowns:    dict,
    overrides:    dict,
    min_margin:   int   = 500,
    min_vol:      int   = 10,
    min_roi_pct:  float = 0.20,
) -> pd.DataFrame:
    """
    Main scanner engine. Returns a fully-scored DataFrame.

    Parameters
    ----------
    mapping     : {item_id: item_info}  from OSRS Wiki mapping endpoint
    latest      : {str(item_id): {high, low, highTime, lowTime}}
    vol5m       : {str(item_id): {highPriceVolume, lowPriceVolume}}
    vol1h       : same structure, 1-hour window
    free_cash   : GP available (total minus locked in active trades)
    acc_type    : "F2P + Members" | "Alleen Members" | "Alleen F2P"
    cooldowns   : {str(item_id): {qty, timestamp}}
    overrides   : {str(item_id): {buy, sell}}
    min_margin  : absolute minimum net margin (GP)
    min_vol     : minimum combined volume
    min_roi_pct : minimum ROI% filter
    """
    if not latest:
        return pd.DataFrame()

    # ── 1. Build raw DataFrame ─────────────────────────────────────────────
    rows = []
    for sid, px in latest.items():
        iid  = int(sid)
        info = mapping.get(iid)
        if not info:
            continue
        high = px.get("high")
        low  = px.get("low")
        if not high or not low or high <= low:
            continue

        v5  = vol5m.get(sid, {})
        v1h = vol1h.get(sid, {})

        rows.append({
            "id":      iid,
            "name":    info.get("name", "?"),
            "icon":    info.get("icon", ""),
            "members": bool(info.get("members", False)),
            "ge_lim":  int(info.get("limit", 0)),
            "high":    int(high),
            "low":     int(low),
            "high_ts": px.get("highTime", 0),
            "low_ts":  px.get("lowTime",  0),
            "vol_5m":  int(v5.get("highPriceVolume", 0))  + int(v5.get("lowPriceVolume", 0)),
            "vol_1h":  int(v1h.get("highPriceVolume", 0)) + int(v1h.get("lowPriceVolume", 0)),
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # ── 2. Account type filter ─────────────────────────────────────────────
    if acc_type == "Alleen F2P":
        df = df[~df["members"]].copy()
    elif acc_type == "Alleen Members":
        df = df[df["members"]].copy()
    if df.empty:
        return df

    # ── 3. Prices & overrides ──────────────────────────────────────────────
    df["buy_p"]        = df["low"]  + 1
    df["sell_p"]       = df["high"] - 1
    df["has_override"] = False

    if overrides:
        for iid_str, ov in overrides.items():
            mask = df["id"] == int(iid_str)
            if mask.any():
                df.loc[mask, "buy_p"]        = int(ov["buy"])
                df.loc[mask, "sell_p"]       = int(ov["sell"])
                df.loc[mask, "has_override"] = True

    df = df[df["sell_p"] > df["buy_p"]].copy()
    if df.empty:
        return df

    # ── 4. Tax & margin ────────────────────────────────────────────────────
    df["tax"]    = ge_tax_vectorized(df["sell_p"])
    df["margin"] = df["sell_p"] - df["tax"] - df["buy_p"]

    # Dynamic noise floor: ignore tiny margins at large capital
    effective_min = (
        max(min_margin, int(free_cash * 0.00005))
        if free_cash > 50_000_000 else min_margin
    )
    df = df[df["margin"] >= effective_min].copy()

    # ── 5. ROI ─────────────────────────────────────────────────────────────
    df["roi"] = (df["margin"] / df["buy_p"]) * 100
    df = df[df["roi"] >= min_roi_pct].copy()

    # ── 6. Volume ──────────────────────────────────────────────────────────
    # Prefer 1h; fallback to 5m×3 (conservative, avoids false positives)
    df["vol_use"] = np.where(df["vol_1h"] > 0, df["vol_1h"], df["vol_5m"] * 3)
    df = df[df["vol_use"] >= min_vol].copy()

    # ── 7. GE limit & cooldown ─────────────────────────────────────────────
    df["ge_lim_fixed"] = np.where(df["ge_lim"] > 0, df["ge_lim"], 50_000)

    def _remaining(row) -> int:
        used = cooldown_remaining_qty(cooldowns.get(str(row["id"]), {}))
        return max(0, int(row["ge_lim_fixed"]) - used)

    df["remaining_lim"] = df.apply(_remaining, axis=1)
    df = df[df["remaining_lim"] > 0].copy()

    # ── 8. Capital allocation ──────────────────────────────────────────────
    if free_cash > 0:
        df["max_aff"] = np.minimum(
            (free_cash // df["buy_p"]).astype(int),
            df["remaining_lim"],
        )
    else:
        df["max_aff"] = 0

    df["qty"]        = df["max_aff"].clip(lower=0)
    df["pot_profit"] = df["qty"] * df["margin"]
    df["invest"]     = df["qty"] * df["buy_p"]

    # ── 9. Freshness ───────────────────────────────────────────────────────
    df["freshness"] = df.apply(
        lambda r: data_freshness(max(r["high_ts"] or 0, r["low_ts"] or 0)),
        axis=1,
    )

    # ── 10. Smart Score — capital-agnostic quality ─────────────────────────
    roi_decimal = df["margin"] / df["buy_p"]
    vol_score   = np.log10(df["vol_use"] + 1)
    depth_score = np.log10(df["ge_lim_fixed"] * df["margin"] + 1)

    df["smart_score"] = roi_decimal * vol_score * depth_score * df["freshness"]

    # ── 11. Action Score — capital-aware, hero card ranking ────────────────
    #
    # Normalise both signals to [0, 1] so neither dominates by scale.
    # Then blend: 55% weight on raw profit (GP you CAN make now) + 45% quality.
    #
    # Why 55/45?  The user asked for "ruwe winst … moet prioriteit krijgen"
    # but we still want quality to prevent a 1gp-margin high-qty item from
    # dominating just because pot_profit is large.
    #
    max_profit = df["pot_profit"].max()
    max_smart  = df["smart_score"].max()

    norm_profit = df["pot_profit"]    / max_profit if max_profit > 0 else 0
    norm_smart  = df["smart_score"]   / max_smart  if max_smart  > 0 else 0

    df["action_score"] = 0.55 * norm_profit + 0.45 * norm_smart

    # ── 12. Final sanity filter ────────────────────────────────────────────
    df = df[df["buy_p"] > 0].copy()

    return df.reset_index(drop=True)
