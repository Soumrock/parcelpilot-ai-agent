import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
load_dotenv(ROOT / ".env")

def _secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, default))
    except Exception:
        return default


HF_TOKEN = _secret("HF_TOKEN")
HF_MODEL = _secret("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")
HF_PROVIDER = _secret("HF_PROVIDER", "auto")

DATASET_SNAPSHOT = "2026-08-16 11:00 Asia/Kolkata"

# Internal demo identity. In production this would come from an authenticated
# employee session, not from the client request.
USER_PROFILES = {
    "Support Agent — ACCT-001 only": {
        "user_id": "support-agent-001",
        "role": "support_agent",
        "authorized_accounts": ["ACCT-001"],
    },
    "Operations Admin — all accounts": {
        "user_id": "ops-admin-001",
        "role": "operations_admin",
        "authorized_accounts": ["ACCT-001", "ACCT-002", "ACCT-003", "ACCT-004"],
    },
}

# Default profile for API/demo usage. Streamlit allows switching profiles to demonstrate scoping.
DEMO_USER = USER_PROFILES["Operations Admin — all accounts"].copy()
