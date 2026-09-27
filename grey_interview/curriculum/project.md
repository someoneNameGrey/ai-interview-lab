# Project deep-dive: explain real ownership

Goal: connect a real constraint to your decision and its evidence.

## Make an evidence card

Write: problem -> users -> constraints -> your responsibility -> decision -> alternative -> evidence
-> limitation -> next improvement. Keep "I did" separate from "our team achieved". If you have no
finished project, label a proposal and describe what you would measure instead of inventing results.

## Worked example (fictional, not your experience)

"For a small internal import tool, I implemented resumable batches because interrupted uploads
forced users to restart. I chose a per-batch checkpoint over a distributed queue because one process
handled the workload. My evidence would be an interruption/restart test and measured completion
time. I have not established that this design supports multiple concurrent writers."

The structure is constraint, own action, alternative, verification and honest limit. For a real
story, replace "would be" with actual evidence only after collecting it. A list of framework names
does not explain why a design fits the problem.

## When challenged

State the strongest reason for an alternative and evidence that would change your decision.
A failed experiment is useful material if you explain what you changed and checked. Do not invent
percentages because an answer seems to need a metric; qualitative evidence or an explicit gap is
better than a fabricated number.

Your exercises produce an evidence card and revisit a decision. A small honest example is enough.
Build the two projects in TRAINING.md for richer independent interview evidence: DeepSWE demonstrates
reliable agents and rigorous evaluation; the Enterprise AI Support Agent demonstrates secure delivery
in a business workflow. Distinguish synthetic pilot results from actual customer adoption and impact.
