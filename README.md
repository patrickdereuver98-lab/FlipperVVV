# ◈ OSRS Elite Flipper — v2.0

A professional, data-driven Grand Exchange trading terminal built with Python and Streamlit.

---

## Architecture

```
osrs_flipper/
├── app.py                      # Main entry point (controller)
├── requirements.txt
├── .streamlit/
│   └── config.toml             # Dark terminal theme
└── src/
    ├── api/
    │   └── client.py           # OSRS Wiki API — cached, retry-protected
    ├── engine/
    │   ├── formulas.py         # Pure math: tax, parse, fmt, age, freshness
    │   └── core.py             # Vectorized Pandas computation engine
    ├── state/
    │   └── session.py          # Multi-profile session + GE cooldown tracking
    └── ui/
        ├── styles.py           # Bloomberg Terminal CSS theme
        ├── sidebar.py          # Capital management sidebar
        ├── components.py       # Shared item detail panel
        ├── scanner.py          # Scanner tab
        ├── watchlist.py        # Watchlist tab
        ├── portfolio.py        # Active Slots tab
        └── ledger.py           # P/L Ledger tab
```

---

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Code & Logic Analysis

### 1. GE Tax

The tax implementation is mathematically correct:
- 1% of sell price, floored (no rounding up).
- Hard cap of 5,000,000 GP for items priced ≥ 500,000,000 GP.
- Vectorized via `numpy.where` for the full DataFrame in one pass.

### 2. Smart Score — v1 vs v2

**v1 (original):**
```python
smart_score = pot_profit * (roi / 100) * log10(vol_use + 1)
           # = qty * margin * (margin / buy_p) * log10(vol + 1)
```

**Problems with v1:**
- `pot_profit` = `qty × margin` is capital-dependent. With 100M cash you rank items
  differently than with 1B cash — ranking is unstable and changes with wallet size.
- Margin is *squared* (hidden): `margin × (margin/buy_p)`. High-margin, low-volume
  items dominate over moderate-margin, high-volume items unfairly.
- No penalty for stale API data — a 2-hour old price gets the same score as a 2-minute
  old price, even though the margin may be completely different in-game.

**v2 (this build):**
```python
roi_decimal  = margin / buy_p               # Capital efficiency
vol_score    = log10(vol_use + 1)           # Market liquidity (log-scaled)
depth_score  = log10(ge_lim × margin + 1)  # Total extractable GP from this market
freshness    = decay(1.0 → 0.25, 0–2h)     # Data quality multiplier

smart_score  = roi_decimal × vol_score × depth_score × freshness
```

**Why this is better:**
- **Capital-agnostic**: The ranking is the same whether you have 10M or 10B. The
  `qty/pot_profit/invest` columns are still calculated for display, but don't affect rank.
- **Market depth** (`ge_lim × margin`) rewards items where the GE limit is large
  enough to extract significant profit — a 5% ROI item with a 10,000 limit beats a
  5% ROI item with a 50-unit limit.
- **Freshness penalty** (0.25–1.0 multiplier) demotes items with stale API data,
  pushing manual-override candidates to the surface automatically.

### 3. Liquidity & Capital Allocation

- `free_cash = total_cash − Σ(qty × buy_p)` for all open slots.
- `qty = min(free_cash // buy_p, remaining_ge_limit)` — greedy single-item allocation.
- The GE 4-hour buy limit cooldown is now properly tracked: `cooldown_remaining_qty()`
  checks elapsed time and returns 0 once 4 hours have passed since the last purchase.
- `dynamic_min_margin = max(min_margin, free_cash × 0.00005)` — scales the noise
  floor with capital so small-margin items disappear at large stack sizes.

### 4. Volume Fallback

```python
vol_use = vol_1h if vol_1h > 0 else vol_5m × 3
```

Multiplying 5m by 3 (not 12) is a conservative estimate — 5m volume spikes do not
extrapolate linearly to 1h. This avoids false positives on flash-volume items.

---

## Workflow

```
1. Set cash stack in sidebar (type or Quick-Add buttons)
2. Scanner tab → ranked item list → click row to open detail card
3. Review margin, ROI, volume, data freshness, price chart
4. Optional: apply Manual Override if API data is stale
5. Click [＋ Add to Slots] → item moves to Active Slots tab
6. Monitor live status (OUTBID / UNDERCUT / OK) in Active Slots
7. When sold in-game: open [✓ Close Trade], enter actual prices
8. P/L is booked to ledger, GE cooldown is updated, capital is freed
```
