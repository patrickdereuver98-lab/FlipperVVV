"""
sidebar.py — Compact sidebar: capital + nav.

Navigation replaces tabs. Pages:
  Terminal (Home) · Market Explorer · Active Slots · Watchlist · P/L Ledger

Returns (free_cash, acc_type, sector).
"""
import streamlit as st
from src.engine.formulas import fmt_gp, parse_osrs_gp
from src.ui.styles import label as section_label
import src.state.session as session

_INCREMENTS = [("+10M", 10_000_000), ("+100M", 100_000_000),
               ("+500M", 500_000_000), ("+1B", 1_000_000_000)]

# Nav items: (page_key, icon, label, badge_fn)
# badge_fn receives prof and returns badge text or ""
def _nav_items(prof):
    n_slots = len(prof["active_flips"])
    n_watch = len(prof["watchlist"])
    return [
        ("terminal",  "◈", "Terminal",        ""),
        ("explorer",  "⊞", "Market Explorer",  ""),
        ("portfolio", "💼", "Active Slots",    f"{n_slots}/{session.MAX_SLOTS}" if n_slots else ""),
        ("watchlist", "☆", "Watchlist",        str(n_watch) if n_watch else ""),
        ("ledger",    "📒", "P/L Ledger",      ""),
    ]


def render(prof: dict) -> tuple[int, str, str]:
    with st.sidebar:
        # ── Branding ──
        st.markdown(
            '<div style="padding:0.4rem 0 1rem; border-bottom:1px solid #30363D; margin-bottom:0.75rem;">'
            '<div style="font-size:0.95rem;font-weight:700;color:#F0B429;letter-spacing:0.05em;">◈ OSRS Elite Flipper</div>'
            '<div style="font-size:0.65rem;color:#545D68;letter-spacing:0.09em;margin-top:1px;">GE TRADING TERMINAL · v4.0</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Navigation ──
        st.markdown('<div class="nav-section">Navigation</div>', unsafe_allow_html=True)
        current_page = st.session_state.get("page", "terminal")

        for page_key, icon, lbl, badge in _nav_items(prof):
            is_active = current_page == page_key
            active_cls = "nav-item-active" if is_active else ""
            badge_html = f'<span class="nav-badge">{badge}</span>' if badge else ""
            # Render the visual row
            st.markdown(
                f'<div class="nav-item {active_cls}">'
                f'<span class="nav-icon">{icon}</span>'
                f'<span>{lbl}</span>'
                f'{badge_html}'
                f'</div>',
                unsafe_allow_html=True,
            )
            # Invisible button overlay for click detection
            if st.button(lbl, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.rerun()

        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        st.markdown('<div style="border-top:1px solid #30363D; margin:0.4rem 0;"></div>',
                    unsafe_allow_html=True)

        # ── Profile selector ──
        section_label("Account")
        profile_names = list(st.session_state.profiles.keys())
        current = st.session_state.get("active_profile", "Main")
        idx = profile_names.index(current) if current in profile_names else 0
        sel = st.selectbox("profile", profile_names, index=idx,
                           label_visibility="collapsed", key="sb_profile")
        if sel != current:
            st.session_state.active_profile = sel
            st.rerun()

        with st.expander("＋ New Account"):
            new_name = st.text_input("Name", key="sb_new_name", placeholder="e.g. Ironman")
            if st.button("Create", key="sb_create_acc", use_container_width=True):
                name = new_name.strip()
                if name and name not in st.session_state.profiles:
                    from src.state.session import _empty_profile
                    st.session_state.profiles[name] = _empty_profile(name)
                    st.session_state.active_profile = name
                    st.rerun()

        st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)

        # ── Cash Stack ──
        section_label("Cash Stack")
        if "raw_cash" not in st.session_state:
            st.session_state.raw_cash = 25_000_000

        cash_str = st.text_input("cash", value=fmt_gp(st.session_state.raw_cash, short=True),
                                  label_visibility="collapsed", placeholder="e.g. 250m")
        parsed = parse_osrs_gp(cash_str)
        if parsed != st.session_state.raw_cash and parsed >= 0:
            st.session_state.raw_cash = parsed
            st.rerun()

        q1, q2, q3, q4 = st.columns(4)
        for col, (lbl, amt) in zip([q1, q2, q3, q4], _INCREMENTS):
            if col.button(lbl, key=f"sb_qa_{lbl}", use_container_width=True):
                st.session_state.raw_cash += amt
                st.rerun()

        if st.button("Reset → 0", key="sb_reset"):
            st.session_state.raw_cash = 0
            st.rerun()

        # Capital summary grid
        locked = sum(f["qty"] * f["buy_p"] for f in prof["active_flips"].values())
        total  = st.session_state.raw_cash
        free   = max(0, total - locked)
        pct    = int(free / total * 100) if total > 0 else 0

        st.markdown(
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-top:8px;">'
            f'<div style="background:#1C2128;border:1px solid #30363D;border-radius:6px;padding:0.42rem 0.5rem;">'
            f'<div style="font-size:0.58rem;color:#545D68;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">Total</div>'
            f'<div style="font-family:monospace;font-size:0.80rem;font-weight:600;color:#CDD9E5;">{fmt_gp(total, short=True)}</div></div>'
            f'<div style="background:#1C2128;border:1px solid #30363D;border-radius:6px;padding:0.42rem 0.5rem;">'
            f'<div style="font-size:0.58rem;color:#545D68;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">Locked</div>'
            f'<div style="font-family:monospace;font-size:0.80rem;font-weight:600;color:#F0B429;">{fmt_gp(locked, short=True)}</div></div>'
            f'<div style="background:#1C2128;border:1px solid #30363D;border-radius:6px;padding:0.42rem 0.5rem;">'
            f'<div style="font-size:0.58rem;color:#545D68;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;">Free</div>'
            f'<div style="font-family:monospace;font-size:0.80rem;font-weight:600;color:#3FB950;">{fmt_gp(free, short=True)}</div></div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if total > 0:
            pct_locked = min(100, locked / total * 100)
            st.markdown(
                f'<div style="height:3px;border-radius:2px;background:#30363D;margin:6px 0 2px;overflow:hidden;">'
                f'<div style="height:100%;width:{pct_locked:.1f}%;background:#F0B429;float:left;border-radius:2px;"></div>'
                f'<div style="height:100%;width:{100-pct_locked:.1f}%;background:#3FB950;float:left;"></div>'
                f'</div>'
                f'<div style="font-size:0.60rem;color:#545D68;">'
                f'<span style="color:#F0B429;">■</span> Locked &nbsp;'
                f'<span style="color:#3FB950;">■</span> Free — {pct}% available</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)

        # ── Filters ──
        section_label("Filters")
        sector = st.selectbox("Sector", ["Alle Markten", "High-Volume Supplies", "High-Value Gear"],
                              key="sb_sector")
        acc_type = st.selectbox("Account", ["F2P + Members", "Alleen Members", "Alleen F2P"],
                                key="sb_acc_type")

        # ── System ──
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("⟳  Force API Sync", use_container_width=True, key="sb_sync"):
            from src.api import client as api
            api.clear_cache()
            st.rerun()

        last_ts = st.session_state.get("last_api_ts")
        if last_ts:
            from src.engine.formulas import fmt_ts
            st.markdown(
                f'<div style="font-size:0.63rem;color:#545D68;margin-top:4px;">Last poll: {fmt_ts(last_ts)}</div>',
                unsafe_allow_html=True,
            )

    return free, acc_type, sector
