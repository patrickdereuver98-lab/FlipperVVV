"""
scanner.py — Action-First Hero Card Scanner.

Layout:
  ┌─────────────────────────────────────────────────────────┐
  │  ← (prev)   [HERO CARD — #1 trade for your cash]  (next) →  │
  │             [★ Watchlist]   [+ Add to Slots CTA]            │
  ├─────────────────────────────────────────────────────────┤
  │  Runner-ups #2 – #9  (compact feed rows)                │
  └─────────────────────────────────────────────────────────┘

The hero card is sorted by action_score (capital-aware) — see core.py.
Runner-ups use the same action_score ranking so the list is consistent.
"""
import math
import pandas as pd
import streamlit as st

import src.api.client as api
from src.engine.formulas import (
    WIKI_ICON_URL, WIKI_ITEM_URL,
    fmt_gp, fmt_pct, fmt_age, age_seconds,
)
import src.state.session as session
from src.ui.styles import T

# ── Constants ──────────────────────────────────────────────────────────────────
HERO_TOP_N    = 10   # How many cards to swipe through
RUNNERUP_N    = 8    # Runner-ups shown below the hero card


# ── Age helper ─────────────────────────────────────────────────────────────────
def _age_class(ts) -> str:
    age = age_seconds(ts)
    if age > 3_600: return "ef-dead"
    if age > 1_200: return "ef-stale"
    return "ef-fresh"


# ── Freshness bar HTML ──────────────────────────────────────────────────────────
def _freshness_bar(pct: float) -> str:
    color = T["green"] if pct > 70 else T["gold"] if pct > 40 else T["red"]
    return (
        f'<div style="display:flex; align-items:center; gap:6px;">'
        f'<div style="flex:1; height:4px; background:#30363D; border-radius:2px; overflow:hidden;">'
        f'<div style="height:100%; width:{pct:.0f}%; background:{color}; border-radius:2px;"></div>'
        f'</div>'
        f'<span style="font-size:0.70rem; color:{color}; font-weight:600; font-family:monospace; width:30px; text-align:right;">{pct:.0f}%</span>'
        f'</div>'
    )


# ── Hero Card renderer ─────────────────────────────────────────────────────────
def _render_hero(r: pd.Series, rank: int, total: int, prof: dict) -> None:
    """Render the hero card for a single item row."""
    iid_str = str(int(r["id"]))
    freshness_pct = float(r.get("freshness", 1.0)) * 100

    # ── Navigation row: ← [card] → ──────────────────────────────────────
    nav_l, card_col, nav_r = st.columns([1, 14, 1], gap="small")

    with nav_l:
        st.markdown("<div style='height:5rem;'></div>", unsafe_allow_html=True)
        if st.button("◀", key="hero_prev", use_container_width=True,
                     disabled=(rank == 0)):
            st.session_state.hero_idx = max(0, rank - 1)
            st.rerun()

    with nav_r:
        st.markdown("<div style='height:5rem;'></div>", unsafe_allow_html=True)
        if st.button("▶", key="hero_next", use_container_width=True,
                     disabled=(rank >= total - 1)):
            st.session_state.hero_idx = min(total - 1, rank + 1)
            st.rerun()

    with card_col:
        # ── Hero card HTML block ─────────────────────────────────────────
        member_pill = (
            '<span class="ef-pill ef-pill-blue">Members</span>'
            if r["members"]
            else '<span class="ef-pill ef-pill-dim">F2P</span>'
        )
        override_pill = (
            '<span class="ef-pill ef-pill-gold" style="margin-left:6px;">Override</span>'
            if r.get("has_override") else ""
        )
        wiki_url = WIKI_ITEM_URL.format(r["name"].replace(" ", "_"))
        icon_url = WIKI_ICON_URL.format(r["icon"].replace(" ", "_")) if r.get("icon") else None
        icon_html = (
            f'<img src="{icon_url}" width="36" height="36" '
            f'style="image-rendering:pixelated; margin-right:10px; flex-shrink:0;">'
            if icon_url else ""
        )

        roi_color   = T["green"] if r["roi"] >= 1.0 else T["gold"]
        invest_str  = fmt_gp(r["invest"], short=True)
        vol_display = f"{int(r['vol_1h']):,}" if r["vol_1h"] > 0 else f"~{int(r['vol_5m']):,}/5m"

        st.markdown(
            f"""
            <div class="hero-card">
              <!-- Top bar: rank + nav indicator -->
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
                <div class="hero-rank">🏆 Rank #{rank + 1} of {total} &nbsp;·&nbsp; Top Pick for Your Stack</div>
                <div style="font-size:0.68rem; color:{T['text_muted']}; font-family:monospace;">
                  {"● " * min(rank+1, 5)}{"○ " * max(0, 5 - rank - 1)}
                </div>
              </div>

              <!-- Item header -->
              <div style="display:flex; align-items:center; margin-bottom:0.5rem;">
                {icon_html}
                <div>
                  <div class="hero-name">{r["name"]} {override_pill}</div>
                  <div class="hero-sub">
                    {member_pill} &nbsp;
                    <a href="{wiki_url}" target="_blank" style="color:{T['blue']}; text-decoration:none; font-size:0.75rem;">↗ Wiki</a>
                    &nbsp;·&nbsp; GE Limit: <span style="font-family:monospace;">{int(r["ge_lim_fixed"]):,}</span>
                  </div>
                </div>
              </div>

              <!-- Big profit number -->
              <div>
                <div class="hero-profit">{fmt_gp(r["pot_profit"])}</div>
                <div class="hero-profit-label">Max Potential Profit &nbsp;·&nbsp; {int(r["qty"]):,} units × {fmt_gp(r["margin"])} margin</div>
              </div>

              <!-- Stat grid -->
              <div class="hero-stat-grid">
                <div class="hero-stat">
                  <div class="hero-stat-label">Buy (instasell)</div>
                  <div class="hero-stat-value">{fmt_gp(r["buy_p"])}</div>
                </div>
                <div class="hero-stat">
                  <div class="hero-stat-label">Sell (instabuy)</div>
                  <div class="hero-stat-value">{fmt_gp(r["sell_p"])}</div>
                </div>
                <div class="hero-stat">
                  <div class="hero-stat-label">Net Margin</div>
                  <div class="hero-stat-value" style="color:{T['green']};">{fmt_gp(r["margin"])}</div>
                </div>
                <div class="hero-stat">
                  <div class="hero-stat-label">ROI</div>
                  <div class="hero-stat-value" style="color:{roi_color};">{fmt_pct(r["roi"])}</div>
                </div>
                <div class="hero-stat">
                  <div class="hero-stat-label">Capital Required</div>
                  <div class="hero-stat-value">{invest_str}</div>
                </div>
                <div class="hero-stat">
                  <div class="hero-stat-label">Volume (1h)</div>
                  <div class="hero-stat-value">{vol_display}</div>
                </div>
              </div>

              <!-- Freshness row -->
              <div style="margin-top:0.85rem; display:flex; align-items:center; gap:1rem;">
                <div style="flex:1;">
                  <div style="font-size:0.62rem; color:{T['text_muted']}; text-transform:uppercase; letter-spacing:0.08em; font-weight:700; margin-bottom:3px;">Data Freshness</div>
                  {_freshness_bar(freshness_pct)}
                </div>
                <div style="text-align:right;">
                  <div style="font-size:0.62rem; color:{T['text_muted']}; text-transform:uppercase; letter-spacing:0.08em; font-weight:700; margin-bottom:3px;">Price Age</div>
                  <div style="font-size:0.75rem;">
                    Low: <span class="{_age_class(r['low_ts'])}">{fmt_age(r['low_ts'])}</span>
                    &nbsp;·&nbsp;
                    High: <span class="{_age_class(r['high_ts'])}">{fmt_age(r['high_ts'])}</span>
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Price chart (inside card_col, below the HTML card) ─────────
        ts_data = api.fetch_timeseries(int(r["id"]))
        if ts_data:
            df_ts = pd.DataFrame(ts_data)
            df_ts["timestamp"] = pd.to_datetime(df_ts["timestamp"], unit="s")
            df_ts = df_ts.set_index("timestamp")
            cols_avail = [c for c in ["avgHighPrice", "avgLowPrice"] if c in df_ts.columns]
            if cols_avail:
                chart_df = df_ts[cols_avail].dropna()
                if not chart_df.empty:
                    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
                    st.line_chart(
                        chart_df,
                        color=["#F85149", "#3FB950"][: len(cols_avail)],
                        height=110,
                        use_container_width=True,
                    )

        # ── CTA buttons ─────────────────────────────────────────────────
        st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
        cta1, cta2, cta3 = st.columns([3, 2, 2])

        in_slots    = iid_str in prof["active_flips"]
        slots_full  = len(prof["active_flips"]) >= session.MAX_SLOTS
        in_watchlist = iid_str in prof["watchlist"]

        with cta1:
            if in_slots:
                st.button("✓  In Active Slots", key=f"h_slot_{iid_str}", disabled=True, use_container_width=True)
            elif slots_full:
                st.button("✗  Slots Full (8/8)", key=f"h_full_{iid_str}", disabled=True, use_container_width=True)
            else:
                if st.button("＋  Add to Slots", key=f"h_add_{iid_str}", type="primary", use_container_width=True):
                    session.add_to_slots(prof, r)
                    st.rerun()

        with cta2:
            if in_watchlist:
                if st.button("✕  Watchlist", key=f"h_wl_rm_{iid_str}", use_container_width=True):
                    prof["watchlist"].remove(iid_str)
                    st.rerun()
            else:
                if st.button("☆  Watchlist", key=f"h_wl_add_{iid_str}", use_container_width=True):
                    prof["watchlist"].append(iid_str)
                    st.rerun()

        with cta3:
            with st.expander("⚙  Override"):
                ov_b = st.number_input("Buy", value=int(r["buy_p"]), step=1, key=f"h_ovb_{iid_str}")
                ov_s = st.number_input("Sell", value=int(r["sell_p"]), step=1, key=f"h_ovs_{iid_str}")
                if st.button("Apply", key=f"h_ov_apply_{iid_str}", use_container_width=True):
                    prof["overrides"][iid_str] = {"buy": ov_b, "sell": ov_s}
                    st.rerun()
                if r.get("has_override"):
                    if st.button("Clear", key=f"h_ov_clear_{iid_str}", use_container_width=True):
                        prof["overrides"].pop(iid_str, None)
                        st.rerun()


# ── Runner-up feed ──────────────────────────────────────────────────────────────
def _render_runnerups(df: pd.DataFrame, hero_rank: int, prof: dict) -> None:
    """Render compact runner-up rows below the hero card."""
    # Show items after the hero, up to RUNNERUP_N items, cycling through the top
    # We always show a fixed slice so the feed feels stable
    # Items at positions 1..RUNNERUP_N+1 (skip hero)
    candidates = df.drop(index=hero_rank, errors="ignore").head(RUNNERUP_N).reset_index(drop=True)

    if candidates.empty:
        return

    st.markdown(
        f'<div class="ef-label" style="margin-top:1.2rem;">Runner-ups</div>',
        unsafe_allow_html=True,
    )

    for i, r in candidates.iterrows():
        iid_str = str(int(r["id"]))
        rank_in_full = df.index[df["id"] == r["id"]].tolist()
        rank_label = rank_in_full[0] + 1 if rank_in_full else i + 2

        col_info, col_nums, col_btn = st.columns([6, 3, 2], gap="small")

        with col_info:
            member_tag = "M" if r["members"] else "F"
            ovr_tag = " ✎" if r.get("has_override") else ""
            st.markdown(
                f"""
                <div class="runnerup">
                  <div class="runnerup-rank">#{rank_label}</div>
                  <div class="runnerup-name">{r["name"]}{ovr_tag}</div>
                  <span class="ef-pill ef-pill-dim" style="margin-right:4px; font-size:0.60rem;">{member_tag}</span>
                  <div class="runnerup-profit">{fmt_gp(r["pot_profit"], short=True)}</div>
                  <div class="runnerup-roi">{fmt_pct(r["roi"])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_nums:
            st.markdown(
                f"""
                <div style="padding:0.35rem 0; font-size:0.78rem; color:{T['text_dim']}; line-height:1.8;">
                  Margin: <span style="color:{T['text']}; font-family:monospace;">{fmt_gp(r["margin"], short=True)}</span>
                  &nbsp;·&nbsp;
                  Vol: <span style="font-family:monospace;">{int(r["vol_1h"]):,}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_btn:
            in_slots = iid_str in prof["active_flips"]
            if in_slots:
                st.button("✓", key=f"ru_s_{iid_str}", disabled=True, use_container_width=True)
            else:
                if st.button("Select", key=f"ru_sel_{iid_str}", use_container_width=True):
                    # Jump hero to this item
                    full_idx = df.index[df["id"] == r["id"]].tolist()
                    if full_idx:
                        st.session_state.hero_idx = int(full_idx[0])
                    st.rerun()


# ── Main render ─────────────────────────────────────────────────────────────────
def render(df_all: pd.DataFrame, prof: dict) -> None:
    """
    Render the Scanner tab.

    df_all is sorted by action_score (capital-aware) before arrival.
    The hero_idx session key controls which item is displayed as hero.
    """
    if df_all.empty:
        st.info(
            "Geen items gevonden. Verhoog je cash stack of pas je filters aan.",
            icon="ℹ",
        )
        return

    # Sort by action_score (capital-aware, computed in core.py)
    sort_col = "action_score" if "action_score" in df_all.columns else "smart_score"
    df_view = (
        df_all.sort_values(sort_col, ascending=False)
        .reset_index(drop=True)
        .head(HERO_TOP_N)
    )

    total = len(df_view)
    if total == 0:
        st.warning("Geen kwalificerende items na filteren.")
        return

    # Initialise / clamp hero index
    if "hero_idx" not in st.session_state:
        st.session_state.hero_idx = 0
    hero_idx = int(st.session_state.hero_idx) % total

    # ── Context bar ──────────────────────────────────────────────────────
    ctx_l, ctx_r = st.columns([5, 3])
    with ctx_l:
        st.markdown(
            f'<div class="ef-muted">'
            f'<span class="ef-dot ef-dot-green"></span>'
            f'<strong style="color:{T["text"]};">{len(df_all):,}</strong> qualifying items &nbsp;·&nbsp;'
            f'Showing top <strong style="color:{T["gold"]};">{total}</strong> by Action Score'
            f'</div>',
            unsafe_allow_html=True,
        )
    with ctx_r:
        st.markdown(
            f'<div style="text-align:right; font-size:0.75rem; color:{T["text_dim"]};">'
            f'Card {hero_idx + 1} of {total} &nbsp;·&nbsp; '
            f'Use ◀ ▶ to navigate'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.3rem;'></div>", unsafe_allow_html=True)

    # ── Hero Card ─────────────────────────────────────────────────────────
    _render_hero(df_view.iloc[hero_idx], hero_idx, total, prof)

    # ── Runner-up feed ────────────────────────────────────────────────────
    # Use full df_all for the feed, sorted same way, excluding current hero
    df_full_sorted = (
        df_all.sort_values(sort_col, ascending=False)
        .reset_index(drop=True)
    )
    _render_runnerups(df_full_sorted, hero_idx, prof)
