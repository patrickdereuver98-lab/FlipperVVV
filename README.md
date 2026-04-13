# ⚔️ OSRS GE Flip Advisor

A Streamlit dashboard for finding the best Grand Exchange flipping opportunities in Old School RuneScape.

Built on the exact same logic as the [Flipping Utilities](https://github.com/Flipping-Utilities/rl-plugin) RuneLite plugin — just in your browser instead of the game client.

![OSRS Theme](https://img.shields.io/badge/theme-OSRS-c8a232?style=flat-square)
![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/streamlit-1.35%2B-FF4B4B?style=flat-square)
![Data](https://img.shields.io/badge/data-OSRS%20Wiki%20API-green?style=flat-square)

---

## 🚀 Quick start

```bash
# 1. Clone the repo
git clone https://github.com/yourname/osrs-ge-flip-advisor.git
cd osrs-ge-flip-advisor

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run app.py
```

Opens at **http://localhost:8501**

---

## 📸 Features

| Feature | Detail |
|---|---|
| **Live data** | OSRS Wiki Prices API — refreshes every 60s automatically |
| **Exact plugin logic** | GE Tax, margin, ROI, qty calculations mirror `GeTax.java` + `FlippingItem.java` |
| **Cash stack input** | Quick presets (100K → 100M) or type any amount |
| **Smart filtering** | Min margin, min ROI, min volume, max buy price, F2P/P2P toggle |
| **Item detail** | Icon, examine text, price boxes, stats, step-by-step flip guide |
| **Navigation** | Click any item or use Prev / Next buttons |
| **OSRS theme** | Dark gold UI matching the game's aesthetic |

---

## 📐 Architecture

```
osrs-ge-flip-advisor/
│
├── app.py                  ← Streamlit entry point (thin orchestration)
├── config.py               ← All constants (API URLs, GE tax, defaults)
├── requirements.txt
├── .gitignore
│
├── api/
│   ├── __init__.py
│   └── osrs_wiki.py        ← OSRS Wiki Prices API client (4 endpoints)
│
├── core/
│   ├── __init__.py
│   ├── ge_tax.py           ← GE tax calculation — mirror of GeTax.java
│   └── flip_engine.py      ← Flip opportunity engine — mirrors FlippingItem.java
│
├── ui/
│   ├── __init__.py
│   ├── theme.py            ← OSRS CSS theme (inject_css)
│   ├── sidebar.py          ← Sidebar: cash stack + filters
│   ├── flip_list.py        ← Left column: scrollable item list
│   └── item_detail.py      ← Right column: detail panel + flip guide
│
└── utils/
    ├── __init__.py
    └── formatters.py       ← fmt_gp, fmt_pct, age_str, fmt_timestamp
```

---

## 🧮 How the flip calculation works

Mirrors the exact logic from the Flipping Utilities RuneLite plugin:

### Prices (FlippingItem.java strategy)
```
buy_price  = instasell_price + 1   (low  + 1)
sell_price = instabuy_price  - 1   (high - 1)
```

### GE Tax (GeTax.java)
```python
# 2% of sell price, capped at 5,000,000 gp
tax = min(floor(sell_price * 0.02), 5_000_000)
net_sell = sell_price - tax
```

### Margin & ROI
```
margin = net_sell(sell_price) - buy_price
roi    = margin / buy_price * 100
```

### Quantity & Potential profit
```
qty            = min(cash_stack // buy_price, ge_buy_limit)
potential_profit = qty * margin
```

---

## 🔌 API Endpoints Used

All data comes from the [OSRS Wiki Real-time Prices API](https://oldschool.runescape.wiki/w/RuneScape:Real-time_Prices):

| Endpoint | Used for | Cache TTL |
|---|---|---|
| `/mapping` | Item names, GE limits, alch values, icons | 1 hour |
| `/latest`  | Live instabuy / instasell prices | 60 seconds |
| `/5m`      | 5-minute trade volume | 2 minutes |
| `/1h`      | 1-hour trade volume (more complete) | 5 minutes |

---

## ⚠️ Disclaimer

- Prices are **estimates** based on crowdsourced RuneLite transaction data
- Always do a **margin check in-game** before placing large orders
- GE prices can change faster than the API updates
- This tool is for informational purposes only

---

## 📜 License

MIT — see [LICENSE](LICENSE)

Plugin logic reference: [Flipping Utilities](https://github.com/Flipping-Utilities/rl-plugin) (BSD-2-Clause)
