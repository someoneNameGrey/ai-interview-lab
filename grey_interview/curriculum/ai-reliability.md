# Durable AI jobs and recovery

A queue decouples acceptance from completion; it does not create capacity or guarantee exactly-once effects. Reuse the design-reliability guide's duplicate-delivery and capacity reasoning. Persist job acceptance and an outbox event atomically, then publish with retries.

## Worked example
A worker updates a CRM record and crashes before acknowledgment. Replaying blindly may duplicate the effect. Use a stable downstream idempotency key or reconcile the remote state. A local “done” flag written after a remote effect cannot close this uncertainty window.

Long-running agents need checkpoints, leases, fencing against stale workers, deadlines and durable cumulative budgets. Reauthorize resumed actions after identity/permission changes. Preserve uncertain effects for investigation instead of inventing success.

Classify permanent errors separately from transient ones; use bounded exponential backoff with jitter. Respect provider rate limits, cap concurrency and use admission control. Circuit breakers prevent repeated dependency pressure; fallbacks must satisfy the same authorization and quality policy.

Cache only with tenant/permission-aware keys and explicit freshness rules. Cancellation may stop future work while a remote effect remains uncertain.

## Evidence gate
Kill a worker at the effect/ack boundary, simulate outage and overload, and show known terminal or reconciliation states. Record queue age, throughput and cost including retries. DeepSWE M5 must demonstrate restart recovery and bounded resource use.

