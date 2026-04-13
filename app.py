"""
app.py  ←  Streamlit entry point
OSRS GE Flip Advisor

Run with:
    streamlit run app.py

The app is split into clean layers:
    config.py          — all constants
    api/osrs_wiki.py   — OSRS Wiki Prices API client
    core/ge_tax.py     — GE tax calculation (mirror of GeTax.java)
    core/flip_engine.py — flip opportunity engine
    ui/theme.py        — OSRS CSS theme
    ui/sidebar.py      — sidebar with filters
    ui/flip_list.py    — left-column item list
    ui/item_detail.py  — right-column detail panel
    utils/formatters.py — GP / pct / timestamp formatters
"""

import streamlit as st

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="OSRS GE Flip Advisor",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Local imports ─────────────────────────────────────────────────────────────
from api       import fetch_all, clear_cache
from core      import compute_flips, sort_flips
from ui        import inject_css, render_sidebar, render_flip_list, render_item_detail
from utils     import fmt_gp, fmt_pct, age_short

# ── Theme ─────────────────────────────────────────────────────────────────────
inject_css()

# ── Session state defaults ────────────────────────────────────────────────────
defaults = {
    "sel_idx":    0,
    "last_ref":   0,
    "_map": {},
    "_lat": {},
    "_5m":  {},
    "_1h":  {},
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">⚔ &nbsp;GE FLIP ADVISOR&nbsp; ⚔</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">'
    'Old School RuneScape · Grand Exchange · Real-time prijsdata via OSRS Wiki API'
    '</div>',
    unsafe_allow_html=True,
)

# ── Sidebar (returns user settings) ──────────────────────────────────────────
settings = render_sidebar(last_refresh=st.session_state["last_ref"])

# ── Data fetch ────────────────────────────────────────────────────────────────
if settings["do_refresh"]:
    clear_cache()
    st.session_state["_map"] = {}   # force reload below

if not st.session_state["_map"]:
    with st.spinner("📡 Prijsdata ophalen van OSRS Wiki…"):
        try:
            mapping, latest, vol5m, vol1h = fetch_all()
            st.session_state["_map"]    = mapping
            st.session_state["_lat"]    = latest
            st.session_state["_5m"]     = vol5m
            st.session_state["_1h"]     = vol1h
            st.session_state["last_ref"] = __import__("time").time()
        except Exception as exc:
            st.error(f"⚠️ API-fout: {exc}")
            st.stop()

# ── Compute flips (recalculated on every filter change) ───────────────────────
df = compute_flips(
    mapping       = st.session_state["_map"],
    latest        = st.session_state["_lat"],
    vol5m         = st.session_state["_5m"],
    vol1h         = st.session_state["_1h"],
    cash_stack    = settings["cash_stack"],
    min_margin    = settings["min_margin"],
    min_roi       = settings["min_roi"],
    min_vol       = settings["min_vol"],
    max_buy_price = settings["max_buy_price"],
    acc_type      = settings["acc_type"],
)

if df.empty:
    st.warning("Geen items gevonden met de huidige filters. Pas de filters in de sidebar aan.")
    st.stop()

df = sort_flips(df, settings["sort_by"])

# ── KPI row ───────────────────────────────────────────────────────────────────
best = df.iloc[0]
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("🏆 Beste flip",      best["Naam"][:22] + ("…" if len(best["Naam"]) > 22 else ""))
k2.metric("💰 Max pot. winst",  fmt_gp(int(best["pot_profit"]), short=True))
k3.metric("📈 Beste ROI",       fmt_pct(best["roi"]))
k4.metric("📊 Items gevonden",  f"{len(df):,}")
k5.metric("🕐 Data leeftijd",   age_short(st.session_state["last_ref"]))

st.markdown("<hr>", unsafe_allow_html=True)

# ── Main layout ───────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.7], gap="medium")

with left_col:
    new_idx = render_flip_list(df, selected_idx=st.session_state["sel_idx"])
    if new_idx is not None:
        st.session_state["sel_idx"] = new_idx
        st.rerun()

with right_col:
    updated_idx = render_item_detail(df, idx=st.session_state["sel_idx"])
    if updated_idx != st.session_state["sel_idx"]:
        st.session_state["sel_idx"] = updated_idx
        st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;color:#3a2810;font-size:0.72rem;'
    'font-style:italic;padding:4px">'
    'OSRS GE Flip Advisor · Data: prices.runescape.wiki · '
    'GE tax 2% per verkoop (max 5.000.000 gp) · '
    'Prijzen zijn schattingen op basis van real-time transacties — '
    'doe altijd een margin check in-game'
    '</div>',
    unsafe_allow_html=True,
)
