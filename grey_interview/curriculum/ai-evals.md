# Datasets, graders and release gates

An eval is a versioned decision procedure, not a score screenshot. Each case needs provenance, input, allowed evidence/tools, expected behavior, prohibited actions, slice labels and a grader version. Split related task/document families together to reduce leakage. Keep development data separate from a frozen holdout.

## Worked example
Baseline succeeds on 30/40 tasks at $0.10 per attempted task; candidate succeeds on 32/40 at $0.20. Total cost per successful task is $4/30 versus $8/32. Two extra successes do not automatically justify doubling spend. Forty cases also leave substantial uncertainty. Repeat stochastic runs with matched budgets and report raw counts and intervals.

Use deterministic graders for test outcomes, schemas and prohibited actions. Use human labels and calibrated LLM judges for open-ended correctness and groundedness. A citation is not proof that a claim is supported. Blind baseline/candidate identity and adjudicate judge-human disagreements. Treat judge input as untrusted.

Report tool selection, argument validity and authorized outcome separately. Taxonomize retrieval, planning, tool, permission, recovery, provider, grading, timeout and budget failures. Include crashes/timeouts in task-success denominators.

## Evidence gate
Keep mocked regressions in CI; budget live release evals. Record data/model/prompt/code versions and latency/token/cost slices. Predeclare quality, security and cost guardrails. Grader changes require recalibration. Collect production corrections and escalations with privacy review and sampling-bias checks.

