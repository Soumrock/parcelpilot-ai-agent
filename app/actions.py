from __future__ import annotations

import uuid
from datetime import datetime


class ActionStore:
    def __init__(self):
        self.pending: dict[str, dict] = {}
        self.executed: list[dict] = []

    def prepare_escalation(self, ticket_id: str, reason: str, priority: str, user: dict) -> dict:
        token = f"ESC-{uuid.uuid4().hex[:10].upper()}"
        item = {
            "confirmation_id": token,
            "action": "create_escalation",
            "ticket_id": ticket_id,
            "reason": reason,
            "priority": priority,
            "requested_by": user["user_id"],
            "status": "AWAITING_CONFIRMATION",
        }
        self.pending[token] = item
        return item

    def confirm(self, confirmation_id: str, user: dict) -> dict:
        item = self.pending.get(confirmation_id)
        if not item:
            return {"ok": False, "error": "Confirmation request not found or already handled."}
        if item["requested_by"] != user["user_id"]:
            return {"ok": False, "error": "Confirmation belongs to a different user."}
        result = {**item, "status": "EXECUTED", "executed_at": datetime.now().isoformat()}
        self.executed.append(result)
        del self.pending[confirmation_id]
        return {"ok": True, "action": result}
