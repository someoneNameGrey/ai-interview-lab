# Lists, dictionaries & sets

Most interview problems become simpler when the collection matches the operation you need.

## 1. Lists: ordered sequences

```python
jobs = ["a", "b", "c"]
first = jobs[0]      # "a"
last = jobs[-1]      # "c"
prefix = jobs[:2]    # ["a", "b"]
jobs.append("d")    # changes jobs; append itself returns None
```

Indexing starts at zero. An invalid index raises `IndexError`. A slice excludes its stop index.
Lists preserve order and allow duplicates. Use `len(jobs)` to count elements and `for job in jobs`
to visit each one. Do not assign `jobs = jobs.append("d")`: that replaces your list name with `None`.

## 2. Dictionaries: lookup by key

```python
status = {"job-1": "queued", "job-2": "done"}
status["job-1"] = "running"
unknown = status.get("job-3", "missing")

for job_id, state in status.items():
    print(job_id, state)
```

`status["job-3"]` raises `KeyError` when the key is absent. `get` lets you choose a default.
Keys must be hashable, such as strings or integers. A list is mutable and cannot be a dictionary key.

## 3. Sets: distinct membership

```python
seen = set()
seen.add("job-1")
seen.add("job-1")
already_seen = "job-1" in seen  # True; only one copy is stored
```

Use sets for uniqueness and membership, not positional order. `set()` makes an empty set; `{}`
makes an empty dictionary. Set/dictionary lookups are usually expected O(1); checking a value in
a list can require scanning O(n) elements. These are algorithmic expectations, not fixed timings.

## 4. Names can share mutable objects

```python
original = ["a"]
alias = original
alias.append("b")
# original is now ["a", "b"] too

independent = original.copy()
independent.append("c")
# original remains ["a", "b"]
```

Assignment copies a reference, not the list. `copy()` is shallow: nested objects would still be
shared. If the list contains only strings and you only append to it, a shallow copy is sufficient.

## Worked example: group by status

```python
groups = {}
for job_id, state in [("a", "queued"), ("b", "done"), ("c", "queued")]:
    if state not in groups:
        groups[state] = []
    groups[state].append(job_id)
# {"queued": ["a", "c"], "done": ["b"]}
```

The dictionary finds a group by status; each list preserves that group's job order. Initializing
the list only for new keys avoids deleting earlier entries.

Before moving on, explain why a set alone cannot return IDs in first-seen order, and why assigning
one list to another name does not protect the original from mutation.
