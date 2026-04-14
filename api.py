import requests
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential

BASE_API = "https://prices.runescape.wiki/api/v1/osrs"
WIKI_HEADERS = {"User-Agent": "OSRS-GE-Flip-Advisor/7.0 (streamlit; enterprise-vectorized)"}

@st.cache_data(ttl=3600, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_mapping() -> dict:
    r = requests.get(f"{BASE_API}/mapping", headers=WIKI_HEADERS, timeout=12)
    r.raise_for_status()
    return {item["id"]: item for item in r.json()}

@st.cache_data(ttl=60, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_latest() -> dict:
    r = requests.get(f"{BASE_API}/latest", headers=WIKI_HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()["data"]

@st.cache_data(ttl=120, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_5m() -> dict:
    r = requests.get(f"{BASE_API}/5m", headers=WIKI_HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()["data"]

@st.cache_data(ttl=300, show_spinner=False)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_1h() -> dict:
    r = requests.get(f"{BASE_API}/1h", headers=WIKI_HEADERS, timeout=12)
    r.raise_for_status()
    return r.json()["data"]

@st.cache_data(ttl=300, show_spinner=False)
@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=3))
def fetch_timeseries(item_id: int) -> list:
    r = requests.get(f"{BASE_API}/timeseries?timestep=5m&id={item_id}", headers=WIKI_HEADERS, timeout=8)
    if r.status_code == 200:
        return r.json().get("data", [])
    return []

def clear_api_cache():
    fetch_mapping.clear()
    fetch_latest.clear()
    fetch_5m.clear()
    fetch_1h.clear()
