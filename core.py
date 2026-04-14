import time
import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone

GE_TAX_RATE = 0.01
WIKI_ICON_URL = "https://oldschool.runescape.wiki/images/{}"
WIKI_ITEM_URL = "https://oldschool.runescape.wiki/w/{}"

def parse_osrs_gp(val) -> int:
    # Nu robuuster: accepteert zowel strings als integers
    if isinstance(val, int): return val
    if not val: return 0
    val = str(val).lower().replace(',', '').replace(' ', '')
    multipliers = {'k': 1e3, 'm': 1e6, 'b': 1e9}
    for suffix, mult in multipliers.items():
        if val.endswith(suffix):
            try: return int(float(val[:-1]) * mult)
            except: return 0
    try: return int(float(val))
    except: return 0

def ge_tax(sell_price: int) -> int:
    if sell_price >= 500_000_000: return 5_000_000
    return int(math.floor(sell_price * GE_TAX_RATE))

def fmt(v, short=False) -> str:
    if pd.isna(v) or v is None: return "—"
    v = int(v)
    if short:
        if abs(v) >= 1_000_000_000: return f"{v/1e9:.2f}B"
        if abs(v) >= 1_000_000:     return f"{v/1e6:.2f}M"
        if abs(v) >= 1_000:         return f"{v/1e3:.1f}K"
        return f"{v:,}"
    return f"{v:,}"

def fmtp(v) -> str: return f"{v:.2f}%"

def get_age_seconds(ts) -> int:
    if not ts or pd.isna(ts): return 999999
    return int(time.time()) - int(ts)

def age_s(ts) -> str:
    d = get_age_seconds(ts)
    if d == 999999: return "?"
    if d < 60: return f"{d}s"
    if d < 3600: return f"{d//60}m"
    return f"{d//3600}u"

def fmt_ts(ts) -> str:
    if not ts: return "—"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M UTC")

def evaluate_active_flip(my_buy, my_sell, live_low, live_high):
    status = []
    if live_low > my_buy: status.append(("🔴 OUTBID", "Verhoog buy-offer", live_low + 1))
    if live_high < my_sell: status.append(("🔴 UNDERCUT", "Verlaag sell-offer", live_high - 1))
    
    current_margin = (live_high - 1) - ge_tax(live_high - 1) - (live_low + 1)
    if current_margin <= 0: status.append(("🚨 ABORT", "Margin is gecrasht!", None))
    if not status: status.append(("🟢 PERFECT", "Positie is competitief", None))
    return status, current_margin

def compute_flips_vectorized(mapping, latest, vol5m, vol1h, free_cash, acc_type, active_cooldowns, manual_overrides, min_margin=100, min_vol=5):
    # Hardcoded background filters voor een schone UI
    min_roi = 0.1 
    max_buy_price = free_cash # Je mag in theorie je hele stack aan 1 item uitgeven

    # 1. Razendsnelle extractie naar platte data
    data = []
    for sid, px in latest.items():
        iid = int(sid)
        info = mapping.get(iid)
        if not info or not px.get('high') or not px.get('low'): continue
        
        data.append({
            'id': iid, 'Naam': info.get('name', '?'), 'icon': info.get('icon', ''),
            'examine': info.get('examine', ''), 'members': info.get('members', False),
            'ge_lim': info.get('limit', 0), 'high': px['high'], 'low': px['low'],
            'high_ts': px.get('highTime', 0), 'low_ts': px.get('lowTime', 0),
            'vol_5m': vol5m.get(sid, {}).get('highPriceVolume', 0) + vol5m.get(sid, {}).get('lowPriceVolume', 0),
            'vol_1h': vol1h.get(sid, {}).get('highPriceVolume', 0) + vol1h.get(sid, {}).get('lowPriceVolume', 0)
        })

    if not data: return pd.DataFrame()
    df = pd.DataFrame(data)

    # 2. Vectorized Filters & Overrides
    if acc_type == "Alleen F2P": df = df[~df['members']]
    elif acc_type == "Alleen Members": df = df[df['members']]

    df['buy_p'] = df['low'] + 1
    df['sell_p'] = df['high'] - 1
    df['has_override'] = False

    if manual_overrides:
        for iid_str, ov in manual_overrides.items():
            mask = df['id'] == int(iid_str)
            if mask.any():
                df.loc[mask, 'buy_p'] = ov['buy']
                df.loc[mask, 'sell_p'] = ov['sell']
                df.loc[mask, 'has_override'] = True

    df = df[df['sell_p'] > df['buy_p']]

    # 3. Vectorized Math (Fiscaal & Liquiditeit)
    df['tax'] = np.where(df['sell_p'] >= 500_000_000, 5_000_000, np.floor(df['sell_p'] * GE_TAX_RATE).astype(int))
    df['margin'] = df['sell_p'] - df['tax'] - df['buy_p']
    
    smart_min_margin = max(min_margin, int(free_cash * 0.00001)) if free_cash > 10_000_000 else min_margin
    df = df[df['margin'] >= smart_min_margin]

    df['roi'] = (df['margin'] / df['buy_p']) * 100
    df = df[(df['roi'] >= min_roi) & (df['buy_p'] <= max_buy_price)]

    df['vol_use'] = np.where(df['vol_1h'] > 0, df['vol_1h'], df['vol_5m'])
    df = df[df['vol_use'] >= min_vol]

    used_qty_series = df['id'].astype(str).map(lambda x: active_cooldowns.get(x, {}).get('qty', 0)).fillna(0)
    df['ge_lim_fixed'] = np.where(df['ge_lim'] > 0, df['ge_lim'], 50_000)
    df['remaining_lim'] = df['ge_lim_fixed'] - used_qty_series
    
    df = df[df['remaining_lim'] > 0]
    df['max_aff'] = (free_cash // df['buy_p']).astype(int)
    df['qty'] = df[['max_aff', 'remaining_lim']].min(axis=1)
    df = df[df['qty'] > 0]

    df['pot_profit'] = df['qty'] * df['margin']
    df['invest'] = df['qty'] * df['buy_p']
    df['smart_score'] = df['pot_profit'] * (df['roi'] / 100) * np.log10(df['vol_use'] + 1)

    return df
