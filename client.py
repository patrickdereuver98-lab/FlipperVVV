"""
client.py — OSRS Wiki Real-time Prices API client.

Endpoints:
  /mapping     — static item metadata (name, icon, GE limit, members)
  /latest      — live instabuy/instasell prices
  /5m          — 5-minute volume aggregates
  /1h          — 1-hour volume aggregates
  /timeseries  — historical OHLC data per item
"""
import streamlit as st
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS  = {
    "User-Agent": "OSRS-Elite-Flipper/2.0 (streamlit; contact=github)",
}


# ── Cached API calls ───────────────────────────────────────────────────────────

@st.cache_data(ttl=3_600, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_mapping() -> dict:
    """Item metadata: name, icon, GE limit, members. Cached 1 hour."""
    r = requests.get(f"{BASE_URL}/mapping", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return {item["id"]: item for item in r.json()}


@st.cache_data(ttl=60, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_latest() -> dict:
    """Live instabuy/instasell prices. Cached 60 seconds."""
    r = requests.get(f"{BASE_URL}/latest", headers=HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()["data"]


@st.cache_data(ttl=120, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_5m() -> dict:
    """5-minute volume aggregates. Cached 2 minutes."""
    r = requests.get(f"{BASE_URL}/5m", headers=HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()["data"]


@st.cache_data(ttl=300, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_1h() -> dict:
    """1-hour volume aggregates. Cached 5 minutes."""
    r = requests.get(f"{BASE_URL}/1h", headers=HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()["data"]


@st.cache_data(ttl=300, show_spinner=False)
@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=5))
def fetch_timeseries(item_id: int) -> list:
    """Historical 5-minute OHLC for a single item. Cached 5 minutes."""
    r = requests.get(
        f"{BASE_URL}/timeseries?timestep=5m&id={item_id}",
        headers=HEADERS,
        timeout=10,
    )
    if r.status_code == 200:
        return r.json().get("data", [])
    return []


def clear_cache() -> None:
    """Force-clear all cached API responses to trigger a fresh poll."""
    fetch_mapping.clear()
    fetch_latest.clear()
    fetch_5m.clear()
    fetch_1h.clear()
