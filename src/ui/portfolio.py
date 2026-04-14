"""
portfolio.py — Active Slots tab (live portfolio tracking).

Shows all open GE trades with:
  • Live status (OUTBID / UNDERCUT / ABORT / OK)
  • Live vs. entry price comparison
  • Close-trade form with actual price input for accurate P/L
  • Running unrealised P/L estimate
"""
import time
from datetime import datetime

import streamlit as st

import src.state.session as session
from src.engine.formulas import (
    fmt_gp,
    fmt_pct,
    ge_tax,
    evaluate_active_flip,
    age_seconds,
    fmt_age,
)
from src.ui.styles import section_label

# Status config: icon, CSS pill class, label
_STATUS_STYLE = {
    "OK":      ("●", "ef-pill-green",  "COMPETITIVE"),
    "OUTBID":  ("▲", "ef-pill-red",   "OUTBID"),
    "UNDERCUT":("▼", "ef-pill-red",   "UNDERCUT"),
    "ABORT":   ("✕", "ef-pill-red",   "ABORT — MARGIN GONE"),
}


def _slot_card(iid_str: str, flip: dict, latest_data: dict, prof: dict, col) -> None:
    """Render a single slot card into the given Streamlit column."""
    live = latest_data.get(iid_str, {})
    l_low  = live.get("low",  0) or 0
    l_high = live.get("high", 0) or 0

    statuses, live_margin = evaluate_active_flip(
        flip["buy_p"], flip["sell_p"], l_low, l_high
    )

    # Unrealised P/L estimate: compare entry sell_p against live market sell
    entry_net  = flip["qty"] * (flip["sell_p"] - ge_tax(flip["sell_p"]) - flip["buy_p"])
    live_net   = flip["qty"] * max(0, live_margin) if l_low and l_high else None

    time_open  = int(time.time()) - flip.get("added_ts", int(time.time()))

    with col.container(border=True):
        # Card header
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                <div style="font-size:0.95rem; font-weight:700; color:#F59E0B;">{flip["name"]}</div>
                <div style="font-size:0.75rem; color:#6B7280;">
                    {flip["qty"]:,}x &nbsp;·&nbsp; open {fmt_age(flip.get("added_ts"))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Status pills
        status_html = ""
        for code, msg, target in statuses:
            icon, pill_cls, label = _STATUS_STYLE.get(code, ("?", "ef-pill-dim", code))
            target_str = f" → {fmt_gp(target)}" if target else ""
            status_html += (
                f'<span class="ef-pill {pill_cls}" style="margin-right:4px;">'
                f'{icon} {label}{target_str}</span> '
            )
        st.markdown(status_html, unsafe_allow_html=True)
        st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

        # Price comparison grid
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Entry Buy",   fmt_gp(flip["buy_p"],  short=True))
        g2.metric("Entry Sell",  fmt_gp(flip["sell_p"], short=True))
        g3.metric("Live Low",    fmt_gp(l_low,  short=True) if l_low  else "—")
        g4.metric("Live High",   fmt_gp(l_high, short=True) if l_high else "—")

        # Profit estimate
        profit_color = "#10B981" if entry_net >= 0 else "#EF4444"
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; margin:0.4rem 0; font-size:0.82rem;">
                <span style="color:#6B7280;">Expected profit</span>
                <span style="color:{profit_color}; font-weight:600; font-family:monospace;">
                    {fmt_gp(entry_net)} ({fmt_pct(entry_net / max(1, flip["qty"] * flip["buy_p"]) * 100)})
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if live_net is not None:
            delta_color = "#10B981" if live_net >= entry_net else "#EF4444"
            st.markdown(
                f'<div style="font-size:0.78rem; color:#6B7280; margin-bottom:0.5rem;">'
                f'Live estimate: <span style="color:{delta_color}; font-family:monospace;">'
                f'{fmt_gp(live_net)}</span></div>',
                unsafe_allow_html=True,
            )

        # ── Close Trade form ─────────────────────────────────────────────
        with st.expander("✓  Close Trade & Book P/L"):
            st.caption("Enter actual transaction prices for accurate ledger recording.")
            fc1, fc2, fc3 = st.columns(3)
            f_qty  = fc1.number_input(
                "Qty",      min_value=1, max_value=flip["qty"], value=flip["qty"],
                key=f"fq_{iid_str}",
            )
            f_buy  = fc2.number_input(
                "Bought at", value=int(flip["buy_p"]),  step=1, key=f"fb_{iid_str}",
            )
            f_sell = fc3.number_input(
                "Sold at",   value=int(flip["sell_p"]), step=1, key=f"fs_{iid_str}",
            )

            # Live preview of what will be booked
            preview_tax    = f_qty * ge_tax(f_sell)
            preview_profit = (f_qty * f_sell) - preview_tax - (f_qty * f_buy)
            preview_roi    = (preview_profit / max(1, f_qty * f_buy)) * 100
            pc = "#10B981" if preview_profit >= 0 else "#EF4444"
            st.markdown(
                f'<div style="background:#0D1117; border-radius:6px; padding:0.5rem 0.75rem; '
                f'margin-bottom:0.5rem; font-size:0.82rem;">'
                f'Net profit: <span style="color:{pc}; font-weight:600; font-family:monospace;">'
                f'{fmt_gp(preview_profit)} ({fmt_pct(preview_roi)})</span>'
                f' &nbsp;·&nbsp; Tax: <span style="font-family:monospace;">{fmt_gp(preview_tax)}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            bk1, bk2 = st.columns(2)
            if bk1.button("💾 Book & Close", type="primary", use_container_width=True, key=f"close_{iid_str}"):
                session.close_flip(prof, iid_str, f_qty, f_buy, f_sell)
                st.rerun()
            if bk2.button("🗑 Cancel Trade", use_container_width=True, key=f"cancel_{iid_str}"):
                del prof["active_flips"][iid_str]
                st.rerun()


def render(prof: dict, latest_data: dict) -> None:
    """
    Render the Active Slots tab.

    Parameters
    ----------
    prof        : Active profile dict.
    latest_data : Live price data from fetch_latest().
    """
    active = prof["active_flips"]
    used   = len(active)
    total  = session.MAX_SLOTS

    # ── Header strip ─────────────────────────────────────────────────────
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Open Slots", f"{used} / {total}")

    if active:
        total_invest  = sum(f["qty"] * f["buy_p"] for f in active.values())
        total_exp_net = sum(
            f["qty"] * (f["sell_p"] - ge_tax(f["sell_p"]) - f["buy_p"])
            for f in active.values()
        )
        roi_exp = (total_exp_net / max(1, total_invest)) * 100
        h2.metric("Capital in Trade",  fmt_gp(total_invest,  short=True))
        h3.metric("Expected Profit",   fmt_gp(total_exp_net, short=True))
        h4.metric("Expected ROI",      fmt_pct(roi_exp))

    st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)

    if not active:
        st.markdown(
            """
            <div style="text-align:center; padding:3rem 0; color:#4B5563;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">💼</div>
                <div>No active trades.</div>
                <div style="font-size:0.82rem; margin-top:0.3rem;">
                    Use the Scanner to find items and click <strong>＋ Add to Slots</strong>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ── Slot cards in 2-column grid ───────────────────────────────────────
    col_a, col_b = st.columns(2, gap="medium")
    columns_cycle = [col_a, col_b]

    for idx, (iid_str, flip) in enumerate(list(active.items())):
        _slot_card(iid_str, flip, latest_data, prof, columns_cycle[idx % 2])
