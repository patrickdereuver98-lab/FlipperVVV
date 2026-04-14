"""
core.py — Vectorized Pandas computation engine.

Nu inclusief:
- Whale Limits (Hard caps op High-Value items)
- Market Share Caps (Max 25% van uurs-volume)
- Crash Prevention (Empty DataFrame afhandeling)
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
    sector:       str,          
    cooldowns:    dict,
    overrides:    dict,
    min_margin:   int   = 500,
    min_vol:      int   = 5,
    min_roi_pct:  float = 0.15,
) -> pd.DataFrame:
    
    if not latest:
        return pd.DataFrame()

    # ── 1. Build raw DataFrame ─────────────────────────────────────────────
    rows = []
    for sid, px in latest.items():
        iid  = int(sid)
        info = mapping.get(iid)
        if not info: continue
        high = px.get("high")
        low  = px.get("low")
        if not high or not low or high <= low: continue

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

    if not rows: return pd.DataFrame()
    df = pd.DataFrame(rows)

    # ── 2. Filters (Account & Sector) ──────────────────────────────────────
    if acc_type == "Alleen F2P": df = df[~df["members"]].copy()
    elif acc_type == "Alleen Members": df = df[df["members"]].copy()
    if df.empty: return df
    
    if sector == "High-Volume Supplies":
        df = df[(df["vol_1h"] >= 1000) & (df["low"] <= 2_000_000)].copy()
    elif sector == "High-Value Gear":
        df = df[(df["low"] >= 2_000_000)].copy()

    if df.empty: return df # <-- CRASH FIX 1

    # ── 3. Prijzen & Overrides ─────────────────────────────────────────────
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
    if df.empty: return df # <-- CRASH FIX 2

    # ── 4. Tax & Netto Winst ───────────────────────────────────────────────
    df["tax"]    = ge_tax_vectorized(df["sell_p"])
    df["margin"] = df["sell_p"] - df["tax"] - df["buy_p"]

    effective_min = max(min_margin, int(free_cash * 0.00002)) if free_cash > 50_000_000 else min_margin
    df = df[df["margin"] >= effective_min].copy()
    if df.empty: return df # <-- CRASH FIX 3

    # ── 5. Basis ROI & Volume ──────────────────────────────────────────────
    df["roi"] = (df["margin"] / df["buy_p"]) * 100
    df = df[(df["roi"] >= min_roi_pct) & (df["roi"] <= 500)].copy() # 500% cap voorkomt manipulation scams
    if df.empty: return df

    df["vol_use"] = np.where(df["vol_1h"] > 0, df["vol_1h"], df["vol_5m"] * 3)
    df = df[df["vol_use"] >= min_vol].copy()
    if df.empty: return df # <-- CRASH FIX 4 (Dit loste je huidige ValueError op)

    # ── 6. GE Limieten & Cooldowns ─────────────────────────────────────────
    df["ge_lim_fixed"] = np.where(df["ge_lim"] > 0, df["ge_lim"], 50_000)
    
    def _remaining(row) -> int:
        used = cooldown_remaining_qty(cooldowns.get(str(row["id"]), {}))
        return max(0, int(row["ge_lim_fixed"]) - used)

    df["remaining_lim"] = df.apply(_remaining, axis=1)
    df = df[df["remaining_lim"] > 0].copy()
    if df.empty: return df

    # ── 7. SMART ALLOCATION (De fix voor de absurd hoge aantallen) ─────────
    # A. Hoeveel kun je betalen?
    max_aff = np.minimum((free_cash // df["buy_p"]).astype(int), df["remaining_lim"])
    
    # B. Market Share Rule: Max 25% van het uurs-volume kapen (minimaal 1)
    market_cap = np.maximum(1, (df["vol_use"] * 0.25).astype(int))

    # C. Whale Risk Limits: Hoe duurder, hoe strakker de inkoop cap
    def risk_cap(price):
        if price >= 50_000_000: return 1   # Boven 50m? Max 1 stuk kopen.
        if price >= 10_000_000: return 3   # Boven 10m? Max 3 stuks kopen.
        if price >=  2_000_000: return 8   # Boven 2m?  Max 8 stuks kopen.
        return 999_999_999                 # Goedkoper? Geen whale cap.

    df["risk_cap"] = df["buy_p"].apply(risk_cap)

    # De ECHTE Quantity is de allerlaagste van deze 3 caps.
    df["real_qty"] = np.minimum(max_aff, np.minimum(market_cap, df["risk_cap"]))
    df["real_qty"] = df["real_qty"].clip(lower=0)
    
    df = df[df["real_qty"] > 0].copy()
    if df.empty: return df

    # We overschrijven "qty" direct, zodat scanner.py automatisch klopt.
    df["qty"]         = df["real_qty"]
    df["real_profit"] = df["qty"] * df["margin"]  
    df["pot_profit"]  = df["real_profit"] # UI toont nu altijd de haalbare winst
    df["invest"]      = df["qty"] * df["buy_p"]

    # ── 8. Scores ──────────────────────────────────────────────────────────
    df["freshness"] = df.apply(lambda r: data_freshness(max(r["high_ts"] or 0, r["low_ts"] or 0)), axis=1)
    
    roi_decimal = df["margin"] / df["buy_p"]
    vol_score   = np.log10(df["vol_use"] + 1)
    depth_score = np.log10(df["ge_lim_fixed"] * df["margin"] + 1)
    df["smart_score"] = roi_decimal * vol_score * depth_score * df["freshness"]

    safe_cash = max(1, free_cash)
    df["portfolio_roi"] = (df["real_profit"] / safe_cash) * 100

    if not df.empty:
        max_port_roi = df["portfolio_roi"].max()
        max_item_roi = df["roi"].max()
        max_smart    = df["smart_score"].max()

        norm_port  = df["portfolio_roi"] / max_port_roi if max_port_roi > 0 else 0
        norm_item  = df["roi"]           / max_item_roi if max_item_roi > 0 else 0
        norm_smart = df["smart_score"]   / max_smart    if max_smart    > 0 else 0

        # Weging: 60% Portfolio groei, 25% ROI efficiëntie, 15% Data kwaliteit
        df["action_score"] = (0.60 * norm_port) + (0.25 * norm_item) + (0.15 * norm_smart)
    else:
        df["action_score"] = 0

    return df.reset_index(drop=True)
