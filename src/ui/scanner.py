"""
scanner.py — Terminal Home: Action-First Hero Card.

Runner-up "View" buttons now navigate to the Item Detail page instead
of just jumping the carousel index.
"""
import pandas as pd
import streamlit as st

import src.api.client as api
import src.state.session as session
from src.engine.formulas import WIKI_ICON_URL, WIKI_ITEM_URL, fmt_gp, fmt_pct, fmt_age, age_seconds
from src.ui.styles import T

HERO_TOP_N  = 15
RUNNERUP_N  = 6


def _age_class(ts) -> str:
    age = age_seconds(ts)
    if age > 3_600: return "ef-dead"
    if age > 1_200: return "ef-stale"
    return "ef-fresh"


def _freshness_bar(pct: float) -> str:
    color = T["green"] if pct > 70 else T["gold"] if pct > 40 else T["red"]
    return (
        f'<div style="display:flex;align-items:center;gap:6px;">'
        f'<div style="flex:1;height:4px;background:#30363D;border-radius:2px;overflow:hidden;">'
        f'<div style="height:100%;width:{pct:.0f}%;background:{color};border-radius:2px;"></div>'
        f'</div>'
        f'<span style="font-size:0.70rem;color:{color};font-weight:600;font-family:monospace;width:30px;text-align:right;">{pct:.0f}%</span>'
        f'</div>'
    )


def _render_hero(r: pd.Series, rank: int, total: int, prof: dict) -> None:
    iid_str = str(int(r["id"]))
    freshness_pct = float(r.get("freshness", 1.0)) * 100
    gross_margin  = r["sell_p"] - r["buy_p"]
    net_per_item  = r["margin"]

    nav_l, card_col, nav_r = st.columns([1, 14, 1], gap="small")

    with nav_l:
        st.markdown("<div style='height:8rem;'></div>", unsafe_allow_html=True)
        if st.button("◀", key="hero_prev", use_container_width=True, disabled=(rank == 0)):
            st.session_state.hero_idx = max(0, rank - 1)
            st.rerun()

    with nav_r:
        st.markdown("<div style='height:8rem;'></div>", unsafe_allow_html=True)
        if st.button("▶", key="hero_next", use_container_width=True, disabled=(rank >= total - 1)):
            st.session_state.hero_idx = min(total - 1, rank + 1)
            st.rerun()

    with card_col:
        icon_url = WIKI_ICON_URL.format(r["icon"].replace(" ", "_")) if r.get("icon") else ""
        wiki_url = WIKI_ITEM_URL.format(r["name"].replace(" ", "_"))
        member_tag = "Members" if r["members"] else "F2P"
        roi_color  = T["green"] if r["roi"] >= 1.0 else T["gold"]

        st.markdown(
            f"""
            <div class="hero-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;">
                <div style="display:flex;align-items:center;gap:12px;">
                  <img src="{icon_url}" width="44" height="44" style="image-rendering:pixelated;">
                  <div>
                    <div class="hero-name">{r["name"]}</div>
                    <div class="hero-sub">
                      Rank #{rank+1} of {total} &nbsp;·&nbsp; {member_tag} &nbsp;·&nbsp;
                      <a href="{wiki_url}" target="_blank" style="color:{T['blue']};text-decoration:none;">↗ Wiki</a>
                    </div>
                  </div>
                </div>
                <div style="text-align:right;">
                  <div class="hero-profit">+{fmt_gp(r["pot_profit"])}</div>
                  <div class="hero-profit-label">Totaal Netto Rendement</div>
                </div>
              </div>

              <div style="background:rgba(255,255,255,0.03);border-radius:6px;padding:14px;margin-bottom:1rem;border:1px solid var(--border);">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                  <div style="flex:1;">
                    <div style="font-size:0.65rem;color:var(--text-dim);text-transform:uppercase;font-weight:600;margin-bottom:3px;">Bruto Marge</div>
                    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;">{fmt_gp(gross_margin)}</div>
                  </div>
                  <div style="font-size:1.2rem;color:var(--text-muted);padding:0 14px;">−</div>
                  <div style="flex:1;">
                    <div style="font-size:0.65rem;color:{T['red']};text-transform:uppercase;font-weight:600;margin-bottom:3px;">GE Tax</div>
                    <div style="font-size:1.1rem;font-weight:600;font-family:monospace;color:{T['red']};"> -{fmt_gp(r['tax'])}</div>
                  </div>
                  <div style="font-size:1.2rem;color:var(--text-muted);padding:0 14px;">=</div>
                  <div style="flex:1;background:rgba(63,185,80,0.08);padding:10px;border-radius:6px;border:1px solid rgba(63,185,80,0.2);">
                    <div style="font-size:0.65rem;color:{T['green']};text-transform:uppercase;font-weight:700;margin-bottom:3px;">Netto per Item</div>
                    <div style="font-size:1.25rem;font-weight:800;font-family:monospace;color:{T['green']};">{fmt_gp(net_per_item)}</div>
                  </div>
                </div>
              </div>

              <div class="hero-stat-grid">
                <div class="hero-stat"><div class="hero-stat-label">Inkoop (Low+1)</div><div class="hero-stat-value">{fmt_gp(r["buy_p"])}</div></div>
                <div class="hero-stat"><div class="hero-stat-label">Verkoop (High-1)</div><div class="hero-stat-value">{fmt_gp(r["sell_p"])}</div></div>
                <div class="hero-stat"><div class="hero-stat-label">Aantal (Qty)</div><div class="hero-stat-value">{int(r["qty"]):,} st</div></div>
                <div class="hero-stat"><div class="hero-stat-label">ROI (Netto)</div><div class="hero-stat-value" style="color:{roi_color};">{fmt_pct(r["roi"])}</div></div>
                <div class="hero-stat"><div class="hero-stat-label">Volume (1u)</div><div class="hero-stat-value">{int(r["vol_1h"]):,}</div></div>
                <div class="hero-stat"><div class="hero-stat-label">Investering</div><div class="hero-stat-value">{fmt_gp(r["invest"], short=True)}</div></div>
              </div>

              <div style="margin-top:1rem;">
                <div style="font-size:0.62rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.08em;font-weight:700;margin-bottom:4px;">Data Versheid</div>
                {_freshness_bar(freshness_pct)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Price chart
        ts_data = api.fetch_timeseries(int(r["id"]))
        if ts_data:
            import pandas as _pd
            df_ts = _pd.DataFrame(ts_data)
            df_ts["timestamp"] = _pd.to_datetime(df_ts["timestamp"], unit="s")
            df_ts = df_ts.set_index("timestamp")
            cols_avail = [c for c in ["avgHighPrice", "avgLowPrice"] if c in df_ts.columns]
            if cols_avail:
                chart_df = df_ts[cols_avail].dropna()
                if not chart_df.empty:
                    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
                    st.line_chart(chart_df, color=["#F85149", "#3FB950"][:len(cols_avail)],
                                  height=110, use_container_width=True)

        # CTAs
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        cta1, cta2, cta3, cta4 = st.columns([3, 2, 2, 2])

        in_slots    = iid_str in prof["active_flips"]
        slots_full  = len(prof["active_flips"]) >= session.MAX_SLOTS
        in_watchlist = iid_str in prof["watchlist"]

        with cta1:
            if in_slots:
                st.button("✓ In Slot", key=f"h_slot_{iid_str}", disabled=True, use_container_width=True)
            elif slots_full:
                st.button("✗ Slots Vol", key=f"h_full_{iid_str}", disabled=True, use_container_width=True)
            else:
                if st.button("＋ Add to Slots", key=f"h_add_{iid_str}", type="primary", use_container_width=True):
                    session.add_to_slots(prof, r)
                    st.rerun()
        with cta2:
            if in_watchlist:
                if st.button("✕ Watchlist", key=f"h_wl_rm_{iid_str}", use_container_width=True):
                    prof["watchlist"].remove(iid_str); st.rerun()
            else:
                if st.button("☆ Watchlist", key=f"h_wl_add_{iid_str}", use_container_width=True):
                    prof["watchlist"].append(iid_str); st.rerun()
        with cta3:
            if st.button("⊞ Explorer", key=f"h_expl_{iid_str}", use_container_width=True):
                session.navigate("explorer")
        with cta4:
            if st.button("Detail →", key=f"h_det_{iid_str}", use_container_width=True):
                session.navigate("detail", int(r["id"]))


def _render_runnerups(df: pd.DataFrame, hero_rank: int, prof: dict) -> None:
    candidates = df.drop(index=hero_rank, errors="ignore").head(RUNNERUP_N).reset_index(drop=True)
    if candidates.empty:
        return

    st.markdown(
        f'<div class="ef-label" style="margin-top:1.2rem;">Andere Top Kansen</div>',
        unsafe_allow_html=True,
    )

    for i, r in candidates.iterrows():
        full_idx = df.index[df["id"] == r["id"]].tolist()
        rank_label = full_idx[0] + 1 if full_idx else i + 2
        col_info, col_btn1, col_btn2 = st.columns([7, 1, 1], gap="small")

        with col_info:
            st.markdown(
                f'<div class="runnerup">'
                f'<div class="runnerup-rank">#{rank_label}</div>'
                f'<div class="runnerup-name">{r["name"]}</div>'
                f'<div class="runnerup-profit">{fmt_gp(r["pot_profit"], short=True)}</div>'
                f'<div class="runnerup-roi">{fmt_pct(r["roi"])}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_btn1:
            if st.button("Card", key=f"ru_card_{r['id']}", use_container_width=True):
                if full_idx:
                    st.session_state.hero_idx = int(full_idx[0])
                st.rerun()
        with col_btn2:
            if st.button("Detail", key=f"ru_det_{r['id']}", use_container_width=True):
                session.navigate("detail", int(r["id"]))


def render(df_all: pd.DataFrame, prof: dict) -> None:
    if df_all.empty:
        st.info("Geen items gevonden. Pas je kapitaal of filters aan.", icon="ℹ")
        return

    df_view = df_all.sort_values("action_score", ascending=False).reset_index(drop=True).head(HERO_TOP_N)
    total = len(df_view)
    if total == 0:
        st.warning("Geen kwalificerende items na filteren.")
        return

    if "hero_idx" not in st.session_state:
        st.session_state.hero_idx = 0
    hero_idx = int(st.session_state.hero_idx) % total

    ctx_l, ctx_r = st.columns([5, 3])
    with ctx_l:
        st.markdown(
            f'<div class="ef-muted"><span class="ef-dot ef-dot-green"></span>'
            f'<strong style="color:{T["text"]};">{len(df_all):,}</strong> qualifying items &nbsp;·&nbsp; '
            f'Top <strong style="color:{T["gold"]};">{total}</strong> by Action Score</div>',
            unsafe_allow_html=True,
        )
    with ctx_r:
        st.markdown(
            f'<div style="text-align:right;font-size:0.75rem;color:{T["text_dim"]};">'
            f'Card {hero_idx+1} of {total} &nbsp;·&nbsp; ◀ ▶ to navigate</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.3rem;'></div>", unsafe_allow_html=True)
    _render_hero(df_view.iloc[hero_idx], hero_idx, total, prof)

    df_full = df_all.sort_values("action_score", ascending=False).reset_index(drop=True)
    _render_runnerups(df_full, hero_idx, prof)
