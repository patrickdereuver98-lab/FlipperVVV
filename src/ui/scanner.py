"""
scanner.py — The main item scanner / discovery tab.

Layout:
  Left column  (40%) : Compact, sortable scanner table. Click row to select.
  Right column (60%) : Full item detail card for the selected row.
"""
import pandas as pd
import streamlit as st

from src.ui.components import render_item_detail
from src.ui.styles import section_label

def render(df_all: pd.DataFrame, prof: dict) -> None:
    if df_all.empty:
        st.info("Geen items gevonden. Pas je filters of kapitaal aan.", icon="ℹ")
        return

    # Sorteer altijd eerst op Smart Score
    df_view = df_all.sort_values("smart_score", ascending=False).reset_index(drop=True)

    # ── Toolbar ──────────────────────────────────────────────────────────
    tb_l, tb_r = st.columns([3, 1])
    with tb_l:
        st.markdown(
            f'<span class="ef-muted">'
            f'Top 100 kansen op basis van Smart Score v2.'
            f'</span>',
            unsafe_allow_html=True
        )

    st.markdown("<hr style='margin: 8px 0;'/>", unsafe_allow_html=True)

# ── Two-column layout ─────────────────────────────────────────────────
    col_list, col_detail = st.columns([4, 6], gap="large")

    with col_list:
        section_label("Market Scanner")

        # Build display table (Stuur NU de ruwe getallen, niet de strings)
        df_table = df_view.head(50).copy()
        df_table["#"]          = df_table.index + 1
        df_table["Item"]       = df_table["name"]
        
        # Ruwe kolommen doorgeven voor de native formatting
        df_table["Margin"]     = df_table["margin"]
        df_table["ROI"]        = df_table["roi"]
        df_table["Vol 1h"]     = df_table["vol_1h"]
        df_table["Max Profit"] = df_table["pot_profit"]
        df_table["Score"]      = df_table["smart_score"]
        df_table["OVR"]        = df_table["has_override"].apply(lambda v: "✎" if v else "")

        display_cols = ["#", "Item", "Margin", "ROI", "Vol 1h", "Max Profit", "Score", "OVR"]

        # Use Streamlit's dataframe with native column_config
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
                # Native formatting fixes sorting én styling!
                "Margin":     st.column_config.NumberColumn(width="small", format="%d gp"),
                "ROI":        st.column_config.NumberColumn(width="small", format="%.2f %%"),
                "Vol 1h":     st.column_config.NumberColumn(width="small", format="%d"),
                "Max Profit": st.column_config.NumberColumn(width="small", format="%d gp"),
                "Score":      st.column_config.NumberColumn(width="small", format="%.2f"),
                "OVR":        st.column_config.TextColumn(width="small"),
            },
        )

        # Track selected row
        sel_rows = event.selection.rows if event.selection else []
        if sel_rows:
            st.session_state.sel_item_id = int(df_view.iloc[sel_rows[0]]["id"])

    with col_detail:
        section_label("Item Detail")

        sel_id = st.session_state.get("sel_item_id")
        if sel_id is not None and not df_view.empty:
            match = df_view[df_view["id"] == sel_id]
            if not match.empty:
                row = match.iloc[0]
            else:
                row = df_view.iloc[0]
        elif not df_view.empty:
            row = df_view.iloc[0]
            
        render_item_detail(row, prof)
