# Values, decisions & loops

Python programs work with values. A name such as `remaining` refers to a value; it is not a box
that permanently has one type. Start by predicting each example before reading its explanation.

## 1. Values and expressions

```python
limit = 10          # int: a whole number
latency = 0.25      # float: an approximate real number
name = "worker"    # str: text
enabled = True     # bool: True or False
result = None      # no result yet

remaining = limit - 3  # 7
message = name + " ready"
```

`=` assigns a value; `==` compares values. `10 == 10` gives `True`. `"10" == 10` gives `False`:
text and integers are different types. Convert deliberately with `int("10")` or `str(10)`.
`7 / 2` is `3.5`, while `7 // 2` is `3`. `%` gives the remainder: `7 % 2` is `1`.

## 2. Make a decision

```python
remaining = 2
if remaining > 0:
    state = "accept"
else:
    state = "wait"
```

The colon starts a block and indentation groups its statements. Use four spaces consistently.
Only one branch runs here. Combine conditions with `and`, `or`, and `not`. For a bounded integer
range, `200 <= status < 300` checks both boundaries. An `elif` adds another branch.

## 3. Repeat work

```python
total = 0
for cost in [2, 3, 1]:
    total = total + cost
# total is now 6

for index in range(3):
    print(index)  # 0, then 1, then 2
```

Trace the accumulator: it starts at 0, then becomes 2, 5, and 6. On an empty list the body never
runs, so the result stays 0. `range` excludes its stop value. A `while` loop repeats as long as its
condition is true; make sure something changes so it can finish.

## 4. Return a result

```python
def doubled(value):
    return value * 2

answer = doubled(4)  # 8
```

`return` gives a value to the caller and exits the function. `print` displays text but is not a
substitute for returning a result. A function without a return value gives `None`.

## Worked trace

```python
def count_large(sizes):
    count = 0
    for size in sizes:
        if size >= 10:
            count += 1
    return count
```

For `[4, 10, 12]`, the counter changes `0 -> 0 -> 1 -> 2`. Returning inside the loop would stop
after its first iteration. For `[]`, the result is 0 because initialization happens before the loop.

## Before moving on

Explain the difference between `=` and `==`, predict an empty loop, and distinguish `print` from
`return`. Then try the knowledge check and the budget/counting exercises. The editor preserves
indentation; model review checks your answer but does not run the code.
