# Architecture Note — ParcelPilot AI Support & Operations Agent

## Agent design
The submission uses one internal support/operations AI agent. The agent receives a natural-language request and decides whether it needs document evidence, structured operational data, or a support action. The application provides three tools: `document_search`, `structured_data_lookup`, and `create_escalation`.

The agent is intentionally single-agent rather than multi-agent. This keeps the system easier to test and explain under the assessment deadline while still supporting multi-step workflows through repeated tool calls.

## Tool design
### 1. Document search
Searches the six supplied PDF documents. Each chunk carries metadata for status, authority, effective date, and account association. Deprecated policy is excluded from normal current-state retrieval.

### 2. Structured data
Loads the supplied workbook's `accounts`, `orders`, and `tickets` sheets. Record lookups are filtered through the authenticated user's authorized account scope before data is returned to the model.

### 3. State-changing action
`create_escalation` prepares an escalation but does not execute it. The application stores the pending action and requires explicit user confirmation. The actual confirmation endpoint performs the mocked state change.

## Multi-step handling
A question can trigger several tools. Example cancellation flow:
1. Look up the order.
2. Identify the account.
3. Search the customer's signed agreement.
4. Search the applicable current SOP/policy.
5. Compare the evidence using source authority rules.
6. Answer or prepare an escalation when evidence is insufficient.

## Source reliability and conflicts
The system carries source metadata into retrieval results. The supplied current support policy states that a signed customer agreement has priority over current support policy, which has priority over current product documentation; historical tickets are context only. Deprecated policy is not used for normal current answers.

When supplied data conflicts or key facts are unknown, the agent is instructed to state the uncertainty and avoid making unsupported promises or state changes.

## Access control
The demo uses a mocked authenticated internal support user with an explicit list of authorized account IDs. The authorization check occurs in the structured-data tool layer, not only in the model prompt.

## Major trade-offs
- Local transparent retrieval instead of a separate vector database: faster to build, easier to inspect, and sufficient for the small supplied document set.
- One agent instead of multiple agents: lower orchestration complexity and easier debugging.
- Mocked escalation state: satisfies the assessment action requirement without pretending to integrate with a production ticketing system.
- Internal support context instead of customer-facing context: demonstrates the required tool/data capabilities while keeping the authentication surface appropriately small for the assessment.


## Validation highlights
The implementation was tested against the supplied assessment cases and edge cases, including:
- Northstar booked-shipment cancellation override.
- LumenWorks failed-pickup credit with the contractual INR 300 amount.
- SwiftShip BOOKED status with a documented webhook delay.
- P1 security-ticket escalation with explicit confirmation before execution.
- Cross-account authorization denial at the structured-data layer.
