"""
scanner.py — Action-First Hero Card Scanner.
Fiscaal gedreven: Bruto Marge - GE Tax = Netto Winst per item.
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
HERO_TOP_N    = 15   # Het aantal top-kansen in de carrousel
RUNNERUP_N    = 6    # Aantal runner-ups onder de kaart


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
        f'<span style="font-size:0.70rem; color:{color}; font-weight:600; font-family:monospace; width:30px; text-align:right;">{pct:.0f} %</span>'
        f'</div>'
    )


# ── Hero Card renderer ─────────────────────────────────────────────────────────
def _render_hero(r: pd.Series, rank: int, total: int, prof: dict) -> None:
    """Render de Hero Card met de expliciete netto winst berekening."""
    iid_str = str(int(r["id"]))
    freshness_pct = float(r.get("freshness", 1.0)) * 100
    
    # Berekening voor de UI (Bruto marge voor belasting)
    gross_margin = r["sell_p"] - r["buy_p"]
    net_profit_per_item = r["margin"] # Margin in core.py is al netto winst

    # ── Navigatie Toolbar ──────────────────────────────────────────────
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

        st.markdown(
            f"""
            <div class="hero-card">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1rem;">
                <div style="display:flex; align-items:center; gap:12px;">
                  <img src="{icon_url}" width="42" height="42" style="image-rendering:pixelated;">
                  <div>
                    <div class="hero-name">{r["name"]}</div>
                    <div class="hero-sub">Rank #{rank + 1} &nbsp;·&nbsp; <a href="{wiki_url}" target="_blank" style="color:{T['blue']}; text-decoration:none;">↗ Wiki</a></div>
                  </div>
                </div>
                <div style="text-align:right;">
                  <div class="hero-profit">+{fmt_gp(r["pot_profit"])}</div>
                  <div class="hero-profit-label">Totaal Netto Rendement</div>
                </div>
              </div>

              <div style="background:rgba(255,255,255,0.03); border-radius:6px; padding:15px; margin-bottom:1rem; border:1px solid var(--border);">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <div style="flex:1;">
                    <div style="font-size:0.7rem; color:var(--text-dim); text-transform:uppercase;">Bruto Marge</div>
                    <div style="font-size:1.1rem; font-weight:600;">{fmt_gp(gross_margin)}</div>
                  </div>
                  <div style="font-size:1.2rem; color:var(--text-muted); padding:0 15px;">−</div>
                  <div style="flex:1;">
                    <div style="font-size:0.7rem; color:var(--red); text-transform:uppercase;">GE Tax (2%)</div>
                    <div style="font-size:1.1rem; font-weight:600; color:var(--red);">-{fmt_gp(r['tax'])}</div>
                  </div>
                  <div style="font-size:1.2rem; color:var(--text-muted); padding:0 15px;">=</div>
                  <div style="flex:1; background:rgba(16,185,129,0.1); padding:8px; border-radius:4px; border:1px solid rgba(16,185,129,0.2);">
                    <div style="font-size:0.7rem; color:var(--green); text-transform:uppercase; font-weight:700;">Winst per item</div>
                    <div style="font-size:1.25rem; font-weight:800; color:var(--green);">{fmt_gp(net_profit_per_item)}</div>
                  </div>
                </div>
              </div>

              <div class="hero-stat-grid">
                <div class="hero-stat">
                    <div class="hero-stat-label">Inkoop (Low+1)</div>
                    <div class="hero-stat-value">{fmt_gp(r["buy_p"])}</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-label">Verkoop (High-1)</div>
                    <div class="hero-stat-value">{fmt_gp(r["sell_p"])}</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-label">Aantal (Qty)</div>
                    <div class="hero-stat-value">{int(r["qty"]):,} st</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-label">ROI (Netto)</div>
                    <div class="hero-stat-value" style="color:{T['green']};">{fmt_pct(r["roi"])}</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-label">Volume (1u)</div>
                    <div class="hero-stat-value">{int(r["vol_1h"]):,}</div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat-label">Investering</div>
                    <div class="hero-stat-value">{fmt_gp(r["invest"], short=True)}</div>
                </div>
              </div>

              <div style="margin-top:1rem;">
                <div style="font-size:0.65rem; color:var(--text-dim); text-transform:uppercase; margin-bottom:4px;">Data Versheid</div>
                {_freshness_bar(freshness_pct)}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── CTA buttons ─────────────────────────────────────────────────
        st.markdown("<div style='height:0.6rem;'></div>", unsafe_allow_html=True)
        cta1, cta2, cta3 = st.columns([3, 2, 2])

        in_slots = iid_str in prof["active_flips"]
        slots_full = len(prof["active_flips"]) >= session.MAX_SLOTS

        with cta1:
            if in_slots:
                st.button("✓ Actief in Slot", key=f"h_slot_{iid_str}", disabled=True, use_container_width=True)
            elif slots_full:
                st.button("⚠ Slots Vol (8/8)", key=f"h_full_{iid_str}", disabled=True, use_container_width=True)
            else:
                if st.button("➕ Toevoegen aan Slots", key=f"h_add_{iid_str}", type="primary", use_container_width=True):
                    session.add_to_slots(prof, r)
                    st.rerun()

        with cta2:
            if iid_str in prof["watchlist"]:
                if st.button("✕ Watchlist", key=f"h_wl_rm_{iid_str}", use_container_width=True):
                    prof["watchlist"].remove(iid_str); st.rerun()
            else:
                if st.button("⭐ Watchlist", key=f"h_wl_add_{iid_str}", use_container_width=True):
                    prof["watchlist"].append(iid_str); st.rerun()

        with cta3:
            with st.expander("⚙ Override"):
                ov_b = st.number_input("Koop", value=int(r["buy_p"]), step=1, key=f"h_ovb_{iid_str}")
                ov_s = st.number_input("Verkoop", value=int(r["sell_p"]), step=1, key=f"h_ovs_{iid_str}")
                if st.button("Bevestig", key=f"h_ov_apply_{iid_str}", use_container_width=True):
                    prof["overrides"][iid_str] = {"buy": ov_b, "sell": ov_s}
                    st.rerun()

# ── Runner-up feed ──────────────────────────────────────────────────────────────
def _render_runnerups(df: pd.DataFrame, hero_rank: int) -> None:
    """Render compacte runner-up rijen gebaseerd op netto winst ranking."""
    candidates = df.drop(index=hero_rank, errors="ignore").head(RUNNERUP_N).reset_index(drop=True)
    if candidates.empty: return

    st.markdown('<div class="section-title">Andere Top Kansen</div>', unsafe_allow_html=True)

    for i, r in candidates.iterrows():
        col_info, col_btn = st.columns([5, 1], gap="small")
        with col_info:
            st.markdown(
                f"""
                <div class="runner-card">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="color:var(--text-dim); font-family:monospace; width:25px;">#{i+2}</span>
                        <span style="font-weight:600;">{r["name"]}</span>
                    </div>
                    <div style="display:flex; gap:15px; align-items:center;">
                        <span style="font-size:0.8rem; color:var(--text-dim);">Netto: <span style="color:var(--green); font-weight:600;">+{fmt_gp(r["margin"], short=True)}</span></span>
                        <span style="font-size:0.8rem; color:var(--text-dim);">Totaal: <span style="color:var(--text); font-weight:600;">{fmt_gp(r["pot_profit"], short=True)}</span></span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button("Bekijk", key=f"ru_sel_{r['id']}", use_container_width=True):
                full_idx = df.index[df["id"] == r["id"]].tolist()
                if full_idx: st.session_state.hero_idx = int(full_idx[0])
                st.rerun()

# ── Main render ─────────────────────────────────────────────────────────────────
def render(df_all: pd.DataFrame, prof: dict) -> None:
    if df_all.empty:
        st.info("Geen items gevonden. Pas je kapitaal of filters aan.", icon="ℹ")
        return

    # Sortering op Action Score (die in core.py nu op Netto Winst leunt)
    df_view = df_all.sort_values("action_score", ascending=False).reset_index(drop=True).head(HERO_TOP_N)
    total = len(df_view)

    if "hero_idx" not in st.session_state: st.session_state.hero_idx = 0
    hero_idx = int(st.session_state.hero_idx) % total

    # Hero Card
    _render_hero(df_view.iloc[hero_idx], hero_idx, total, prof)

    # Feed
    _render_runnerups(df_view, hero_idx)
