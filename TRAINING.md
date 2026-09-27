# Production AI engineering roadmap

Prepare as an experienced software engineer specializing in production AI systems. Target Backend
Software Engineer on an AI team, Generative AI Software Engineer, and Applied AI Engineer roles.
Build on eight years of backend/full-stack, cloud, API, database and distributed-systems experience,
including shipped LLM API, RAG, vector database and tool-calling products.

The primary reference is [OpenAI Applied AI Engineer, Singapore](https://openai.com/careers/applied-ai-engineer-singapore/)
(accessed 27 September 2026). Its hands-on engineering, systematic evaluation, enterprise integration,
operational readiness and customer impact drive this plan. Other teams have different requirements;
this is not their official interview process.

Read [COURSE_AUDIT.md](COURSE_AUDIT.md) for the pre-edit audit and reuse decisions. This is the advanced
roadmap. The browser/CLI now includes the advanced lesson guides, exercises, checks and project
reviews. Implement and execute portfolio projects outside the app, then submit evidence for review.

## Schedule and dependencies

Plan for **24 weeks at 12–15 hours/week (288–360 hours)**. Advance on evidence, not elapsed time.
Each week allocate 7–9 hours to projects, 3 hours to unassisted interviews, and 2–3 hours to reading,
evaluation review and communication. Skip remedial reading when the diagnostic supports it.

| Phase | Weeks | Dependencies | Primary output |
| --- | --- | --- | --- |
| 0. Baseline | 1 | None | Skill gaps, prior-project evidence and acceptance criteria |
| 1. Production Python | 2–4 | 0 | Typed, tested async service and client |
| 2. Evaluation engineering | 5–6 | 1 | Versioned harness and baseline dataset |
| 3. Agents and safe execution | 7–9 | 1, 2 | DeepSWE bounded agent and isolated tools |
| 4. Reliability and observability | 10–12 | 3 | DeepSWE release evidence and incident drill |
| 5. Retrieval evaluation | 13–14 | 2, 4 | Measured enterprise retrieval baseline |
| 6. Enterprise architecture/security | 15–17 | 4, 5 | Support-agent design, integrations and permissions |
| 7. Enterprise delivery/outcomes | 18–21 | 6 | Support-agent pilot, rollout and outcome report |
| 8. Interview and portfolio defense | 22–24 | Both project gates | Fresh mocks and reviewed portfolio |

Interview practice and communication start in week 1. Threat modeling precedes executable tools;
Phase 6 extends it to enterprise identity and governance. Evals precede optimization. Project 2
starts after the DeepSWE gate, reusing engineering patterns rather than its application logic.

Required ML/LLM fundamentals: approximately four hours within Phases 0–2 on tokens, context limits,
probabilistic output, embeddings, model limitations, structured-output failures, sampling variability
and measured model selection. Fine-tuning is a conceptual alternative after prompt/retrieval/workflow
baselines fail, not a required build. No required foundation-model training, advanced deep learning,
CUDA/kernel programming, distributed training, RLHF, pretraining, advanced fine-tuning research or
heavy mathematical derivations. Existing `post-training` and `research-engineering` tracks receive
**zero required hours**; reuse evaluation discipline without taking an ML career detour.

## Phase 0 — Baseline and calibration

**Objectives:** distinguish Python gaps from established engineering judgment; turn past delivery
into verifiable evidence; establish what each project must prove.

**Exercises:** without AI, build a small API-response aggregator with errors and tests in 60 minutes.
In 45 minutes, design a queued AI request service and explain duplicate delivery, capacity and
authorization. Review one shipped AI product using the existing evidence-card format: ownership,
decision, alternative, actual outcome and limitation. Exclude confidential data.

**Deliverables/gate:** skills matrix with evidence/gaps, two project charters with users/scope and
initial quality/cost/latency targets, and a baseline coding attempt. Use Python basics/collections/
functions and design-basics only for gaps exposed by this diagnostic.

**Interview exercise:** explain your direction in two minutes as a software engineer extending
production expertise into AI. **Demonstrates:** senior-level calibration and honest ownership.

## Phase 1 — Production Python

**Objectives:** typing (`Protocol`, generics, unions), dataclasses for internal state, Pydantic for
boundary validation, package architecture and exception design. Master async/await, asyncio,
bounded concurrency, cancellation, deadlines, backpressure and cleanup. Explain async I/O versus
threads for blocking I/O and processes for CPU work; recognize event-loop blocking.

**Exercises:** build a typed model/API client with a fake transport, then a job API and worker.
Separate domain, adapters, persistence and interfaces. Add queue contracts, structured logging,
correlation IDs and typed retryable/permanent errors. Use pytest fixtures, parametrization, mocking
at external boundaries, async tests and fake clocks. Test cancellation and leaked resources; run
a type checker and lint checks. Reuse the existing functions/errors and reliability guides.

**Deliverables/gate:** installable package, API/error contract, executed test report and load fixture.
Demonstrate 429s, timeouts, malformed responses, partial failure and cancellation without unlimited
tasks or leaked clients. Reimplement one client operation and explain its tests without AI.

**Project milestone:** DeepSWE M1 service skeleton. **Interview exercise:** implement a bounded
concurrent mapper in 45 minutes; discuss ordering, exceptions and cancellation.
**Demonstrates:** production-quality Python, debugging and independent fluency.

## Phase 2 — Evaluation engineering

**Objectives:** representative datasets, deterministic graders, calibrated LLM-as-a-judge rubrics,
human evaluation, production signals and regression decisions. Separate component quality,
end-to-end task success, security violations, latency, tokens and cost. Judge preference alone does
not establish correctness.

**Exercises:** implement the shared evaluation contract below before optimizing either project.
Use the existing AI-systems grounding example briefly and the research guide's controlled cache
comparison as an experiment template. Label failures before fixes. Ask a human to review a
stratified sample; compare judge disagreements and refine ambiguous rubrics. Inject a plausible
wrong answer and instructions in judge input to test grader robustness.

**Deliverables/gate:** dataset schema/splits, tested graders, baseline report, failure taxonomy and
CI command. A deliberately broken tool selector or answer must fail its grader. Report denominators,
uncertainty and slice regressions rather than only an aggregate score.

**Project milestone:** DeepSWE M2 scripted baseline/harness. **Interview exercise:** assess a
four-point success-rate gain with doubled cost, including sample size, repeated runs and safety.
**Demonstrates:** evaluation judgment, experiment discipline and release criteria.

### Shared eval contract

Each case records ID, source/consent or synthetic provenance, version, scenario/difficulty,
tenant/role when relevant, input, allowed evidence/tools, expected outcome, prohibited actions,
grader/rubric versions and slice labels. Store only permitted data. Split by repository/task family
for DeepSWE and customer/intent/document family for support to reduce near-duplicate leakage.
Separate development from a frozen held-out set and record its use. Retire repeatedly tuned-on
holdouts into development data and collect fresh final evaluation cases.

| Signal | Measurement and interpretation |
| --- | --- |
| Task success rate | Successful completed tasks / all attempted eligible tasks; crashes/timeouts count as failures. Publish raw counts, exclusions and slices. |
| Tool-call accuracy | Correct tool selection, schema-valid arguments and authorized action semantics; score separately and include cases where no call is correct. |
| Correctness/groundedness | Deterministic tests/business checks first; human-labeled claim support and calibrated judges for open-ended text. A citation may not support the claim. |
| Human evaluation | Blind baseline/candidate identity, fixed rubric and adjudication; report sampling, judge-human agreement and unresolved ambiguity. |
| Failure taxonomy | Planning, retrieval, evidence use, tool selection/arguments, authorization, sandbox, state/recovery, provider, grading, timeout, budget. Record primary and contributing causes. |
| Efficiency | p50/p95 end-to-end and queue/model/tool latency; input/output tokens; per-attempt cost and total cost per successful task including failed attempts/retries. |
| Production signals | Escalations, corrections, reopened cases, feedback, incidents and adoption; inspect selection bias before adding them to offline evals. |

Run deterministic tests and a fixed mocked regression suite on every change. Run a small live suite
before release within an explicit budget; larger benchmark runs are deliberate project work, not
uncontrolled CI spend. Redact PII/secrets from reports. Record code revision, model identifier,
prompts, dataset, tool/sandbox image and configuration versions.

Repeat stochastic runs with matched workload and budgets. Report pass@1, raw counts and a binomial
or bootstrap interval with assumptions; do not compare best-of-many with a single attempt.
Predeclare the improvement hypothesis and acceptable quality/safety/cost/latency changes. Promote
only with held-out evidence and satisfied guardrails; report inconclusive differences honestly.
Recalibrate changed graders/models rather than silently comparing incompatible scores.

## Phase 3 — Agent architecture and sandboxed tools

**Objectives:** explicit loop: observe -> plan -> choose tool -> validate -> authorize -> execute
-> persist -> check stop conditions. Cover structured outputs, bounded replanning, state machines,
context selection and retries. Decide between a deterministic workflow, a single model call, a
single agent and subagents based on the need for dynamic decisions.

**Exercises:** implement DeepSWE read/search/edit/test tools with schemas and server-side policy.
Track task/step/attempt IDs, deadlines, permissions and cumulative budgets. Manage context with
selected files, bounded tool output and summaries linked to source evidence; compare truncation
and summary strategies on identical tasks. Summaries can omit facts and remain untrusted.
Try one reviewer subagent with bounded scope and independent permissions; retain it only if measured
benefit justifies coordination failure, latency and cost. Define state ownership and handoff contracts.

**Execution lab:** run shell/code only in an isolated disposable environment, never directly on the
host. Use a dedicated unprivileged identity, scoped workspace mounts, no host secrets or container
engine socket, a read-only base where practical, restricted network egress, CPU/memory/process/disk/
time/output limits and process-tree cleanup. Validate canonical paths, traversal and symlinks.
A shell allowlist alone is not a sandbox. Document chosen isolation, residual shared-kernel risk
and what a stronger VM boundary changes.

Test attempted host-file reads, symlink escape, network exfiltration, secret access, process
exhaustion, endless output and timeout cleanup with harmless fixtures. Treat repository text,
comments and tool output as indirect prompt-injection sources. Audit attempted and denied actions
without secrets. The model cannot grant itself permissions.

**Deliverables/gate:** architecture, tool schemas, permission matrix, threat model, isolation test
report and bounded agent that safely stops. Executable tools cannot pass without boundary tests.
**Project milestone:** DeepSWE M3–M4. **Interview exercise:** explain why fixed lint/test automation
needs no agent, then design unfamiliar bug repair. **Demonstrates:** agent judgment and execution safety.

## Phase 4 — Production reliability and observability

**Objectives:** long-running agents with durable checkpoints, leases, restart recovery, idempotency,
queues, async processing, rate limits, backoff/jitter, circuit breakers, fallbacks and graceful
degradation. Reuse queue/outbox and capacity material rather than reteaching databases.

**Exercises:** kill a worker after a tool effect but before acknowledgment. Recover using downstream
idempotency or reconciliation for uncertain effects; do not promise exactly-once behavior from a
queue. Test expired leases, stale results, cancellation races, retry exhaustion and dead-letter replay.
Enforce job/tenant/provider budgets, concurrency caps and admission control. Compare caching,
smaller context and model fallback with quality/security evals. Permission-aware cache keys and
expiry must prevent data leakage and stale policy. Reauthorize before resumed side effects.

Instrument request -> queue -> agent step -> model/tool call traces with consistent IDs and redacted
structured logs. Track queue age, success, timeouts, failures, denied actions, tokens, estimated versus
reconciled cost and latency distributions. Define actionable alerts, owners, runbook and rollback/
kill switch. Record trace sampling limitations and retain failed-call accounting where available.

**Deliverables/gate:** load/fault report, incident review, dashboard or saved metric views, runbook
and baseline comparison. Show restart, provider outage and exhausted budget ending in known states.
**Project milestone:** DeepSWE M5–M6/release. **Interview exercise:** diagnose rising p95 with stable
average model latency, calculate queue growth and propose discriminating measurements.
**Demonstrates:** distributed systems and AI operations.

## Project 1 — DeepSWE-style autonomous coding agent

Prove: **“I can engineer reliable AI agents and evaluate them rigorously.”**
This is application engineering, not a model-training research reproduction. Use disposable copies
of permitted small repositories and repair tasks. Output reviewable patches, test results and traces;
do not auto-merge/publish or provide production credentials.

| Milestone | Deliverable | Acceptance evidence |
| --- | --- | --- |
| M1. Service skeleton | Submit/status/cancel, persistent state, typed model adapter and fake tools | Duplicate submission, restart and cancellation tests |
| M2. Benchmark first | At least 40 tasks: 25 development / 15 frozen held-out; bugs, edits, multi-file changes, impossible tasks and adversarial content | Versioned fixtures, independent protected tests, scripted baseline and explicit abstention/unsafe-task grading |
| M3. Agent loop | Planning, tool use, inspection, revision, context management and stopping | Bounded repairs, no-progress termination and contextual evidence |
| M4. Enforced tools | Sandboxed read/search/edit/test tools and policy | Forbidden path/network, escape, resource and secret tests with audit trail |
| M5. Operations | Queue, checkpoints, recovery, retries, budgets and tracing | Worker/provider faults, controlled load and explainable terminal states |
| M6. Release evidence | Benchmark comparison, failure analysis, regressions and demo | Task success, latency/cost by slice, repeated runs, limitations and one rejected optimization |

Forty cases is a portfolio starting set, not a statistically powerful industry benchmark. Keep
evaluator-owned tests outside agent-writeable paths; run them from a trusted copy after patch
application inside isolation. Detect disabled tests, edited assertions and output-marker gaming.
Distinguish test/compilation failures, incorrect behavior and security violations. Name dataset
version/subset, harness, environment and budget in benchmark comparisons; do not claim public
leaderboard equivalence from custom subsets or unverified contamination assumptions.

**Release gate:** a reviewer can reproduce the run, inspect success/failure traces and verify held-out
success/cost and security tests. Publish predeclared targets and whether they were met. No critical
permission test may fail. Analyze weak success rates instead of hiding them behind a polished demo.

## Phase 5 — RAG and retrieval evaluation

**Objectives:** retrieval quality beyond basic RAG: chunk boundaries/overlap, metadata, embeddings,
lexical/dense hybrid retrieval, fusion, reranking, query rewriting and context selection. Handle
stale, conflicting, missing and access-restricted evidence; reduce unsupported answers.

**Exercises:** label at least 50 queries with relevance and answer evidence; use 30 development /
20 held-out grouped by intent/document family. Include synonyms, exact identifiers, multiple relevant
passages, no-answer queries and malicious content. Compare dense baseline, hybrid retrieval,
reranking and one chunking/query-rewrite change separately. Hold model/data/token budgets constant
where possible and disclose changes that cannot be isolated.

| Metric | Definition | Diagnostic use |
| --- | --- | --- |
| Recall@K | Relevant retrieved items / all labeled relevant items | Missing evidence; incomplete judgments limit interpretation |
| Precision@K | Relevant items in top K / K | Context noise; predefine behavior when fewer than K results exist |
| MRR | Mean reciprocal rank of first relevant item; zero if absent | How early useful evidence appears |
| NDCG@K | Discounted graded relevance / ideal ranking gain; declare gain/discount convention | Ranking quality with relevance degrees |

Define relevance unit (chunk/document) and duplicate policy before comparing chunk sizes.
Macro-average by query; report slices and separately score no-relevant-answer cases where recall/
normalized gain is undefined. Evaluate answer correctness, groundedness and abstention separately:
better retrieval does not guarantee better generation.

**Deliverables/gate:** relevance dataset, calculations checked on a hand-worked ranking, ablations,
latency/cost report and ten diagnosed failures. Trace errors to indexing, authorization filtering,
retrieval, ranking, context truncation or generation. **Project milestone:** Support S1.
**Interview exercise:** explain high Recall@10 but poor answers and design the next experiment.
**Demonstrates:** retrieval engineering and failure diagnosis.

## Phase 6 — Enterprise architecture and security

**Objectives:** turn “we want AI in customer support” into problem definition, business metrics,
AI-versus-deterministic decisions, architecture, RAG/agent/tool design, integrations, eval strategy,
security, rollout and monitoring. Distinguish authentication, OAuth delegation/scopes and application
authorization. Enforce tenant isolation and RBAC in the server, not in model instructions.

**Discovery exercise:** interview a stakeholder role-player about ticket types, handling time,
error/reopen rate, volume/peaks, systems of record, policies, data owners, allowable actions,
latency, failure cost, adoption constraints and outcome ownership. Record unknowns/assumptions.
Start with rules-based lookup/routing; justify where language understanding or dynamic tools help.

**Build exercise:** typed CRM ticket/history, billing/account lookup and knowledge adapters using
synthetic records. Derive tenant/user from authenticated server context, never model arguments.
Apply access filters before retrieval; authorize each tool/action and returned object. Partition
caches, queues, storage and traces. Test cross-tenant identifiers, role changes and revoked access.
Treat CRM notes, documents and retrieved snippets as untrusted.

Separate read-only tools from mutations. Begin with drafts/recommendations; require approval for
refunds, account changes and outbound communication. Bind approval to exact action/arguments,
actor/tenant and expiry; invalidate changed arguments. Reauthorize at execution; record decision and
downstream idempotency key. A model assertion that approval exists is not evidence.

**Security/governance exercise:** threat-model direct/indirect prompt injection, tool abuse,
exfiltration and confused-deputy behavior. Test malicious documents requesting cross-account reads
or uploads. Minimize PII, redact/tokenize where feasible, keep secrets at adapter boundaries, and
define retention/deletion, audit access, provenance and provider data-flow review. Identify governance
owners and unresolved risks; do not invent compliance claims. Prompt wording cannot enforce controls.

**Deliverables/gate:** discovery brief, architecture/data-flow diagram, decision record, permission
matrix, threat model, attack suite, integration contracts and implementation plan.
**Project milestone:** Support S2–S3. **Interview exercise:** defend the design to engineering,
product and security reviewers with conflicting goals. **Demonstrates:** enterprise architecture,
identity, privacy, governance and requirements discovery.

## Phase 7 — Enterprise delivery and business outcomes

**Objectives:** integrate retrieval, tools, human escalation, approvals and recovery in a deployed
workflow. Reuse DeepSWE's eval/trace/budget patterns while keeping datasets and permissions separate.

**Exercises:** run multi-step troubleshooting, CRM/billing questions, missing evidence, outages,
expired approvals and human handoff. Persist escalation reason and redacted context. Test duplicate
callbacks, partial writes and human takeover so automation stops when ownership changes.

Deploy with synthetic data to a controlled environment first. Plan shadow mode, staff-assist,
limited pilot and expansion with gates, owners, rollback and kill switch. Use an authorized CRM
sandbox for at least one integration when available; otherwise provide a contract-tested adapter
and label external integration unverified. A mock is not evidence of live enterprise integration.

Compare manual/rules baseline with assisted workflow on matched ticket categories. Measure resolution
quality, handling time, reopen rate, escalation quality, adoption and total cost per resolved ticket
including human review. State observation windows/confounders. Faster closure without correct
resolution is not value. Estimate ROI transparently; synthetic results are not customer savings.
Actual business-impact claims require observed usage and authorized data.

**Deliverables/gate:** Support S4–S6, operations runbook, rollout decision, outcome report and reusable
customer implementation playbook. **Interview exercise:** five-minute executive launch recommendation
with business result, risk, evidence and next decision. **Demonstrates:** end-to-end delivery and
communication tied to customer outcomes.

## Project 2 — Enterprise AI Support Agent

Prove: **“I can design and deploy a secure enterprise AI system tied to a real business workflow.”**
A synthetic pilot shows engineering readiness; label it honestly and use existing shipped experience
when discussing actual business impact.

| Milestone | Deliverable | Acceptance evidence |
| --- | --- | --- |
| S1. Retrieval | Versioned corpus, citations, access metadata and retrieval evals | Ranking, groundedness, abstention and retrieval failure report |
| S2. Architecture | Discovery brief, deterministic baseline, success criteria and design | Explain AI/agent choice and alternatives |
| S3. Integrations/security | CRM, billing/account tools, RBAC, tenant isolation, PII policy and audit logs | Cross-tenant, role, injection, exfiltration and secrets tests |
| S4. Human controls | Escalation, approval-bound actions, resume/revoke behavior | Takeover, changed arguments, expired approval and duplicate effects |
| S5. Evals/operations | At least 60 end-to-end cases: 40 development / 20 held-out, plus traces/cost/latency views | Task success, tool accuracy, grounding, security, escalation and outage slices; CI regressions |
| S6. Deployment/value | Controlled deployment, rollback drill, pilot report and implementation playbook | Reproducible demo, measured workflow outcomes, synthetic/real evidence distinction |

**Release gate:** all critical tenant/permission/approval tests pass. Quality and p95/cost meet
predeclared workload-specific targets. Graceful degradation and human handoff work during outages.
A reviewer can trace identity -> evidence -> tools -> approval -> effect -> audit without seeing PII.
Publish observed outcomes separately from projections and disclose remaining delivery gaps.

## Applied AI system-design case rotation

Complete one 45–60 minute case weekly from Phase 3, then repeat under changed constraints. Submit a
one-page brief, diagram, failure table and five eval examples. In **every** case answer: Why AI?
Why an agent? Why not deterministic? Which tools? Which approvals? How evaluate? What failure modes?
How protect PII? How handle prompt injection? How measure business value?

| Scenario | Additional challenge | Outcome |
| --- | --- | --- |
| Customer support agent | Conflicting policies, billing outage, human takeover | Correct resolution, reopens, handling time |
| Internal knowledge assistant | Document permissions change after indexing | Supported answers and time to useful information |
| Sales agent | Malicious CRM notes; approval before customer contact | Qualified approved follow-ups and factual errors |
| Coding agent | Malicious repository and runaway execution | Valid repairs, review burden, cost per repair |
| Document processing agent | OCR ambiguity, schema drift, duplicate invoices | Field accuracy and rework |
| Financial operations agent | Reconciliation; approval before any transfer | Accuracy and duplicate/unauthorized actions |
| Enterprise search | Exact identifiers, freshness, access-sensitive ranking | Relevance and authorized successful searches |
| Multi-agent workflow | Conflicting plans, delegated rights and partial failures | Quality gain versus single-agent cost/latency |

For multi-agent cases specify state ownership, handoff contracts, permission inheritance, cancellation,
shared budgets and recovery. A single agent or deterministic workflow is a valid final choice when
delegation does not demonstrate a benefit.

## Customer-facing technical communication

| Audience | Exercise | Deliverable and criterion |
| --- | --- | --- |
| Discovery stakeholder | 20-minute ambiguous requirements interview | Workflow, quantified baseline, unknowns and next decision |
| Engineers | Walk API/tool contract and failure path | Implementable contract, sequence diagram and justified alternative |
| Product managers | Negotiate scope/rollout | Milestones tied to user outcomes |
| Security team | Defend identity, data flow and threat model | Controls, test evidence, residual risks and owners |
| CTO/executives | Five-minute recommendation and questions | Business case, options, investment, risks and decision request |

Run a cross-functional role-play for each project and obtain peer review. Explain the same architecture
in two minutes and fifteen minutes. Turn one incident into product feedback: reproducible symptom,
customer impact, evidence, mitigation and proposed change. Practice implementation-plan negotiation
and defending decisions with evidence rather than framework names.

## Interview Mode and Work Mode

These are learning disciplines. The app offers `practice`, `mock` and guided training; it does not
have an automated Work Mode. Keep assisted project evidence separate from fresh interview attempts.

**Interview Mode — no AI during the attempt:** two 45-minute coding sessions weekly plus a 90-minute
design/case/behavioral rotation. Disable AI autocomplete. Cover arrays/hash maps, two pointers/sliding
windows, stacks/queues, binary search, trees, heaps, graphs and basic dynamic programming. Explain
invariants, complexity, edge cases and executed tests. Rotate backend coding, distributed systems,
Applied AI cases, behavioral interviews and project defense. Preserve the original attempt before
AI review; test learning on a fresh problem without help.

**Work Mode — use AI actively:** architecture brainstorming, bounded code changes, test generation,
debugging, documentation, eval generation, threat modeling and design review. Inspect every diff,
run meaningful tests, verify generated labels with human/domain judgment and challenge suggested
security boundaries. Log accepted/rejected suggestions. Weekly, reimplement or debug a critical
component without AI and explain every line.

## Phase 8 — Interview and portfolio defense

**Objectives:** demonstrate independent competence, adapt to unfamiliar constraints and present
credible ownership. **Exercises:** two full six-track mocks on fresh questions over the final three
weeks, two Applied AI customer cases, one production incident, and a 30-minute defense of each
project. Prepare six truthful stories: ambiguity, disagreement, failure, security tradeoff, customer
delivery and cross-functional influence. Reuse existing project/behavioral evidence-card methods.

**Deliverables/gate:** reviewed original attempts, gap/remediation log, two portfolio case studies,
role-specific evidence matrix and human mock feedback. Repeat weak areas on fresh tasks; course
completion alone does not establish readiness. **Demonstrates:** independent coding, system design,
communication, technical depth and honest senior ownership.

## Use the existing trainer

```powershell
.\.venv\Scripts\grey.exe web
.\.venv\Scripts\grey.exe learn --list
.\.venv\Scripts\grey.exe learn --lesson design-reliability
.\.venv\Scripts\grey.exe learn --lesson ai-systems
.\.venv\Scripts\grey.exe run --tracks coding system-design ai-systems --turns 2
.\.venv\Scripts\grey.exe run --mode mock
```

Automatic `learn` now begins with `role-diagnostic` and follows the required applied-AI path. Reuse
`coding`, `system-design`, `ai-systems`, `project`, `debugging` and `behavioral` as the six practice
tracks. Use `learn --list` for the new module IDs, including `production-python`, `ai-evals`,
`deepswe`, `support-agent` and `dsa-sequences`. DSA runs alongside the project phases; its three
guides cover weeks 1–24 with easy-to-medium progression. Guides/checks work offline; feedback needs the
configured provider. The trainer reviews code but does not execute it; run project tests yourself.
Keep the existing 60–90 minute practice loop: attempt -> review -> repair -> fresh task -> decision log.

New installations use the target profile below by default; this workspace's active profile has
also been updated. For another existing installation, merge these fields into `.grey/config.json`.
Do not replace provider settings or the entire file. Existing sessions preserve profile snapshots.

```json
{
  "background": "Software engineer with around 8 years in backend/full-stack, cloud, APIs, databases and distributed systems; shipped LLM API, RAG, vector database and tool-calling products.",
  "target": "Backend SWE on AI teams, Generative AI SWE and Applied AI Engineer; primary reference: OpenAI Applied AI Engineer Singapore. Prioritize production Python, evals, agents, enterprise security and customer outcomes, not ML research."
}
```

Update `project_context` only with actual work/results. See README for provider setup, resume,
review and saved-answer recovery. Model scores guide practice; they are not hiring predictions.

## Portfolio and application readiness

Each project needs runnable source, setup instructions, architecture decisions, a short demo,
automated tests, versioned eval data/graders, baseline/candidate results, representative traces,
threat model, operations runbook and limitations. Include raw counts, workload, measurement date
and personal ownership. Remove abandoned experiments and unused code from edited files; retain
useful failed-approach evidence in decision logs rather than dead code.

| Target role | Strongest portfolio evidence | Remaining interview bar |
| --- | --- | --- |
| Backend SWE on an AI team | Typed services, queues, consistency, recovery, performance and operations | Independent coding, distributed systems and senior scope |
| Generative AI SWE | Agents/tools, retrieval diagnosis, evals and measured optimization | Model-behavior judgment, integration/debugging depth and AI design |
| Applied AI Engineer | Enterprise deployment, discovery, security, rollout, outcomes and stakeholder defense | Customer leadership under ambiguity and actual enterprise impact |

**Would this credibly support applications? Yes, if you meet the evidence gates and can defend and
modify the work independently.** Combined with prior production experience, this portfolio supports
applications to relevant software/applied-AI teams at OpenAI, Anthropic, Spotify, Amazon, Google,
Salesforce, NVIDIA and similar companies. It does not imply identical hiring bars, role availability,
seniority or interview formats. It does not prepare you for research, training-infrastructure or
CUDA roles merely because they share an AI title.

Before applying, map a current posting to evidence, identify remaining gaps and tailor the narrative.
Obtain external code/design review and a human mock. If Support uses synthetic users, call it a
controlled pilot and use prior shipped work for real adoption/business-impact claims. Model scores
and course completion cannot replace independent ability or customer delivery.
