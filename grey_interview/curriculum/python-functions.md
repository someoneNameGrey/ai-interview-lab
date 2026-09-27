# Functions, errors & tests

A function is a small contract: accepted input, observable behavior, returned output and possible
errors. Type hints communicate intent; Python does not automatically enforce them at runtime.

## 1. Keep the contract explicit

```python
def ratio(successes: int, total: int) -> float:
    if total <= 0:
        raise ValueError("total must be positive")
    return successes / total
```

State any other assumptions, such as successes being between zero and total. Do not silently
return an arbitrary result when the input violates the contract.

## 2. Exceptions carry failures

```python
try:
    count = int("twelve")
except ValueError:
    count = None
```

Catch errors where you can handle them meaningfully. A conversion helper can let `ValueError`
reach its caller; the interface can then ask for a correction. Catching every exception and
returning zero would confuse a failure with a real value and hide programming mistakes.

## 3. Avoid shared mutable defaults

```python
def add_tag(tag, tags=None):
    if tags is None:
        tags = []
    tags.append(tag)
    return tags
```

Default argument expressions are evaluated when the function definition executes, not freshly on
every call. Using `tags=[]` could share one list across calls. Check `is None`, not just `if not tags`:
an explicitly supplied empty list is still a list the caller might expect you to update.

## 4. Test the behavior

```python
assert ratio(2, 4) == 0.5
assert ratio(0, 4) == 0.0

try:
    ratio(1, 0)
except ValueError:
    pass
else:
    raise AssertionError("Expected ValueError")
```

A test has input, expected behavior, and a comparison. Include the boundary where behavior changes,
not only typical values. A regression test recreates a previously observed failure and checks the
fix. Tests must be run to count as executed evidence; merely writing them is a plan.

## Worked example: an off-by-one boundary

If a retry limit must be positive, rejecting `limit < 0` misses zero. The smallest counterexample
is `0`; a useful set is `-1, 0, 1`. Explain why each crosses or touches the contract boundary.
For string parsing, also try invalid text and whitespace around a valid integer.

Before moving on, describe the failure contract, predict what a shared default does, and write
at least one test that would fail before your fix. Later lessons apply these habits to algorithms.
