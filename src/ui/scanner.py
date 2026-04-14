"""
scanner.py — The main item scanner / discovery tab.

Layout:
  Left column  (40%) : Compact, sortable scanner table. Click row to select.
  Right column (60%) : Full item detail card for the selected row.
"""
import pandas as pd
import streamlit as st

from src.engine.formulas import fmt_gp, fmt_pct
from src.ui.components import render_item_detail
from src.ui.styles import section_label


# Columns shown in the scanner table (subset of full df)
_TABLE_COLS = {
    "name":       "Item",
    "margin":     "Margin",
    "roi":        "ROI %",
    "vol_1h":     "Vol 1h",
    "pot_profit": "Max Profit",
    "smart_score":"Score",
}


def render(df_all: pd.DataFrame, prof: dict) -> None:
    """
    Render the Scanner tab.

    Parameters
    ----------
    df_all : Full ranked DataFrame from compute_flips().
    prof   : Active profile dict.
    """
    if df_all.empty:
        st.info("No items match the current filters. Adjust your capital or filters.", icon="ℹ")
        return

    df_view = df_all.sort_values("smart_score", ascending=False).reset_index(drop=True)

    # ── Toolbar ──────────────────────────────────────────────────────────
    tb_l, tb_r = st.columns([3, 1])
    with tb_l:
        st.markdown(
            f'<span class="ef-muted">'
            f'Showing top <strong style="color:#E5E7EB;">{min(50, len(df_view))}</strong> of '
            f'<strong style="color:#E5E7EB;">{len(df_view)}</strong> qualifying items'
            f'</span>',
            unsafe_allow_html=True,
        )
    with tb_r:
        sort_col = st.selectbox(
            "Sort by",
            ["Smart Score", "ROI %", "Margin", "Volume", "Max Profit"],
            label_visibility="collapsed",
            key="scanner_sort",
        )
        sort_map = {
            "Smart Score":  "smart_score",
            "ROI %":        "roi",
            "Margin":       "margin",
            "Volume":       "vol_1h",
            "Max Profit":   "pot_profit",
        }
        df_view = df_view.sort_values(sort_map[sort_col], ascending=False).reset_index(drop=True)

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

    # ── Two-column layout ─────────────────────────────────────────────────
    col_list, col_detail = st.columns([4, 6], gap="large")

    with col_list:
        section_label("Market Scanner")

        # Build display table
        df_table = df_view.head(50).copy()
        df_table["#"]          = df_table.index + 1
        df_table["Item"]       = df_table["name"]
        df_table["Margin"]     = df_table["margin"].apply(lambda v: fmt_gp(v, short=True))
        df_table["ROI"]        = df_table["roi"].apply(fmt_pct)
        df_table["Vol 1h"]     = df_table["vol_1h"].apply(lambda v: f"{int(v):,}")
        df_table["Max Profit"] = df_table["pot_profit"].apply(lambda v: fmt_gp(v, short=True))
        df_table["Score"]      = df_table["smart_score"].apply(lambda v: f"{v:.3f}")
        df_table["OVR"]        = df_table["has_override"].apply(lambda v: "✎" if v else "")

        display_cols = ["#", "Item", "Margin", "ROI", "Vol 1h", "Max Profit", "Score", "OVR"]

        # Use Streamlit's dataframe with single-row selection
        event = st.dataframe(
            df_table[display_cols],
            use_container_width=True,
            hide_index=True,
            height=600,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "#":          st.column_config.NumberColumn(width="small"),
                "Item":       st.column_config.TextColumn(width="medium"),
                "Margin":     st.column_config.TextColumn(width="small"),
                "ROI":        st.column_config.TextColumn(width="small"),
                "Vol 1h":     st.column_config.TextColumn(width="small"),
                "Max Profit": st.column_config.TextColumn(width="small"),
                "Score":      st.column_config.TextColumn(width="small"),
                "OVR":        st.column_config.TextColumn(width="small"),
            },
        )

        # Track selected row
        sel_rows = event.selection.rows if event.selection else []
        if sel_rows:
            st.session_state.sel_item_id = int(df_view.iloc[sel_rows[0]]["id"])

    with col_detail:
        section_label("Item Detail")

        # Determine which item to display
        sel_id = st.session_state.get("sel_item_id")
        if sel_id is not None and not df_view.empty:
            match = df_view[df_view["id"] == sel_id]
            if not match.empty:
                row = match.iloc[0]
            else:
                row = df_view.iloc[0]
        elif not df_view.empty:
            row = df_view.iloc[0]
        else:
            st.info("Select an item from the scanner to view details.")
            return

        render_item_detail(row, prof)
