"""
app.py — OSRS Elite Flipper — Main Streamlit entry point.

Architecture:
  src/api/client.py      — OSRS Wiki API (cached, retry-protected)
  src/engine/formulas.py — Pure math utilities (tax, fmt, parse, age)
  src/engine/core.py     — Vectorized Pandas computation engine
  src/state/session.py   — Session state & profile management
  src/ui/styles.py       — Bloomberg Terminal CSS theme
  src/ui/sidebar.py      — Capital management sidebar
  src/ui/scanner.py      — Scanner tab (discovery + detail)
  src/ui/watchlist.py    — Watchlist tab
  src/ui/portfolio.py    — Active Slots tab (live P/L)
  src/ui/ledger.py       — P/L Ledger tab (history + analytics)

Data Flow:
  [API poll every 60s]
       ↓
  compute_flips()  →  df_all (ranked DataFrame)
       ↓
  Tabs: Scanner | Watchlist | Portfolio | Ledger
"""
import sys
import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="OSRS Elite Flipper",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Add src to path for clean imports ─────────────────────────────────────────
import os
sys.path.insert(0, os.path.dirname(__file__))

# ── Internal imports ───────────────────────────────────────────────────────────
import src.api.client       as api
import src.state.session    as session
import src.engine.core      as core
from src.ui            import styles, sidebar, scanner, watchlist, portfolio, ledger
from src.engine.formulas import fmt_ts

# ── Inject CSS theme ──────────────────────────────────────────────────────────
styles.inject()

# ── Auto-refresh every 60 seconds ─────────────────────────────────────────────
st_autorefresh(interval=60_000, key="osrs_api_refresh")

# ── Initialise session state ───────────────────────────────────────────────────
prof = session.init()

# ── Sidebar: capital management + account filter ───────────────────────────────
free, acc_type, sector = sidebar.render(prof)

# ── API polling ────────────────────────────────────────────────────────────────
st.session_state.api_error = None
try:
    mapping  = api.fetch_mapping()
    latest   = api.fetch_latest()
    vol_5m   = api.fetch_5m()
    vol_1h   = api.fetch_1h()
    st.session_state.last_api_ts = int(time.time())
except Exception as exc:
    st.session_state.api_error = f"API error: {exc}"
    st.error(f"⚠ Could not reach OSRS Wiki API — {exc}", icon="⚠")
    st.stop()

# ── Computation engine ─────────────────────────────────────────────────────────
df_all = core.compute_flips(
    mapping      = mapping,
    latest       = latest,
    vol5m        = vol_5m,
    vol1h        = vol_1h,
    free_cash    = free,
    acc_type     = acc_type,
    sector       = sector,         # <-- FIX: sector doorgegeven aan de motor
    cooldowns    = prof["cooldowns"],
    overrides    = prof["overrides"],
)

# ── Page header ────────────────────────────────────────────────────────────────
hdr_l, hdr_r = st.columns([6, 2])
with hdr_l:
    st.markdown(
        f"""
        <div style="display:flex; align-items:baseline; gap:0.75rem; margin-bottom:0.1rem;">
            <span style="font-size:1.35rem; font-weight:700; color:#F59E0B; letter-spacing:0.04em;">
                OSRS ELITE FLIPPER
            </span>
            <span style="font-size:0.72rem; color:#4B5563; letter-spacing:0.1em; text-transform:uppercase;">
                GE Trading Terminal &nbsp;·&nbsp; v2.0
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hdr_r:
    last_ts = st.session_state.last_api_ts
    item_count = len(df_all)
    st.markdown(
        f"""
        <div style="text-align:right; font-size:0.75rem; color:#6B7280; padding-top:0.3rem;">
            <span style="color:#10B981;">●</span> Live &nbsp;·&nbsp;
            Last poll: {fmt_ts(last_ts)} &nbsp;·&nbsp;
            <strong style="color:#E5E7EB;">{item_count:,}</strong> qualifying items
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:0.1rem;'></div>", unsafe_allow_html=True)

# ── Main tabs ──────────────────────────────────────────────────────────────────
n_watchlist = len(prof["watchlist"])
n_slots     = len(prof["active_flips"])

tab_scanner, tab_watch, tab_slots, tab_ledger = st.tabs([
    "🔍  Scanner",
    f"☆  Watchlist  {f'({n_watchlist})' if n_watchlist else ''}",
    f"💼  Active Slots  ({n_slots}/{session.MAX_SLOTS})",
    "📒  P/L Ledger",
])

with tab_scanner:
    scanner.render(df_all, prof)

with tab_watch:
    watchlist.render(df_all, prof)

with tab_slots:
    portfolio.render(prof, latest)

with tab_ledger:
    ledger.render(prof)
