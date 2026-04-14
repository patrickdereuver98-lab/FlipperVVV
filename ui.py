import streamlit as st
import pandas as pd
from datetime import datetime
import time
import core
import api

def render_item_detail(r, prof, is_watchlist=False):
    iid_str = str(r['id'])
    low_age_sec = core.get_age_seconds(r['low_ts'])
    high_age_sec = core.get_age_seconds(r['high_ts'])
    def get_age_class(age): return "age-danger" if age > 3600 else "age-warning" if age > 1800 else "text-green"

    h1, h2, h3 = st.columns([1, 5, 3])
    with h1:
        if r["icon"]: st.image(core.WIKI_ICON_URL.format(r["icon"].replace(" ", "_")), width=40)
    with h2:
        title = f"{r['Naam']} {'(🛠️ Override)' if r.get('has_override') else ''}"
        st.markdown(f'<div style="font-size:1.4rem; font-weight:bold;" class="text-orange">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="text-muted"><a href="{core.WIKI_ITEM_URL.format(r["Naam"].replace(" ", "_"))}" target="_blank" style="color:var(--rl-orange)">Wiki</a></div>', unsafe_allow_html=True)
    with h3:
        if iid_str in prof['watchlist']:
            if st.button("❌ Verwijder Watchlist", key=f"wl_del_{iid_str}", use_container_width=True):
                prof['watchlist'].remove(iid_str)
                st.rerun()
        else:
            if st.button("⭐ Naar Watchlist", key=f"wl_add_{iid_str}", use_container_width=True):
                prof['watchlist'].append(iid_str)
                st.rerun()
                
        if iid_str not in prof['active_flips']:
            if st.button("➕ Naar Slots", type="primary", key=f"slot_add_{iid_str}", use_container_width=True):
                if len(prof['active_flips']) < 8:
                    prof['active_flips'][iid_str] = {"name": r["Naam"], "qty": int(r["qty"]), "buy_p": int(r["buy_p"]), "sell_p": int(r["sell_p"])}
                    st.rerun()
                else: st.error("Maximum slots bereikt!")
        else:
            st.button("✅ In Portfolio", disabled=True, key=f"slot_dis_{iid_str}", use_container_width=True)

    ts_data = api.fetch_timeseries(r['id'])
    if ts_data:
        df_ts = pd.DataFrame(ts_data)
        df_ts['timestamp'] = pd.to_datetime(df_ts['timestamp'], unit='s')
        df_ts.set_index('timestamp', inplace=True)
        st.line_chart(df_ts[['avgHighPrice', 'avgLowPrice']].dropna(), color=["#f44336", "#4caf50"], height=150)

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Bod (Low+1)", core.fmt(r['buy_p']))
        c2.metric("Vraag (High-1)", core.fmt(r['sell_p']))
        c3.metric("Netto Margin", core.fmt(r['margin']))

    with st.container(border=True):
        c1, c2 = st.columns(2)
        c1.write(f"**Max Aantal (Vrij Cash):** {int(r['qty']):,}")
        c1.write(f"**GE Limiet (Resterend):** {int(r['remaining_lim']):,}")
        c1.write(f"**Benodigd Kapitaal:** {core.fmt(r['invest'])}")
        c1.write(f"**Potentiële Winst:** :green[{core.fmt(r['pot_profit'])}]")
        
        c2.write(f"**Volume (1u):** {int(r['vol_1h']):,}")
        c2.write(f"**ROI:** {core.fmtp(r['roi'])}")
        if not r.get('has_override'):
            c2.markdown(f"**Laatste Bod:** <span class='{get_age_class(low_age_sec)}'>{core.age_s(r['low_ts'])}</span>", unsafe_allow_html=True)
            c2.markdown(f"**Laatste Vraag:** <span class='{get_age_class(high_age_sec)}'>{core.age_s(r['high_ts'])}</span>", unsafe_allow_html=True)

    with st.expander("🛠️ Handmatige Margin Override"):
        o1, o2 = st.columns(2)
        new_buy = o1.number_input("In-game Bod", value=r['buy_p'], step=1, key=f"ovb_{iid_str}")
        new_sell = o2.number_input("In-game Vraag", value=r['sell_p'], step=1, key=f"ovs_{iid_str}")
        o3, o4 = st.columns(2)
        if o3.button("Toepassen", use_container_width=True, key=f"ov_apply_{iid_str}"):
            prof['overrides'][iid_str] = {'buy': new_buy, 'sell': new_sell}
            st.rerun()
        if r.get('has_override') and o4.button("Reset", use_container_width=True, key=f"ov_res_{iid_str}"):
            del prof['overrides'][iid_str]
            st.rerun()

def render_portfolio_tab(prof, latest_data):
    st.markdown('<div class="section-title">Live Portfolio Tracking</div>', unsafe_allow_html=True)
    if not prof['active_flips']: return st.info("Geen actieve slots.")
    
    cols = st.columns(2)
    for idx, (iid_str, flip) in enumerate(list(prof['active_flips'].items())):
        live_data = latest_data.get(iid_str, {})
        l_low, l_high = live_data.get("low", 0), live_data.get("high", 0)
        status_msgs, _ = core.evaluate_active_flip(flip["buy_p"], flip["sell_p"], l_low, l_high)
        
        with cols[idx % 2].container(border=True):
            st.markdown(f"<h4 class='text-orange'>{flip['name']} ({flip['qty']}x)</h4>", unsafe_allow_html=True)
            sc1, sc2 = st.columns(2)
            sc1.write(f"**Bod:** {core.fmt(flip['buy_p'])}")
            sc2.write(f"**Vraag:** {core.fmt(flip['sell_p'])}")
            st.divider()
            sc3, sc4 = st.columns(2)
            sc3.write(f"*Live Bod:* {core.fmt(l_low)}")
            sc4.write(f"*Live Vraag:* {core.fmt(l_high)}")
            
            for (icon, msg, target) in status_msgs:
                st.write(f"**{icon}:** {msg}" + (f" *({core.fmt(target)})*" if target else ""))
            
            with st.expander("✅ Afronden & Fiscale Invoer"):
                f_qty = st.number_input("Aantal", min_value=1, max_value=flip['qty'], value=flip['qty'], key=f"fq_{iid_str}")
                f_buy = st.number_input("Inkoop", value=flip['buy_p'], key=f"fb_{iid_str}")
                f_sell = st.number_input("Verkoop", value=flip['sell_p'], key=f"fs_{iid_str}")
                
                if st.button("Opslaan & Sluiten", type="primary", key=f"fsave_{iid_str}", use_container_width=True):
                    tax_paid = f_qty * core.ge_tax(f_sell)
                    winst = (f_qty * f_sell) - tax_paid - (f_qty * f_buy)
                    prof['history'].append({
                        "Datum": datetime.now().strftime("%Y-%m-%d %H:%M"), "Item": flip['name'],
                        "Aantal": f_qty, "Investering": f_qty * f_buy, "Tax Betaald": tax_paid,
                        "Netto Winst": winst, "ROI": (winst / (f_qty * f_buy) * 100) if f_buy > 0 else 0
                    })
                    prof['cooldowns'][iid_str] = {'qty': prof['cooldowns'].get(iid_str, {}).get('qty', 0) + f_qty, 'timestamp': int(time.time())}
                    del prof['active_flips'][iid_str]
                    st.rerun()

            if st.button("🗑️ Annuleren", key=f"del_{iid_str}", use_container_width=True):
                del prof['active_flips'][iid_str]
                st.rerun()

def render_history_tab(prof):
    st.markdown('<div class="section-title">Grootboek & P/L</div>', unsafe_allow_html=True)
    if not prof['history']: return st.info("Geen transacties.")
    
    df_h = pd.DataFrame(prof['history'])
    tot_i, tot_w, tot_t = df_h["Investering"].sum(), df_h["Netto Winst"].sum(), df_h["Tax Betaald"].sum()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Netto Winst", f"{core.fmt(tot_w)} gp")
    m2.metric("GE Tax", f"{core.fmt(tot_t)} gp")
    m3.metric("Flips", len(df_h))
    m4.metric("Gem. ROI", core.fmtp((tot_w / tot_i * 100) if tot_i > 0 else 0))
    
    df_disp = df_h.copy()
    for col in ["Investering", "Tax Betaald", "Netto Winst"]: df_disp[col] = df_disp[col].apply(core.fmt)
    df_disp["ROI"] = df_disp["ROI"].apply(core.fmtp)
    st.dataframe(df_disp, use_container_width=True, hide_index=True)
    if st.button("Wis P/L"):
        prof['history'] = []
        st.rerun()
