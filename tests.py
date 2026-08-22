from pathlib import Path
from app.actions import ActionStore
from app.config import DATA_DIR, USER_PROFILES
from app.data_store import DataStore
from app.retrieval import DocumentRetriever


def main():
    user_all = {"user_id": "u1", "authorized_accounts": ["ACCT-001", "ACCT-002", "ACCT-003", "ACCT-004"]}
    user_northstar = {"user_id": "u2", "authorized_accounts": ["ACCT-001"]}

    store = DataStore(DATA_DIR / "ParcelPilot_Assessment_Data.xlsx")
    assert len(store.accounts) == 4
    assert len(store.orders) == 6
    assert len(store.tickets) == 7
    assert store.get_order("ORD-1001", user_northstar)["status"] == "BOOKED"
    assert USER_PROFILES["Support Agent — ACCT-001 only"]["authorized_accounts"] == ["ACCT-001"]
    assert USER_PROFILES["Operations Admin — all accounts"]["authorized_accounts"] == ["ACCT-001", "ACCT-002", "ACCT-003", "ACCT-004"]

    try:
        store.get_order("ORD-2001", user_northstar)
    except PermissionError:
        pass
    else:
        raise AssertionError("Unauthorized cross-account lookup was allowed")

    r = DocumentRetriever(DATA_DIR)
    result = r.search("Northstar BOOKED cancellation fee", account_id="ACCT-001")
    assert result["results"]
    assert result["results"][0]["authority"] == "signed_customer_agreement"

    deprecated = r.search("old support policy response target", include_deprecated=False)
    assert all(x["status"] != "DEPRECATED" for x in deprecated["results"])

    actions = ActionStore()

    # Contract-sensitive generic question should request account/order context
    # instead of silently choosing a customer agreement.
    from app.agent import Agent
    agent = Agent(store, r, actions)
    clarification = agent._context_clarification(
        "A pickup is three hours late because of carrier fault. Should I get a service credit?"
    )
    assert clarification and "account, order, or ticket" in clarification

    pending = actions.prepare_escalation("TKT-505", "Possible credential exposure", "P1", user_all)
    assert pending["status"] == "AWAITING_CONFIRMATION"
    executed = actions.confirm(pending["confirmation_id"], user_all)
    assert executed["ok"] is True
    assert executed["action"]["status"] == "EXECUTED"

    print("ALL LOCAL TOOL TESTS PASSED")


if __name__ == "__main__":
    main()

# Known-issue grounding: response logic should rely on the current product guide
# and not claim unsupported actions or guaranteed future timing.
def test_swiftship_known_issue_grounding():
    from app.agent import Agent
    store = DataStore(DATA_DIR / "ParcelPilot_Assessment_Data.xlsx")
    retriever = DocumentRetriever(DATA_DIR)
    agent = Agent(store, retriever, ActionStore())
    ctx = agent._known_issue_context(
        "What should I tell a customer if a SwiftShip shipment is still showing BOOKED even though the carrier says it was picked up?"
    )
    assert ctx is not None
    text = " ".join(x["text"] for x in ctx["evidence"]["results"])
    assert "20 minutes late" in text
    assert "verify the carrier status" in text
