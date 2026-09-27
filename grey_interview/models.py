import os
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CORE = ["coding", "system-design", "ai-systems", "project", "debugging", "behavioral"]
OPTIONAL = ["post-training", "research-engineering"]
COMPETENCIES = {
    "coding": "Production Python, typing, asyncio, pytest, DSA, complexity and tested implementation",
    "system-design": "Enterprise discovery, integrations, distributed systems, reliability, RBAC and rollout",
    "ai-systems": "Agents, sandboxed tools, retrieval evaluation, graders, injection defenses, cost and tracing",
    "project": "Real ownership, architecture, measured outcomes, failed approaches and lessons",
    "debugging": "Reproduction, hypotheses, logs, root cause, minimal fixes and regression tests",
    "behavioral": "Customer discovery, stakeholder communication, ambiguity, honest ownership and tradeoffs",
    "post-training": "SFT, preference optimization, reward hacking, data quality and evaluation leakage",
    "research-engineering": "Experiment design, reproducibility, ablations, numerical issues and ML debugging",
}
DIMENSIONS = ["correctness", "reasoning", "verification", "communication"]
Effort = Literal["none", "minimal", "low", "medium", "high", "xhigh", "max", "ultra"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Config(StrictModel):
    name: str = "Grey"
    background: str = (
        "Software engineer with around 8 years in backend/full-stack, cloud, APIs, databases "
        "and distributed systems; shipped LLM API, RAG, vector database and tool-calling products."
    )
    target: str = (
        "Backend SWE on AI teams, Generative AI SWE and Applied AI Engineer; primary reference: "
        "OpenAI Applied AI Engineer Singapore. Production software engineering, not ML research."
    )
    language: str = "Python"
    project_context: str = (
        "No project supplied yet; ask for actual experience before assuming details."
    )
    provider: Literal["codex", "claude", "openai"] = "codex"
    model: str | None = Field(default=None, min_length=1)
    evaluator_model: str | None = Field(default=None, min_length=1)
    effort: Effort | None = None
    evaluator_effort: Effort | None = None
    tutor_model: str | None = Field(default=None, min_length=1)
    tutor_effort: Effort | None = None
    initial_difficulty: int = Field(default=2, ge=1, le=5)
    turns_per_round: int = Field(default=2, ge=1, le=4)
    max_output_tokens: int = Field(default=6000, ge=1000, le=20000)
    timeout_seconds: int = Field(default=90, ge=5, le=300)

    def with_environment(self):
        """Explicit environment overrides also apply when resuming saved sessions."""
        values = self.model_dump()
        provider = os.getenv("GREY_LLM_PROVIDER", "").strip().lower()
        if provider:
            if provider != self.provider:
                values.update(
                    model=None,
                    evaluator_model=None,
                    effort=None,
                    evaluator_effort=None,
                    tutor_model=None,
                    tutor_effort=None,
                )
            values["provider"] = provider
        model = os.getenv("GREY_LLM_MODEL", "").strip()
        if model:
            values.update(model=model, evaluator_model=None)
        evaluator = os.getenv("GREY_LLM_EVALUATOR_MODEL", "").strip()
        if evaluator:
            values["evaluator_model"] = evaluator
        effort = os.getenv("GREY_LLM_EFFORT", "").strip().lower()
        if effort:
            values.update(effort=effort, evaluator_effort=None)
        evaluator_effort = os.getenv("GREY_LLM_EVALUATOR_EFFORT", "").strip().lower()
        if evaluator_effort:
            values["evaluator_effort"] = evaluator_effort
        tutor_model = os.getenv("GREY_LLM_TUTOR_MODEL", "").strip()
        tutor_effort = os.getenv("GREY_LLM_TUTOR_EFFORT", "").strip().lower()
        if tutor_model:
            values["tutor_model"] = tutor_model
        if tutor_effort:
            values["tutor_effort"] = tutor_effort
        return Config.model_validate(values)

    def model_for(self, task):
        model = (
            self.evaluator_model
            if task == "evaluate"
            else self.tutor_model
            if task in ("tutor", "coach")
            else None
        )
        return model or self.model or ("gpt-6-astra" if self.provider == "openai" else None)

    def effort_for(self, task):
        effort = (
            self.evaluator_effort
            if task == "evaluate"
            else self.tutor_effort
            if task in ("tutor", "coach")
            else None
        )
        return effort or self.effort


class Question(StrictModel):
    title: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    constraints: list[str]
    starter_code: str
    acceptance_checks: list[str] = Field(min_length=1)
    minutes: int = Field(ge=5, le=60)
    interviewer_notes: str = Field(min_length=1)


class Dimension(StrictModel):
    name: Literal["correctness", "reasoning", "verification", "communication"]
    score: int = Field(ge=0, le=4)
    evidence: str = Field(min_length=1)
    improvement: str = Field(min_length=1)


class Evaluation(StrictModel):
    dimensions: list[Dimension] = Field(min_length=4, max_length=4)
    strengths: list[str]
    gaps: list[str]
    lesson: str = Field(min_length=1)
    exercise: str = Field(min_length=1)
    followup_focus: str = Field(min_length=1)
    confidence: Literal["low", "medium", "high"]


class Coaching(StrictModel):
    reply: str = Field(min_length=1)


def score(evaluation: dict) -> int:
    return round(sum(d["score"] for d in evaluation["dimensions"]) / 16 * 100)
