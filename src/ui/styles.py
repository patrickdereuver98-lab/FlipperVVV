"""
styles.py — Global CSS injection for the Bloomberg Terminal dark theme.
Call inject() once in app.py before rendering any UI.
"""
import streamlit as st

# ── Colour palette ─────────────────────────────────────────────────────────────
COLORS = {
    "bg":          "#080B11",
    "panel":       "#0D1117",
    "card":        "#161B22",
    "border":      "#21262D",
    "border_accent":"#30363D",
    "gold":        "#F59E0B",    # Primary accent — OSRS coin
    "gold_dim":    "#92660A",
    "green":       "#10B981",    # Positive / profit
    "red":         "#EF4444",    # Negative / loss
    "amber":       "#F59E0B",    # Warning
    "text":        "#E5E7EB",
    "text_dim":    "#6B7280",
    "text_muted":  "#4B5563",
    "blue":        "#3B82F6",
    "purple":      "#8B5CF6",
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ─────────────────────────────────────────────────────────── */
:root {
    --bg:           #080B11;
    --panel:        #0D1117;
    --card:         #161B22;
    --border:       #21262D;
    --border-hi:    #30363D;
    --gold:         #F59E0B;
    --gold-dim:     #78440A;
    --green:        #10B981;
    --red:          #EF4444;
    --amber:        #F59E0B;
    --text:         #E5E7EB;
    --text-dim:     #6B7280;
    --text-muted:   #4B5563;
    --blue:         #3B82F6;
    --radius:       6px;
    --radius-lg:    10px;
    --mono:         'JetBrains Mono', 'Fira Code', monospace;
    --sans:         'Inter', 'Segoe UI', system-ui, sans-serif;
}

html, body, .stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-size: 14px;
}

#MainMenu, footer { visibility: hidden !important; }
/* Verberg de header-balk, maar laat de knoppen (zoals de sidebar-toggle) bruikbaar */
header { 
    background-color: transparent !important; 
    border: none !important;
}

.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    max-width: 1700px !important;
}

/* ── Sidebar ──────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--panel) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label {
    color: var(--text-dim) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

/* ── Inputs ───────────────────────────────────────────────────────────────── */
input, textarea, [data-baseweb="input"] input {
    background-color: var(--card) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s !important;
}
input:focus, [data-baseweb="input"] input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2) !important;
    outline: none !important;
}

/* ── Select boxes ─────────────────────────────────────────────────────────── */
[data-baseweb="select"] > div {
    background-color: var(--card) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
}
[data-baseweb="menu"] {
    background-color: var(--panel) !important;
    border: 1px solid var(--border-hi) !important;
}
[data-baseweb="option"]:hover { background-color: var(--card) !important; }

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.stButton > button {
    background-color: var(--card) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
    font-family: var(--sans) !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    padding: 0.35rem 0.7rem !important;
    transition: all 0.15s ease !important;
    letter-spacing: 0.02em;
}
.stButton > button:hover {
    background-color: var(--border-hi) !important;
    border-color: var(--gold) !important;
    color: var(--gold) !important;
}
/* Primary action button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #78440A 0%, var(--gold) 100%) !important;
    border-color: var(--gold) !important;
    color: #000 !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    filter: brightness(1.1) !important;
    color: #000 !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    gap: 0 !important;
    border-bottom: 2px solid var(--border) !important;
    padding-bottom: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    border: none !important;
    color: var(--text-dim) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em;
    padding: 0.5rem 1.2rem !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
    transition: all 0.15s !important;
}
.stTabs [aria-selected="true"] {
    color: var(--gold) !important;
    border-bottom-color: var(--gold) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text) !important;
    background-color: var(--border) !important;
}
[data-testid="stTabContent"] { padding-top: 1rem !important; }

/* ── DataFrames / Tables ──────────────────────────────────────────────────── */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
}

/* ── Metrics ──────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background-color: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 0.75rem 1rem !important;
}
[data-testid="stMetricLabel"] p {
    color: var(--text-dim) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    font-weight: 500;
}
[data-testid="stMetricValue"] {
    font-family: var(--mono) !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: var(--text) !important;
}
[data-testid="stMetricDelta"] {
    font-family: var(--mono) !important;
    font-size: 0.78rem !important;
}

/* ── Containers / Cards ───────────────────────────────────────────────────── */
[data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > div:has(> .stContainer) {
    border-radius: var(--radius-lg) !important;
}
[data-testid="element-container"] > div[style*="border"] {
    border-color: var(--border) !important;
    border-radius: var(--radius-lg) !important;
    background-color: var(--card) !important;
}

/* ── Expanders ────────────────────────────────────────────────────────────── */
details {
    background-color: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
summary { color: var(--text-dim) !important; font-size: 0.82rem !important; }

/* ── Alerts / Info boxes ──────────────────────────────────────────────────── */
.stAlert {
    background-color: var(--card) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--radius) !important;
    color: var(--text) !important;
}

/* ── Charts ───────────────────────────────────────────────────────────────── */
[data-testid="stArrowVegaLiteChart"] { border-radius: var(--radius) !important; }

/* ── Scrollbar ────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Custom helper classes ────────────────────────────────────────────────── */
.ef-section-label {
    color: var(--text-dim);
    font-size: 0.70rem;
    font-weight: 600;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    padding-bottom: 4px;
    margin-bottom: 8px;
}
.ef-item-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--gold);
    line-height: 1.25;
}
.ef-pill {
    display: inline-block;
    padding: 1px 7px;
    border-radius: 99px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.ef-pill-green  { background: rgba(16,185,129,0.15); color: #10B981; border: 1px solid rgba(16,185,129,0.3); }
.ef-pill-red    { background: rgba(239,68,68,0.15);  color: #EF4444; border: 1px solid rgba(239,68,68,0.3); }
.ef-pill-gold   { background: rgba(245,158,11,0.15); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); }
.ef-pill-dim    { background: rgba(75,85,99,0.2);    color: #9CA3AF; border: 1px solid rgba(75,85,99,0.3); }
.ef-mono        { font-family: var(--mono); }
.ef-profit      { color: #10B981; font-weight: 600; font-family: var(--mono); }
.ef-loss        { color: #EF4444; font-weight: 600; font-family: var(--mono); }
.ef-muted       { color: var(--text-dim); font-size: 0.82rem; }
.ef-stale-warn  { color: #F59E0B; font-weight: 600; }
.ef-stale-crit  { color: #EF4444; font-weight: 600; }

/* ── Override Streamlit's number_input spinner arrows ────────────────────── */
[data-baseweb="form-control"] input[type="number"] {
    -moz-appearance: textfield;
}
[data-baseweb="form-control"] input[type="number"]::-webkit-inner-spin-button,
[data-baseweb="form-control"] input[type="number"]::-webkit-outer-spin-button {
    opacity: 0.4;
}

/* ── Status indicator dots ────────────────────────────────────────────────── */
.ef-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    margin-right: 5px;
    vertical-align: middle;
}
.ef-dot-green  { background: #10B981; box-shadow: 0 0 6px #10B981; }
.ef-dot-red    { background: #EF4444; box-shadow: 0 0 6px #EF4444; }
.ef-dot-amber  { background: #F59E0B; box-shadow: 0 0 6px #F59E0B; }
"""


def inject() -> None:
    """Inject the full terminal CSS into the Streamlit page."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


def section_label(text: str) -> None:
    """Render a small uppercase section heading."""
    st.markdown(f'<div class="ef-section-label">{text}</div>', unsafe_allow_html=True)
