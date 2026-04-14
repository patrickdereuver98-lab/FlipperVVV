"""
watchlist.py — Watchlist tab.

Shows items the user has starred, with live market data.
Items that fall outside current filters (e.g. margin < threshold) are shown
with a warning rather than being silently hidden.
"""
import pandas as pd
import streamlit as st

from src.engine.formulas import fmt_gp, fmt_pct
from src.ui.components import render_item_detail
from src.ui.styles import section_label


def render(df_all: pd.DataFrame, prof: dict) -> None:
    """
    Render the Watchlist tab.

    Parameters
    ----------
    df_all : Full ranked DataFrame (all qualifying items).
    prof   : Active profile dict.
    """
    if not prof["watchlist"]:
        st.markdown(
            """
            <div style="text-align:center; padding:3rem 0; color:#4B5563;">
                <div style="font-size:2rem; margin-bottom:0.5rem;">☆</div>
                <div>Your watchlist is empty.</div>
                <div style="font-size:0.82rem; margin-top:0.3rem;">
                    Click <strong>☆ Watchlist</strong> on any item in the Scanner to add it here.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Match watchlist IDs against the live dataset
    watched_ids = set(prof["watchlist"])
    df_watched = df_all[df_all["id"].astype(str).isin(watched_ids)].copy()
    offline_ids = watched_ids - set(df_watched["id"].astype(str))

    if not df_watched.empty:
        df_watched = df_watched.sort_values("smart_score", ascending=False).reset_index(drop=True)

    col_list, col_detail = st.columns([4, 6], gap="large")

    with col_list:
        section_label(f"Watchlist — {len(watched_ids)} items")

        if df_watched.empty:
            st.warning("All watched items are currently outside filter thresholds.", icon="⚠")
        else:
            # Build compact watch table
            df_table = df_watched.copy()
            df_table["Item"]       = df_table["name"]
            df_table["Margin"]     = df_table["margin"].apply(lambda v: fmt_gp(v, short=True))
            df_table["ROI"]        = df_table["roi"].apply(fmt_pct)
            df_table["Max Profit"] = df_table["pot_profit"].apply(lambda v: fmt_gp(v, short=True))
            df_table["OVR"]        = df_table["has_override"].apply(lambda v: "✎" if v else "")

            event = st.dataframe(
                df_table[["Item", "Margin", "ROI", "Max Profit", "OVR"]],
                use_container_width=True,
                hide_index=True,
                height=400,
                on_select="rerun",
                selection_mode="single-row",
                column_config={
                    "Item":       st.column_config.TextColumn(width="medium"),
                    "Margin":     st.column_config.TextColumn(width="small"),
                    "ROI":        st.column_config.TextColumn(width="small"),
                    "Max Profit": st.column_config.TextColumn(width="small"),
                    "OVR":        st.column_config.TextColumn(width="small"),
                },
            )

            sel_rows = event.selection.rows if event.selection else []
            if sel_rows:
                st.session_state.watch_item_id = int(df_watched.iloc[sel_rows[0]]["id"])

        # Show items that fell off the radar
        if offline_ids:
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            section_label("Off Radar")
            for iid_str in offline_ids:
                col_name, col_rm = st.columns([4, 1])
                col_name.markdown(
                    f'<span class="ef-muted">⚬ Item #{iid_str} — outside current filters</span>',
                    unsafe_allow_html=True,
                )
                if col_rm.button("✕", key=f"wl_offrad_rm_{iid_str}", use_container_width=True):
                    prof["watchlist"].remove(iid_str)
                    st.rerun()

    with col_detail:
        section_label("Item Detail")
        if df_watched.empty:
            st.info("No watchlist items with live data to display.")
            return

        sel_id = st.session_state.get("watch_item_id")
        if sel_id is not None:
            match = df_watched[df_watched["id"] == sel_id]
            row = match.iloc[0] if not match.empty else df_watched.iloc[0]
        else:
            row = df_watched.iloc[0]

        render_item_detail(row, prof, show_watchlist_remove=True)
