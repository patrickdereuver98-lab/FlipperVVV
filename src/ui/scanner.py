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

    # Sorteer altijd eerst op Smart Score
    df_view = df_all.sort_values("smart_score", ascending=False).reset_index(drop=True)

    # ── Toolbar ──────────────────────────────────────────────────────────
    tb_l, tb_r = st.columns([3, 1])
    with tb_l:
        st.markdown(
            f'<span class="ef-muted">'
            f'Showing top 100 opportunities sorted by Smart Score.'
            f'</span>',
            unsafe_allow_html=True
        )

    st.markdown("<hr style='margin: 8px 0;'/>", unsafe_allow_html=True)

    # ── Layout ───────────────────────────────────────────────────────────
    col_list, col_detail = st.columns([1, 1.3], gap="large")

    with col_list:
        section_label("Live Opportunities")
        
        # 1. Maak een kopie om waarschuwingen te voorkomen
        df_display = df_view.head(100).copy()
        
        # 2. Voeg een simpele indexering toe (1, 2, 3...)
        df_display.insert(0, "#", range(1, len(df_display) + 1))
        
        # 3. Voeg een Override indicator toe ("🛠️") als visuele hint
        df_display["OVR"] = df_display["has_override"].apply(lambda x: "🛠️" if x else "")

        # 4. Formatteer de kolommen voor de weergave (We gebruiken de JUISTE keys uit core.py)
        # We maken nieuwe string-kolommen aan voor weergave, originele data blijft behouden voor details
        df_display["Item"]       = df_display["name"]
        df_display["Margin"]     = df_display["margin"].apply(lambda v: fmt_gp(v, short=True))
        df_display["ROI"]        = df_display["roi"].apply(fmt_pct)
        df_display["Vol 1h"]     = df_display["vol_1h"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else "0")
        df_display["Max Profit"] = df_display["pot_profit"].apply(lambda v: fmt_gp(v, short=True))
        df_display["Score"]      = df_display["smart_score"].apply(lambda x: f"{int(x):,}")

        # 5. Selecteer alleen de kolommen die we willen zien
        show_cols = ["#", "Item", "Margin", "ROI", "Vol 1h", "Max Profit", "Score", "OVR"]
        df_table = df_display[show_cols]

        # 6. Render the interactive dataframe
        event = st.dataframe(
            df_table,
            use_container_width=True,
            hide_index=True,
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
            # df_display heeft exact dezelfde volgorde en lengte als df_table
            st.session_state.sel_item_id = int(df_display.iloc[sel_rows[0]]["id"])

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
            
        render_item_detail(row, prof)
