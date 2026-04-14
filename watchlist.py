"""
core.py — Vectorized Pandas computation engine.

Smart Score (v2) — Capital-agnostic ranking formula:
────────────────────────────────────────────────────
The v1 formula used `pot_profit` (qty × margin) which is capital-dependent:
ranking changed based on how much cash you had, making comparisons unstable.

v2 separates intrinsic item quality from your current capital:

  smart_score = roi_decimal
              × log10(vol_use + 1)          ← market liquidity
              × log10(market_depth + 1)     ← total extractable value
              × freshness_factor            ← data reliability penalty

  Where:
    roi_decimal    = margin / buy_p          (capital efficiency)
    vol_use        = 1h volume (fallback 5m)
    market_depth   = ge_lim × margin        (how much GP this market can yield)
    freshness      = decays from 1.0→0.25 over 2h of data staleness

This answers: "Which item gives the best ROI, from the deepest liquid market,
with the most reliable price data?" — independent of your wallet size.

The qty / pot_profit / invest columns are still computed for display purposes
(how much YOU can trade given your current capital + remaining GE limit).
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
    mapping:          dict,
    latest:           dict,
    vol5m:            dict,
    vol1h:            dict,
    free_cash:        int,
    acc_type:         str,
    cooldowns:        dict,
    overrides:        dict,
    min_margin:       int   = 500,
    min_vol:          int   = 10,
    min_roi_pct:      float = 0.20,
) -> pd.DataFrame:
    """
    Main scanner engine. Returns a ranked DataFrame of all flippable items.

    Parameters
    ----------
    mapping     : {item_id: item_info}  from OSRS Wiki mapping endpoint
    latest      : {str(item_id): {high, low, highTime, lowTime}}
    vol5m       : {str(item_id): {highPriceVolume, lowPriceVolume}}
    vol1h       : same structure, 1-hour window
    free_cash   : GP available (total minus locked in active trades)
    acc_type    : "F2P + Members" | "Alleen Members" | "Alleen F2P"
    cooldowns   : {str(item_id): {qty, timestamp}}
    overrides   : {str(item_id): {buy, sell}}  — manual margin overrides
    min_margin  : absolute minimum net margin to show (GP)
    min_vol     : minimum combined volume to show
    min_roi_pct : minimum ROI% to show (default 0.20%)
    """
    if not latest:
        return pd.DataFrame()

    # ── 1. Build raw DataFrame ─────────────────────────────────────────────
    rows = []
    for sid, px in latest.items():
        iid = int(sid)
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
            "id":       iid,
            "name":     info.get("name", "?"),
            "icon":     info.get("icon", ""),
            "members":  bool(info.get("members", False)),
            "ge_lim":   int(info.get("limit", 0)),
            "high":     int(high),
            "low":      int(low),
            "high_ts":  px.get("highTime", 0),
            "low_ts":   px.get("lowTime",  0),
            "vol_5m":   int(v5.get("highPriceVolume", 0)) + int(v5.get("lowPriceVolume", 0)),
            "vol_1h":   int(v1h.get("highPriceVolume", 0)) + int(v1h.get("lowPriceVolume", 0)),
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

    # ── 3. Base prices (instabuy = high-1, instasell = low+1) ─────────────
    df["buy_p"]        = df["low"]  + 1
    df["sell_p"]       = df["high"] - 1
    df["has_override"] = False

    # Apply manual overrides
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

    # Dynamic minimum margin: scales with capital so small items vanish at scale
    effective_min_margin = (
        max(min_margin, int(free_cash * 0.00005))
        if free_cash > 50_000_000
        else min_margin
    )
    df = df[df["margin"] >= effective_min_margin].copy()

    # ── 5. ROI filter ──────────────────────────────────────────────────────
    df["roi"] = (df["margin"] / df["buy_p"]) * 100
    df = df[df["roi"] >= min_roi_pct].copy()

    # ── 6. Volume ──────────────────────────────────────────────────────────
    # Prefer 1h volume; fall back to 5m × 3 (conservative) if 1h is zero
    df["vol_use"] = np.where(
        df["vol_1h"] > 0,
        df["vol_1h"],
        df["vol_5m"] * 3,
    )
    df = df[df["vol_use"] >= min_vol].copy()

    # ── 7. GE limit & cooldown ─────────────────────────────────────────────
    df["ge_lim_fixed"] = np.where(df["ge_lim"] > 0, df["ge_lim"], 50_000)

    # Compute remaining buy limit accounting for 4h cooldown resets
    def _remaining(row) -> int:
        used = cooldown_remaining_qty(cooldowns.get(str(row["id"]), {}))
        return max(0, int(row["ge_lim_fixed"]) - used)

    df["remaining_lim"] = df.apply(_remaining, axis=1)
    df = df[df["remaining_lim"] > 0].copy()

    # ── 8. Capital allocation (display only, not used in ranking) ──────────
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

    # ── 9. Freshness factor (penalises stale API data) ─────────────────────
    # Use the *older* of the two timestamps as the freshness anchor
    df["freshness"] = df.apply(
        lambda r: data_freshness(max(r["high_ts"] or 0, r["low_ts"] or 0)),
        axis=1,
    )

    # ── 10. SMART SCORE v2 — Capital-agnostic ranking ──────────────────────
    #
    #   roi_decimal   = margin / buy_p             (capital efficiency)
    #   vol_score     = log10(vol_use + 1)         (market liquidity)
    #   depth_score   = log10(ge_lim * margin + 1) (total market yield)
    #   freshness     = data quality multiplier
    #
    roi_decimal  = df["margin"] / df["buy_p"]
    vol_score    = np.log10(df["vol_use"] + 1)
    depth_score  = np.log10(df["ge_lim_fixed"] * df["margin"] + 1)

    df["smart_score"] = roi_decimal * vol_score * depth_score * df["freshness"]

    # ── 11. Drop items that would require 0 investment (no usable qty) ─────
    # (items still shown for watchlist even if qty=0)
    df = df[df["buy_p"] > 0].copy()

    return df.reset_index(drop=True)
