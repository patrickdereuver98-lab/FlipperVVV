"""
styles.py — Global CSS.

GitHub Dark palette: readable, accessible, app-like.
New additions in v4:
  • .nav-btn / .nav-btn-active — sidebar navigation items
  • .expl-row / .expl-row:hover — Explorer list rows
  • .badge-* — Copilot AI badges
  • .detail-* — Item Detail page layout
"""
import streamlit as st

# Python token map (used in f-strings inside page modules)
T = {
    "bg":        "#0F1117", "panel":    "#161B22", "card":     "#1C2128",
    "card_hi":   "#22272E", "border":   "#30363D", "border_hi":"#444C56",
    "gold":      "#F0B429", "gold_dim": "#7D5A06", "gold_bg":  "rgba(240,180,41,0.10)",
    "green":     "#3FB950", "green_bg": "rgba(63,185,80,0.10)",
    "red":       "#F85149", "red_bg":   "rgba(248,81,73,0.10)",
    "blue":      "#58A6FF", "blue_bg":  "rgba(88,166,255,0.10)",
    "purple":    "#BC8CFF", "purple_bg":"rgba(188,140,255,0.10)",
    "text":      "#CDD9E5", "text_dim": "#8B949E", "text_muted":"#545D68",
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Variables ─────────────────────────────────────────────────────────────── */
:root {
    --bg:#0F1117; --panel:#161B22; --card:#1C2128; --card-hi:#22272E;
    --border:#30363D; --border-hi:#444C56;
    --gold:#F0B429; --gold-dim:#7D5A06; --gold-bg:rgba(240,180,41,0.10);
    --green:#3FB950; --green-bg:rgba(63,185,80,0.10);
    --red:#F85149;   --red-bg:rgba(248,81,73,0.10);
    --blue:#58A6FF;  --blue-bg:rgba(88,166,255,0.10);
    --purple:#BC8CFF; --purple-bg:rgba(188,140,255,0.10);
    --text:#CDD9E5; --text-dim:#8B949E; --text-muted:#545D68;
    --mono:'JetBrains Mono','Fira Code',monospace;
    --sans:'Inter','Segoe UI',system-ui,sans-serif;
    --r:6px; --r-lg:10px; --r-xl:14px;
}

/* ── Shell ─────────────────────────────────────────────────────────────────── */
html,body,.stApp { background-color:var(--bg) !important; color:var(--text) !important; font-family:var(--sans) !important; font-size:14px; line-height:1.5; }
#MainMenu,footer { visibility:hidden !important; }
header { background-color:transparent !important; border-bottom:none !important; }
.block-container { padding-top:1rem !important; padding-bottom:2.5rem !important; max-width:1700px !important; }

/* ── Sidebar shell ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] { background-color:var(--panel) !important; border-right:1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color:var(--text) !important; }

/* ── Inputs ────────────────────────────────────────────────────────────────── */
.stTextInput>div>div { background-color:var(--card) !important; border:1px solid var(--border-hi) !important; border-radius:var(--r) !important; }
.stTextInput>div>div:focus-within { border-color:var(--gold) !important; box-shadow:0 0 0 2px var(--gold-bg) !important; }
.stTextInput input { color:var(--text) !important; font-family:var(--mono) !important; }
[data-baseweb="base-input"] { background-color:var(--card) !important; }
[data-testid="stNumberInput"]>div { background-color:var(--card) !important; border:1px solid var(--border-hi) !important; border-radius:var(--r) !important; }

/* ── Select ────────────────────────────────────────────────────────────────── */
[data-baseweb="select"]>div { background-color:var(--card) !important; border:1px solid var(--border-hi) !important; border-radius:var(--r) !important; }
[data-baseweb="select"] * { color:var(--text) !important; }
[data-baseweb="menu"] { background-color:var(--panel) !important; border:1px solid var(--border-hi) !important; border-radius:var(--r) !important; }
[data-baseweb="option"] { background-color:transparent !important; color:var(--text) !important; }
[data-baseweb="option"]:hover,[aria-selected="true"][data-baseweb="option"] { background-color:var(--card-hi) !important; }

/* ── Buttons ───────────────────────────────────────────────────────────────── */
.stButton>button { background-color:var(--card) !important; border:1px solid var(--border-hi) !important; border-radius:var(--r) !important; color:var(--text) !important; font-family:var(--sans) !important; font-size:0.82rem !important; font-weight:500 !important; padding:0.32rem 0.75rem !important; transition:background 0.12s,border-color 0.12s,color 0.12s !important; }
.stButton>button:hover { background-color:var(--card-hi) !important; border-color:var(--gold) !important; color:var(--gold) !important; }
.stButton>button:active { transform:scale(0.98) !important; }
.stButton>button[kind="primary"] { background:linear-gradient(135deg,#5C3D00 0%,var(--gold-dim) 60%,#B8860B 100%) !important; border-color:var(--gold) !important; color:#FFF5CC !important; font-weight:600 !important; box-shadow:0 1px 6px rgba(240,180,41,0.25) !important; }
.stButton>button[kind="primary"]:hover { filter:brightness(1.12) !important; }
.stButton>button:disabled { opacity:0.4 !important; cursor:not-allowed !important; }

/* ── Metrics ───────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] { background-color:var(--card) !important; border:1px solid var(--border) !important; border-radius:var(--r-lg) !important; padding:0.7rem 0.9rem !important; }
[data-testid="stMetricLabel"] p { color:var(--text-dim) !important; font-size:0.70rem !important; font-weight:600 !important; letter-spacing:0.07em; text-transform:uppercase; }
[data-testid="stMetricValue"] { color:var(--text) !important; font-family:var(--mono) !important; font-size:1.05rem !important; font-weight:600 !important; }
[data-testid="stMetricDelta"]>div { font-family:var(--mono) !important; font-size:0.75rem !important; }

/* ── Containers ────────────────────────────────────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] { background-color:var(--card) !important; border:1px solid var(--border) !important; border-radius:var(--r-lg) !important; }

/* ── Expanders ─────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] { background-color:var(--card) !important; border:1px solid var(--border) !important; border-radius:var(--r) !important; }
[data-testid="stExpander"] summary { color:var(--text-dim) !important; font-size:0.83rem !important; }

/* ── Alerts ────────────────────────────────────────────────────────────────── */
.stAlert>div { background-color:var(--card) !important; border:1px solid var(--border-hi) !important; border-radius:var(--r) !important; color:var(--text) !important; }

/* ── DataFrames ────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border:1px solid var(--border) !important; border-radius:var(--r-lg) !important; }

/* ── Misc ──────────────────────────────────────────────────────────────────── */
hr { border-color:var(--border) !important; margin:0.6rem 0 !important; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--border-hi); border-radius:4px; }
.stDownloadButton>button { background-color:var(--card) !important; border:1px solid var(--border-hi) !important; color:var(--text) !important; border-radius:var(--r) !important; font-size:0.82rem !important; }
.stDownloadButton>button:hover { border-color:var(--gold) !important; color:var(--gold) !important; }

/* ════════════════════════════════════════════════════════════════════════════
   HELPER CLASSES
   ════════════════════════════════════════════════════════════════════════════ */
.ef-label { display:block; color:var(--text-muted); font-size:0.68rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; border-bottom:1px solid var(--border); padding-bottom:5px; margin-bottom:10px; }
.ef-mono  { font-family:var(--mono); }
.ef-profit { color:var(--green); font-weight:600; font-family:var(--mono); }
.ef-loss   { color:var(--red);   font-weight:600; font-family:var(--mono); }
.ef-gold   { color:var(--gold);  font-weight:600; }
.ef-muted  { color:var(--text-dim); font-size:0.82rem; }

.ef-pill { display:inline-block; padding:1px 8px; border-radius:99px; font-size:0.68rem; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; line-height:1.6; }
.ef-pill-green  { background:var(--green-bg); color:var(--green); border:1px solid rgba(63,185,80,0.35); }
.ef-pill-red    { background:var(--red-bg);   color:var(--red);   border:1px solid rgba(248,81,73,0.35); }
.ef-pill-gold   { background:var(--gold-bg);  color:var(--gold);  border:1px solid rgba(240,180,41,0.35); }
.ef-pill-blue   { background:var(--blue-bg);  color:var(--blue);  border:1px solid rgba(88,166,255,0.35); }
.ef-pill-purple { background:var(--purple-bg);color:var(--purple);border:1px solid rgba(188,140,255,0.35); }
.ef-pill-dim    { background:rgba(84,93,104,0.2); color:var(--text-dim); border:1px solid rgba(84,93,104,0.3); }

.ef-fresh { color:var(--green); font-weight:600; }
.ef-stale { color:var(--gold);  font-weight:600; }
.ef-dead  { color:var(--red);   font-weight:600; }

.ef-dot { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:5px; vertical-align:middle; }
.ef-dot-green { background:var(--green); box-shadow:0 0 5px var(--green); }
.ef-dot-red   { background:var(--red);   box-shadow:0 0 5px var(--red); }
.ef-dot-gold  { background:var(--gold);  box-shadow:0 0 5px var(--gold); }

/* ── Sidebar Navigation ────────────────────────────────────────────────────── */
.nav-section { font-size:0.60rem; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; color:var(--text-muted); margin:1rem 0 0.35rem 0.1rem; }
.nav-item { display:flex; align-items:center; gap:10px; padding:0.42rem 0.75rem; border-radius:var(--r); margin-bottom:2px; cursor:pointer; transition:background 0.1s; color:var(--text-dim); font-size:0.84rem; font-weight:500; border:1px solid transparent; }
.nav-item:hover { background:var(--card); color:var(--text); }
.nav-item-active { background:var(--card) !important; border-color:var(--border) !important; color:var(--gold) !important; font-weight:600 !important; }
.nav-icon { font-size:1rem; width:20px; text-align:center; flex-shrink:0; }
.nav-badge { margin-left:auto; background:var(--gold-bg); color:var(--gold); font-size:0.62rem; font-weight:700; padding:0 5px; border-radius:99px; border:1px solid rgba(240,180,41,0.3); }

/* ── Market Explorer rows ──────────────────────────────────────────────────── */
.expl-row { display:flex; align-items:center; gap:0; padding:0.6rem 0.9rem; background:var(--card); border:1px solid var(--border); border-radius:var(--r); margin-bottom:3px; transition:border-color 0.1s,background 0.1s; }
.expl-row:hover { border-color:var(--border-hi); background:var(--card-hi); }
.expl-icon { width:32px; height:32px; image-rendering:pixelated; margin-right:12px; flex-shrink:0; }
.expl-name { flex:1; font-weight:600; font-size:0.88rem; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; min-width:0; }
.expl-price { font-family:var(--mono); font-size:0.82rem; color:var(--text-dim); width:90px; text-align:right; flex-shrink:0; }
.expl-margin { font-family:var(--mono); font-size:0.82rem; color:var(--green); width:80px; text-align:right; flex-shrink:0; }
.expl-roi { font-family:var(--mono); font-size:0.78rem; color:var(--text-dim); width:60px; text-align:right; flex-shrink:0; }
.expl-badges { display:flex; gap:4px; margin-left:12px; flex-shrink:0; min-width:140px; justify-content:flex-end; }
.expl-nodata { color:var(--text-muted); font-size:0.78rem; font-style:italic; }

/* Copilot Badges */
.badge { display:inline-block; padding:1px 7px; border-radius:99px; font-size:0.60rem; font-weight:700; letter-spacing:0.04em; text-transform:uppercase; white-space:nowrap; }
.badge-liq    { background:var(--green-bg);  color:var(--green);  border:1px solid rgba(63,185,80,0.3); }
.badge-eff    { background:var(--blue-bg);   color:var(--blue);   border:1px solid rgba(88,166,255,0.3); }
.badge-deep   { background:var(--gold-bg);   color:var(--gold);   border:1px solid rgba(240,180,41,0.3); }
.badge-risky  { background:var(--red-bg);    color:var(--red);    border:1px solid rgba(248,81,73,0.3); }
.badge-top    { background:var(--purple-bg); color:var(--purple); border:1px solid rgba(188,140,255,0.3); }
.badge-slow   { background:rgba(84,93,104,0.15); color:var(--text-muted); border:1px solid rgba(84,93,104,0.25); }
.badge-ovr    { background:var(--gold-bg); color:var(--gold); border:1px solid rgba(240,180,41,0.3); }

/* ── Hero Card ─────────────────────────────────────────────────────────────── */
.hero-card { background:linear-gradient(145deg,var(--card) 0%,var(--card-hi) 100%); border:1px solid var(--border-hi); border-radius:var(--r-xl); padding:1.5rem 1.75rem 1.25rem; position:relative; overflow:hidden; }
.hero-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,var(--gold-dim),var(--gold),var(--gold-dim)); opacity:0.8; }
.hero-rank  { font-size:0.68rem; font-weight:700; letter-spacing:0.15em; text-transform:uppercase; color:var(--gold); margin-bottom:0.35rem; }
.hero-name  { font-size:1.5rem; font-weight:700; color:var(--text); line-height:1.2; margin-bottom:0.15rem; }
.hero-sub   { font-size:0.78rem; color:var(--text-dim); margin-bottom:0.9rem; }
.hero-profit { font-size:2.2rem; font-weight:800; color:var(--green); font-family:var(--mono); line-height:1.1; letter-spacing:-0.02em; }
.hero-profit-label { font-size:0.68rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.1em; font-weight:600; margin-top:2px; }
.hero-stat-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:0.5rem; margin-top:1rem; }
.hero-stat { background:rgba(0,0,0,0.20); border:1px solid var(--border); border-radius:var(--r); padding:0.45rem 0.65rem; }
.hero-stat-label { font-size:0.60rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); margin-bottom:2px; }
.hero-stat-value { font-family:var(--mono); font-size:0.88rem; font-weight:600; color:var(--text); }

/* ── Runner-up feed ────────────────────────────────────────────────────────── */
.runnerup { display:flex; align-items:center; gap:0.75rem; padding:0.5rem 0.8rem; background:var(--card); border:1px solid var(--border); border-radius:var(--r); margin-bottom:3px; }
.runnerup-rank   { font-size:0.70rem; font-weight:700; color:var(--text-muted); width:20px; text-align:center; flex-shrink:0; }
.runnerup-name   { font-size:0.84rem; font-weight:500; color:var(--text); flex:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.runnerup-profit { font-family:var(--mono); font-size:0.82rem; font-weight:600; color:var(--green); flex-shrink:0; }
.runnerup-roi    { font-family:var(--mono); font-size:0.75rem; color:var(--text-dim); width:52px; text-align:right; flex-shrink:0; }

/* ── Item Detail page ──────────────────────────────────────────────────────── */
.detail-header { display:flex; align-items:center; gap:16px; margin-bottom:1.2rem; }
.detail-icon { width:52px; height:52px; image-rendering:pixelated; }
.detail-title { font-size:1.65rem; font-weight:700; color:var(--text); line-height:1.1; }
.detail-sub { font-size:0.8rem; color:var(--text-dim); margin-top:3px; }
.copilot-card { background:linear-gradient(135deg,var(--card) 0%,#1A1F2E 100%); border:1px solid rgba(188,140,255,0.3); border-radius:var(--r-lg); padding:1rem 1.2rem; margin-bottom:0.8rem; position:relative; overflow:hidden; }
.copilot-card::before { content:''; position:absolute; top:0;left:0;right:0; height:2px; background:linear-gradient(90deg,var(--purple),#58A6FF); }
.copilot-title { font-size:0.65rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:var(--purple); margin-bottom:0.4rem; }
.copilot-verdict { font-size:1.0rem; font-weight:600; color:var(--text); margin-bottom:0.5rem; }
.copilot-detail { font-size:0.82rem; color:var(--text-dim); line-height:1.55; }
.fiscal-row { display:flex; align-items:stretch; gap:8px; background:rgba(255,255,255,0.02); border:1px solid var(--border); border-radius:var(--r); padding:0.9rem 1rem; margin-bottom:0.7rem; }
.fiscal-cell { flex:1; text-align:center; }
.fiscal-cell-label { font-size:0.60rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); margin-bottom:3px; }
.fiscal-cell-value { font-family:var(--mono); font-size:1.05rem; font-weight:700; }
.fiscal-sep { display:flex; align-items:center; color:var(--text-muted); font-size:1.1rem; padding:0 4px; }
"""


def inject() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def label(text: str) -> None:
    st.markdown(f'<div class="ef-label">{text}</div>', unsafe_allow_html=True)


section_label = label  # backward compat
