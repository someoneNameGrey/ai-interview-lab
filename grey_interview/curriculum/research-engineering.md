# Research engineering: design an experiment you can trust

Optional module. The goal is a reproducible comparison with a falsifiable claim.

## From an idea to a test

State a hypothesis, baseline, changed factor, controls, metrics, acceptance rule, and what result
would reject the idea. Record code, data, configuration, environment and raw outputs. Use repeated
runs or appropriate uncertainty analysis; explain what varies between runs.

## Worked example: a response cache

Hypothesis: caching repeated requests reduces median latency on a workload with a stated repeat
rate, without returning stale results. Compare cache on and off using the same request sequence,
model, hardware and measurement boundaries. Measure hit rate, latency and stale-result failures.
Include warmup and invalidation cases. Declare improvement and correctness limits before testing.

If only the cached run uses easier requests, the comparison cannot isolate the cache effect.
If the mean improves but variability grows, inspect distributions instead of selecting the best
run. A small sample does not justify a confident general claim.

## A minimal experiment record

Question; hypothesis; baseline; controls; changed factor; workload/version; measurement method;
raw results; uncertainty; failure analysis; conclusion; next experiment.

Your exercises compare batching policies and reason about noisy results. Describe a plan as a
plan; never turn unrun experiments into claims of measured improvement.
