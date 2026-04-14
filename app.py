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

/* Custom Styling for the new Sidebar Quick-Add Buttons */
.quick-add-btn { width: 100%; display: flex; justify-content: space-between; gap: 5px; margin-bottom: 15px; }
.quick-add-btn button { flex: 1; padding: 4px 0 !important; font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

prof = state.init_session()

# Initializeer de cash stack in de session state als deze nog niet bestaat
if "raw_cash" not in st.session_state:
    st.session_state.raw_cash = 25000000 # Startwaarde 25M

# ── Controller: Sidebar & Kapitaal ──
with st.sidebar:
    st.markdown('<div class="section-title">Profiel Selectie</div>', unsafe_allow_html=True)
    sel_prof = st.selectbox("Actief Account", list(st.session_state.profiles.keys()), index=list(st.session_state.profiles.keys()).index(st.session_state.active_profile), label_visibility="collapsed")
    if sel_prof != st.session_state.active_profile:
        st.session_state.active_profile = sel_prof
        st.rerun()

    st.markdown('<div class="section-title">Kapitaal Invoer</div>', unsafe_allow_html=True)
    
    # Handmatige invoer
    cash_input = st.text_input("Cash Stack", value=core.fmt(st.session_state.raw_cash, short=True), key="cash_input_field")
    st.session_state.raw_cash = core.parse_osrs_gp(cash_input)

    # De "Quick Add" Knoppen
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("+10M", use_container_width=True):
        st.session_state.raw_cash += 10_000_000
        st.rerun()
    if c2.button("+100M", use_container_width=True):
        st.session_state.raw_cash += 100_000_000
        st.rerun()
    if c3.button("+500M", use_container_width=True):
        st.session_state.raw_cash += 500_000_000
        st.rerun()
    if c4.button("+1B", use_container_width=True):
        st.session_state.raw_cash += 1_000_000_000
        st.rerun()
    
    if st.button("Reset Cash", use_container_width=True):
        st.session_state.raw_cash = 0
        st.rerun()

    total_cash = st.session_state.raw_cash
    locked_cash = sum(f['qty'] * f['buy_p'] for f in prof['active_flips'].values())
    free_cash = max(0, total_cash - locked_cash)
    
    st.metric("Vrij Kapitaal", f"{core.fmt(free_cash)} gp", delta=f"-{core.fmt(locked_cash)} in slots", delta_color="inverse")
    
    st.markdown('<div class="section-title">Account Filter</div>', unsafe_allow_html=True)
    acc_type = st.selectbox("Status", ["F2P + Members", "Alleen Members", "Alleen F2P"], label_visibility="collapsed")
    
    st.markdown('<div class="section-title">Systeem</div>', unsafe_allow_html=True)
    if st.button("↻ Forceer Data Sync", use_container_width=True):
        api.clear_api_cache()
    if st.session_state.last_ref:
        st.caption(f"Laatste API poll: {core.fmt_ts(st.session_state.last_ref)}")

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
SORT_MAP = {"Smart Score (Balans)": "smart_score"} # Sorteren doen we default op Smart Score
df_all = core.compute_flips_vectorized(
    st.session_state["_map"], st.session_state["_lat"], st.session_state["_5m"], st.session_state["_1h"],
    free_cash, acc_type, prof['cooldowns'], prof['overrides']
)

# ── Controller: View Routing (Tabs) ──
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Scanner", f"⭐ Watchlist ({len(prof['watchlist'])})", f"💼 Slots ({len(prof['active_flips'])}/8)", "📈 P/L"])

with tab1:
    if df_all.empty: st.warning("Geen resultaten.")
    else:
        df_view = df_all.sort_values(SORT_MAP["Smart Score (Balans)"], ascending=False).reset_index(drop=True)
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
        if df_w.empty: st.warning("Watchlist items vallen momenteel buiten de radar.")
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
