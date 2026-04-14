"""
styles.py — Global CSS injection.

Palette: GitHub Dark / Linear / Discord — soft greys, not pitch-black.
Design goals:
  • bg surfaces at #0F1117 / #161B22 / #1C2128 — readable without eye strain
  • Text at #CDD9E5 / #8B949E — high contrast without harshness
  • Gold #F0B429 / Green #3FB950 / Red #F85149 — vivid but not neon
  • Minimal !important wars with Streamlit internals — override only surfaces
    we control (custom HTML, containers, metrics, tabs, sidebar shell)
"""
import streamlit as st

# Token map (Python-side, for inline f-string styles)
T = {
    "bg":       "#0F1117", "panel":    "#161B22", "card":     "#1C2128",
    "card_hi":  "#22272E", "border":   "#30363D", "border_hi":"#444C56",
    "gold":     "#F0B429", "gold_dim": "#7D5A06", "gold_bg":  "rgba(240,180,41,0.10)",
    "green":    "#3FB950", "green_bg": "rgba(63,185,80,0.10)",
    "red":      "#F85149", "red_bg":   "rgba(248,81,73,0.10)",
    "blue":     "#58A6FF",
    "text":     "#CDD9E5", "text_dim": "#8B949E", "text_muted":"#545D68",
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:        #0F1117; --panel:     #161B22; --card:      #1C2128;
    --card-hi:   #22272E; --border:    #30363D; --border-hi: #444C56;
    --gold:      #F0B429; --gold-dim:  #7D5A06; --gold-bg:   rgba(240,180,41,0.10);
    --green:     #3FB950; --green-bg:  rgba(63,185,80,0.10);
    --red:       #F85149; --red-bg:    rgba(248,81,73,0.10);
    --blue:      #58A6FF;
    --text:      #CDD9E5; --text-dim:  #8B949E; --text-muted:#545D68;
    --mono: 'JetBrains Mono','Fira Code',monospace;
    --sans: 'Inter','Segoe UI',system-ui,sans-serif;
    --r: 6px; --r-lg: 10px; --r-xl: 14px;
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 14px; line-height: 1.5;
}
#MainMenu, footer { visibility: hidden !important; }
header { background-color: transparent !important; border-bottom: none !important; }
.block-container { padding-top: 1.1rem !important; padding-bottom: 2.5rem !important; max-width: 1700px !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background-color: var(--panel) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: var(--text) !important; }

/* ── Inputs ── */
.stTextInput > div > div {
    background-color: var(--card) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--r) !important;
}
.stTextInput > div > div:focus-within {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px var(--gold-bg) !important;
}
.stTextInput input { color: var(--text) !important; font-family: var(--mono) !important; }
[data-baseweb="base-input"] { background-color: var(--card) !important; }
[data-testid="stNumberInput"] > div { background-color: var(--card) !important; border: 1px solid var(--border-hi) !important; border-radius: var(--r) !important; }

/* ── Select ── */
[data-baseweb="select"] > div { background-color: var(--card) !important; border: 1px solid var(--border-hi) !important; border-radius: var(--r) !important; }
[data-baseweb="select"] * { color: var(--text) !important; }
[data-baseweb="menu"] { background-color: var(--panel) !important; border: 1px solid var(--border-hi) !important; border-radius: var(--r) !important; }
[data-baseweb="option"] { background-color: transparent !important; color: var(--text) !important; }
[data-baseweb="option"]:hover, [aria-selected="true"][data-baseweb="option"] { background-color: var(--card-hi) !important; }

/* ── Buttons ── */
.stButton > button {
    background-color: var(--card) !important; border: 1px solid var(--border-hi) !important;
    border-radius: var(--r) !important; color: var(--text) !important;
    font-family: var(--sans) !important; font-size: 0.82rem !important;
    font-weight: 500 !important; padding: 0.32rem 0.75rem !important;
    transition: background 0.12s, border-color 0.12s, color 0.12s !important;
}
.stButton > button:hover { background-color: var(--card-hi) !important; border-color: var(--gold) !important; color: var(--gold) !important; }
.stButton > button:active { transform: scale(0.98) !important; }
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #5C3D00 0%, var(--gold-dim) 60%, #B8860B 100%) !important;
    border-color: var(--gold) !important; color: #FFF5CC !important;
    font-weight: 600 !important; box-shadow: 0 1px 6px rgba(240,180,41,0.25) !important;
}
.stButton > button[kind="primary"]:hover { filter: brightness(1.12) !important; }
.stButton > button:disabled { opacity: 0.4 !important; cursor: not-allowed !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background-color: transparent !important; border-bottom: 1px solid var(--border) !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important; border: none !important;
    border-bottom: 2px solid transparent !important; margin-bottom: -1px !important;
    padding: 0.55rem 1.25rem !important; color: var(--text-dim) !important;
    font-size: 0.83rem !important; font-weight: 500 !important;
    transition: color 0.12s, border-color 0.12s !important;
}
.stTabs [aria-selected="true"] { color: var(--gold) !important; border-bottom-color: var(--gold) !important; }
.stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; background-color: rgba(255,255,255,0.03) !important; }
[data-testid="stTabContent"] { padding-top: 1.2rem !important; background-color: transparent !important; }

/* ── Metrics ── */
[data-testid="stMetric"] { background-color: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-lg) !important; padding: 0.7rem 0.9rem !important; }
[data-testid="stMetricLabel"] p { color: var(--text-dim) !important; font-size: 0.70rem !important; font-weight: 600 !important; letter-spacing: 0.07em; text-transform: uppercase; }
[data-testid="stMetricValue"] { color: var(--text) !important; font-family: var(--mono) !important; font-size: 1.05rem !important; font-weight: 600 !important; }
[data-testid="stMetricDelta"] > div { font-family: var(--mono) !important; font-size: 0.75rem !important; }

/* ── Containers with border ── */
[data-testid="stVerticalBlockBorderWrapper"] { background-color: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--r-lg) !important; }

/* ── Expanders ── */
[data-testid="stExpander"] { background-color: var(--card) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; }
[data-testid="stExpander"] summary { color: var(--text-dim) !important; font-size: 0.83rem !important; }

/* ── Alerts ── */
.stAlert > div { background-color: var(--card) !important; border: 1px solid var(--border-hi) !important; border-radius: var(--r) !important; color: var(--text) !important; }

/* ── DataFrames ── */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: var(--r-lg) !important; }

/* ── Misc ── */
hr { border-color: var(--border) !important; margin: 0.6rem 0 !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 4px; }
.stDownloadButton > button { background-color: var(--card) !important; border: 1px solid var(--border-hi) !important; color: var(--text) !important; border-radius: var(--r) !important; font-size: 0.82rem !important; }
.stDownloadButton > button:hover { border-color: var(--gold) !important; color: var(--gold) !important; }

/* ══ HELPER CLASSES ══════════════════════════════════════════════════════════ */
.ef-label { display:block; color:var(--text-muted); font-size:0.68rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; border-bottom:1px solid var(--border); padding-bottom:5px; margin-bottom:10px; }
.ef-mono  { font-family: var(--mono); }
.ef-profit { color:var(--green); font-weight:600; font-family:var(--mono); }
.ef-loss   { color:var(--red);   font-weight:600; font-family:var(--mono); }
.ef-gold   { color:var(--gold);  font-weight:600; }
.ef-muted  { color:var(--text-dim); font-size:0.82rem; }

.ef-pill { display:inline-block; padding:1px 8px; border-radius:99px; font-size:0.68rem; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; line-height:1.6; }
.ef-pill-green { background:var(--green-bg); color:var(--green); border:1px solid rgba(63,185,80,0.35); }
.ef-pill-red   { background:var(--red-bg);   color:var(--red);   border:1px solid rgba(248,81,73,0.35); }
.ef-pill-gold  { background:var(--gold-bg);  color:var(--gold);  border:1px solid rgba(240,180,41,0.35); }
.ef-pill-dim   { background:rgba(84,93,104,0.2); color:var(--text-dim); border:1px solid rgba(84,93,104,0.3); }
.ef-pill-blue  { background:rgba(88,166,255,0.12); color:var(--blue); border:1px solid rgba(88,166,255,0.3); }

.ef-fresh { color:var(--green); font-weight:600; }
.ef-stale { color:var(--gold);  font-weight:600; }
.ef-dead  { color:var(--red);   font-weight:600; }

.ef-dot { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:5px; vertical-align:middle; }
.ef-dot-green { background:var(--green); box-shadow:0 0 5px var(--green); }
.ef-dot-red   { background:var(--red);   box-shadow:0 0 5px var(--red); }
.ef-dot-gold  { background:var(--gold);  box-shadow:0 0 5px var(--gold); }

/* ── Hero Card ── */
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

/* ── Runner-up feed ── */
.runnerup { display:flex; align-items:center; gap:0.75rem; padding:0.5rem 0.8rem; background:var(--card); border:1px solid var(--border); border-radius:var(--r); margin-bottom:3px; }
.runnerup-rank   { font-size:0.70rem; font-weight:700; color:var(--text-muted); width:20px; text-align:center; flex-shrink:0; }
.runnerup-name   { font-size:0.84rem; font-weight:500; color:var(--text); flex:1; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.runnerup-profit { font-family:var(--mono); font-size:0.82rem; font-weight:600; color:var(--green); flex-shrink:0; }
.runnerup-roi    { font-family:var(--mono); font-size:0.75rem; color:var(--text-dim); width:52px; text-align:right; flex-shrink:0; }
"""


def inject() -> None:
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def label(text: str) -> None:
    st.markdown(f'<div class="ef-label">{text}</div>', unsafe_allow_html=True)


# Backward compat
section_label = label
