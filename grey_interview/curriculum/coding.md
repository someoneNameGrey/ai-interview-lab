# Coding: solve a small problem out loud

Goal: explain the contract, maintain a simple invariant, and verify the result.

## A repeatable sequence

1. Clarify valid input, output, ordering, mutation and failure behavior.
2. Walk through a tiny example by hand, including a boundary case.
3. Choose a simple correct approach and name what stays true after each step.
4. Implement it. State time and space costs, distinguishing output from extra storage.
5. Show concrete tests. Only claim execution if you actually ran them yourself.

## Worked example: count job statuses

Contract: given status strings, return a mapping from each observed status to its count.
An empty list gives an empty mapping. We do not modify the input.

```python
def counts(statuses):
    result = {}
    for status in statuses:
        result[status] = result.get(status, 0) + 1
    return result

assert counts([]) == {}
assert counts(["queued", "done", "queued"]) == {"queued": 2, "done": 1}
```

After each iteration, the mapping counts exactly the prefix processed so far. That invariant
explains why the final mapping is correct. With expected constant-time dictionary operations,
time is O(n) and output storage is O(k), where k is the number of distinct statuses.
These are example assertions; the trainer does not execute them.

## Try it yourself

Exercise 1 preserves first occurrences; Exercise 2 splits jobs into bounded batches. Borrow the
habit of explaining an invariant, not the exact counting algorithm. A correct simple baseline
with honest complexity is a useful first attempt.

Common mistakes: sorting when order must stay unchanged; validating a parameter only inside a
loop; testing only the happy path; and claiming O(1) space while returning a growing structure.

Before submitting: can you explain empty input, repeated items, and an invalid batch size?
