# Course audit before revision

Audited 27 September 2026, before modifying course files. Inspected README, TRAINING,
the bundled lesson catalog and guides, curriculum loader, profile/competency defaults,
interviewer/tutor/evaluator prompts, and training tests. This folder has no Git metadata;
repository history was unavailable for checking an earlier DeepSWE definition.

| Existing material | Finding | Reuse decision |
| --- | --- | --- |
| Curriculum loader and lessons.json | 13 guides, 26 exercises, 39 checks; five foundations, six core tracks, two optional tracks. Recommendations start with foundations. | Keep the trainer; experienced learners select lessons explicitly. Advanced roadmap phases are manual work, not new app lesson IDs. |
| Python foundations | Useful contracts, errors, mutable defaults and boundary tests; insufficient senior Python depth. | Diagnostic/remediation only, followed by typed async clients, pytest, cancellation and packages. |
| Design basics/reliability and system design | Good APIs, durable acceptance, outbox, duplicate delivery, queues and capacity. | Reuse in both projects; skip already-mastered reading. |
| Coding/debugging | Useful invariants, complexity, reproduction and regression discipline. | Retain for independent interviews and operational drills. |
| AI systems | Sound grounding, abstention, injection awareness, held-out comparisons and cost/latency principles; introductory exercises. | Brief refresher, then first-class evals, retrieval metrics, agent state and enforceable security. |
| Project/behavioral | Strong evidence cards, ownership, alternatives and limitations. | Retain and extend with discovery, stakeholder communication and architecture defense. |
| Post-training | Already optional; label quality and leakage useful, training outside target. | Zero required hours; transfer evaluation principles into evals. |
| Research engineering | Already optional; controlled cache experiment and reproducibility template useful. | Reuse experiment discipline; zero required ML research hours. |
| TRAINING inference job service | Good job, retry, model-adapter, eval, operations and permission milestones. | Fold into DeepSWE instead of retaining a competing third capstone. |
| DeepSWE | No definition or implementation found in inspected files or text search. | Define requested DeepSWE-style coding agent as Project 1; do not claim an implementation was preserved. |
| Trainer behavior/tests | Guided versus independent scores, saved sessions, recovery and mocks supported; code reviewed, not executed. | Keep boundaries; collect executed project evidence outside trainer. |
| Profile/prompt defaults | Broad AI Systems Engineer target omits supplied experience and exact roles. | Document targeted profile update; preserve personal settings and snapshots. |

Main gaps: production Python; agent lifecycle; tool isolation; rigorous evals; retrieval diagnosis;
observability; enterprise identity/privacy; integrations/rollout; customer communication and outcomes.
TRAINING makes these required with dependencies, exercises and evidence gates.

The first revision changed roadmap and entry guidance. The subsequent lab integration added 19
applied/DSA lessons (38 exercises, 57 checks), updated the recommended path, readiness, prompts and
profile, and retained legacy lesson IDs/session snapshots. The lab now has 32 lessons, 64 exercises
and 96 checks. Portfolio implementation still takes place outside the trainer; guided project
reviews do not certify deployment. The inference-service capstone is superseded by its reused
DeepSWE milestones. The table above records the original audit state, not the expanded catalog.

Primary reference: [OpenAI Applied AI Engineer, Singapore](https://openai.com/careers/applied-ai-engineer-singapore/),
accessed 27 September 2026. It emphasizes hands-on Python, evaluation, enterprise delivery,
operational/security judgment, stakeholder communication and measurable customer outcomes.
This plan is not an official interview syllabus or hiring guarantee.
