"""
sidebar.py — Compact capital management sidebar.

Goals:
  • Quick-add in one row of 4 buttons (no 2×2 grid)
  • Cash input inline with a small reset link — no heavy block
  • Capital summary as a tight 3-stat row, not a stacked metric wall
  • Profile selector and account filter kept minimal
  • System controls (force sync) tucked at the bottom
"""
import streamlit as st

from src.engine.formulas import fmt_gp, parse_osrs_gp
from src.ui.styles import label as section_label

_INCREMENTS = [
    ("+10M",  10_000_000),
    ("+100M", 100_000_000),
    ("+500M", 500_000_000),
    ("+1B",   1_000_000_000),
]


def render(prof: dict) -> tuple[int, str]:
    """Render the sidebar. Returns (free_cash: int, acc_type: str)."""

    with st.sidebar:

        # ── Branding ──────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="padding:0.4rem 0 1rem 0; border-bottom:1px solid #30363D; margin-bottom:1rem;">
              <div style="font-size:0.95rem; font-weight:700; color:#F0B429; letter-spacing:0.05em;">◈ OSRS Elite Flipper</div>
              <div style="font-size:0.65rem; color:#545D68; letter-spacing:0.09em; margin-top:1px;">GE TRADING TERMINAL</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Profile selector ──────────────────────────────────────────────
        section_label("Account")
        profile_names = list(st.session_state.profiles.keys())
        current       = st.session_state.get("active_profile", "Main")
        idx           = profile_names.index(current) if current in profile_names else 0

        sel = st.selectbox(
            "profile",
            profile_names,
            index=idx,
            label_visibility="collapsed",
            key="sb_profile",
        )
        if sel != current:
            st.session_state.active_profile = sel
            st.rerun()

        # Inline add profile
        with st.expander("+ New Account"):
            new_name = st.text_input("Name", key="sb_new_name", placeholder="e.g. Ironman")
            if st.button("Create", key="sb_create_acc", use_container_width=True):
                name = new_name.strip()
                if name and name not in st.session_state.profiles:
                    from src.state.session import _empty_profile
                    st.session_state.profiles[name] = _empty_profile(name)
                    st.session_state.active_profile = name
                    st.rerun()

        st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

        # ── Cash Stack ────────────────────────────────────────────────────
        section_label("Cash Stack")

        # Ensure state exists
        if "raw_cash" not in st.session_state:
            st.session_state.raw_cash = 25_000_000

        # Text input (compact, mono font via CSS)
        cash_str = st.text_input(
            "cash",
            value=fmt_gp(st.session_state.raw_cash, short=True),
            key="sb_cash_input",
            label_visibility="collapsed",
            placeholder="e.g. 250m",
        )
        parsed = parse_osrs_gp(cash_str)
        if parsed != st.session_state.raw_cash and parsed >= 0:
            st.session_state.raw_cash = parsed

        # Quick-add row — 4 buttons in one line
        q1, q2, q3, q4 = st.columns(4)
        for col, (lbl, amt) in zip([q1, q2, q3, q4], _INCREMENTS):
            if col.button(lbl, key=f"sb_qa_{lbl}", use_container_width=True):
                st.session_state.raw_cash += amt
                st.rerun()

        # Reset link
        if st.button("Reset → 0", key="sb_reset", use_container_width=False):
            st.session_state.raw_cash = 0
            st.rerun()

        # ── Capital summary (compact 3-stat row) ──────────────────────────
        locked = sum(f["qty"] * f["buy_p"] for f in prof["active_flips"].values())
        total  = st.session_state.raw_cash
        free   = max(0, total - locked)
        pct    = int(free / total * 100) if total > 0 else 0

        st.markdown(
            f"""
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; margin-top:8px;">
              <div style="background:#1C2128; border:1px solid #30363D; border-radius:6px; padding:0.45rem 0.5rem;">
                <div style="font-size:0.60rem; color:#545D68; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;">Total</div>
                <div style="font-family:monospace; font-size:0.82rem; font-weight:600; color:#CDD9E5;">{fmt_gp(total, short=True)}</div>
              </div>
              <div style="background:#1C2128; border:1px solid #30363D; border-radius:6px; padding:0.45rem 0.5rem;">
                <div style="font-size:0.60rem; color:#545D68; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;">Locked</div>
                <div style="font-family:monospace; font-size:0.82rem; font-weight:600; color:#F0B429;">{fmt_gp(locked, short=True)}</div>
              </div>
              <div style="background:#1C2128; border:1px solid #30363D; border-radius:6px; padding:0.45rem 0.5rem;">
                <div style="font-size:0.60rem; color:#545D68; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;">Free</div>
                <div style="font-family:monospace; font-size:0.82rem; font-weight:600; color:#3FB950;">{fmt_gp(free, short=True)}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Thin capital bar
        if total > 0:
            pct_locked = min(100, locked / total * 100)
            st.markdown(
                f"""
                <div style="height:3px; border-radius:2px; background:#30363D; margin:6px 0 2px; overflow:hidden;">
                  <div style="height:100%; width:{pct_locked:.1f}%; background:#F0B429; float:left; border-radius:2px;"></div>
                  <div style="height:100%; width:{100-pct_locked:.1f}%; background:#3FB950; float:left;"></div>
                </div>
                <div style="font-size:0.62rem; color:#545D68;">
                  <span style="color:#F0B429;">■</span> Locked &nbsp;
                  <span style="color:#3FB950;">■</span> Free — {pct}% available
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

        # ── Account filter ────────────────────────────────────────────────
        section_label("Filter")
        acc_type = st.selectbox(
            "account_filter",
            ["F2P + Members", "Alleen Members", "Alleen F2P"],
            label_visibility="collapsed",
            key="sb_acc_type",
        )

        # ── System ────────────────────────────────────────────────────────
        st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
        if st.button("⟳  Force API Sync", use_container_width=True, key="sb_sync"):
            from src.api import client as api
            api.clear_cache()
            st.rerun()

        last_ts = st.session_state.get("last_api_ts")
        if last_ts:
            from src.engine.formulas import fmt_ts
            st.markdown(
                f'<div style="font-size:0.65rem; color:#545D68; margin-top:4px;">Last poll: {fmt_ts(last_ts)}</div>',
                unsafe_allow_html=True,
            )

    return free, acc_type
