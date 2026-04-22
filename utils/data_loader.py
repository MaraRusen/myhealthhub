"""Load mock data from JSON files with caching."""
import json
from pathlib import Path
import streamlit as st

DATA_DIR = Path(__file__).parent.parent / "data"


@st.cache_data
def load_celina() -> dict:
    with open(DATA_DIR / "celina.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_appointments() -> dict:
    with open(DATA_DIR / "appointments.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_records() -> dict:
    with open(DATA_DIR / "records.json", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_finances() -> dict:
    with open(DATA_DIR / "finances.json", encoding="utf-8") as f:
        return json.load(f)


def load_all() -> dict:
    return {
        "celina": load_celina(),
        "appointments": load_appointments(),
        "records": load_records(),
        "finances": load_finances(),
    }
