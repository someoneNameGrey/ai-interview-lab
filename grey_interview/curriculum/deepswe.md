# Project 1 · DeepSWE

DeepSWE demonstrates reliable agent engineering and rigorous evaluation, not foundation-model training. Reuse durable jobs, typed adapters, isolated tools, context management and trace infrastructure. Work only on disposable copies of permitted repositories; return a reviewable patch, never auto-publish or auto-merge.

## Milestones
M1: durable submit/status/cancel and a fake adapter. M2: benchmark before optimization. M3: autonomous plan/read/search/edit/test loop with explicit stop conditions. M4: enforced sandbox permissions. M5: queue, retries, restart recovery and budget controls. M6: release comparison and operations evidence.

Start with at least 40 tasks (25 development, 15 held-out), grouped by task/repository family. Include multi-file repair, impossible requests and adversarial repository text. This is a small portfolio benchmark, not broad statistical proof.

## Worked example
An agent “fixes” a bug by deleting the failing assertion. Tests under its write access are not a trustworthy grader. Apply the patch to a disposable evaluation checkout and run protected evaluator-owned tests from a trusted copy in isolation. Detect changed/disabled tests and grade behavioral outcomes.

Record task success rate, failures by taxonomy, tool-call accuracy, p50/p95, tokens and cost per successful task. Compare a scripted baseline to the candidate on matched tasks/budgets, with repeated runs and explicit limitations.

## Release gate
Provide runnable setup, dataset/grader versions, failed and successful traces, attack tests, fault/load report, runbook, demo and rejected optimization. Critical permission failures block release. Claims must match executed evidence.

