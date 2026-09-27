# AI systems: evaluate a grounded assistant

Goal: distinguish retrieving evidence from using it correctly.

## The pipeline

Question -> retrieve passages -> select evidence -> generate a grounded answer -> check support
and record measurements. Retrieved text is untrusted; instructions inside it must not override
application rules. When evidence is absent, abstain or ask for clarification.

## Worked example: fictional library policy

Source: "Books may be borrowed for 14 days. Renewals are allowed once if no reservation exists."
Question: "Can I renew a reserved book?" A supported answer says no under this policy and points
to the condition. "What is the late fee?" is unanswerable from this source. Inventing a plausible
fee would be a generation failure, even if the answer sounded confident.

Record whether the needed passage was retrieved and whether the final answer used it correctly.
A citation's presence alone does not show that its text supports a claim.

For a small evaluation set, specify question, evidence, expected behavior and a checkable criterion
before testing changes. Include missing evidence, conflicts and instruction-like content. Keep
tuning examples separate from the final held-out comparison.

## Measure a tradeoff

Track correctness alongside latency and usage. A larger retrieved context may help one case and
hurt cost or evidence selection elsewhere. Compare one change at a time on the same inputs.
Do not turn a judge model's preference into an unexplained claim of correctness.

The exercises use fictional reimbursement facts and a regression table. No special model API
knowledge is needed. Explain what evidence distinguishes retrieval from generation failures.
