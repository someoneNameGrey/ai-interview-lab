# DSA 3 · Dynamic programming and mocks

Weeks 17–20 focus on basic dynamic programming; weeks 21–24 mix earlier patterns under interview conditions. Avoid advanced contest theory unless a target interview warrants it. State the subproblem before writing a recurrence.

## Worked example
For nonnegative gains where adjacent jobs cannot both be chosen, let best[i] be the best total using the first i jobs. Then best[i] = max(best[i-1], best[i-2]+gain[i-1]), with best[0]=0 and an explicit first-item base. The choices are skip or take; greedy choice of the largest next item can miss the global optimum. Rolling state saves memory only if old values are preserved correctly.

For coin change, define whether order matters and whether coins may be reused. Minimum count is different from counting combinations. An unreachable state is not zero; distinguish it from the empty target.

## Practice rotation
Climbing-step variants, nonadjacent maximum, minimum coins and grid paths. Then mix hashing, search, graphs and one DP problem so recognition is not cued by the lesson title.

## Evidence gate
Clarify input, derive state/transition/base, implement, explain complexity and execute boundary tests. Preserve the first attempt. Repeat missed concepts on fresh problems. A correct memorized recurrence without explanation is weak interview evidence.

