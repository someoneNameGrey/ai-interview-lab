# Project 2 · Enterprise support agent

Build an enterprise support workflow with RAG, CRM ticket/history, billing/account lookup, RBAC, tenant isolation, audit logs, injection defense, PII handling and human escalation. Reuse DeepSWE eval/trace/budget infrastructure, not its application permissions.

## Milestones
S1: evaluated retrieval and citations. S2: discovery, baseline and architecture. S3: typed integrations and security controls. S4: approval-bound actions and human handoff. S5: evals, tracing, cost/latency and failure handling. S6: controlled deployment, rollback and outcome report.

## Worked example
A support agent cannot confidently answer a billing dispute. It creates an escalation with redacted evidence and reason, then yields ownership. If a human accepts, queued automation must not continue and send a conflicting answer. Persist ownership and check it before every consequential action.

Use at least 60 end-to-end cases, 40 development / 20 held-out by family. Include normal tickets, no evidence, conflicting policy, cross-tenant attacks, expired approval, outages and duplicate callbacks. Test accuracy, grounding, tools, permission denials and escalation quality.

## Release gate
Show actual implementation/test evidence, a controlled deployment, runbook and rollback. Use an authorized CRM sandbox if available; label mocked adapters unverified externally. Compare matched manual/rules and assisted workflows on quality, handling time, reopens, adoption and total cost including human review. Synthetic savings are estimates, not observed customer impact.

