"""
sidebar.py — Capital management sidebar.

Renders:
  • Profile selector + management
  • Cash stack input + Quick-Add buttons
  • Live capital summary (Total / Locked / Free)
  • Account type filter
  • System: force-sync, last-poll timestamp
"""
import streamlit as st

import src.state.session as session
import src.api.client as api
from src.engine.formulas import parse_gp, fmt_gp, fmt_ts
from src.ui.styles import section_label


def render(prof: dict) -> tuple[int, str]:
    """
    Render the full sidebar and return (free_cash, acc_type).
    """
    with st.sidebar:
        # ── Logo / Branding ───────────────────────────────────────────────
        st.markdown(
            """
            <div style="padding: 0.5rem 0 1.2rem 0; border-bottom: 1px solid #21262D; margin-bottom: 1rem;">
                <div style="font-size:1.05rem; font-weight:700; color:#F59E0B; letter-spacing:0.06em;">
                    ◈ OSRS ELITE FLIPPER
                </div>
                <div style="font-size:0.68rem; color:#4B5563; letter-spacing:0.08em; margin-top:2px;">
                    GE TRADING TERMINAL
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Profile Selector ──────────────────────────────────────────────
        section_label("Account")
        profile_names = list(st.session_state.profiles.keys())
        sel = st.selectbox(
            "Account",
            profile_names,
            index=profile_names.index(st.session_state.active_profile),
            label_visibility="collapsed",
            key="sb_profile_sel",
        )
        if sel != st.session_state.active_profile:
            st.session_state.active_profile = sel
            st.rerun()

        with st.expander("Manage Accounts"):
            new_name = st.text_input("New account name", key="sb_new_acc", placeholder="e.g. Iron Man")
            if st.button("＋ Add", key="sb_add_acc", use_container_width=True):
                if new_name.strip():
                    session.add_profile(new_name.strip())
                    st.session_state.active_profile = new_name.strip()
                    st.rerun()
            if len(profile_names) > 1:
                if st.button(
                    f"🗑 Delete '{sel}'",
                    key="sb_del_acc",
                    use_container_width=True,
                ):
                    session.delete_profile(sel)
                    st.rerun()

        st.divider()

        # ── Capital Input ─────────────────────────────────────────────────
        section_label("Cash Stack")

        cash_str = st.text_input(
            "Cash",
            value=fmt_gp(st.session_state.raw_cash, short=True),
            key="sb_cash_input",
            label_visibility="collapsed",
            placeholder="e.g. 250m",
        )
        # Only update if the value changed to avoid reset-on-rerun issues
        parsed = parse_gp(cash_str)
        if parsed != st.session_state.raw_cash and parsed >= 0:
            st.session_state.raw_cash = parsed

        # Quick-Add buttons
        cols = st.columns(4)
        increments = [("10M", 10_000_000), ("100M", 100_000_000), ("500M", 500_000_000), ("1B", 1_000_000_000)]
        for col, (label, amount) in zip(cols, increments):
            if col.button(f"+{label}", use_container_width=True, key=f"sb_add_{label}"):
                st.session_state.raw_cash += amount
                st.rerun()

        if st.button("Reset to Zero", use_container_width=True, key="sb_reset_cash"):
            st.session_state.raw_cash = 0
            st.rerun()

        # ── Capital Summary ───────────────────────────────────────────────
        total  = session.total_cash()
        locked = session.locked_cash(prof)
        free   = session.free_cash(prof)

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Total",  fmt_gp(total, short=True))
        c2.metric("Locked", fmt_gp(locked, short=True), delta=f"-{fmt_gp(locked, short=True)}", delta_color="inverse")
        st.metric(
            "Free Capital",
            fmt_gp(free, short=True),
            delta=f"{free / total * 100:.0f}% available" if total > 0 else "0% available",
        )

        # ── Capital bar visualisation ─────────────────────────────────────
        if total > 0:
            pct_locked = min(100, locked / total * 100)
            pct_free   = 100 - pct_locked
            st.markdown(
                f"""
                <div style="height:5px; border-radius:3px; background:#21262D; margin:-0.4rem 0 0.8rem 0; overflow:hidden;">
                    <div style="height:100%; width:{pct_locked:.1f}%; background:#F59E0B; float:left; border-radius:3px 0 0 3px;"></div>
                    <div style="height:100%; width:{pct_free:.1f}%;  background:#10B981; float:left;"></div>
                </div>
                <div style="font-size:0.68rem; color:#4B5563; margin-top:2px;">
                    <span style="color:#F59E0B;">■</span> Locked &nbsp;
                    <span style="color:#10B981;">■</span> Free
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()

        # ── Account Filter ────────────────────────────────────────────────
        section_label("Item Filter")
        acc_type = st.selectbox(
            "Account type",
            ["F2P + Members", "Alleen Members", "Alleen F2P"],
            label_visibility="collapsed",
            key="sb_acc_type",
        )

        st.divider()

        # ── System ────────────────────────────────────────────────────────
        section_label("System")
        if st.button("⟳  Force Data Sync", use_container_width=True, key="sb_force_sync"):
            api.clear_cache()
            st.rerun()

        last_ts = st.session_state.last_api_ts
        if last_ts:
            st.markdown(
                f'<div class="ef-muted" style="margin-top:4px;">Last poll: {fmt_ts(last_ts)}</div>',
                unsafe_allow_html=True,
            )

        if st.session_state.api_error:
            st.error(st.session_state.api_error, icon="⚠")

        # Version tag
        st.markdown(
            '<div style="position:absolute; bottom:1rem; font-size:0.65rem; color:#374151;">v2.0 — Elite Flipper</div>',
            unsafe_allow_html=True,
        )

    return free, acc_type
