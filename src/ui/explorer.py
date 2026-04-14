"""
explorer.py — Market Explorer: osrs.exchange-style searchable item list.

Features:
  • Global search bar — filters the full Wiki mapping (all ~4000 items)
    using simple string-match. No extra API calls needed.
  • Results split into two tiers:
      Tier 1 — items in df_all (pass flip thresholds): full margin / ROI / badges
      Tier 2 — items only in mapping+latest (no flip potential shown): price only
  • Copilot AI Badges on each qualifying item row
  • Sort by: Action Score | ROI | Margin | Volume | Price
  • Click "→" button on any row → navigate to Item Detail page
"""
import pandas as pd
import streamlit as st

import src.state.session as session
from src.engine.formulas import (
    WIKI_ICON_URL, WIKI_ITEM_URL,
    fmt_gp, fmt_pct, age_seconds,
)
from src.ui.styles import T, label as section_label

# ── Sort options ───────────────────────────────────────────────────────────────
_SORT_OPTS = {
    "Action Score": "action_score",
    "ROI %":        "roi",
    "Netto Marge":  "margin",
    "Volume (1h)":  "vol_1h",
    "Potentieel":   "pot_profit",
}

# ── Copilot badge definitions ──────────────────────────────────────────────────
# Each entry: (condition_fn, css_class, label)
_BADGE_DEFS = [
    (lambda r: r.get("action_score", 0) >= 0.75,          "badge-top",  "⭐ Top Pick"),
    (lambda r: r.get("vol_1h", 0) >= 500,                 "badge-liq",  "💧 High Liquidity"),
    (lambda r: r.get("roi", 0) >= 2.0,                    "badge-eff",  "⚡ Capital Efficient"),
    (lambda r: r.get("ge_lim_fixed", 0) >= 1000
               and r.get("margin", 0) >= 5_000,           "badge-deep", "📊 Deep Market"),
    (lambda r: r.get("freshness", 1.0) < 0.45,            "badge-risky","⚠ Stale Data"),
    (lambda r: r.get("vol_1h", 0) > 0
               and r.get("vol_1h", 0) < 50,               "badge-slow", "🐢 Low Volume"),
    (lambda r: bool(r.get("has_override")),                "badge-ovr",  "✎ Override"),
]
MAX_BADGES = 3


def _get_badges(r: dict) -> list[tuple[str, str]]:
    """Return up to MAX_BADGES (css_class, label) for a row dict/Series."""
    results = []
    for cond, css, lbl in _BADGE_DEFS:
        try:
            if cond(r):
                results.append((css, lbl))
        except Exception:
            pass
        if len(results) >= MAX_BADGES:
            break
    return results


def _badges_html(badges: list) -> str:
    if not badges:
        return ""
    return "".join(f'<span class="badge {css}">{lbl}</span>' for css, lbl in badges)


# ── Single explorer row ────────────────────────────────────────────────────────
def _row(r: pd.Series, idx: int, is_flip_candidate: bool) -> None:
    """Render one item row as HTML + a Streamlit detail button."""
    iid = int(r["id"])
    iid_str = str(iid)
    icon_url = WIKI_ICON_URL.format(r["icon"].replace(" ", "_")) if r.get("icon") else ""

    if is_flip_candidate:
        margin_html = f'<div class="expl-margin">{fmt_gp(r["margin"], short=True)}</div>'
        roi_html    = f'<div class="expl-roi">{fmt_pct(r["roi"])}</div>'
        badges      = _get_badges(r.to_dict() if hasattr(r, "to_dict") else r)
        badges_html = f'<div class="expl-badges">{_badges_html(badges)}</div>'
    else:
        margin_html = '<div class="expl-margin expl-nodata">—</div>'
        roi_html    = '<div class="expl-roi expl-nodata">—</div>'
        badges_html = '<div class="expl-badges"><span class="badge badge-slow">No Flip Data</span></div>'

    buy_price = r.get("buy_p", r.get("low", 0))

    col_row, col_btn = st.columns([12, 1], gap="small")

    with col_row:
        st.markdown(
            f'<div class="expl-row">'
            f'<img src="{icon_url}" class="expl-icon" onerror="this.style.display=\'none\'">'
            f'<div class="expl-name">{r["name"]}</div>'
            f'<div class="expl-price">{fmt_gp(buy_price, short=True)}</div>'
            f'{margin_html}'
            f'{roi_html}'
            f'{badges_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_btn:
        if st.button("→", key=f"expl_det_{iid}_{idx}", use_container_width=True):
            session.navigate("detail", iid)


# ── Main render ────────────────────────────────────────────────────────────────
def render(df_all: pd.DataFrame, mapping: dict, latest: dict, prof: dict) -> None:
    """
    Render the Market Explorer page.

    Parameters
    ----------
    df_all   : Scored flip candidates from compute_flips().
    mapping  : Full {item_id: info} dict from Wiki API (all items).
    latest   : Live prices dict {str(item_id): {high, low, ...}}.
    prof     : Active profile dict.
    """

    # ── Page header ──────────────────────────────────────────────────────
    st.markdown(
        f'<div style="margin-bottom:0.75rem;">'
        f'<div style="font-size:1.25rem;font-weight:700;color:{T["text"]};">⊞ Market Explorer</div>'
        f'<div class="ef-muted">'
        f'Search every tradeable item &nbsp;·&nbsp; '
        f'<strong style="color:{T["gold"]};">{len(df_all):,}</strong> flip candidates from '
        f'<strong style="color:{T["text"]};">{len(mapping):,}</strong> total items'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── Search bar + sort ─────────────────────────────────────────────────
    sb_col, sort_col, mode_col = st.columns([5, 2, 2], gap="small")

    with sb_col:
        query = st.text_input(
            "search",
            value=st.session_state.get("search_query", ""),
            placeholder="🔍  Search items... (e.g. 'shark', 'rune', 'abyssal')",
            label_visibility="collapsed",
            key="expl_search",
        )
        st.session_state.search_query = query

    with sort_col:
        sort_label = st.selectbox(
            "Sort by",
            list(_SORT_OPTS.keys()),
            index=0,
            key="expl_sort_select",
            label_visibility="collapsed",
        )
        sort_col_key = _SORT_OPTS[sort_label]

    with mode_col:
        show_all = st.toggle("Show all items", value=False, key="expl_show_all",
                              help="Include items with no flip margin data")

    st.markdown("<div style='height:0.25rem;'></div>", unsafe_allow_html=True)

    # ── Build item pool ───────────────────────────────────────────────────
    query_lower = query.strip().lower()

    if query_lower:
        # Search all mapping items by name
        matched_ids = [
            iid for iid, info in mapping.items()
            if query_lower in info.get("name", "").lower()
        ]
    else:
        # No query: show flip candidates (sorted), optionally all items
        matched_ids = None

    if matched_ids is not None:
        # Search mode: split into flip candidates vs price-only
        candidate_mask = df_all["id"].isin(matched_ids)
        df_candidates  = df_all[candidate_mask].copy()
        candidate_ids  = set(df_candidates["id"].tolist())
        other_ids      = [iid for iid in matched_ids if iid not in candidate_ids]

        # Build price-only rows for non-candidates
        price_only_rows = []
        for iid in other_ids[:50]:  # cap at 50
            info = mapping.get(iid, {})
            px   = latest.get(str(iid), {})
            if not px:
                continue
            price_only_rows.append({
                "id":   iid,
                "name": info.get("name", "?"),
                "icon": info.get("icon", ""),
                "low":  px.get("low", 0),
                "buy_p": (px.get("low", 0) or 0) + 1,
                "members": bool(info.get("members", False)),
            })
        df_price_only = pd.DataFrame(price_only_rows) if price_only_rows else pd.DataFrame()

    else:
        # No-query mode
        df_candidates  = df_all.copy()
        df_price_only  = pd.DataFrame()
        other_ids      = []

    # Sort candidates
    if sort_col_key in df_candidates.columns and not df_candidates.empty:
        df_candidates = df_candidates.sort_values(sort_col_key, ascending=False)
    df_candidates = df_candidates.reset_index(drop=True)

    # Result count display
    n_cand  = len(df_candidates)
    n_other = len(df_price_only) if not df_price_only.empty else 0
    n_total = n_cand + (n_other if show_all else 0)

    st.markdown(
        f'<div class="ef-muted" style="margin-bottom:0.5rem;">'
        f'Showing <strong style="color:{T["text"]};">{n_total}</strong> items'
        + (f' (<span style="color:{T["green"]};">{n_cand} flip candidates</span>'
           f' + <span style="color:{T["text_dim"]};">{n_other} price-only</span>)'
           if show_all and n_other else "")
        + f'</div>',
        unsafe_allow_html=True,
    )

    # ── Column headers ────────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:0;padding:0.3rem 0.9rem;'
        f'font-size:0.63rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;'
        f'color:{T["text_muted"]}; margin-bottom:3px;">'
        f'<div style="width:44px;flex-shrink:0;"></div>'
        f'<div style="flex:1;">Item</div>'
        f'<div style="width:90px;text-align:right;flex-shrink:0;">Price</div>'
        f'<div style="width:80px;text-align:right;flex-shrink:0;">Margin</div>'
        f'<div style="width:60px;text-align:right;flex-shrink:0;">ROI</div>'
        f'<div style="width:140px;text-align:right;flex-shrink:0;">Copilot</div>'
        f'<div style="width:40px;flex-shrink:0;"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Flip candidates ───────────────────────────────────────────────────
    if df_candidates.empty and not query_lower:
        st.info("Geen flip-kandidaten gevonden. Verhoog je cash stack of pas de filters aan.", icon="ℹ")
    else:
        # Paginate: show 50 at a time
        PAGE_SIZE = 50
        if "expl_page" not in st.session_state:
            st.session_state.expl_page = 0
        # Reset page on query/sort change
        if st.session_state.get("_last_expl_query") != query_lower:
            st.session_state.expl_page = 0
            st.session_state["_last_expl_query"] = query_lower

        start = st.session_state.expl_page * PAGE_SIZE
        end   = start + PAGE_SIZE
        df_page = df_candidates.iloc[start:end]

        for i, r in df_page.iterrows():
            _row(r, i, is_flip_candidate=True)

        # Pagination controls
        if len(df_candidates) > PAGE_SIZE:
            total_pages = (len(df_candidates) - 1) // PAGE_SIZE + 1
            pg_l, pg_mid, pg_r = st.columns([2, 3, 2])
            with pg_l:
                if st.button("← Previous", key="expl_prev_pg",
                             disabled=(st.session_state.expl_page == 0)):
                    st.session_state.expl_page -= 1
                    st.rerun()
            with pg_mid:
                st.markdown(
                    f'<div style="text-align:center;font-size:0.78rem;color:{T["text_dim"]};padding-top:0.4rem;">'
                    f'Page {st.session_state.expl_page+1} of {total_pages}</div>',
                    unsafe_allow_html=True,
                )
            with pg_r:
                if st.button("Next →", key="expl_next_pg",
                             disabled=(st.session_state.expl_page >= total_pages - 1)):
                    st.session_state.expl_page += 1
                    st.rerun()

    # ── Price-only results (search mode, show_all) ────────────────────────
    if show_all and not df_price_only.empty:
        st.markdown(
            f'<div class="ef-label" style="margin-top:1rem;">Other matches — no flip margin</div>',
            unsafe_allow_html=True,
        )
        for i, r in df_price_only.iterrows():
            _row(r, f"po_{i}", is_flip_candidate=False)
