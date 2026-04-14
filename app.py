"""
app.py — OSRS Elite Flipper v4 — Page Router.

Architecture:
  src/api/client.py       — OSRS Wiki API (cached, retry-protected)
  src/engine/formulas.py  — Pure math utilities
  src/engine/core.py      — Vectorized computation + scoring
  src/state/session.py    — Multi-profile session + page routing
  src/ui/styles.py        — GitHub Dark CSS theme
  src/ui/sidebar.py       — Capital + nav sidebar
  src/ui/scanner.py       — Terminal Home (Hero Card)
  src/ui/explorer.py      — Market Explorer (search + exchange list)
  src/ui/item_detail.py   — Item Detail + Copilot Analysis
  src/ui/portfolio.py     — Active Slots (live P/L)
  src/ui/watchlist.py     — Watchlist
  src/ui/ledger.py        — P/L Ledger + CSV export

Navigation lives in the sidebar. Pages are rendered here in the main area.
"""
import sys, os, time
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="OSRS Elite Flipper",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

sys.path.insert(0, os.path.dirname(__file__))

import src.api.client     as api
import src.state.session  as session
import src.engine.core    as core
from src.ui import styles, sidebar, scanner, watchlist, portfolio, ledger
from src.ui import explorer, item_detail
from src.engine.formulas import fmt_ts

# ── Theme ─────────────────────────────────────────────────────────────────────
styles.inject()

# ── Auto-refresh every 60 s ───────────────────────────────────────────────────
st_autorefresh(interval=60_000, key="osrs_api_refresh")

# ── Session state ─────────────────────────────────────────────────────────────
prof = session.init()

# ── Sidebar: returns (free_cash, acc_type, sector) ────────────────────────────
free, acc_type, sector = sidebar.render(prof)

# ── API polling ───────────────────────────────────────────────────────────────
st.session_state.api_error = None
try:
    mapping = api.fetch_mapping()
    latest  = api.fetch_latest()
    vol_5m  = api.fetch_5m()
    vol_1h  = api.fetch_1h()
    st.session_state.last_api_ts = int(time.time())
except Exception as exc:
    st.session_state.api_error = str(exc)
    st.error(f"⚠ OSRS Wiki API niet bereikbaar — {exc}", icon="⚠")
    st.stop()

# ── Computation engine ────────────────────────────────────────────────────────
df_all = core.compute_flips(
    mapping   = mapping,
    latest    = latest,
    vol5m     = vol_5m,
    vol1h     = vol_1h,
    free_cash = free,
    acc_type  = acc_type,
    sector    = sector,
    cooldowns = prof["cooldowns"],
    overrides = prof["overrides"],
)

# ── Global top bar ─────────────────────────────────────────────────────────────
current_page = st.session_state.get("page", "terminal")

PAGE_TITLES = {
    "terminal":  ("◈ Terminal Home",    "Hero Card · Action-First Advisor"),
    "explorer":  ("⊞ Market Explorer",  "Exchange-Style Item Browser"),
    "detail":    ("🔍 Item Detail",      "Copilot Deep-Dive Analysis"),
    "portfolio": ("💼 Active Slots",     "Live Open Positions"),
    "watchlist": ("☆  Watchlist",        "Starred Items Monitor"),
    "ledger":    ("📒 P/L Ledger",       "Trade History & Analytics"),
}
page_title, page_sub = PAGE_TITLES.get(current_page, ("", ""))

last_ts     = st.session_state.last_api_ts
item_count  = len(df_all)

hdr_l, hdr_r = st.columns([7, 3])
with hdr_l:
    st.markdown(
        f'<div style="display:flex;align-items:baseline;gap:0.75rem;margin-bottom:0.05rem;">'
        f'<span style="font-size:1.2rem;font-weight:700;color:#F0B429;letter-spacing:0.03em;">{page_title}</span>'
        f'<span style="font-size:0.70rem;color:#545D68;letter-spacing:0.08em;text-transform:uppercase;">{page_sub}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
with hdr_r:
    st.markdown(
        f'<div style="text-align:right;font-size:0.72rem;color:#545D68;padding-top:0.25rem;">'
        f'<span style="color:#3FB950;">●</span> Live &nbsp;·&nbsp; '
        f'Poll: {fmt_ts(last_ts)} &nbsp;·&nbsp; '
        f'<strong style="color:#CDD9E5;">{item_count:,}</strong> candidates'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown('<hr style="border-color:#30363D;margin:0.4rem 0 0.9rem;">', unsafe_allow_html=True)

# ── Page Router ───────────────────────────────────────────────────────────────
if current_page == "terminal":
    scanner.render(df_all, prof)

elif current_page == "explorer":
    explorer.render(df_all, mapping, latest, prof)

elif current_page == "detail":
    # Track where the user came from so the back button works
    if st.session_state.get("_prev_page") != "detail":
        st.session_state["_detail_from_page"] = st.session_state.get("_prev_page", "explorer")
    item_detail.render(df_all, mapping, latest, prof)

elif current_page == "portfolio":
    portfolio.render(prof, latest)

elif current_page == "watchlist":
    watchlist.render(df_all, prof)

elif current_page == "ledger":
    ledger.render(prof)

else:
    scanner.render(df_all, prof)

# Track previous page for back-button logic
st.session_state["_prev_page"] = current_page
