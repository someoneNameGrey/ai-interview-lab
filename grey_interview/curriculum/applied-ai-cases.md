# Eight enterprise design cases

Rotate eight cases: customer support, internal knowledge assistant, sales agent, coding agent, document processing, financial operations, enterprise search and multi-agent workflow. Spend 45–60 minutes per case, then repeat under changed scale, data or reliability constraints.

For every case answer: why AI, why an agent, why not deterministic, which tools, which approvals, how evaluated, what failure modes, how PII is handled, how injection is contained, and how business value is measured. Produce a diagram, five eval cases and a failure table.

## Worked example
A financial-operations assistant may reconcile invoice fields using deterministic rules plus extraction, while proposing exceptions for human review. It does not need autonomous fund transfers. A sales agent should draft grounded follow-ups, with approval before contact. Both require authorization and audit, but their business success metrics differ.

Knowledge/search cases challenge document permissions and freshness. Document processing challenges OCR ambiguity, schema drift and duplicates. Coding cases challenge sandboxing and test integrity. Support cases challenge policy conflicts, outages and takeover.

For multi-agent workflows define state ownership, handoff schemas, inherited permissions, cancellation and shared budget. Benchmark against a single agent; choose the simpler option if measured benefit is absent.

## Evidence gate
A design must survive a changed constraint and an alternative proposal. A large architecture diagram without contracts, security checks or measurable outcomes is incomplete.

