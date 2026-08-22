from __future__ import annotations

import streamlit as st

from app.actions import ActionStore
from app.agent import Agent
from app.config import DATA_DIR, DEMO_USER, HF_MODEL, HF_TOKEN, USER_PROFILES
from app.data_store import DataStore
from app.retrieval import DocumentRetriever

st.set_page_config(page_title="ParcelPilot AI Support Agent", page_icon="📦", layout="centered")

@st.cache_resource
def build_services():
    store = DataStore(DATA_DIR / "ParcelPilot_Assessment_Data.xlsx")
    retriever = DocumentRetriever(DATA_DIR)
    actions = ActionStore()
    agent = Agent(store, retriever, actions)
    return store, retriever, actions, agent

store, retriever, actions, agent = build_services()

with st.sidebar:
    st.subheader("Demo identity")
    profile_name = st.selectbox("User role", list(USER_PROFILES.keys()), index=1)
    current_user = USER_PROFILES[profile_name].copy()
    agent.set_user(current_user)

st.title("ParcelPilot Support & Operations Agent")
st.caption("Internal support demo · support_agent · dataset snapshot: 16 Aug 2026 11:00 IST")

with st.sidebar:
    st.subheader("System")
    st.write(f"Model: `{HF_MODEL}`")
    st.write(f"HF connection: {'configured' if HF_TOKEN else 'missing'}")
    st.write(f"User: `{current_user['user_id']}`")
    st.write(f"Role: `{current_user['role']}`")
    st.write("Authorized accounts: " + ", ".join(current_user["authorized_accounts"]))
    st.divider()
    st.caption("Required state-changing actions always require explicit confirmation.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("tool_trace"):
            with st.expander("Tool trace"):
                for trace in msg["tool_trace"]:
                    st.code(f"{trace['tool']}({trace['arguments']})", language="text")

if st.session_state.get("pending_confirmation"):
    pending = st.session_state["pending_confirmation"]
    st.warning(
        f"Confirmation required: {pending['action']} · ticket {pending['ticket_id']} · {pending['priority']}"
    )
    st.write(pending["reason"])
    if st.button("Confirm action", type="primary"):
        result = actions.confirm(pending["confirmation_id"], current_user)
        if result.get("ok"):
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Action executed successfully: {result['action']['ticket_id']} was escalated as {result['action']['priority']}.",
            })
            st.session_state.pending_confirmation = None
            st.rerun()
        else:
            st.error(result.get("error", "Action could not be executed."))

prompt = st.chat_input("Ask about an order, ticket, SLA, cancellation, service credit, or known issue...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    prior_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]
        if m["role"] in {"user", "assistant"}
    ]
    with st.chat_message("assistant"):
        with st.spinner("Investigating..."):
            result = agent.chat(prompt, prior_history)
        st.markdown(result["answer"])
        if result.get("tool_trace"):
            with st.expander("Tool trace", expanded=True):
                for trace in result["tool_trace"]:
                    st.code(f"{trace['tool']}({trace['arguments']})", language="text")
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "tool_trace": result.get("tool_trace", []),
    })

    # The action tool prepares an escalation; it never executes it directly.
    for trace in result.get("tool_trace", []):
        if trace["tool"] == "create_escalation":
            pending_items = [
                item for item in actions.pending.values()
                if item["requested_by"] == current_user["user_id"]
            ]
            if pending_items:
                st.session_state.pending_confirmation = pending_items[-1]
                break
    st.rerun()
