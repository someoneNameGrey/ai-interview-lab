# AI traces, costs and incidents

Observability must explain an individual failure and show whether it is systemic. Propagate request, task, step and attempt IDs through queue, model and tool spans. Structured logs capture redacted outcomes; metrics summarize counts/distributions; traces connect the sequence. Avoid raw prompts, PII and credentials by default.

## Worked example
End-to-end p95 rises while mean model service time stays flat. Queue delay, tail tool calls, extra retries, workload mix or missing spans may explain it. Percentiles of components do not simply add to the end-to-end percentile. Compare consistent cohorts and time windows before choosing a cause.

Measure queue age, success/timeout/error rates, denied tools, tokens, cumulative spend and p50/p95 latency. Include failed calls and retries where usage is available; identify gaps between estimates and provider billing. Cost per success includes money spent on failed tasks.

Create actionable alerts with owner, threshold, investigation query and runbook. Use sampling consciously: rare failures may need different retention, with privacy controls.

## Evidence gate
A release runs deterministic CI tests plus a budgeted live eval suite. Record an incident, mitigation, root cause hypothesis, reproducer, regression and rollback criteria. Feed production corrections/escalations into reviewed eval cases rather than copying sensitive logs wholesale.

