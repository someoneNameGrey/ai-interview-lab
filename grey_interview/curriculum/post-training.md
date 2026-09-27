# Post-training: reason about data and evaluation

Optional module. Start after AI systems if these terms are new.

Supervised fine-tuning learns from examples of desired outputs. Preference-based approaches use
comparisons or related feedback about outputs. In both cases, data and objectives can encode
unwanted shortcuts. A better proxy metric is not automatically better task performance.

## Worked example: formatting versus correctness

Suppose reviewers prefer answers with headings. A model could win more comparisons by adding
headings while leaving factual mistakes untouched. A separate correctness check can reveal this
mismatch. Review guidance should define good evidence and correctness, not just professional style.

If near-identical prompts occur in training and evaluation, held-out performance may overstate
generalization. Group related examples before splitting; record versions and inspect leakage paths.
A split is an experimental design choice, not a guarantee by itself.

## Before a training run

State the target behavior, audit labels, establish a baseline, and define a held-out comparison.
Record exclusions and uncertainty. Inspect failure categories as well as aggregate win rate.
Preserve a final set that was not repeatedly used for tuning.

The exercises audit preferences and investigate conflicting metrics. They require reasoning about
evidence, not training a model on your machine.
