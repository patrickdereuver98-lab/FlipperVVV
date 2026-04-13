import streamlit as st
import requests
import pandas as pd
import math

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OSRS GE Flip Advisor",
    page_icon="💰",
    layout="wide",
)

# ── OSRS Wiki API ─────────────────────────────────────────────────────────────
WIKI_HEADERS = {"User-Agent": "OSRS-Flip-Advisor/1.0 (streamlit dashboard)"}
BASE = "https://prices.runescape.wiki/api/v1"

GE_TAX = 0.02
GE_TAX_CAP = 5_000_000
MAX_PRICE_FOR_TAX = 250_000_000


def ge_tax(sell_price: int) -> int:
    """Calculate GE tax on a sale (2%, max 5M). Mirror of GeTax.java."""
    if sell_price >= MAX_PRICE_FOR_TAX:
        return GE_TAX_CAP
    return math.floor(sell_price * GE_TAX)


def net_sell(sell_price: int) -> int:
    return sell_price - ge_tax(sell_price)


@st.cache_data(ttl=120)
def fetch_mapping():
    r = requests.get(f"{BASE}/mapping", headers=WIKI_HEADERS, timeout=10)
    r.raise_for_status()
    data = r.json()
    return {item["id"]: item for item in data}


@st.cache_data(ttl=60)
def fetch_latest():
    r = requests.get(f"{BASE}/latest", headers=WIKI_HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()["data"]


@st.cache_data(ttl=60)
def fetch_volume():
    """5-min endpoint gives recent trade volumes."""
    r = requests.get(f"{BASE}/5m", headers=WIKI_HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()["data"]


def fmt_gp(val):
    if val is None:
        return "—"
    if abs(val) >= 1_000_000:
        return f"{val/1_000_000:.2f}M gp"
    if abs(val) >= 1_000:
        return f"{val/1_000:.1f}K gp"
    return f"{val:,} gp"


def fmt_pct(val):
    return f"{val:.1f}%"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://oldschool.runescape.com/img/rsp777/ge/ge-icon.png",
        width=48,
    )
    st.title("⚙️ Instellingen")

    cash_stack = st.number_input(
        "💰 Jouw cash stack (gp)",
        min_value=1_000,
        max_value=2_147_483_647,
        value=10_000_000,
        step=1_000_000,
        format="%d",
    )

    st.markdown("---")
    st.subheader("Filters")
    min_margin = st.slider("Min. margin per item (gp)", 0, 100_000, 500, step=500)
    min_roi = st.slider("Min. ROI (%)", 0.0, 20.0, 0.5, step=0.1)
    min_volume = st.slider("Min. volume (5m periode)", 0, 1000, 5, step=5)
    max_item_price = st.number_input(
        "Max. inkoopprijs per item (gp)",
        min_value=1,
        max_value=2_147_483_647,
        value=int(cash_stack),
        step=100_000,
        format="%d",
    )

    sort_by = st.selectbox(
        "Sorteren op",
        ["Pot. winst / limit", "ROI %", "Margin per item", "Volume"],
        index=0,
    )

    st.markdown("---")
    st.caption("Data: OSRS Wiki Prices API\nPlugin gebaseerd op: Flipping Utilities")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("💰 OSRS GE Flip Advisor")
st.markdown(
    f"**Cash stack:** `{fmt_gp(cash_stack)}` — live prijsdata van de OSRS Wiki API (ververst elke 60s)"
)

# ── Data laden ────────────────────────────────────────────────────────────────
with st.spinner("Prijsdata ophalen van OSRS Wiki…"):
    try:
        mapping = fetch_mapping()
        latest = fetch_latest()
        volume_data = fetch_volume()
    except Exception as e:
        st.error(f"Kon data niet ophalen: {e}")
        st.stop()

# ── Berekeningen ──────────────────────────────────────────────────────────────
rows = []
for item_id_str, prices in latest.items():
    item_id = int(item_id_str)
    info = mapping.get(item_id)
    if not info:
        continue

    high = prices.get("high")   # insta-sell (jij verkoopt hier)
    low = prices.get("low")     # insta-buy  (jij koopt hier)

    if not high or not low or high <= 0 or low <= 0:
        continue

    # Margin = wat je netto krijgt bij verkoop minus wat je betaalt bij aankoop
    # Koop voor 'low+1', verkoop voor 'high-1' (standaard flip strategie)
    buy_price = low + 1
    sell_price = high - 1

    if buy_price >= sell_price:
        continue

    margin = net_sell(sell_price) - buy_price
    if margin <= 0:
        continue

    roi = margin / buy_price * 100

    buy_limit = info.get("limit", 0) or 0

    # Volume uit 5m data
    vol_entry = volume_data.get(item_id_str, {})
    vol = (vol_entry.get("highVolume") or 0) + (vol_entry.get("lowVolume") or 0)

    # Hoeveel items kan je kopen met je cash stack?
    affordable = min(int(cash_stack // buy_price), buy_limit) if buy_price > 0 else 0
    # Potentiële winst als je de hele limiet koopt (of wat je kan betalen)
    potential_profit = affordable * margin

    rows.append({
        "id": item_id,
        "Naam": info.get("name", "?"),
        "Inkoopprijs": buy_price,
        "Verkoopprijs": sell_price,
        "Margin (netto)": margin,
        "ROI %": roi,
        "GE Limiet": buy_limit,
        "Betaalbaar (qty)": affordable,
        "Pot. winst / limit": potential_profit,
        "Volume (5m)": vol,
        "Members": info.get("members", False),
    })

df = pd.DataFrame(rows)

if df.empty:
    st.warning("Geen data beschikbaar.")
    st.stop()

# ── Filters toepassen ─────────────────────────────────────────────────────────
df = df[df["Margin (netto)"] >= min_margin]
df = df[df["ROI %"] >= min_roi]
df = df[df["Volume (5m)"] >= min_volume]
df = df[df["Inkoopprijs"] <= max_item_price]
df = df[df["Betaalbaar (qty)"] > 0]

# Sorteren
sort_map = {
    "Pot. winst / limit": "Pot. winst / limit",
    "ROI %": "ROI %",
    "Margin per item": "Margin (netto)",
    "Volume": "Volume (5m)",
}
df = df.sort_values(sort_map[sort_by], ascending=False).reset_index(drop=True)

# ── KPI tiles ─────────────────────────────────────────────────────────────────
top = df.head(1)
if not top.empty:
    best = top.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💎 Beste flip", best["Naam"])
    col2.metric("📈 Pot. winst", fmt_gp(int(best["Pot. winst / limit"])))
    col3.metric("📊 ROI", fmt_pct(best["ROI %"]))
    col4.metric("🔢 Resultaten gevonden", f"{len(df):,}")

st.markdown("---")

# ── Top 10 tabel ──────────────────────────────────────────────────────────────
st.subheader(f"🏆 Top flips voor {fmt_gp(cash_stack)}")

display_df = df.head(25).copy()
display_df["Inkoopprijs"] = display_df["Inkoopprijs"].apply(fmt_gp)
display_df["Verkoopprijs"] = display_df["Verkoopprijs"].apply(fmt_gp)
display_df["Margin (netto)"] = display_df["Margin (netto)"].apply(fmt_gp)
display_df["ROI %"] = display_df["ROI %"].apply(fmt_pct)
display_df["Pot. winst / limit"] = display_df["Pot. winst / limit"].apply(fmt_gp)
display_df["Members"] = display_df["Members"].apply(lambda x: "✅" if x else "🆓")

st.dataframe(
    display_df[[
        "Naam", "Inkoopprijs", "Verkoopprijs", "Margin (netto)",
        "ROI %", "GE Limiet", "Betaalbaar (qty)", "Pot. winst / limit",
        "Volume (5m)", "Members"
    ]],
    use_container_width=True,
    hide_index=True,
    height=650,
)

# ── Detail uitleg ─────────────────────────────────────────────────────────────
with st.expander("ℹ️ Hoe werkt dit dashboard?"):
    st.markdown("""
**Gebaseerd op de Flipping Utilities RuneLite plugin logica:**

| Begrip | Uitleg |
|---|---|
| **Inkoopprijs** | Laagste insta-sell + 1 (jij biedt iets meer om zeker te kopen) |
| **Verkoopprijs** | Hoogste insta-buy - 1 (jij vraagt iets minder voor snelle verkoop) |
| **GE Tax** | 2% van verkoopprijs, max 5.000.000 gp (sinds mei 2025) |
| **Margin (netto)** | Verkoopprijs − GE Tax − Inkoopprijs |
| **ROI %** | Netto margin / inkoopprijs × 100 |
| **GE Limiet** | Max items per 4 uur te kopen (OSRS mechanisme) |
| **Betaalbaar (qty)** | Min(GE limiet, wat jij kan betalen met jouw cashstack) |
| **Pot. winst / limit** | Betaalbaar qty × margin — winst als je de limiet vol koopt |

**Tips:**
- Hoge volume = snellere uitvoering van je orders
- Hoge ROI = efficiënter gebruik van je cash
- Hoge pot. winst = meeste goud per 4-uur cyclus
    """)

# ── Bar chart top 10 ──────────────────────────────────────────────────────────
st.subheader("📊 Potentiële winst — Top 15")
chart_df = df.head(15)[["Naam", "Pot. winst / limit", "ROI %"]].copy()
chart_df = chart_df.set_index("Naam")
st.bar_chart(chart_df["Pot. winst / limit"])
