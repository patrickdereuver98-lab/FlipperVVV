"""
OSRS GE Flip Advisor — Streamlit Dashboard
Gebaseerd op de Flipping Utilities RuneLite plugin logica
API: https://oldschool.runescape.wiki/w/RuneScape:Real-time_Prices
"""

import math
import time
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OSRS GE Flip Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── OSRS Theme CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=IM+Fell+English&display=swap');

:root {
    --bg-dark:      #130f08;
    --bg-panel:     #1e160a;
    --bg-card:      #261b0c;
    --border-gold:  #7a5c12;
    --border-gold2: #c8a232;
    --text-gold:    #f0c040;
    --text-light:   #e8d5a0;
    --text-dim:     #8a6e44;
    --green:        #4caf50;
    --red:          #e53935;
    --blue:         #42a5f5;
}

.stApp {
    background: var(--bg-dark);
    background-image: radial-gradient(ellipse at top, #241908 0%, #130f08 70%);
    color: var(--text-light);
    font-family: 'IM Fell English', serif;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1rem !important; max-width: 1440px; }

[data-testid="stSidebar"] {
    background: var(--bg-panel) !important;
    border-right: 2px solid var(--border-gold);
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stNumberInput label {
    color: var(--text-light) !important;
    font-family: 'IM Fell English', serif !important;
}

input[type="number"], input[type="text"] {
    background: #170f04 !important;
    border: 1.5px solid var(--border-gold) !important;
    border-radius: 4px !important;
    color: var(--text-gold) !important;
    font-family: 'IM Fell English', serif !important;
    font-size: 1rem !important;
}
input[type="number"]:focus, input[type="text"]:focus {
    border-color: var(--border-gold2) !important;
    box-shadow: 0 0 10px rgba(200,162,50,0.35) !important;
}
[data-baseweb="select"] > div {
    background: #170f04 !important;
    border-color: var(--border-gold) !important;
    color: var(--text-light) !important;
}
[data-baseweb="menu"] { background: #1e160a !important; }
[data-baseweb="option"] { color: var(--text-light) !important; }
[data-baseweb="option"]:hover { background: #2c1f0e !important; }

.stButton button {
    background: linear-gradient(180deg, #5c4200 0%, #321f00 100%) !important;
    border: 2px solid var(--border-gold2) !important;
    border-radius: 4px !important;
    color: var(--text-gold) !important;
    font-family: 'Cinzel', serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    transition: all 0.15s !important;
}
.stButton button:hover {
    background: linear-gradient(180deg, #7a5800 0%, #4a2e00 100%) !important;
    box-shadow: 0 0 14px rgba(200,162,50,0.45) !important;
}

[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-gold) !important;
    border-top: 2px solid var(--border-gold2) !important;
    border-radius: 6px !important;
    padding: 0.7rem 0.9rem !important;
}
[data-testid="stMetricLabel"] { color: var(--text-dim) !important; font-family: 'IM Fell English', serif !important; font-size: 0.82rem !important; }
[data-testid="stMetricValue"] { color: var(--text-gold) !important; font-family: 'Cinzel', serif !important; font-weight: 700 !important; }

hr { border: none !important; border-top: 1px solid var(--border-gold) !important; opacity: 0.45 !important; margin: 0.75rem 0 !important; }

.osrs-card {
    background: var(--bg-card);
    border: 1px solid var(--border-gold);
    border-left: 3px solid transparent;
    border-radius: 5px;
    padding: 0.65rem 0.9rem;
    margin-bottom: 0.4rem;
    transition: all 0.15s;
}
.osrs-card:hover { border-left-color: var(--border-gold2); background: #2e2010; }
.osrs-card.active { border-left-color: var(--text-gold); background: #322415; box-shadow: 0 0 12px rgba(200,162,50,0.2); }
.item-name { color: var(--text-gold); font-family: 'Cinzel', serif; font-size: 0.95rem; font-weight: 600; }
.item-meta { color: var(--text-dim); font-size: 0.78rem; margin-top: 1px; }
.stat-green { color: #66bb6a; font-weight: 600; }
.stat-gold  { color: var(--text-gold); }
.stat-blue  { color: #64b5f6; }
.badge-mem { background:#2d0e4a; color:#ce93d8; border:1px solid #6a1b9a; border-radius:3px; padding:1px 5px; font-size:0.68rem; }
.badge-f2p { background:#0a2e18; color:#69f0ae; border:1px solid #1b5e20; border-radius:3px; padding:1px 5px; font-size:0.68rem; }

.section-hdr {
    color: var(--text-gold);
    font-family: 'Cinzel', serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    padding-bottom: 3px;
    border-bottom: 1px solid var(--border-gold);
    margin: 0.8rem 0 0.5rem;
}

.page-title {
    font-family: 'Cinzel', serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-gold);
    text-shadow: 0 0 30px rgba(240,192,64,0.4), 0 2px 6px rgba(0,0,0,0.8);
    letter-spacing: 4px;
    text-align: center;
    margin-bottom: 0.1rem;
}
.page-sub {
    text-align: center;
    color: var(--text-dim);
    font-style: italic;
    font-size: 0.88rem;
    margin-bottom: 0.8rem;
}

.detail-title {
    color: var(--text-gold);
    font-family: 'Cinzel', serif;
    font-size: 1.5rem;
    font-weight: 700;
    text-shadow: 0 0 20px rgba(200,162,50,0.35);
}
.detail-examine { color: var(--text-dim); font-style: italic; font-size: 0.88rem; margin: 3px 0 8px; }

.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    border-bottom: 1px solid rgba(122,92,18,0.2);
    font-size: 0.9rem;
}
.stat-lbl { color: var(--text-dim); }
.stat-val { color: var(--text-gold); font-weight: 600; }

.price-box {
    text-align: center;
    padding: 0.75rem 0.5rem;
    border-radius: 6px;
    margin-bottom: 4px;
}
.pb-buy   { background:#0a2010; border:1px solid #1b5e20; }
.pb-sell  { background:#200a0a; border:1px solid #7f1010; }
.pb-marg  { background:#1a1100; border:1px solid #7f5200; }
.pb-label { font-size:0.72rem; letter-spacing:1.5px; text-transform:uppercase; margin-bottom:4px; }
.pb-value { font-family:'Cinzel',serif; font-size:1.15rem; font-weight:700; }
.pb-sub   { font-size:0.72rem; margin-top:2px; opacity:0.7; }

.flip-list { max-height: 70vh; overflow-y: auto; padding-right: 3px; scrollbar-width: thin; scrollbar-color: var(--border-gold) var(--bg-dark); }
.flip-list::-webkit-scrollbar { width: 5px; }
.flip-list::-webkit-scrollbar-track { background: var(--bg-dark); }
.flip-list::-webkit-scrollbar-thumb { background: var(--border-gold); border-radius: 3px; }

.rank-num {
    display: inline-flex; align-items: center; justify-content: center;
    width: 20px; height: 20px;
    background: #3d2d00;
    border: 1px solid var(--border-gold);
    border-radius: 50%;
    color: var(--text-gold);
    font-size: 0.65rem;
    font-weight: 700;
    font-family: 'Cinzel', serif;
    margin-right: 7px;
    flex-shrink: 0;
}

[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-gold) !important;
    border-radius: 6px !important;
}
[data-testid="stExpander"] summary { color: var(--text-gold) !important; font-family: 'IM Fell English', serif !important; }
[data-testid="stExpander"] p, [data-testid="stExpander"] li { color: var(--text-light) !important; }

.step-box {
    background: var(--bg-panel);
    border: 1px solid var(--border-gold);
    border-radius: 5px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.5rem;
}
.step-num { color: var(--border-gold2); font-family: 'Cinzel', serif; font-weight: 700; font-size: 0.78rem; letter-spacing: 1px; }
.step-text { color: var(--text-light); margin-top: 3px; font-size: 0.92rem; }
.highlight-gp { color: var(--text-gold); font-weight: 700; font-family: 'Cinzel', serif; }
.highlight-green { color: #66bb6a; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
GE_TAX_RATE        = 0.02
GE_TAX_CAP         = 5_000_000
MAX_PRICE_FOR_TAX  = 250_000_000
WIKI_HEADERS       = {"User-Agent": "OSRS-GE-Flip-Advisor/2.0 (streamlit; github.com)"}
BASE_API           = "prices.runescape.wiki/api/v1/osrs"
WIKI_ICON_URL      = "https://oldschool.runescape.wiki/images/{}"
WIKI_ITEM_URL      = "https://oldschool.runescape.wiki/w/{}"


# ── Plugin-exact GE Tax (GeTax.java mirror) ───────────────────────────────────
def ge_tax(sell_price: int) -> int:
    if sell_price >= MAX_PRICE_FOR_TAX:
        return GE_TAX_CAP
    return int(math.floor(sell_price * GE_TAX_RATE))

def net_sell(sell_price: int) -> int:
    return sell_price - ge_tax(sell_price)


# ── Formatters ────────────────────────────────────────────────────────────────
def fmt(v, short=False) -> str:
    if v is None: return "—"
    v = int(v)
    if short:
        if abs(v) >= 1_000_000_000: return f"{v/1e9:.2f}B"
        if abs(v) >= 1_000_000:     return f"{v/1e6:.2f}M"
        if abs(v) >= 1_000:         return f"{v/1e3:.1f}K"
        return f"{v:,}"
    if abs(v) >= 1_000_000_000: return f"{v/1e9:.3f}B gp"
    if abs(v) >= 1_000_000:     return f"{v/1e6:.2f}M gp"
    if abs(v) >= 1_000:         return f"{v/1e3:.1f}K gp"
    return f"{v:,} gp"

def fmtp(v) -> str: return f"{v:.2f}%"

def age_s(ts) -> str:
    if not ts: return "?"
    d = int(time.time()) - int(ts)
    if d < 60:   return f"{d}s"
    if d < 3600: return f"{d//60}m"
    return f"{d//3600}u"

def fmt_ts(ts) -> str:
    if not ts: return "—"
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%H:%M UTC")


# ── API fetchers (gecached) ───────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_mapping() -> dict:
    r = requests.get(f"{BASE_API}/mapping", headers=WIKI_HEADERS, timeout=12)
    r.raise_for_status()
    return {item["id"]: item for item in r.json()}

@st.cache_data(ttl=60, show_spinner=False)
def fetch_latest() -> dict:
    r = requests.get(f"{BASE_API}/latest", headers=WIKI_HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()["data"]

@st.cache_data(ttl=120, show_spinner=False)
def fetch_5m() -> dict:
    r = requests.get(f"{BASE_API}/5m", headers=WIKI_HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()["data"]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_1h() -> dict:
    r = requests.get(f"{BASE_API}/1h", headers=WIKI_HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()["data"]


# ── Core flip engine (Flipping Utilities logica) ──────────────────────────────
def compute_flips(mapping, latest, vol5m, vol1h, cash_stack,
                  min_margin, min_roi, min_vol, max_buy_price,
                  acc_type):
    rows = []
    for sid, px in latest.items():
        iid  = int(sid)
        info = mapping.get(iid)
        if not info:
            continue

        is_mem = info.get("members", False)
        if acc_type == "Alleen F2P"      and is_mem:  continue
        if acc_type == "Alleen Members"  and not is_mem: continue

        high    = px.get("high")
        low     = px.get("low")
        high_ts = px.get("highTime", 0)
        low_ts  = px.get("lowTime",  0)

        if not high or not low or high <= 0 or low <= 0:
            continue

        # Exact plugin strategie: koop op low+1, verkoop op high-1
        buy_p  = low  + 1
        sell_p = high - 1
        if sell_p <= buy_p:
            continue

        margin = net_sell(sell_p) - buy_p
        if margin < min_margin:
            continue

        roi = margin / buy_p * 100
        if roi < min_roi:
            continue

        if buy_p > max_buy_price:
            continue

        ge_lim = info.get("limit") or 0

        v5  = vol5m.get(sid, {})
        v1  = vol1h.get(sid, {})
        vol_5m  = (v5.get("highVolume") or 0) + (v5.get("lowVolume") or 0)
        vol_1h  = (v1.get("highVolume") or 0) + (v1.get("lowVolume") or 0)
        vol_use = vol_1h if vol_1h > 0 else vol_5m
        if vol_use < min_vol:
            continue

        max_aff = int(cash_stack // buy_p) if buy_p > 0 else 0
        qty     = min(max_aff, ge_lim) if ge_lim > 0 else min(max_aff, 50_000)
        if qty <= 0:
            continue

        rows.append({
            "id":        iid,
            "Naam":      info.get("name", "?"),
            "icon":      info.get("icon", ""),
            "examine":   info.get("examine", ""),
            "members":   is_mem,
            "buy_p":     buy_p,
            "sell_p":    sell_p,
            "tax":       ge_tax(sell_p),
            "margin":    margin,
            "roi":       roi,
            "ge_lim":    ge_lim,
            "qty":       qty,
            "pot_profit":qty * margin,
            "invest":    qty * buy_p,
            "vol_5m":    vol_5m,
            "vol_1h":    vol_1h,
            "high_ts":   high_ts,
            "low_ts":    low_ts,
            "lowalch":   info.get("lowalch") or 0,
            "highalch":  info.get("highalch") or 0,
        })

    return pd.DataFrame(rows)


# ── Session state init ────────────────────────────────────────────────────────
for k, v in [("sel_idx", 0), ("last_ref", 0), ("_map", {}), ("_lat", {}), ("_5m", {}), ("_1h", {})]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">⚔ &nbsp;GE FLIP ADVISOR&nbsp; ⚔</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Old School RuneScape · Grand Exchange · Real-time prijsdata via OSRS Wiki API</div>', unsafe_allow_html=True)


# ═══ SIDEBAR ══════════════════════════════════════════════════════════════════
with st.sidebar:

    st.markdown('<div class="section-hdr">💰 Cash Stack</div>', unsafe_allow_html=True)

    # Quick preset buttons
    presets = [("100K", 100_000), ("500K", 500_000), ("1M", 1_000_000), ("5M", 5_000_000),
               ("10M", 10_000_000), ("25M", 25_000_000), ("50M", 50_000_000), ("100M", 100_000_000)]
    pr = st.columns(4)
    for i, (lbl, amt) in enumerate(presets):
        with pr[i % 4]:
            if st.button(lbl, key=f"pre_{lbl}", use_container_width=True):
                st.session_state["_cash_val"] = amt

    cash_stack = st.number_input(
        "Bedrag", min_value=1_000, max_value=2_147_483_647,
        value=st.session_state.get("_cash_val", 10_000_000),
        step=500_000, format="%d", label_visibility="collapsed",
    )
    st.markdown(f'<div style="color:var(--text-gold);font-family:Cinzel,serif;font-size:1rem;text-align:center;margin-bottom:4px">💼 {fmt(cash_stack)}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">⚙️ Filters</div>', unsafe_allow_html=True)

    acc_type = st.selectbox("Account type", ["F2P + Members", "Alleen Members", "Alleen F2P"])
    sort_opt = st.selectbox("Sorteren op",  ["Pot. winst", "ROI %", "Margin", "Volume (1u)", "Volume (5m)"])

    c1, c2 = st.columns(2)
    with c1: min_margin = st.number_input("Min margin (gp)", 0, 500_000, 100, step=50)
    with c2: min_roi    = st.number_input("Min ROI (%)",     0.0, 50.0, 0.1, step=0.1, format="%.1f")
    c3, c4 = st.columns(2)
    with c3: min_vol    = st.number_input("Min vol (1u)",    0, 50_000, 2, step=1)
    with c4: max_bp_pct = st.number_input("Max item prijs (% van cash)", 1, 100, 100, step=5)

    max_buy_price = int(cash_stack * max_bp_pct / 100)
    st.caption(f"Max inkoopprijs: {fmt(max_buy_price, short=True)}")

    st.markdown('<div class="section-hdr">🔄 Verversen</div>', unsafe_allow_html=True)
    do_refresh = st.button("⚡  Data vernieuwen", use_container_width=True)
    if st.session_state.last_ref:
        st.caption(f"Ververst: {fmt_ts(st.session_state.last_ref)}")

    st.markdown("---")
    st.markdown(
        '<div style="color:#4a3418;font-size:0.72rem;text-align:center;font-style:italic;line-height:1.6">'
        'Data: OSRS Wiki Prices API<br>GE Tax: 2% (max 5M gp) per verkoop<br>'
        'Prijzen zijn live schattingen<br>Doe altijd een margin check in-game'
        '</div>', unsafe_allow_html=True,
    )


# ═══ DATA LADEN ═══════════════════════════════════════════════════════════════
if do_refresh:
    for fn in [fetch_mapping, fetch_latest, fetch_5m, fetch_1h]:
        fn.clear()

if do_refresh or not st.session_state["_map"]:
    with st.spinner("📡 Prijsdata ophalen van OSRS Wiki…"):
        try:
            st.session_state["_map"] = fetch_mapping()
            st.session_state["_lat"] = fetch_latest()
            st.session_state["_5m"]  = fetch_5m()
            st.session_state["_1h"]  = fetch_1h()
            st.session_state["last_ref"] = int(time.time())
        except Exception as e:
            st.error(f"⚠️ API-fout: {e}")
            st.stop()

# Herbereken bij elke filter-wijziging
SORT_MAP = {"Pot. winst": "pot_profit", "ROI %": "roi", "Margin": "margin",
            "Volume (1u)": "vol_1h", "Volume (5m)": "vol_5m"}

df = compute_flips(
    st.session_state["_map"], st.session_state["_lat"],
    st.session_state["_5m"],  st.session_state["_1h"],
    cash_stack, min_margin, min_roi, min_vol, max_buy_price, acc_type,
)

if df.empty:
    st.warning("Geen items gevonden. Pas de filters in de sidebar aan.")
    st.stop()

df = df.sort_values(SORT_MAP[sort_opt], ascending=False).reset_index(drop=True)


# ═══ KPI RIJ ══════════════════════════════════════════════════════════════════
best = df.iloc[0]
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("🏆 Beste flip",       best["Naam"][:20] + ("…" if len(best["Naam"]) > 20 else ""))
m2.metric("💰 Max pot. winst",   fmt(int(best["pot_profit"]), short=True))
m3.metric("📈 Beste ROI",        fmtp(best["roi"]))
m4.metric("📊 Items gevonden",   f"{len(df):,}")
m5.metric("🕐 Data leeftijd",    age_s(st.session_state["last_ref"]))

st.markdown("<hr>", unsafe_allow_html=True)


# ═══ HOOFD LAYOUT: lijst links | detail rechts ════════════════════════════════
lcol, rcol = st.columns([1, 1.7], gap="medium")


# ─── LINKS: Flip lijst ────────────────────────────────────────────────────────
with lcol:
    st.markdown('<div class="section-hdr">📋 Top Flips</div>', unsafe_allow_html=True)

    srch = st.text_input("🔍", placeholder="Zoek item…", label_visibility="collapsed", key="search")
    if srch:
        view = df[df["Naam"].str.lower().str.contains(srch.lower(), na=False)].reset_index(drop=True)
    else:
        view = df.head(100).reset_index(drop=True)

    st.caption(f"{len(view)} items")

    # Render item kaarten als HTML (visueel)
    cards_html = '<div class="flip-list">'
    for i, r in view.iterrows():
        active = "active" if i == st.session_state.sel_idx else ""
        badge  = '<span class="badge-mem">P2P</span>' if r["members"] else '<span class="badge-f2p">F2P</span>'
        cards_html += f"""
<div class="osrs-card {active}">
  <div style="display:flex;align-items:center">
    <span class="rank-num">{i+1}</span>
    <div style="flex:1;min-width:0">
      <div class="item-name" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{r['Naam']} {badge}</div>
      <div class="item-meta">{fmt(r['buy_p'],short=True)} → {fmt(r['sell_p'],short=True)} &nbsp;|&nbsp; vol {r['vol_1h']:,}/u</div>
    </div>
    <div style="text-align:right;flex-shrink:0;padding-left:8px">
      <div class="stat-green" style="font-size:0.92rem">{fmt(r['margin'],short=True)}</div>
      <div style="color:var(--text-dim);font-size:0.74rem">{fmtp(r['roi'])} ROI</div>
    </div>
  </div>
  <div style="display:flex;gap:14px;margin-top:5px;font-size:0.76rem;color:var(--text-dim)">
    <span>🎯 <span class="stat-gold">{fmt(r['pot_profit'],short=True)}</span></span>
    <span>📦 <span class="stat-blue">{int(r['qty']):,}×</span></span>
    <span>💸 {fmt(r['invest'],short=True)}</span>
  </div>
</div>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)

    # Echte Streamlit select-buttons
    st.markdown('<div class="section-hdr" style="margin-top:0.6rem">Selecteer item</div>', unsafe_allow_html=True)
    for i, r in view.iterrows():
        label = f"#{i+1}  {r['Naam']}  ·  {fmt(r['margin'],short=True)}  ·  {fmtp(r['roi'])}"
        if st.button(label, key=f"btn_{i}", use_container_width=True):
            st.session_state.sel_idx = i
            st.rerun()


# ─── RECHTS: Item detail ───────────────────────────────────────────────────────
with rcol:
    si = min(st.session_state.sel_idx, len(view) - 1)
    r  = view.iloc[si]

    st.markdown('<div class="section-hdr">🔎 Item detail</div>', unsafe_allow_html=True)

    # Header: icon + naam
    icon_url = WIKI_ICON_URL.format(r["icon"].replace(" ", "_")) if r["icon"] else None
    wiki_url = WIKI_ITEM_URL.format(r["Naam"].replace(" ", "_"))

    hd1, hd2 = st.columns([1, 6])
    with hd1:
        if icon_url:
            try:
                st.image(icon_url, width=60)
            except Exception:
                st.markdown("🗡️", unsafe_allow_html=True)
    with hd2:
        badge = '<span class="badge-mem">Members Only</span>' if r["members"] else '<span class="badge-f2p">Free to Play</span>'
        st.markdown(
            f'<div class="detail-title">{r["Naam"]}</div>'
            f'<div style="margin:3px 0">{badge}</div>'
            f'<div class="detail-examine">{r["examine"]}</div>'
            f'<a href="{wiki_url}" target="_blank" style="color:var(--border-gold2);font-size:0.8rem">📖 OSRS Wiki →</a>',
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── 3 prijs-boxes ──
    pb1, pb2, pb3 = st.columns(3)
    with pb1:
        st.markdown(
            f'<div class="price-box pb-buy">'
            f'<div class="pb-label" style="color:#69f0ae">📥 Inkoopprijs</div>'
            f'<div class="pb-value" style="color:#66bb6a">{fmt(r["buy_p"])}</div>'
            f'<div class="pb-sub" style="color:#3a7a3a">low + 1 gp</div>'
            f'</div>', unsafe_allow_html=True,
        )
    with pb2:
        st.markdown(
            f'<div class="price-box pb-sell">'
            f'<div class="pb-label" style="color:#ff8a80">📤 Verkoopprijs</div>'
            f'<div class="pb-value" style="color:#ef5350">{fmt(r["sell_p"])}</div>'
            f'<div class="pb-sub" style="color:#7a2a2a">high − 1 gp</div>'
            f'</div>', unsafe_allow_html=True,
        )
    with pb3:
        st.markdown(
            f'<div class="price-box pb-marg">'
            f'<div class="pb-label" style="color:#ffe082">💰 Netto margin</div>'
            f'<div class="pb-value" style="color:#ffd54f">{fmt(r["margin"])}</div>'
            f'<div class="pb-sub" style="color:#7a6010">{fmtp(r["roi"])} ROI</div>'
            f'</div>', unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 2 kolommen stats ──
    sc1, sc2 = st.columns(2)

    with sc1:
        st.markdown('<div class="section-hdr" style="font-size:0.72rem">📊 Flip stats</div>', unsafe_allow_html=True)
        for lbl, val in [
            ("GE Belasting / item",  fmt(r["tax"])),
            ("GE Koop limiet",       f"{int(r['ge_lim']):,}×"),
            ("Jij koopt (qty)",      f"{int(r['qty']):,}×"),
            ("Totale investering",   fmt(r["invest"])),
            ("Potentiële winst",     f'<span class="stat-green">{fmt(r["pot_profit"])}</span>'),
            ("Winst per item",       fmt(r["margin"])),
        ]:
            st.markdown(
                f'<div class="stat-row"><span class="stat-lbl">{lbl}</span>'
                f'<span class="stat-val">{val}</span></div>',
                unsafe_allow_html=True,
            )

    with sc2:
        st.markdown('<div class="section-hdr" style="font-size:0.72rem">📈 Volume & timing</div>', unsafe_allow_html=True)
        for lbl, val in [
            ("Vol. (5 min)",     f"{int(r['vol_5m']):,} trades"),
            ("Vol. (1 uur)",     f"{int(r['vol_1h']):,} trades"),
            ("Sell gezien",      age_s(r["high_ts"])),
            ("Buy gezien",       age_s(r["low_ts"])),
            ("Low alch",         fmt(r["lowalch"]) if r["lowalch"] else "—"),
            ("High alch",        fmt(r["highalch"]) if r["highalch"] else "—"),
        ]:
            st.markdown(
                f'<div class="stat-row"><span class="stat-lbl">{lbl}</span>'
                f'<span class="stat-val">{val}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stap-voor-stap flip instructies ──
    with st.expander("📖 Stap-voor-stap flip instructie"):
        st.markdown(
            f"""
<div class="step-box">
  <div class="step-num">STAP 1 — MARGIN CHECK</div>
  <div class="step-text">
    Koop <strong>1×</strong> <span class="highlight-gp">{r['Naam']}</span> voor max prijs (insta-buy).<br>
    Verkoop daarna voor <strong>1 gp</strong> (insta-sell). Noteer de prijzen.
  </div>
</div>
<div class="step-box">
  <div class="step-num">STAP 2 — KOOP ORDER PLAATSEN</div>
  <div class="step-text">
    Zet een buy order voor <span class="highlight-gp">{int(r['qty']):,}×</span> op:<br>
    → Prijs: <span class="highlight-gp">{fmt(r['buy_p'])}</span> per stuk<br>
    → Totale investering: <span class="highlight-gp">{fmt(r['invest'])}</span>
  </div>
</div>
<div class="step-box">
  <div class="step-num">STAP 3 — WACHT OP VULLING</div>
  <div class="step-text">
    Wacht tot de order gevuld is. Volume van dit item: <span class="highlight-gp">{int(r['vol_1h']):,}/u</span>.
    GE limiet: <span class="highlight-gp">{int(r['ge_lim']):,}×</span> per 4 uur.
  </div>
</div>
<div class="step-box">
  <div class="step-num">STAP 4 — VERKOOP ORDER PLAATSEN</div>
  <div class="step-text">
    Zet een sell order voor <span class="highlight-gp">{int(r['qty']):,}×</span> op:<br>
    → Prijs: <span class="highlight-gp">{fmt(r['sell_p'])}</span> per stuk<br>
    → GE belasting: <span style="color:#ef5350">{fmt(int(r['tax'])*int(r['qty']))}</span> totaal
  </div>
</div>
<div class="step-box" style="border-color:var(--border-gold2)">
  <div class="step-num" style="color:var(--text-gold)">✅ NETTO WINST</div>
  <div class="step-text" style="font-size:1.05rem">
    <span class="highlight-green">{fmt(r['pot_profit'])}</span>
    &nbsp;·&nbsp; {fmtp(r['roi'])} ROI
    &nbsp;·&nbsp; {fmt(r['margin'])} per item
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

    # ── Navigatie ──
    st.markdown("<br>", unsafe_allow_html=True)
    nv1, nv2, nv3 = st.columns([1, 1.2, 1])
    with nv1:
        if si > 0 and st.button("⬅️ Vorige", use_container_width=True):
            st.session_state.sel_idx = si - 1
            st.rerun()
    with nv2:
        st.markdown(
            f'<div style="text-align:center;color:var(--text-dim);padding-top:7px;font-size:0.82rem">'
            f'#{si+1} van {len(view)}</div>',
            unsafe_allow_html=True,
        )
    with nv3:
        if si < len(view) - 1 and st.button("Volgende ➡️", use_container_width=True):
            st.session_state.sel_idx = si + 1
            st.rerun()


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;color:#3a2810;font-size:0.75rem;font-style:italic;padding:4px">'
    'OSRS GE Flip Advisor · Data via prices.runescape.wiki · '
    'GE tax: 2% per verkoop (max 5.000.000 gp) · '
    'Prijzen zijn inschattingen op basis van real-time transacties — doe altijd een margin check in-game'
    '</div>',
    unsafe_allow_html=True,
)
