"""
ledger.py — P/L Ledger tab.

Displays the full trade history with:
  • Summary metrics: total profit, avg ROI, tax drag, best flip
  • Cumulative P/L chart
  • Full sortable trade table
  • Export to CSV
"""
import pandas as pd
import streamlit as st
from datetime import datetime

from src.engine.formulas import fmt_gp, fmt_pct, GE_TAX_RATE
from src.ui.styles import section_label


def render(prof: dict) -> None:
    """
    Render the P/L Ledger tab.

    Parameters
    ----------
    prof : Active profile dict.
    """
    history = prof["history"]

    if not history:
        st.markdown(
            """
            <div style="text-align:center; padding:3rem 0; color:#4B5563;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">📒</div>
                <div>No completed trades yet.</div>
                <div style="font-size:0.82rem; margin-top:0.3rem;">
                    Close your first trade from the <strong>Active Slots</strong> tab to start tracking.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(history)

    # ── Summary metrics ───────────────────────────────────────────────────
    total_invest = df["invest"].sum()
    total_profit = df["net_profit"].sum()
    total_tax    = df["tax_paid"].sum()
    avg_roi      = (total_profit / total_invest * 100) if total_invest > 0 else 0.0
    best_flip    = df.loc[df["net_profit"].idxmax()]
    worst_flip   = df.loc[df["net_profit"].idxmin()]
    win_rate     = (df["net_profit"] > 0).mean() * 100

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Net Profit",  fmt_gp(total_profit, short=True),
              delta=f"+{fmt_pct(avg_roi)} avg ROI")
    m2.metric("Total Invested", fmt_gp(total_invest, short=True))
    m3.metric("GE Tax Paid", fmt_gp(total_tax, short=True),
              delta=f"{total_tax/max(1,total_invest)*100:.2f}% drag", delta_color="inverse")
    m4.metric("Trades",      len(df))
    m5.metric("Win Rate",    fmt_pct(win_rate))
    m6.metric("Best Flip",   fmt_gp(best_flip["net_profit"], short=True),
              delta=best_flip["name"])

    st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)

    # ── Cumulative P/L chart ──────────────────────────────────────────────
    section_label("Cumulative P/L")

    df_chart = df.copy()
    df_chart["trade_num"]  = range(1, len(df_chart) + 1)
    df_chart["cumulative"] = df_chart["net_profit"].cumsum()

    st.line_chart(
        df_chart.set_index("trade_num")[["cumulative"]],
        color=["#10B981"],
        height=180,
        use_container_width=True,
    )

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

    # ── Trade table ───────────────────────────────────────────────────────
    section_label("Trade History")

    df_disp = df.copy()

    # Format timestamp
    if "ts" in df_disp.columns:
        df_disp["Date / Time"] = pd.to_datetime(df_disp["ts"], unit="s").dt.strftime("%Y-%m-%d %H:%M")
    else:
        df_disp["Date / Time"] = "—"

    df_disp["Item"]       = df_disp["name"]
    df_disp["Qty"]        = df_disp["qty"].apply(lambda v: f"{int(v):,}")
    df_disp["Buy Price"]  = df_disp["buy_p"].apply(fmt_gp)
    df_disp["Sell Price"] = df_disp["sell_p"].apply(fmt_gp)
    df_disp["Invested"]   = df_disp["invest"].apply(lambda v: fmt_gp(v, short=True))
    df_disp["Tax Paid"]   = df_disp["tax_paid"].apply(lambda v: fmt_gp(v, short=True))
    df_disp["Net Profit"] = df_disp["net_profit"].apply(lambda v: fmt_gp(v, short=True))
    df_disp["ROI"]        = df_disp["roi"].apply(fmt_pct)

    display_cols = ["Date / Time", "Item", "Qty", "Buy Price", "Sell Price",
                    "Invested", "Tax Paid", "Net Profit", "ROI"]

    st.dataframe(
        df_disp[display_cols],
        use_container_width=True,
        hide_index=True,
        height=min(400, 38 + len(df_disp) * 35),
        column_config={
            "Net Profit": st.column_config.TextColumn(width="medium"),
            "ROI":        st.column_config.TextColumn(width="small"),
        },
    )

    # ── Action row ────────────────────────────────────────────────────────
    act_l, act_r = st.columns([1, 1])

    # CSV export
    csv_bytes = df_disp[display_cols].to_csv(index=False).encode("utf-8")
    act_l.download_button(
        "⬇  Export CSV",
        data=csv_bytes,
        file_name=f"osrs_flipper_ledger_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if act_r.button("🗑  Clear History", use_container_width=True, key="ledger_clear"):
        prof["history"] = []
        st.rerun()
