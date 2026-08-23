# Product Note — ParcelPilot

## 1. Additional client problem selected

**Trust & Reliability**

ParcelPilot's broader concern is that policies can change, customer contracts can override general rules, different sources can disagree, and historical support answers may be wrong. A support system that gives a confident but unsupported answer would reduce trust quickly.

## 2. How the submission addresses it

The MVP makes reliability explicit in the workflow:

- Source status, authority, and account association are carried with retrieved documents.
- Customer-specific agreements are retrieved in the context of the customer's account.
- Deprecated policy is excluded from normal current-state retrieval.
- Historical ticket guidance is treated as context rather than policy authority.
- Missing customer context is clarified instead of silently choosing a contract.
- Unsupported claims and guaranteed timing are avoided when the source pack does not justify them.
- State-changing actions require explicit user confirmation.
- Account authorization is enforced in the data/tool layer.

## 3. What I would build next

### Priority 1 — Real identity and role-based authorization

Replace mocked demo identities with the customer's SSO/identity system and persistent role/account permissions. This is the most important production step because the current system protects data correctly only within the assessment's mocked identity model.

### Priority 2 — Persistent ticketing and audit integration

Connect escalations to a real ticketing system and store an audit trail covering the evidence used, decision, confirmation, and resulting action.

### Priority 3 — Automated evaluation and feedback loops

Create a continuously growing evaluation set covering factual accuracy, source selection, tool choice, authorization, and refusal/escalation behavior. This would make reliability measurable as the source base changes.

### Priority 4 — Proactive issue detection

Add an internal analytics workflow that identifies recurring complaints, SLA risk, unusual support activity, and issues affecting multiple customers. This addresses the second broader client problem without making the initial chatbot unnecessarily complex.

## 4. Intentionally left out of the submission

The first-round submission deliberately does not include:

- Full customer-facing authentication and account-login flows.
- A production ticketing-system integration.
- Production-grade observability and distributed infrastructure.
- A full proactive issue-detection platform.

These would be valuable next steps, but they were excluded to keep the required assessment system small, reliable, and demonstrable.

## 5. One product metric

**Safe Resolution Rate** — the percentage of evaluated support requests where the system reaches a correct, evidence-grounded resolution or appropriate escalation without an unsupported claim or unauthorized action.

This metric captures the core product promise better than raw chat volume because the main risk for ParcelPilot is an incorrect or unsafe answer.
