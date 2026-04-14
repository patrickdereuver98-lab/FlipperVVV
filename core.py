"""
session.py — Streamlit session state management.

Manages multi-account profiles, capital tracking, and GE cooldown state.
Each profile is isolated: its own watchlist, active slots, history, and overrides.
"""
import time
import streamlit as st

# ── Profile schema ─────────────────────────────────────────────────────────────
def _empty_profile(name: str = "Main") -> dict:
    return {
        "name":         name,
        "active_flips": {},   # {str(item_id): FlipEntry}
        "watchlist":    [],   # [str(item_id), ...]
        "history":      [],   # [HistoryEntry, ...]
        "cooldowns":    {},   # {str(item_id): {qty, timestamp}}
        "overrides":    {},   # {str(item_id): {buy, sell}}
    }


# ── Initialisation ─────────────────────────────────────────────────────────────
def init() -> dict:
    """
    Initialise all required session state keys.
    Returns the currently active profile dict.
    """
    if "profiles" not in st.session_state:
        st.session_state.profiles = {
            "Main":      _empty_profile("Main"),
            "Alt":       _empty_profile("Alt"),
        }
    if "active_profile" not in st.session_state:
        st.session_state.active_profile = "Main"
    if "raw_cash" not in st.session_state:
        st.session_state.raw_cash = 25_000_000   # Default: 25M
    if "last_api_ts" not in st.session_state:
        st.session_state.last_api_ts = None
    if "sel_item_id" not in st.session_state:
        st.session_state.sel_item_id = None      # Currently selected item in scanner
    if "watch_item_id" not in st.session_state:
        st.session_state.watch_item_id = None    # Currently selected item in watchlist
    if "api_error" not in st.session_state:
        st.session_state.api_error = None

    return active_profile()


def active_profile() -> dict:
    """Return the currently active profile dict."""
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
    """Capital currently tied up in open trades."""
    return sum(
        f["qty"] * f["buy_p"]
        for f in prof["active_flips"].values()
    )


def free_cash(prof: dict) -> int:
    return max(0, total_cash() - locked_cash(prof))


# ── Slot management ────────────────────────────────────────────────────────────
MAX_SLOTS = 8


def add_to_slots(prof: dict, row: dict) -> bool:
    """
    Add an item to the active flip slots.
    Returns True on success, False if slots are full.
    """
    iid_str = str(int(row["id"]))
    if len(prof["active_flips"]) >= MAX_SLOTS:
        return False
    prof["active_flips"][iid_str] = {
        "name":    row["name"],
        "qty":     int(row["qty"]),
        "buy_p":   int(row["buy_p"]),
        "sell_p":  int(row["sell_p"]),
        "added_ts": int(time.time()),
    }
    return True


def close_flip(
    prof:     dict,
    iid_str:  str,
    qty:      int,
    buy_p:    int,
    sell_p:   int,
) -> dict:
    """
    Record a completed flip in the ledger, update the cooldown,
    and remove it from active slots.
    Returns the history entry dict.
    """
    from src.engine.formulas import ge_tax
    tax_paid = qty * ge_tax(sell_p)
    net_profit = (qty * sell_p) - tax_paid - (qty * buy_p)
    invest = qty * buy_p

    entry = {
        "ts":           int(time.time()),
        "name":         prof["active_flips"][iid_str]["name"],
        "qty":          qty,
        "buy_p":        buy_p,
        "sell_p":       sell_p,
        "invest":       invest,
        "tax_paid":     tax_paid,
        "net_profit":   net_profit,
        "roi":          (net_profit / invest * 100) if invest > 0 else 0.0,
    }
    prof["history"].append(entry)

    # Update 4h cooldown: extend qty used
    prev = prof["cooldowns"].get(iid_str, {})
    from src.engine.formulas import GE_COOLDOWN_HOURS, cooldown_remaining_qty
    still_locked = cooldown_remaining_qty(prev)
    prof["cooldowns"][iid_str] = {
        "qty":       still_locked + qty,
        "timestamp": int(time.time()),
    }

    del prof["active_flips"][iid_str]
    return entry
