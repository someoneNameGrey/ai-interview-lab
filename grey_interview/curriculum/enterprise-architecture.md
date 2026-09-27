# From business request to AI architecture

“We want AI in support” is a starting question, not a solution specification. Discover ticket categories, current handling/reopen rates, peak volume, policy owners, systems of record, permitted actions, acceptable delay, cost of mistakes and who owns adoption.

## Worked example
If 60% of tickets ask for a deterministic account status, a typed lookup plus rules may solve much of the problem. Use retrieval for policy evidence and language models for ambiguous explanations; add an agent only when dynamic multi-step decisions are needed. Start in staff-assist mode before autonomous mutations.

Trace one request through authenticated identity, retrieval, model, tool policy, approval, effect and audit. Define integration contracts, versioning, timeout/error behavior and reconciliation. A transactional outbox can couple local state and event publication; it cannot atomically commit an external vendor effect.

Predeclare eval slices, quality/security/cost/latency gates and business outcomes. Plan shadow mode, limited pilot, rollout, rollback and monitoring with owners. Count human review costs and correction/reopen rates; fast incorrect closure is not value.

## Evidence gate
Produce discovery brief, architecture/data-flow diagram, AI-versus-rules decision, tool/permission matrix, integration contracts, eval and staged delivery plan. This is Support S2; revisit discovery if technical assumptions change.

