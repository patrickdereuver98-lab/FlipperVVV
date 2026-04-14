"""
session.py — Session state management.

Manages multi-account profiles, capital, GE cooldowns, and page routing.

Page keys:
  st.session_state.page           — "terminal" | "explorer" | "detail"
                                    | "portfolio" | "watchlist" | "ledger"
  st.session_state.detail_item_id — int | None   (item to show in detail view)
  st.session_state.search_query   — str           (explorer search bar)
  st.session_state.explorer_sort  — str           (explorer sort column)
  st.session_state.hero_idx       — int           (terminal carousel index)
"""
import time
import streamlit as st


# ── Profile schema ─────────────────────────────────────────────────────────────
def _empty_profile(name: str = "Main") -> dict:
    return {
        "name":         name,
        "active_flips": {},
        "watchlist":    [],
        "history":      [],
        "cooldowns":    {},
        "overrides":    {},
    }


# ── Initialisation ─────────────────────────────────────────────────────────────
def init() -> dict:
    """Initialise all session state. Returns active profile."""
    # Profiles
    if "profiles" not in st.session_state:
        st.session_state.profiles = {
            "Main": _empty_profile("Main"),
            "Alt":  _empty_profile("Alt"),
        }
    if "active_profile" not in st.session_state:
        st.session_state.active_profile = "Main"

    # Capital
    if "raw_cash" not in st.session_state:
        st.session_state.raw_cash = 25_000_000

    # API meta
    if "last_api_ts"  not in st.session_state: st.session_state.last_api_ts  = None
    if "api_error"    not in st.session_state: st.session_state.api_error    = None

    # ── Page routing ──────────────────────────────────────────────────────
    if "page"           not in st.session_state: st.session_state.page           = "terminal"
    if "detail_item_id" not in st.session_state: st.session_state.detail_item_id = None
    if "search_query"   not in st.session_state: st.session_state.search_query   = ""
    if "explorer_sort"  not in st.session_state: st.session_state.explorer_sort  = "action_score"
    if "hero_idx"       not in st.session_state: st.session_state.hero_idx       = 0
    if "watch_item_id"  not in st.session_state: st.session_state.watch_item_id  = None

    return active_profile()


def navigate(page: str, item_id: int | None = None) -> None:
    """Switch page and optionally pre-select an item for the detail view."""
    st.session_state.page = page
    if item_id is not None:
        st.session_state.detail_item_id = item_id
    st.rerun()


def active_profile() -> dict:
    return st.session_state.profiles[st.session_state.active_profile]


def add_profile(name: str) -> None:
    if name and name not in st.session_state.profiles:
        st.session_state.profiles[name] = _empty_profile(name)


def delete_profile(name: str) -> None:
    if name in st.session_state.profiles and len(st.session_state.profiles) > 1:
        del st.session_state.profiles[name]
        st.session_state.active_profile = list(st.session_state.profiles.keys())[0]


# ── Capital helpers ────────────────────────────────────────────────────────────
def total_cash() -> int:
    return st.session_state.raw_cash


def locked_cash(prof: dict) -> int:
    return sum(f["qty"] * f["buy_p"] for f in prof["active_flips"].values())


def free_cash(prof: dict) -> int:
    return max(0, total_cash() - locked_cash(prof))


# ── Slot management ────────────────────────────────────────────────────────────
MAX_SLOTS = 8


def add_to_slots(prof: dict, row) -> bool:
    """Add item to active slots. Returns True on success."""
    iid_str = str(int(row["id"]))
    if len(prof["active_flips"]) >= MAX_SLOTS:
        return False
    prof["active_flips"][iid_str] = {
        "name":     row["name"],
        "qty":      int(row["qty"]),
        "buy_p":    int(row["buy_p"]),
        "sell_p":   int(row["sell_p"]),
        "added_ts": int(time.time()),
    }
    return True


def close_flip(prof: dict, iid_str: str, qty: int, buy_p: int, sell_p: int) -> dict:
    """Book a completed flip and free the slot."""
    from src.engine.formulas import ge_tax, cooldown_remaining_qty, GE_COOLDOWN_HOURS
    tax_paid   = qty * ge_tax(sell_p)
    net_profit = (qty * sell_p) - tax_paid - (qty * buy_p)
    invest     = qty * buy_p

    entry = {
        "ts":         int(time.time()),
        "name":       prof["active_flips"][iid_str]["name"],
        "qty":        qty,
        "buy_p":      buy_p,
        "sell_p":     sell_p,
        "invest":     invest,
        "tax_paid":   tax_paid,
        "net_profit": net_profit,
        "roi":        (net_profit / invest * 100) if invest > 0 else 0.0,
    }
    prof["history"].append(entry)

    prev = prof["cooldowns"].get(iid_str, {})
    still_locked = cooldown_remaining_qty(prev)
    prof["cooldowns"][iid_str] = {
        "qty":       still_locked + qty,
        "timestamp": int(time.time()),
    }
    del prof["active_flips"][iid_str]
    return entry
