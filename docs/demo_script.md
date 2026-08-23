# 5-Minute Demo Script

## 0:00–0:40 — What we built

**Say:**

“ParcelPilot Support & Operations Agent is an internal AI support agent. The user enters a natural-language request, and the agent can use three capabilities: document retrieval, structured operational data, and a confirmation-gated escalation action. Authorization is enforced in the data layer, and state changes require explicit confirmation.”

Show the left-side demo identity and the tool trace area.

## 0:40–1:35 — Multi-step cancellation

Ask:

> Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.

**Show:** the evidence and tool trace.

**Explain:**

“The system first uses the operational data to identify the order and account, then retrieves the Northstar agreement and current cancellation guidance. The signed customer agreement overrides the default cancellation fee rule, so the answer is no cancellation fee.”

## 1:35–2:25 — Contract-specific service credit

Ask:

> For ORD-2002, is LumenWorks eligible for a service credit? Calculate the amount and explain why.

**Explain:**

“The agent combines the order timing and fault data with the LumenWorks agreement and the current SOP. The LumenWorks agreement sets a more-than-four-hour threshold and a fixed INR 300 credit, so the result is INR 300.”

## 2:25–3:10 — Reliability and uncertainty

Ask:

> What should I tell a customer if a SwiftShip shipment is still showing BOOKED even though the carrier says it was picked up?

**Explain:**

“The current product guide documents a SwiftShip webhook delay of up to 20 minutes. The agent does not treat BOOKED as proof that pickup failed; it recommends verifying carrier status or waiting through the documented delay window.”

## 3:10–4:15 — P1 escalation with confirmation

Ask:

> What should we do about TKT-505?

**Show:** the prepared escalation and confirmation control.

**Explain:**

“The ticket is a P1 security incident, so the agent prepares an escalation. Importantly, it cannot execute the state change from model output alone. The user must explicitly confirm.”

Click **Confirm action**.

Show the success message.

## 4:15–4:45 — Access control

Switch to:

**Support Agent — ACCT-001 only**

Ask:

> Show me the details for ACCT-002.

**Explain:**

“The structured-data tool denies access before protected account data is returned. The model is not relied on as the security boundary.”

## 4:45–5:00 — Key decisions

**Say:**

“The main design decisions were to keep the system single-agent and lightweight, use transparent local retrieval for the small supplied document set, enforce authorization in the tool layer, treat source reliability explicitly, and require confirmation before actions. The broader product focus we chose was Trust & Reliability.”
