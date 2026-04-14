"""
components.py — Shared UI components.

  render_item_detail()  — Full detail card for a single item row.
  Reused by both the Scanner tab and the Watchlist tab.
"""
import pandas as pd
import streamlit as st

import src.api.client as api
import src.state.session as session
from src.engine.formulas import (
    WIKI_ICON_URL,
    WIKI_ITEM_URL,
    fmt_gp,
    fmt_pct,
    fmt_age,
    age_seconds,
)
from src.ui.styles import section_label


def _age_html(ts) -> str:
    """Return an HTML-coloured age badge."""
    age = age_seconds(ts)
    label = fmt_age(ts)
    if age > 3_600:
        css = "ef-stale-crit"
    elif age > 1_200:
        css = "ef-stale-warn"
    else:
        css = "ef-profit"
    return f'<span class="{css}">{label}</span>'


def render_item_detail(r: pd.Series, prof: dict, show_watchlist_remove: bool = False) -> None:
    """
    Full detail card for a single scanner/watchlist row.

    Parameters
    ----------
    r                     : A row from the compute_flips DataFrame.
    prof                  : Active profile dict.
    show_watchlist_remove : If True, show "Remove from Watchlist" instead of "Add".
    """
    iid_str = str(int(r["id"]))

    # ── Header ─────────────────────────────────────────────────────────────
    h_icon, h_title, h_actions = st.columns([1, 5, 3], gap="small")

    with h_icon:
        if r["icon"]:
            url = WIKI_ICON_URL.format(r["icon"].replace(" ", "_"))
            st.markdown(
                f'<img src="{url}" width="44" style="margin-top:4px; image-rendering:pixelated;">',
                unsafe_allow_html=True,
            )

    with h_title:
        override_tag = (
            '<span class="ef-pill ef-pill-gold" style="margin-left:6px;">OVERRIDE</span>'
            if r.get("has_override")
            else ""
        )
        wiki_url = WIKI_ITEM_URL.format(r["name"].replace(" ", "_"))
        st.markdown(
            f"""
            <div class="ef-item-title">{r["name"]}{override_tag}</div>
            <div class="ef-muted" style="margin-top:3px;">
                <a href="{wiki_url}" target="_blank" style="color:#3B82F6; text-decoration:none;">
                    ↗ Wiki
                </a>
                &nbsp;·&nbsp;
                {"Members" if r["members"] else "F2P"}
                &nbsp;·&nbsp; GE Limit: <span class="ef-mono">{int(r["ge_lim_fixed"]):,}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with h_actions:
        # Watchlist toggle
        if show_watchlist_remove or iid_str in prof["watchlist"]:
            if st.button("✕ Watchlist", key=f"wl_rm_{iid_str}", use_container_width=True):
                if iid_str in prof["watchlist"]:
                    prof["watchlist"].remove(iid_str)
                st.rerun()
        else:
            if st.button("☆ Watchlist", key=f"wl_add_{iid_str}", use_container_width=True):
                prof["watchlist"].append(iid_str)
                st.rerun()

        # Slot action
        if iid_str in prof["active_flips"]:
            st.button("✓ In Slots", key=f"slot_dis_{iid_str}", disabled=True, use_container_width=True)
        else:
            slots_full = len(prof["active_flips"]) >= session.MAX_SLOTS
            btn_label  = "＋ Add to Slots" if not slots_full else "✗ Slots Full"
            if st.button(btn_label, key=f"slot_add_{iid_str}", type="primary",
                         use_container_width=True, disabled=slots_full):
                if not session.add_to_slots(prof, r):
                    st.warning("Alle 8 slots zijn bezet.", icon="⚠")
                else:
                    st.rerun()

    st.markdown("<hr style='border-color:#21262D; margin:0.6rem 0;'>", unsafe_allow_html=True)

    # ── Price Chart ─────────────────────────────────────────────────────────
    ts_data = api.fetch_timeseries(int(r["id"]))
    if ts_data:
        df_ts = pd.DataFrame(ts_data)
        df_ts["timestamp"] = pd.to_datetime(df_ts["timestamp"], unit="s")
        df_ts = df_ts.set_index("timestamp")
        cols_available = [c for c in ["avgHighPrice", "avgLowPrice"] if c in df_ts.columns]
        if cols_available:
            chart_df = df_ts[cols_available].dropna()
            if not chart_df.empty:
                st.line_chart(
                    chart_df,
                    color=["#EF4444", "#10B981"][: len(cols_available)],
                    height=130,
                    use_container_width=True,
                )

    # ── Core Metrics ────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Buy (instasell)", fmt_gp(r["buy_p"]))
    m2.metric("Sell (instabuy)", fmt_gp(r["sell_p"]))
    m3.metric(
        "Net Margin",
        fmt_gp(r["margin"]),
        delta=f"ROI {fmt_pct(r['roi'])}",
    )
    m4.metric("GE Tax", fmt_gp(r["tax"]))

    # ── Trade Details ───────────────────────────────────────────────────────
    with st.container(border=True):
        d1, d2 = st.columns(2)

        with d1:
            section_label("Trade Plan")
            st.markdown(
                f"""
                <table style="width:100%; border-collapse:collapse; font-size:0.83rem;">
                    <tr>
                        <td style="color:#6B7280; padding:3px 0;">Quantity</td>
                        <td style="text-align:right; font-family:var(--mono,monospace);">{int(r["qty"]):,}</td>
                    </tr>
                    <tr>
                        <td style="color:#6B7280; padding:3px 0;">GE Limit remaining</td>
                        <td style="text-align:right; font-family:var(--mono,monospace);">{int(r["remaining_lim"]):,}</td>
                    </tr>
                    <tr>
                        <td style="color:#6B7280; padding:3px 0;">Capital required</td>
                        <td style="text-align:right; font-family:var(--mono,monospace);">{fmt_gp(r["invest"])}</td>
                    </tr>
                    <tr style="border-top:1px solid #21262D;">
                        <td style="color:#6B7280; padding:5px 0 3px;">Potential profit</td>
                        <td style="text-align:right; font-family:var(--mono,monospace); color:#10B981; font-weight:600;">
                            {fmt_gp(r["pot_profit"])}
                        </td>
                    </tr>
                </table>
                """,
                unsafe_allow_html=True,
            )

        with d2:
            section_label("Market Intelligence")
            freshness_pct = int(r.get("freshness", 1.0) * 100)
            freshness_color = "#10B981" if freshness_pct > 70 else "#F59E0B" if freshness_pct > 40 else "#EF4444"

            st.markdown(
                f"""
                <table style="width:100%; border-collapse:collapse; font-size:0.83rem;">
                    <tr>
                        <td style="color:#6B7280; padding:3px 0;">Volume (1h)</td>
                        <td style="text-align:right; font-family:var(--mono,monospace);">{int(r["vol_1h"]):,}</td>
                    </tr>
                    <tr>
                        <td style="color:#6B7280; padding:3px 0;">Volume (5m)</td>
                        <td style="text-align:right; font-family:var(--mono,monospace);">{int(r["vol_5m"]):,}</td>
                    </tr>
                    <tr>
                        <td style="color:#6B7280; padding:3px 0;">Data age (low)</td>
                        <td style="text-align:right;">{_age_html(r["low_ts"])}</td>
                    </tr>
                    <tr>
                        <td style="color:#6B7280; padding:3px 0;">Data age (high)</td>
                        <td style="text-align:right;">{_age_html(r["high_ts"])}</td>
                    </tr>
                    <tr style="border-top:1px solid #21262D;">
                        <td style="color:#6B7280; padding:5px 0 3px;">Data freshness</td>
                        <td style="text-align:right; color:{freshness_color}; font-weight:600;">
                            {freshness_pct}%
                        </td>
                    </tr>
                </table>
                """,
                unsafe_allow_html=True,
            )

    # ── Manual Override Expander ─────────────────────────────────────────────
    with st.expander("⚙  Manual Margin Override"):
        st.caption("Override stale API data with your actual in-game margin check.")
        ov_c1, ov_c2 = st.columns(2)
        new_buy  = ov_c1.number_input("Actual Buy",  value=int(r["buy_p"]),  step=1, key=f"ov_b_{iid_str}")
        new_sell = ov_c2.number_input("Actual Sell", value=int(r["sell_p"]), step=1, key=f"ov_s_{iid_str}")

        ov_a1, ov_a2 = st.columns(2)
        if ov_a1.button("Apply Override", use_container_width=True, key=f"ov_apply_{iid_str}"):
            prof["overrides"][iid_str] = {"buy": new_buy, "sell": new_sell}
            st.rerun()
        if r.get("has_override"):
            if ov_a2.button("Clear Override", use_container_width=True, key=f"ov_clear_{iid_str}"):
                prof["overrides"].pop(iid_str, None)
                st.rerun()
