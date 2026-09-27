# Debugging: turn a symptom into a regression test

Goal: narrow the cause with evidence before editing code.

## A small investigation loop

Record expected versus actual behavior. Reproduce the smallest failure. List hypotheses and a
measurement that would disprove each. Fix one cause. Re-run the reproducer and nearby cases.
Separate a mitigation that reduces harm from a fix that removes the cause.

## Worked example: missing the final item

```python
def copy_items(items):
    return [items[i] for i in range(len(items) - 1)]
```

Expected: copy all items. Actual: ["a", "b"] becomes ["a"]. A singleton becomes [] and is a smaller
reproducer. The range ends before the last index. Returning list(items) fixes this contract.
Check empty, singleton and multi-item inputs; also check the result is a distinct list.
Assertions are a regression plan until you run them in your own environment.

## Operational failures

Split elapsed time into queue wait, service and dependencies. Ask which population and time window
a percentile describes. An unchanged average does not rule out a worse tail. Compare deployments,
load shape and measurement changes before deciding on a cause.

Use observation -> competing hypotheses -> discriminating measurement -> change -> verification.
"Add logs" is incomplete without saying which value and comparison would change your mind.

Your exercises include a queue bug and an incident where the cause is deliberately unknown.
