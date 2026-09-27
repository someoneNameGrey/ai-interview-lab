# DSA 2 · Trees, heaps and graphs

Weeks 9–16 rotate tree traversal/depth, heap-based top K, unweighted shortest paths, connected components and dependency ordering. Start with one structure, then add cycles, ties, streaming input or scale constraints. Continue two unaided 45-minute sessions each week.

## Worked example
In an unweighted graph, BFS visits nodes by nondecreasing distance from the source. Mark a node visited when enqueuing it, not when dequeuing, to avoid duplicate frontier work. Parent pointers reconstruct one shortest path; DFS does not generally produce a shortest path.

For trees, distinguish a legitimate empty child from a missing node and consider recursion-depth limits. For heaps, store only k candidates when the problem allows it; define ties explicitly. For dependency graphs, indegrees count unmet prerequisites. A queue of zero-indegree nodes produces a topological order; fewer emitted nodes than total means a cycle.

## Practice rotation
Tree depth, level-order traversal, kth largest stream, graph reachability, shortest hops, connected components and course scheduling. Explain O(V+E) with an adjacency list; repeatedly scanning all edges can invalidate that bound.

## Evidence gate
Tests include disconnected graphs, cycles, empty input, singleton and duplicate edges under a stated policy. Defend BFS versus DFS versus a heap without naming an algorithm as a substitute for reasoning.

