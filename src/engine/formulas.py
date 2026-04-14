"""
formulas.py — Pure math utilities for OSRS GE calculations.
No Streamlit imports. All functions are deterministic and testable.
"""
import math
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

# ── Constants ─────────────────────────────────────────────────────────────────
GE_TAX_RATE       = 0.02
GE_TAX_CAP        = 5_000_000
GE_TAX_THRESHOLD  = 500_000_000
GE_COOLDOWN_HOURS = 4          # GE buy limit resets every 4 hours
WIKI_ICON_URL     = "https://oldschool.runescape.wiki/images/{}"
WIKI_ITEM_URL     = "https://oldschool.runescape.wiki/w/{}"


# ── Parsing ───────────────────────────────────────────────────────────────────
def parse_gp(val) -> int:
    """Parse '25m', '1.5b', '500k', or plain integers into a GP integer."""
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, float):
        return int(val)
    if not val:
        return 0
    val = str(val).lower().strip().replace(",", "").replace(" ", "").replace("gp", "")
    multipliers = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    for suffix, mult in multipliers.items():
        if val.endswith(suffix):
            try:
                return int(float(val[:-1]) * mult)
            except ValueError:
                return 0
    try:
        return int(float(val))
    except ValueError:
        return 0


# ── Tax ───────────────────────────────────────────────────────────────────────
def ge_tax(sell_price: int) -> int:
    """GE 1% transaction tax, capped at 5M for items ≥ 500M."""
    if sell_price >= GE_TAX_THRESHOLD:
        return GE_TAX_CAP
    return int(math.floor(sell_price * GE_TAX_RATE))


def ge_tax_vectorized(sell_series: pd.Series) -> pd.Series:
    """Vectorized GE tax for entire DataFrame columns."""
    return np.where(
        sell_series >= GE_TAX_THRESHOLD,
        GE_TAX_CAP,
        np.floor(sell_series * GE_TAX_RATE).astype(int),
    )


# ── Formatting ────────────────────────────────────────────────────────────────
def fmt_gp(v, short: bool = False) -> str:
    """Format an integer as a GP string. Short mode: 1.23M / 456.7K."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    v = int(v)
    if short:
        if abs(v) >= 1_000_000_000:
            return f"{v / 1e9:.2f}B"
        if abs(v) >= 1_000_000:
            return f"{v / 1e6:.2f}M"
        if abs(v) >= 1_000:
            return f"{v / 1e3:.1f}K"
        return f"{v:,}"
    return f"{v:,}"


def fmt_pct(v: float) -> str:
    """Format a float as a percentage string."""
    return f"{v:.2f}%"


def fmt_age(ts) -> str:
    """Human-readable age string from a Unix timestamp."""
    if not ts or (isinstance(ts, float) and math.isnan(ts)):
        return "?"
    age = int(time.time()) - int(ts)
    if age < 0:
        return "now"
    if age < 60:
        return f"{age}s"
    if age < 3_600:
        return f"{age // 60}m"
    return f"{age // 3_600}h"


def fmt_ts(ts) -> str:
    """Format a Unix timestamp as HH:MM UTC."""
    if not ts:
        return "—"
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%H:%M UTC")


def age_seconds(ts) -> int:
    """Return seconds since a Unix timestamp. Returns 999_999 for missing."""
    if not ts or (isinstance(ts, float) and math.isnan(ts)):
        return 999_999
    return max(0, int(time.time()) - int(ts))


def data_freshness(ts) -> float:
    """
    Returns a freshness multiplier [0.25, 1.0].
    Fresh data (< 5 min) = 1.0. Decays linearly to 0.25 at 2 hours.
    Stale data penalises the Smart Score so old prices rank lower.
    """
    age = age_seconds(ts)
    if age <= 300:      # ≤ 5 min: fully fresh
        return 1.0
    if age >= 7_200:    # ≥ 2 h: heavily penalised
        return 0.25
    # Linear decay between 5 min and 2 h
    return 1.0 - 0.75 * ((age - 300) / (7_200 - 300))


# ── GE Cooldown ───────────────────────────────────────────────────────────────
def cooldown_remaining_qty(cooldown_entry: dict) -> int:
    """
    Returns how many units are still on cooldown for a given item.
    The GE buy limit resets every 4 hours from the time of first purchase.
    """
    if not cooldown_entry:
        return 0
    ts = cooldown_entry.get("timestamp", 0)
    elapsed_hours = (time.time() - ts) / 3_600
    if elapsed_hours >= GE_COOLDOWN_HOURS:
        return 0   # Fully reset
    return cooldown_entry.get("qty", 0)


# ── Trade Evaluation ──────────────────────────────────────────────────────────
def evaluate_active_flip(
    my_buy: int, my_sell: int, live_low: int, live_high: int
) -> tuple[list, int]:
    """
    Compare your open trade prices against live market data.
    Returns (status_list, current_market_margin).
    """
    statuses = []
    if live_low > my_buy:
        statuses.append(("OUTBID",    "Verhoog buy-offer",  live_low + 1))
    if live_high < my_sell:
        statuses.append(("UNDERCUT",  "Verlaag sell-offer", live_high - 1))

    current_margin = (live_high - 1) - ge_tax(live_high - 1) - (live_low + 1)
    if current_margin <= 0:
        statuses.append(("ABORT",     "Margin gecrasht!",   None))
    if not statuses:
        statuses.append(("OK",        "Positie competitief", None))

    return statuses, current_margin

def parse_osrs_gp(val) -> int:
    """
    Slimme parser voor OSRS GP. 
    Zet strings zoals '2.5b', '100m', of '500k' direct om in integers.
    """
    if isinstance(val, int): 
        return val
    if not val: 
        return 0
        
    val = str(val).lower().replace(',', '').replace(' ', '')
    multipliers = {'k': 1e3, 'm': 1e6, 'b': 1e9}
    
    for suffix, mult in multipliers.items():
        if val.endswith(suffix):
            try: 
                return int(float(val[:-1]) * mult)
            except ValueError: 
                return 0
                
    try: 
        return int(float(val))
    except ValueError: 
        return 0
    
