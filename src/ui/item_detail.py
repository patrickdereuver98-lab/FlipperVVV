"""
item_detail.py — Item Detail deep-dive page.

Sections:
  1. Header     — icon, name, badges, wiki link, back button
  2. Fiscal row — Bruto → Tax → Netto (visual equation)
  3. Copilot AI Analysis card — verdict + detailed explanation
  4. Price chart (timeseries 5m)
  5. Trade Plan — qty, invest, potential profit
  6. Market Intelligence — volume, freshness, data age
  7. CTAs — Add to Slots, Watchlist, Manual Override
"""
import pandas as pd
import streamlit as st

import src.api.client as api
import src.state.session as session
from src.engine.formulas import (
    WIKI_ICON_URL, WIKI_ITEM_URL,
    fmt_gp, fmt_pct, fmt_age, age_seconds,
)
from src.ui.styles import T, label as section_label
from src.ui.explorer import _get_badges, _badges_html


# ── Copilot verdict engine ─────────────────────────────────────────────────────
def _copilot_verdict(r: pd.Series) -> tuple[str, str, str]:
    """
    Returns (verdict_html, detail_text, border_color).
    Verdict is a short human-readable recommendation.
    """
    roi         = r.get("roi", 0)
    vol         = r.get("vol_1h", 0)
    freshness   = r.get("freshness", 1.0)
    margin      = r.get("margin", 0)
    buy_p       = r.get("buy_p", 1)
    ge_lim      = r.get("ge_lim_fixed", 0)
    action      = r.get("action_score", 0)
    pot_profit  = r.get("pot_profit", 0)
    invest      = r.get("invest", 0)

    issues  = []
    pros    = []

    # Freshness
    if freshness < 0.45:
        issues.append("prijsdata is ouder dan 30 minuten — doe altijd een in-game margin check")
    elif freshness > 0.85:
        pros.append("zeer verse prijsdata (< 5 min)")

    # ROI
    if roi >= 3.0:
        pros.append(f"uitstekende ROI van {fmt_pct(roi)}")
    elif roi >= 1.0:
        pros.append(f"solide ROI van {fmt_pct(roi)}")
    elif roi < 0.5:
        issues.append(f"lage ROI van slechts {fmt_pct(roi)} — overweeg een beter item")

    # Volume
    if vol < 50:
        issues.append(f"laag volume ({vol:,}/u) — risico op slechte fill rate")
    elif vol >= 500:
        pros.append(f"hoog volume ({vol:,}/u) — snelle fills verwacht")

    # Margin vs price ratio (spread tightness)
    spread_pct = (margin / buy_p * 100) if buy_p > 0 else 0
    if spread_pct < 0.3:
        issues.append("erg krappe spread — gevoelig voor competitie")

    # Capital utilisation
    util_pct = (invest / max(1, st.session_state.raw_cash)) * 100
    if util_pct > 80:
        issues.append(f"bindt {util_pct:.0f}% van je cash — overweeg spreiding")
    elif util_pct < 5:
        pros.append("lage kapitaalbinding — laat cash vrij voor andere flips")

    # Verdict
    if action >= 0.75 and not issues:
        verdict = "🏆  Sterk aanbevolen — ideale flip voor je huidige stack"
        color   = T["green"]
    elif issues and len(issues) >= 2:
        verdict = "⚠️  Risicovol — evalueer zorgvuldig"
        color   = T["red"]
    elif issues:
        verdict = "🟡  Matig — let op de risicopunten hieronder"
        color   = T["gold"]
    else:
        verdict = "✅  Solide keuze — geen grote bezwaren"
        color   = T["green"]

    # Build detail text
    parts = []
    if pros:
        parts.append("✔ " + (" &nbsp;·&nbsp; ✔ ".join(pros)).capitalize() + ".")
    if issues:
        parts.append("⚠ " + (" &nbsp;·&nbsp; ⚠ ".join(issues)).capitalize() + ".")

    detail = " &nbsp; ".join(parts) if parts else "Geen bijzonderheden."

    return verdict, detail, color


def _age_cls(ts) -> str:
    age = age_seconds(ts)
    if age > 3_600: return "ef-dead"
    if age > 1_200: return "ef-stale"
    return "ef-fresh"


# ── Main renderer ──────────────────────────────────────────────────────────────
def render(df_all: pd.DataFrame, mapping: dict, latest: dict, prof: dict) -> None:
    """
    Render the Item Detail page for detail_item_id stored in session state.
    Falls back to the top action_score item if no ID is set.
    """
    iid = st.session_state.get("detail_item_id")

    # Find the row
    r: pd.Series | None = None
    if iid is not None and not df_all.empty:
        match = df_all[df_all["id"] == iid]
        if not match.empty:
            r = match.iloc[0]

    # Fallback: construct a basic row from mapping + latest
    if r is None and iid is not None:
        info = mapping.get(iid, {})
        px   = latest.get(str(iid), {})
        if info and px:
            low  = px.get("low", 0) or 0
            high = px.get("high", 0) or 0
            buy_p  = low + 1
            sell_p = high - 1
            r = pd.Series({
                "id": iid, "name": info.get("name", "?"), "icon": info.get("icon", ""),
                "members": bool(info.get("members", False)),
                "ge_lim": int(info.get("limit", 0)), "ge_lim_fixed": int(info.get("limit", 0) or 50_000),
                "high": high, "low": low, "buy_p": buy_p, "sell_p": sell_p,
                "high_ts": px.get("highTime", 0), "low_ts": px.get("lowTime", 0),
                "vol_1h": 0, "vol_5m": 0, "vol_use": 0,
                "tax": 0, "margin": 0, "roi": 0.0,
                "qty": 0, "pot_profit": 0, "invest": 0,
                "freshness": 1.0, "smart_score": 0.0, "action_score": 0.0,
                "has_override": False, "remaining_lim": 0,
            })

    if r is None:
        st.info("Selecteer een item uit de Explorer of de Terminal.", icon="ℹ")
        if st.button("← Terug naar Explorer", key="det_back_empty"):
            session.navigate("explorer")
        return

    iid_str     = str(int(r["id"]))
    icon_url    = WIKI_ICON_URL.format(r["icon"].replace(" ", "_")) if r.get("icon") else ""
    wiki_url    = WIKI_ITEM_URL.format(r["name"].replace(" ", "_"))
    is_full_row = r.get("margin", 0) > 0  # True if we have flip data

    # ── Back button + header ──────────────────────────────────────────────
    back_col, spacer = st.columns([2, 8])
    with back_col:
        if st.button("← Terug", key="det_back", use_container_width=True):
            prev = st.session_state.get("_detail_from_page", "explorer")
            session.navigate(prev)

    badges = _get_badges(r.to_dict() if hasattr(r, "to_dict") else {})
    badge_html = _badges_html(badges)
    member_tag = "Members" if r["members"] else "F2P"

    st.markdown(
        f'<div class="detail-header">'
        f'<img src="{icon_url}" class="detail-icon" onerror="this.style.display:none">'
        f'<div>'
        f'<div class="detail-title">{r["name"]}</div>'
        f'<div class="detail-sub">'
        f'{badge_html} &nbsp;'
        f'<span class="ef-pill ef-pill-{"blue" if r["members"] else "dim"}">{member_tag}</span>'
        f' &nbsp;·&nbsp; GE Limit: <span style="font-family:monospace;">{int(r.get("ge_lim_fixed", 0) or 0):,}</span>'
        f' &nbsp;·&nbsp; <a href="{wiki_url}" target="_blank" style="color:{T["blue"]};text-decoration:none;">↗ Wiki</a>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Fiscal equation row ───────────────────────────────────────────────
    if is_full_row:
        gross = r["sell_p"] - r["buy_p"]
        st.markdown(
            f'<div class="fiscal-row">'
            f'<div class="fiscal-cell">'
            f'<div class="fiscal-cell-label">Bruto Marge</div>'
            f'<div class="fiscal-cell-value" style="color:{T["text"]};">{fmt_gp(gross)}</div>'
            f'</div>'
            f'<div class="fiscal-sep">−</div>'
            f'<div class="fiscal-cell">'
            f'<div class="fiscal-cell-label" style="color:{T["red"]};">GE Tax (2%)</div>'
            f'<div class="fiscal-cell-value" style="color:{T["red"]};">-{fmt_gp(r["tax"])}</div>'
            f'</div>'
            f'<div class="fiscal-sep">=</div>'
            f'<div class="fiscal-cell" style="background:rgba(63,185,80,0.06);border-radius:6px;padding:8px;">'
            f'<div class="fiscal-cell-label" style="color:{T["green"]};">Netto per Item</div>'
            f'<div class="fiscal-cell-value" style="color:{T["green"]};">{fmt_gp(r["margin"])}</div>'
            f'</div>'
            f'<div class="fiscal-sep">&nbsp;</div>'
            f'<div class="fiscal-cell">'
            f'<div class="fiscal-cell-label">ROI</div>'
            f'<div class="fiscal-cell-value" style="color:{T["green"] if r["roi"] >= 1 else T["gold"]};">{fmt_pct(r["roi"])}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Price chart ───────────────────────────────────────────────────────
    ts_data = api.fetch_timeseries(int(r["id"]))
    if ts_data:
        import pandas as _pd
        df_ts = _pd.DataFrame(ts_data)
        df_ts["timestamp"] = _pd.to_datetime(df_ts["timestamp"], unit="s")
        df_ts = df_ts.set_index("timestamp")
        avail = [c for c in ["avgHighPrice", "avgLowPrice"] if c in df_ts.columns]
        if avail:
            chart_df = df_ts[avail].dropna()
            if not chart_df.empty:
                section_label("Prijshistorie (5m)")
                st.line_chart(chart_df, color=["#F85149", "#3FB950"][:len(avail)],
                              height=160, use_container_width=True)

    # ── Two-column body ───────────────────────────────────────────────────
    left, right = st.columns([5, 4], gap="large")

    with left:
        # Copilot Analysis
        if is_full_row:
            verdict, detail, c_color = _copilot_verdict(r)
            st.markdown(
                f'<div class="copilot-card">'
                f'<div class="copilot-title">🤖 Copilot Analyse</div>'
                f'<div class="copilot-verdict" style="color:{c_color};">{verdict}</div>'
                f'<div class="copilot-detail">{detail}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Trade Plan
        section_label("Trade Plan")
        if is_full_row:
            st.markdown(
                f"""
                <table style="width:100%;border-collapse:collapse;font-size:0.84rem;">
                  <tr><td style="color:{T['text_dim']};padding:4px 0;">Inkoop (Low+1)</td>
                      <td style="text-align:right;font-family:monospace;">{fmt_gp(r["buy_p"])}</td></tr>
                  <tr><td style="color:{T['text_dim']};padding:4px 0;">Verkoop (High-1)</td>
                      <td style="text-align:right;font-family:monospace;">{fmt_gp(r["sell_p"])}</td></tr>
                  <tr><td style="color:{T['text_dim']};padding:4px 0;">Aantal (qty)</td>
                      <td style="text-align:right;font-family:monospace;">{int(r.get('qty', 0)):,}</td></tr>
                  <tr><td style="color:{T['text_dim']};padding:4px 0;">GE Limiet (resterend)</td>
                      <td style="text-align:right;font-family:monospace;">{int(r.get('remaining_lim', 0)):,}</td></tr>
                  <tr><td style="color:{T['text_dim']};padding:4px 0;">Benodigde investering</td>
                      <td style="text-align:right;font-family:monospace;">{fmt_gp(r.get('invest', 0))}</td></tr>
                  <tr style="border-top:1px solid {T['border']};">
                    <td style="color:{T['text_dim']};padding:6px 0 3px;font-weight:600;">Potentieel Rendement</td>
                    <td style="text-align:right;font-family:monospace;color:{T['green']};font-weight:700;font-size:1rem;">
                      {fmt_gp(r.get('pot_profit', 0))}
                    </td>
                  </tr>
                </table>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="ef-muted">Dit item heeft momenteel geen kwalificerende flip marge.<br>'
                f'Controleer de prijzen in-game voor een handmatige override.</div>',
                unsafe_allow_html=True,
            )

    with right:
        # Market Intelligence
        section_label("Market Intelligence")
        freshness_pct = int(r.get("freshness", 1.0) * 100)
        fc = T["green"] if freshness_pct > 70 else T["gold"] if freshness_pct > 40 else T["red"]

        st.markdown(
            f"""
            <table style="width:100%;border-collapse:collapse;font-size:0.83rem;">
              <tr><td style="color:{T['text_dim']};padding:4px 0;">Volume (1h)</td>
                  <td style="text-align:right;font-family:monospace;">{int(r.get('vol_1h',0)):,}</td></tr>
              <tr><td style="color:{T['text_dim']};padding:4px 0;">Volume (5m)</td>
                  <td style="text-align:right;font-family:monospace;">{int(r.get('vol_5m',0)):,}</td></tr>
              <tr><td style="color:{T['text_dim']};padding:4px 0;">Leeftijd (low)</td>
                  <td style="text-align:right;"><span class="{_age_cls(r.get('low_ts'))}">{fmt_age(r.get('low_ts'))}</span></td></tr>
              <tr><td style="color:{T['text_dim']};padding:4px 0;">Leeftijd (high)</td>
                  <td style="text-align:right;"><span class="{_age_cls(r.get('high_ts'))}">{fmt_age(r.get('high_ts'))}</span></td></tr>
              <tr style="border-top:1px solid {T['border']};">
                <td style="color:{T['text_dim']};padding:6px 0 3px;">Data Versheid</td>
                <td style="text-align:right;color:{fc};font-weight:600;">{freshness_pct}%</td>
              </tr>
            </table>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

        # Action buttons
        section_label("Acties")
        in_slots    = iid_str in prof["active_flips"]
        slots_full  = len(prof["active_flips"]) >= session.MAX_SLOTS
        in_watchlist = iid_str in prof["watchlist"]

        if is_full_row:
            if in_slots:
                st.button("✓ Al in Actieve Slots", disabled=True,
                          key=f"det_slot_dis_{iid_str}", use_container_width=True)
            elif slots_full:
                st.button("✗ Slots Vol (8/8)", disabled=True,
                          key=f"det_full_{iid_str}", use_container_width=True)
            else:
                if st.button("＋ Toevoegen aan Slots", type="primary",
                             key=f"det_add_{iid_str}", use_container_width=True):
                    session.add_to_slots(prof, r)
                    st.rerun()

        if in_watchlist:
            if st.button("✕ Verwijder uit Watchlist", key=f"det_wl_rm_{iid_str}",
                         use_container_width=True):
                prof["watchlist"].remove(iid_str)
                st.rerun()
        else:
            if st.button("☆ Voeg toe aan Watchlist", key=f"det_wl_add_{iid_str}",
                         use_container_width=True):
                prof["watchlist"].append(iid_str)
                st.rerun()

        # Manual override
        with st.expander("⚙  Manual Margin Override"):
            st.caption("Gebruik actuele in-game margin check prijzen.")
            ov_c1, ov_c2 = st.columns(2)
            new_buy  = ov_c1.number_input("Inkoop prijs", value=int(r.get("buy_p", 1)),
                                           step=1, key=f"det_ovb_{iid_str}")
            new_sell = ov_c2.number_input("Verkoop prijs", value=int(r.get("sell_p", 1)),
                                           step=1, key=f"det_ovs_{iid_str}")
            ov_a, ov_b = st.columns(2)
            if ov_a.button("Toepassen", key=f"det_ov_apply_{iid_str}", use_container_width=True):
                prof["overrides"][iid_str] = {"buy": new_buy, "sell": new_sell}
                st.rerun()
            if r.get("has_override"):
                if ov_b.button("Reset", key=f"det_ov_clear_{iid_str}", use_container_width=True):
                    prof["overrides"].pop(iid_str, None)
                    st.rerun()
