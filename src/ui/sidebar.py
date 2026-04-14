"""
sidebar.py — Global controls for capital and accounts.
"""
import streamlit as st
from src.engine.formulas import fmt_gp, parse_osrs_gp
from src.ui.styles import section_label

def render(prof: dict):
    """
    Renders the sidebar and returns (free_cash, acc_type).
    """
    with st.sidebar:
        # ── Account & Profiel ──
        section_label("Account Management")
        active_prof = st.session_state.get("active_profile", "Main")
        
        # Profielwissel
        all_profs = list(st.session_state.profiles.keys())
        sel_prof = st.selectbox(
            "Actief Profiel",
            options=all_profs,
            index=all_profs.index(active_prof),
            label_visibility="collapsed"
        )
        
        if sel_prof != active_prof:
            st.session_state.active_profile = sel_prof
            st.rerun()

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        # ── Kapitaalbeheer ──
        section_label("Kapitaal & Liquiditeit")
        
        # Initializeer raw_cash als het ontbreekt
        if "raw_cash" not in st.session_state:
            st.session_state.raw_cash = 25_000_000

        # Quick-add sectie voor efficiëntie
        c1, c2 = st.columns(2)
        if c1.button("+10M", use_container_width=True):
            st.session_state.raw_cash += 10_000_000
            st.rerun()
        if c2.button("+100M", use_container_width=True):
            st.session_state.raw_cash += 100_000_000
            st.rerun()
            
        c3, c4 = st.columns(2)
        if c3.button("+500M", use_container_width=True):
            st.session_state.raw_cash += 500_000_000
            st.rerun()
        if c4.button("+1B", use_container_width=True):
            st.session_state.raw_cash += 1_000_000_000
            st.rerun()

        # Manuele invoer (voor finetuning)
        cash_str = st.text_input(
            "Totale Cash Stack", 
            value=fmt_gp(st.session_state.raw_cash, short=True),
            help="Typ bijv. 2.5b of 500m"
        )
        st.session_state.raw_cash = parse_osrs_gp(cash_str)

        # Liquiditeitsberekening (Dynamisch)
        locked = sum(f["qty"] * f["buy_p"] for f in prof["active_flips"].values())
        free = max(0, st.session_state.raw_cash - locked)

        st.metric(
            label="Vrij Beschikbaar", 
            value=f"{fmt_gp(free, short=True)}", 
            delta=f"-{fmt_gp(locked, short=True)} in slots",
            delta_color="inverse"
        )

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

        # ── Filters ──
        section_label("Markt Filters")
        acc_type = st.selectbox(
            "Account Status",
            ["F2P + Members", "Alleen Members", "Alleen F2P"],
            label_visibility="collapsed"
        )

        st.divider()
        
        # Systeem status
        if st.button("↻ Forceer API Sync", use_container_width=True):
            from src.api import client as api
            api.clear_cache()
            st.rerun()

    return free, acc_type
