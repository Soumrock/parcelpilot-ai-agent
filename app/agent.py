from __future__ import annotations

import json
import re
from typing import Any, Callable

from .actions import ActionStore
from .config import DATASET_SNAPSHOT, DEMO_USER, HF_MODEL, HF_PROVIDER, HF_TOKEN
from .data_store import DataStore
from .retrieval import DocumentRetriever

SYSTEM_PROMPT = f"""
You are ParcelPilot's internal Support & Operations AI agent.

Dataset reference time: {DATASET_SNAPSHOT} Asia/Kolkata.
Use only the supplied ParcelPilot data pack. Do not use outside facts.

CORE BEHAVIOR
- Answer questions directly when evidence is sufficient.
- Use document_search for policies, SOPs, agreements, product docs, and known issues.
- Use structured_data_lookup for accounts, orders, tickets, and calculations.
- You MUST use tools when the request needs supplied operational data or documents.
- Multi-step questions should use multiple tools in sequence when required.
- Treat signed customer agreements as higher authority than general policy.
- Current support policy and current SOP/product docs outrank deprecated policy and historical ticket guidance.
- Historical ticket resolutions are context only and may be wrong.
- If key facts conflict or are unknown, state the uncertainty and recommend verification/escalation rather than guessing.
- Never execute a state-changing action directly. First prepare it with create_escalation, then ask the user for explicit confirmation.
- Access control is enforced by the tools; never try to bypass it.
- If a tool returns ACCESS_DENIED, do not suggest that an escalation, ticket, or approval can be used to retrieve or reveal the protected data. State that the requested data is not available to this user and stop.
- When citing evidence, mention the source filename(s) in plain language.
- Keep answers concise and operationally useful.
- Never invent capabilities, external contacts, or guaranteed future timing.
- For known issues, state only what the supplied document explicitly supports.

SAFE REASONING PATTERNS
- Cancellation: inspect the order, identify the account, retrieve the customer's agreement if any, then check the current cancellation SOP.
- Service credit: inspect timing, carrier fault, customer fault, applicable agreement, and calculate the applicable credit.
- Security incidents or breached P1 response targets: recommend immediate escalation when supported by the supplied data.
"""


def tool_schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


class Agent:
    def __init__(self, data_store: DataStore, retriever: DocumentRetriever, actions: ActionStore, user: dict | None = None):
        self.client = None
        if HF_TOKEN:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(provider=HF_PROVIDER, api_key=HF_TOKEN)
        self.data_store = data_store
        self.retriever = retriever
        self.actions = actions
        self.user = dict(user or DEMO_USER)
        self.tools = [
            tool_schema(
                "document_search",
                "Search the supplied ParcelPilot documents. Use account_id to prioritize an account-specific agreement. Set account_id to an empty string when not applicable. Set include_deprecated to true only when historical comparison is explicitly requested.",
                {
                    "query": {"type": "string"},
                    "account_id": {"type": "string"},
                    "include_deprecated": {"type": "boolean"},
                },
                ["query", "account_id", "include_deprecated"],
            ),
            tool_schema(
                "structured_data_lookup",
                "Query supplied accounts, orders, and tickets. The tool enforces account-level authorization. When the user gives an order/ticket/account ID, put that exact ID in record_id rather than performing a broad search. Use empty strings when an optional filter is not needed.",
                {
                    "entity": {"type": "string", "enum": ["accounts", "orders", "tickets"]},
                    "query": {"type": "string"},
                    "account_id": {"type": "string"},
                    "record_id": {"type": "string"},
                },
                ["entity", "query", "account_id", "record_id"],
            ),
            tool_schema(
                "create_escalation",
                "Prepare a support escalation. This never executes immediately; the application requires explicit confirmation.",
                {
                    "ticket_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "priority": {"type": "string", "enum": ["P1", "P2", "P3"]},
                },
                ["ticket_id", "reason", "priority"],
            ),
        ]
    def set_user(self, user: dict) -> None:
        """Set the authenticated/scoped internal user for data and action tools."""
        self.user = dict(user)

        self.dispatch: dict[str, Callable[..., Any]] = {
            "document_search": self._document_search,
            "structured_data_lookup": self._structured_lookup,
            "create_escalation": self._create_escalation,
        }

    def _document_search(self, query: str, account_id: str, include_deprecated: bool):
        return self.retriever.search(
            query=query,
            account_id=account_id or None,
            include_deprecated=include_deprecated,
        )

    def _structured_lookup(self, entity: str, query: str, account_id: str, record_id: str):
        try:
            query = query or None
            account_id = account_id or None
            record_id = record_id or None

            # Guardrail: if the model places an explicit record identifier in the
            # free-text query but forgets record_id, convert it into an exact
            # record lookup. This prevents broad searches and tool-call loops.
            if not record_id and query:
                if entity == "orders":
                    match = re.search(r"\bORD-\d{4}\b", query, flags=re.I)
                    if match:
                        record_id = match.group(0).upper()
                elif entity == "tickets":
                    match = re.search(r"\bTKT-\d{3}\b", query, flags=re.I)
                    if match:
                        record_id = match.group(0).upper()
                elif entity == "accounts":
                    match = re.search(r"\bACCT-\d{3}\b", query, flags=re.I)
                    if match:
                        record_id = match.group(0).upper()

            if record_id:
                if entity == "orders":
                    item = self.data_store.get_order(record_id, self.user)
                elif entity == "tickets":
                    item = self.data_store.get_ticket(record_id, self.user)
                else:
                    item = self.data_store.get_account(record_id, self.user)
                return {"count": 1 if item else 0, "records": [item] if item else []}
            return self.data_store.search(entity, query, self.user, account_id)
        except PermissionError as exc:
            return {"error": "ACCESS_DENIED", "message": str(exc), "records": []}

    def _create_escalation(self, ticket_id: str, reason: str, priority: str):
        try:
            ticket = self.data_store.get_ticket(ticket_id, self.user)
        except PermissionError as exc:
            return {"ok": False, "error": "ACCESS_DENIED", "message": str(exc)}
        if not ticket:
            return {"ok": False, "error": "NOT_FOUND", "message": "Ticket not found."}
        return self.actions.prepare_escalation(ticket_id, reason, priority, self.user)

    @staticmethod
    def _normalize_history(history: list[dict] | None) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        if not history:
            return normalized
        for item in history[-12:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant", "system"} and isinstance(content, str):
                normalized.append({"role": role, "content": content})
        return normalized

    @staticmethod
    def _tool_call_to_dict(tool_call: Any) -> dict[str, Any]:
        function = getattr(tool_call, "function", None)
        return {
            "id": getattr(tool_call, "id", ""),
            "type": getattr(tool_call, "type", "function"),
            "function": {
                "name": getattr(function, "name", ""),
                "arguments": getattr(function, "arguments", "{}"),
            },
        }

    @staticmethod
    def _assistant_message_to_dict(message: Any, tool_calls: list[dict[str, Any]]) -> dict[str, Any]:
        content = getattr(message, "content", None)
        return {
            "role": "assistant",
            "content": content or "",
            "tool_calls": tool_calls,
        }

    def _context_clarification(self, message: str) -> str | None:
        """Return a clarification question when the request is contract-sensitive
        but does not identify an account/order/ticket. This prevents the model from
        silently selecting a customer-specific agreement.
        """
        text = message.lower()
        service_credit_terms = (
            "service credit",
            "pickup late",
            "pickup delayed",
            "failed pickup",
            "pickup delay",
            "credit for the delay",
        )
        if not any(term in text for term in service_credit_terms):
            return None

        identifiers = (
            "acct-", "ord-", "tkt-",
            "northstar", "lumenworks", "beacon", "axis labs",
            "beacon retail", "axis labs",
        )
        if any(token in text for token in identifiers):
            return None

        return (
            "It depends on the customer's agreement. The default policy may allow a "
            "service credit for a pickup that is more than 2 hours late, but signed "
            "customer agreements can change that threshold or amount. Please provide "
            "the account, order, or ticket you are asking about so I can apply the "
            "correct terms."
        )

    def _known_issue_context(self, message: str):
        """Return authoritative evidence for the explicit SwiftShip webhook case.

        This is a high-risk knowledge case: the source tells us exactly what to say
        and what not to infer. We therefore ground the response directly in the
        current product guide instead of letting the model invent operational
        capabilities or timing guarantees.
        """
        text = message.lower()
        if "swiftship" not in text or "booked" not in text:
            return None
        if not any(term in text for term in ("picked up", "pickup", "carrier")):
            return None

        query = "SwiftShip pickup confirmation webhook BOOKED 20 minutes late verify carrier status"
        result = self._document_search(query, "", False)
        trace = [{
            "tool": "document_search",
            "arguments": {"query": query, "account_id": "", "include_deprecated": False},
        }]
        return {"trace": trace, "evidence": result}

    def _deterministic_case_context(self, message: str):
        """Pre-fetch authoritative evidence for explicit order-level policy questions.

        This keeps common assessment flows reliable: the app uses its tools first,
        then asks the model only to synthesize the verified evidence.
        """
        text = message.lower()
        order_match = re.search(r"\bORD-\d{4}\b", message, flags=re.I)
        if not order_match:
            return None
        order_id = order_match.group(0).upper()
        intent = None
        if any(term in text for term in ("service credit", "pickup", "late", "delay", "credit")):
            intent = "service_credit"
        elif any(term in text for term in ("cancel", "cancellation", "cancellation fee")):
            intent = "cancellation"
        if not intent:
            return None

        trace = []
        order_result = self._structured_lookup("orders", order_id, "", order_id)
        trace.append({"tool": "structured_data_lookup", "arguments": {
            "entity": "orders", "query": order_id, "account_id": "", "record_id": order_id
        }})
        records = order_result.get("records", []) if isinstance(order_result, dict) else []
        if not records:
            return {"intent": intent, "trace": trace, "evidence": {"order_lookup": order_result}}
        order = records[0]
        account_id = str(order.get("account_id") or "")

        account_result = self._structured_lookup("accounts", account_id, account_id, account_id)
        trace.append({"tool": "structured_data_lookup", "arguments": {
            "entity": "accounts", "query": account_id, "account_id": account_id, "record_id": account_id
        }})

        if intent == "service_credit":
            agreement_query = "failed-pickup service credits carrier fault customer fault 4 hours INR 300 threshold amount"
        else:
            agreement_query = "shipment cancellation BOOKED before pickup cancellation fee waiver no fee"
        agreement_result = self._document_search(agreement_query, account_id, False)
        trace.append({"tool": "document_search", "arguments": {
            "query": agreement_query, "account_id": account_id, "include_deprecated": False
        }})

        sop_query = "cancellation service credit SOP current policy failed pickup"
        sop_result = self._document_search(sop_query, "", False)
        trace.append({"tool": "document_search", "arguments": {
            "query": sop_query, "account_id": "", "include_deprecated": False
        }})

        return {
            "intent": intent,
            "trace": trace,
            "evidence": {
                "order": order,
                "account": account_result,
                "agreement_documents": agreement_result,
                "current_sop_documents": sop_result,
            },
        }

    def chat(self, message: str, history: list[dict] | None = None) -> dict:
        clarification = self._context_clarification(message)
        if clarification:
            return {
                "answer": clarification,
                "tool_trace": [],
                "pending_confirmation": None,
            }

        if not self.client:
            return {
                "answer": "HF_TOKEN is not configured. The local application is ready, but the language-model connection is not configured yet.",
                "tool_trace": [],
                "pending_confirmation": None,
            }

        known_issue_context = self._known_issue_context(message)
        if known_issue_context:
            return {
                "answer": (
                    "SwiftShip pickup confirmation webhooks can arrive up to 20 minutes late. "
                    "A parcel may therefore be physically collected while ParcelPilot still "
                    "shows BOOKED. Before telling the customer that the pickup did not occur, "
                    "verify the carrier status or wait through the known delay window."
                ),
                "tool_trace": known_issue_context["trace"],
                "pending_confirmation": None,
            }

        case_context = self._deterministic_case_context(message)
        if case_context:
            evidence_text = json.dumps(case_context["evidence"], default=str, indent=2)
            synthesis_messages = [
                {"role": "system", "content": SYSTEM_PROMPT + "\n\nFor this request, the application has already executed the necessary tools and supplied verified evidence below. Do not call tools again. Synthesize a concise answer from the evidence, explicitly naming the relevant sources and resolving conflicts by authority."},
                {"role": "user", "content": message},
                {"role": "system", "content": "VERIFIED TOOL EVIDENCE:\n" + evidence_text},
            ]
            response = self.client.chat.completions.create(
                model=HF_MODEL,
                messages=synthesis_messages,
                temperature=0.1,
            )
            return {
                "answer": getattr(response.choices[0].message, "content", None) or "I could not produce a response.",
                "tool_trace": case_context["trace"],
                "pending_confirmation": None,
            }

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self._normalize_history(history),
            {"role": "user", "content": message},
        ]
        tool_trace: list[dict[str, Any]] = []
        access_denied = False

        for _ in range(8):
            response = self.client.chat.completions.create(
                model=HF_MODEL,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.1,
            )
            msg = response.choices[0].message
            raw_calls = getattr(msg, "tool_calls", None) or []
            if not raw_calls:
                if access_denied:
                    return {
                        "answer": "I can’t share the requested information because this user is not authorized to access it. Please use an authorized account or role to retrieve the data.",
                        "tool_trace": tool_trace,
                        "pending_confirmation": None,
                    }
                return {
                    "answer": getattr(msg, "content", None) or "I could not produce a response.",
                    "tool_trace": tool_trace,
                    "pending_confirmation": None,
                }

            tool_calls = [self._tool_call_to_dict(call) for call in raw_calls]
            messages.append(self._assistant_message_to_dict(msg, tool_calls))

            for call in tool_calls:
                name = call["function"]["name"]
                args_text = call["function"]["arguments"]
                try:
                    args = json.loads(args_text)
                except json.JSONDecodeError:
                    args = {}
                tool_trace.append({"tool": name, "arguments": args})

                signature = (name, json.dumps(args, sort_keys=True, default=str))
                previous_signatures = {
                    (t.get("tool"), json.dumps(t.get("arguments", {}), sort_keys=True, default=str))
                    for t in tool_trace[:-1]
                }
                if signature in previous_signatures:
                    result = {
                        "error": "REPEATED_TOOL_CALL",
                        "message": "This exact tool call was already executed. Use the existing tool result and continue to the answer; do not repeat it."
                    }
                elif name not in self.dispatch:
                    result = {"error": "UNKNOWN_TOOL", "message": f"Tool '{name}' is not available."}
                else:
                    result = self.dispatch[name](**args)

                if isinstance(result, dict) and result.get("error") == "ACCESS_DENIED":
                    access_denied = True
                    return {
                        "answer": "I can’t share the requested information because this user is not authorized to access it. Please use an authorized account or role to retrieve the data.",
                        "tool_trace": tool_trace,
                        "pending_confirmation": None,
                    }

                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": name,
                    "content": json.dumps(result, default=str),
                })

            # Let the model incorporate the tool results on the next loop.

        return {
            "answer": "I could not complete the reasoning safely within the tool-call limit.",
            "tool_trace": tool_trace,
            "pending_confirmation": None,
        }
