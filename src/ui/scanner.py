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

    # ── Layout ───────────────────────────────────────────────────────────
    col_list, col_detail = st.columns([1, 1.3], gap="large")

    with col_list:
        section_label("Live Opportunities")
        
        df_display = df_view.head(100).copy()
        df_display.insert(0, "#", range(1, len(df_display) + 1))
        
        # We veranderen de naam naar wat de weergave verwacht
        df_display["Item"] = df_display["name"]
        df_display["OVR"]  = df_display["has_override"].apply(lambda x: "🛠️" if x else "")

        # We geven nu de RUWE getallen door, niet de geformatteerde strings!
        show_cols = ["#", "Item", "margin", "roi", "vol_1h", "pot_profit", "smart_score", "OVR"]
        df_table = df_display[show_cols]

        # 6. Render the interactive dataframe met Native Streamlit Formatting
        event = st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "#": st.column_config.NumberColumn(width="small"),
                "Item": st.column_config.TextColumn(width="medium"),
                
                # Laat Streamlit de getallen tekenen (lost het zwarte-tekst probleem op)
                "margin": st.column_config.NumberColumn("Margin", format="%d gp", width="small"),
                "roi": st.column_config.NumberColumn("ROI", format="%.2f %%", width="small"),
                "vol_1h": st.column_config.NumberColumn("Vol 1h", format="%d", width="small"),
                "pot_profit": st.column_config.NumberColumn("Max Profit", format="%d gp", width="small"),
                "smart_score": st.column_config.NumberColumn("Score", format="%d", width="small"),
                
                "OVR": st.column_config.TextColumn("OVR", width="small"),
            },
        )

        # Track selected row
        sel_rows = event.selection.rows if event.selection else []
        if sel_rows:
            st.session_state.sel_item_id = int(df_display.iloc[sel_rows[0]]["id"])

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
