"""
core.py — Vectorized Pandas computation engine.
Nu inclusief "Budget-First" Portfolio ROI logica.
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
    min_vol:      int   = 10,
    min_roi_pct:  float = 0.20,
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

    # ── 2. Filters (Account & Sector) ──────────────────────────────────────────
    if acc_type == "Alleen F2P": df = df[~df["members"]].copy()
    elif acc_type == "Alleen Members": df = df[df["members"]].copy()
    
    if sector == "High-Volume Supplies":
        df = df[(df["vol_1h"] >= 1000) & (df["low"] <= 2_000_000)].copy()
    elif sector == "High-Value Gear":
        df = df[(df["low"] >= 2_000_000)].copy()

    if df.empty: return df

    # ── 3. Prijzen & Overrides ──────────────────────────────────────────────────
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
    if df.empty: return df

    # ── 4. Tax & Netto Winst ──────────────────────────────────────────────────
    df["tax"]    = ge_tax_vectorized(df["sell_p"])
    # Netto Marge (Fiscaal gezuiverd)
    df["margin"] = df["sell_p"] - df["tax"] - df["buy_p"]

    # Ruisfilter: Negeer micro-marges als je extreem veel geld hebt
    effective_min = max(min_margin, int(free_cash * 0.00002)) if free_cash > 50_000_000 else min_margin
    df = df[df["margin"] >= effective_min].copy()

    # ── 5. Basis ROI & Volume ──────────────────────────────────────────────────
    df["roi"] = (df["margin"] / df["buy_p"]) * 100
    df = df[df["roi"] >= min_roi_pct].copy()

    df["vol_use"] = np.where(df["vol_1h"] > 0, df["vol_1h"], df["vol_5m"] * 3)
    df = df[df["vol_use"] >= min_vol].copy()

    # ── 6. GE Limieten & Cooldowns ───────────────────────────────────────────
    df["ge_lim_fixed"] = np.where(df["ge_lim"] > 0, df["ge_lim"], 50_000)
    df["remaining_lim"] = df.apply(lambda r: max(0, int(r["ge_lim_fixed"]) - cooldown_remaining_qty(cooldowns.get(str(r["id"]), {}))), axis=1)
    df = df[df["remaining_lim"] > 0].copy()

    # ── 7. Budget-First Allocatie & Volume Capping ─────────────────────────
    # Hoeveel KUNNEN we kopen met ONS BUDGET?
    if free_cash > 0:
        df["max_aff"] = np.minimum((free_cash // df["buy_p"]).astype(int), df["remaining_lim"])
    else:
        df["max_aff"] = 0

    df["qty"] = df["max_aff"].clip(lower=0)
    
    # Hoeveel GAAN we er echt kopen in een uur? (Volume Limit)
    df["real_qty"] = np.minimum(df["qty"], df["vol_use"]) 

    # Financiële impact op ONZE portemonnee
    df["pot_profit"]  = df["qty"] * df["margin"]      
    df["real_profit"] = df["real_qty"] * df["margin"]  
    df["invest"]      = df["real_qty"] * df["buy_p"]

    df["freshness"] = df.apply(lambda r: data_freshness(max(r["high_ts"] or 0, r["low_ts"] or 0)), axis=1)

    # ── 8. De Eindbaas Scores ────────────────────────────────────────────────
    # Smart Score (voor datakwaliteit)
    roi_decimal = df["margin"] / df["buy_p"]
    vol_score   = np.log10(df["vol_use"] + 1)
    depth_score = np.log10(df["ge_lim_fixed"] * df["margin"] + 1)
    df["smart_score"] = roi_decimal * vol_score * depth_score * df["freshness"]

    # BUDGET-FIRST METRIC: Portfolio ROI
    # Hoeveel procent groeit onze HELE cash stack met deze ene slot?
    safe_cash = max(1, free_cash)
    df["portfolio_roi"] = (df["real_profit"] / safe_cash) * 100

    if not df.empty:
        max_port_roi    = df["portfolio_roi"].max()
        max_item_roi    = df["roi"].max()
        max_smart       = df["smart_score"].max()

        norm_port = df["portfolio_roi"] / max_port_roi if max_port_roi > 0 else 0
        norm_item = df["roi"]           / max_item_roi if max_item_roi > 0 else 0
        norm_smart= df["smart_score"]   / max_smart    if max_smart > 0 else 0

        # WEGING:
        # 60% Portfolio ROI: (Kijkt EERST naar je budget, dwingt hoogste cash winst af o.b.v. realistisch volume)
        # 25% Item ROI: (Beschermt je tegen items die je héle budget opslokken voor nauwelijks winst - de 'Venator Bow Trap')
        # 15% Smart Score: (Bewaakt de versheid en diepte van de data)
        df["action_score"] = (0.60 * norm_port) + (0.25 * norm_item) + (0.15 * norm_smart)
    else:
        df["action_score"] = 0

    df = df[df["buy_p"] > 0].copy()
    return df.reset_index(drop=True)
