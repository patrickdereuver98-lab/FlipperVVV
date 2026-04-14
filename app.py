import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import api
import state
import core
import ui

st.set_page_config(page_title="OSRS Elite Flipper", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
st_autorefresh(interval=60000, key="osrs_api_refresh")

st.markdown("""
<style>
.stApp { font-family: 'Inter', 'Segoe UI', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 1600px; }
.section-title { color: #ff9800; font-size: 1.1rem; font-weight: bold; margin: 15px 0 10px 0; border-bottom: 1px solid #3e3e3e; padding-bottom: 5px; }
.text-orange { color: #ff9800; } .text-green { color: #4caf50; font-weight: bold; } .text-muted { color: #a0a0a0; font-size: 0.85rem; }
.age-warning { color: #ff9800; font-weight: bold; } .age-danger { color: #f44336; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

prof = state.init_session()

# ── Controller: Sidebar & Kapitaal ──
with st.sidebar:
    st.markdown('<div class="section-title">Profiel Selectie</div>', unsafe_allow_html=True)
    sel_prof = st.selectbox("Actief Account", list(st.session_state.profiles.keys()), index=list(st.session_state.profiles.keys()).index(st.session_state.active_profile))
    if sel_prof != st.session_state.active_profile:
        st.session_state.active_profile = sel_prof
        st.rerun()

    st.markdown('<div class="section-title">Kapitaal Beheer</div>', unsafe_allow_html=True)
    total_cash = core.parse_osrs_gp(st.text_input("Totale Cash Stack", value="25m"))
    locked_cash = sum(f['qty'] * f['buy_p'] for f in prof['active_flips'].values())
    free_cash = max(0, total_cash - locked_cash)
    
    st.metric("Liquiditeit", f"{core.fmt(free_cash)} gp", delta=f"-{core.fmt(locked_cash)} in slots", delta_color="inverse")
    max_bp_pct = st.slider("Max prijs (% vrij kapitaal)", 1, 100, 100)
    
    st.markdown('<div class="section-title">Scanner Filters</div>', unsafe_allow_html=True)
    acc_type = st.selectbox("Account Status", ["F2P + Members", "Alleen Members", "Alleen F2P"])
    sort_opt = st.selectbox("Sorteer op", ["Smart Score (Balans)", "Pot. winst", "ROI %", "Margin", "Volume (1u)"])
    c1, c2 = st.columns(2)
    with c1: min_margin = st.number_input("Min Margin", value=100, step=50)
    with c2: min_roi = st.number_input("Min ROI (%)", value=0.5, step=0.1)
    min_vol = st.number_input("Min Volume (1 uur)", value=5, step=1)

# ── Controller: API Polling ──
try:
    st.session_state["_map"] = api.fetch_mapping()
    st.session_state["_lat"] = api.fetch_latest()
    st.session_state["_5m"]  = api.fetch_5m()
    st.session_state["_1h"]  = api.fetch_1h()
    st.session_state["last_ref"] = int(time.time())
except Exception as e:
    st.error(f"Fout bij ophalen API: {e}. Retrying in background...")
    st.stop()

# ── Controller: Vectorized Engine ──
SORT_MAP = {"Smart Score (Balans)": "smart_score", "Pot. winst": "pot_profit", "ROI %": "roi", "Margin": "margin", "Volume (1u)": "vol_1h"}
df_all = core.compute_flips(
    st.session_state["_map"], st.session_state["_lat"], st.session_state["_5m"], st.session_state["_1h"],
    free_cash, min_margin, min_roi, min_vol, int(free_cash * max_bp_pct / 100), acc_type, prof['cooldowns'], prof['overrides']
)

# ── Controller: View Routing (Tabs) ──
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Scanner", f"⭐ Watchlist ({len(prof['watchlist'])})", f"💼 Slots ({len(prof['active_flips'])}/8)", "📈 P/L"])

with tab1:
    if df_all.empty: st.warning("Geen resultaten.")
    else:
        df_view = df_all.sort_values(SORT_MAP[sort_opt], ascending=False).reset_index(drop=True)
        col_list, col_detail = st.columns([1, 1.5], gap="large")
        with col_list:
            with st.container(height=650, border=True):
                for i, r in df_view.head(50).iterrows():
                    prefix = "🛠️ " if r.get('has_override') else ""
                    if st.button(f"#{i+1} {prefix}{r['Naam']} ({core.fmt(r['pot_profit'], short=True)})", key=f"btn_s_{i}", use_container_width=True):
                        st.session_state.sel_idx = i
                        st.rerun()
        with col_detail:
            si = min(st.session_state.sel_idx, len(df_view.head(50)) - 1)
            ui.render_item_detail(df_view.iloc[si], prof)

with tab2:
    if not prof['watchlist']: st.info("Watchlist is leeg.")
    else:
        df_w = df_all[df_all['id'].astype(str).isin(prof['watchlist'])].reset_index(drop=True)
        if df_w.empty: st.warning("Watchlist items vallen momenteel buiten filters.")
        else:
            wl, wd = st.columns([1, 1.5], gap="large")
            with wl:
                for i, r in df_w.iterrows():
                    if st.button(f"{r['Naam']} (M: {core.fmt(r['margin'], short=True)})", key=f"btn_w_{i}", use_container_width=True):
                        st.session_state.watch_idx = i
                        st.rerun()
            with wd:
                wi = min(st.session_state.get('watch_idx', 0), len(df_w) - 1)
                ui.render_item_detail(df_w.iloc[wi], prof, True)

with tab3: ui.render_portfolio_tab(prof, st.session_state["_lat"])
with tab4: ui.render_history_tab(prof)
