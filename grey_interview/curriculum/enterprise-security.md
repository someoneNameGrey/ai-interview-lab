# Identity, privacy and enterprise controls

Authentication establishes identity; authorization decides which action on which object is allowed. OAuth delegation/scopes do not replace business authorization. Derive user and tenant from trusted server context, never a model-supplied tenant_id. Check access before retrieval and again for returned objects and tool effects.

## Worked example
A user in tenant A asks about account B123. A tool accepts the model's tenant B argument and returns billing data. A warning in the prompt would not prevent this confused-deputy failure. Bind tool context to authenticated tenant A and reject unauthorized object access. Cache keys, queues, traces and storage need equivalent tenant separation.

Treat direct user instructions, CRM notes and retrieved content as potential injection. Limit available tools, validate schemas, restrict egress and redact sensitive context. PII minimization, retention/deletion, secret rotation, audit access and provider data-flow review are engineering requirements with named owners.

Approval must bind exact action, arguments, actor, tenant and expiry. Reauthorize at execution; invalidate changed arguments or revoked access. Human-in-the-loop is a state machine, not a model saying “approved.”

## Evidence gate
Attack-test cross-tenant reads, role changes, malicious documents, exfiltration and expired approvals. Audit decisions without secrets. Document residual risks and governance questions; do not claim compliance without evidence.

