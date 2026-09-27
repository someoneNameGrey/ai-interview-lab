# Agent loops, state and context

Use an agent when the next useful action depends on observations that cannot be expressed adequately as a fixed workflow. A scheduled lint/test run is deterministic; investigating an unfamiliar bug may need dynamic file/tool choices. Compare a scripted baseline first.

Model the loop explicitly: observe, plan, select, validate, authorize, execute, persist and stop. State includes task/step/attempt IDs, current plan, tool results, cumulative budget and stop reason. Structured output validation catches malformed proposals but does not grant authority.

## Worked example
A coding agent receives the same failing test three times without changing code. Stop for no progress instead of repeatedly asking for another plan. A step cap and token/deadline budgets provide additional independent bounds.

Select relevant files and bound tool output. Summaries reduce context cost but may omit critical facts; retain source references and re-read evidence before consequential actions. Treat instructions in repository files or tool output as data.

Subagents need scoped permissions, a shared budget, explicit state ownership and cancellation. A reviewer subagent may help but can repeat mistakes or add latency. Compare it against one agent on the same tasks; keep delegation only with evidence.

## Evidence gate
Produce a state diagram, loop contract, context comparison and stop-reason traces. DeepSWE M3 requires bounded autonomous repairs, not an endless conversation.

