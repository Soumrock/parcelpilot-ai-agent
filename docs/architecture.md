# Architecture Note — ParcelPilot AI Support & Operations Agent

## 1. Agent design

The submission uses one internal Support & Operations AI agent. A user enters a natural-language support or investigation request through the Streamlit interface. The agent decides whether it needs supplied document evidence, structured operational data, or a state-changing support action.

The agent is intentionally single-agent rather than multi-agent. This keeps orchestration, debugging, and evaluation straightforward while still supporting multi-step workflows through sequential tool use.

The agent also has deterministic guardrails around high-risk paths. For explicit order-level cancellation and service-credit questions, the application assembles the relevant operational evidence first and then asks the model to synthesize the answer. This reduces unnecessary tool-call loops and keeps critical business-rule decisions grounded in retrieved evidence.

## 2. Tool design

### Document retrieval tool

`document_search` searches the six supplied PDFs. Each retrieval result includes source metadata such as document name, status, authority, effective date, and account association. Deprecated policy is excluded from normal current-state retrieval unless historical comparison is explicitly requested.

### Structured-data tool

`structured_data_lookup` reads the supplied workbook's `accounts`, `orders`, and `tickets` sheets. It supports exact record lookup for known IDs and broader searches when appropriate.

Authorization is enforced inside this data layer: the tool checks the authenticated demo user's authorized account IDs before returning an account, order, or ticket.

### State-changing action tool

`create_escalation` prepares an escalation for an authorized ticket. Preparing the action does not execute it. The application stores the pending action and requires an explicit user confirmation before the mocked action store records the escalation as executed.

## 3. Multi-step workflow

A typical cancellation investigation follows this sequence:

1. Identify the order from structured data.
2. Identify the associated account.
3. Retrieve the relevant customer agreement, if one exists.
4. Retrieve the current cancellation/service-credit guidance.
5. Compare the retrieved evidence using source authority and customer-specific override rules.
6. Answer directly when the evidence is sufficient; otherwise state uncertainty or prepare an escalation.

For a service-credit investigation, the agent also checks timing, carrier fault, customer fault, agreement-specific terms, and the applicable amount before responding.

## 4. Document and structured-data handling

The workbook's README snapshot time is used as the reference time for time-based questions. The structured data is loaded from the supplied Excel workbook without hard-coding the example order or ticket IDs.

The six supplied PDFs are short assessment documents, so the retrieval layer keeps each document as a single authoritative retrieval unit. This avoids separating a contractual threshold from its corresponding amount or exception clause and makes source metadata easy to inspect.

## 5. Source reliability and conflict handling

The supplied current support policy states that when sources conflict, the signed customer agreement comes first, followed by the current support policy and current product documentation; historical tickets/internal notes are context only and may contain incorrect guidance.

The application represents source authority explicitly in retrieval metadata. Customer-specific agreements are associated with their account IDs. Deprecated policy is excluded from ordinary current-state retrieval.

When important facts are missing or conflicting, the agent is instructed not to guess. For example, a service-credit question without an account/order/ticket is clarified rather than silently applying one customer's contract terms.

Known-issue responses also avoid unsupported claims. For the SwiftShip webhook issue, the agent reports only what the supplied product guide supports: a pickup can physically occur while ParcelPilot still shows `BOOKED`, and carrier status should be verified or the known delay window should be allowed to pass.

## 6. Access control and action safety

The submission uses mocked internal identities with explicit account scopes. A support user limited to `ACCT-001` is denied access to `ACCT-002` by the structured-data layer before protected data can reach the model.

State-changing actions have a separate confirmation boundary:

`prepare escalation → explicit confirmation → execute mocked action`

This prevents model output alone from performing a state change.

## 7. Major technical trade-offs

- **Local TF-IDF retrieval instead of a separate vector database:** the supplied document set is small, so a transparent local retriever is easier to inspect, test, and deploy under the assessment deadline.
- **One agent instead of multiple agents:** reduces orchestration complexity while still supporting multi-step tool workflows.
- **Streamlit instead of a separate frontend/backend deployment:** reduces operational complexity and makes the hosted demo straightforward.
- **Hugging Face Inference Providers instead of a paid model API dependency:** fits the free-first deployment strategy used for the assessment.
- **Mocked escalation action instead of a real ticketing integration:** satisfies the required state-changing action behavior without pretending to have access to ParcelPilot's production systems.
- **Internal support context instead of customer-facing context:** keeps the authentication surface small while allowing the submission to demonstrate authorization, investigation, retrieval, and safe actions.

## 8. Validation highlights

The working application was validated against the supplied assessment scenarios and edge cases, including:

- Northstar cancellation override for `ORD-1001`.
- Missing-account clarification for a contract-sensitive service-credit question.
- LumenWorks service-credit calculation for `ORD-2002`, including the contractual INR 300 amount.
- SwiftShip `BOOKED` status with the documented webhook-delay issue.
- P1 security-ticket escalation for `TKT-505`, including confirmation before execution.
- Cross-account denial for a support user limited to `ACCT-001` requesting `ACCT-002`.
