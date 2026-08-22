# Product Note — ParcelPilot

## Additional client problem selected
**Problem 2: Trust and Reliability.**

The submission focuses on preventing confidently incorrect support answers by making source authority, freshness, uncertainty, and human confirmation explicit parts of the workflow.

## How it is addressed
- Current and deprecated sources are distinguished in retrieval metadata.
- Signed customer agreements are surfaced as customer-specific authority.
- Historical ticket resolutions are treated as context, not policy.
- The agent is instructed to identify uncertainty instead of inventing missing facts.
- State-changing actions require explicit confirmation.
- Data access is scoped in the tool layer.

## What I would build next
1. Real identity and role-based authorization.
2. A persistent escalation/ticket integration with an audit log.
3. Automated evaluation datasets for factual accuracy, source selection, and tool choice.
4. Proactive issue detection for recurring complaints and SLA risk.

## Intentionally left out
A full customer-facing authentication flow, real ticketing-system integration, and a production-grade observability platform were left out of the first-round submission to keep the required system small and reliable.

## One product metric
**Safe Resolution Rate:** percentage of evaluated support requests where the system reaches a correct, evidence-grounded resolution (or appropriate escalation) without an unsupported claim or unauthorized action.
