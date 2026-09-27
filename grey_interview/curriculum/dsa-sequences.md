# DSA 1 · Arrays, windows and search

Use two 45-minute unassisted sessions weekly. Weeks 1–4: arrays/hash maps, two pointers and sliding windows. Weeks 5–8: stacks/queues and binary search. Begin with a straightforward problem; move to combined/medium variants only after two fresh correct attempts with explained invariants and tests. These are original LeetCode-style exercises, not a linked LeetCode problem catalog.

## Worked example
To find the first repeated event ID, scan left to right with a seen set. Before index i, seen contains exactly IDs from the preceding prefix. If the current ID is present, it is the first repeated event encountered. Expected time is O(n), extra space O(n). Sorting loses encounter order.

For windows, state what makes the current range valid and how moving each boundary restores validity. For a monotonic stack, say which candidates can never matter again. For binary search, define a half-open interval and the predicate separating false from true; duplicate values expose vague invariants.

## Practice rotation
Try pair sums, sorted pair search, deduplication, longest valid window, balanced delimiters and lower-bound search. Change ordering, duplicates or empty input on the repeat.

## Evidence gate
Clarify contract, implement, state complexity and test empty/singleton/duplicates/boundaries. After feedback, solve a fresh variant without hints. Guided lesson scores remain assisted; use independent coding practice/mock for readiness.

