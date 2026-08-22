# 5-Minute Demo Script

## 0:00–0:40 — Architecture
Explain that this is an internal support/operations agent with one LLM agent and three tools: document search, structured-data lookup, and escalation. Emphasize that authorization lives in the data/tool layer and state changes require confirmation.

## 0:40–1:40 — Multi-step cancellation
Ask: “Can Northstar cancel ORD-1001 without a cancellation fee? Explain why.”

Show the tool trace and explain: the system finds the order, identifies Northstar, retrieves the signed agreement and current SOP, and applies the customer-specific override.

## 1:40–2:40 — Service credit reasoning
Ask about the missed pickup for ORD-2002 and whether a service credit applies. Explain that the agent checks order timing/fault data, then the current SOP and LumenWorks agreement before calculating the applicable amount.

## 2:40–3:35 — Reliability / known issue
Show a query about TKT-504. Explain that the current product guide warns SwiftShip pickup webhooks can be delayed, so the system should verify carrier status before telling the customer the pickup failed.

## 3:35–4:20 — Action with confirmation
Ask the agent to investigate TKT-505 and prepare an escalation. Show the prepared action and then explicitly click Confirm. Explain that the action cannot execute from model output alone.

## 4:20–5:00 — Key decisions
Summarize: internal context, source precedence, tool-layer authorization, confirmation before actions, and deliberate uncertainty handling. Mention the Trust & Reliability product choice and the safe-resolution metric.
