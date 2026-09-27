"""Bundled lessons and the applied-AI learning path; readable without model calls."""

import hashlib
import json
from importlib.resources import files

from pydantic import Field

from .models import CORE, OPTIONAL, Question, StrictModel

FOUNDATIONS = [
    "python-basics",
    "python-collections",
    "python-functions",
    "design-basics",
    "design-reliability",
]
APPLIED = [
    "role-diagnostic", "production-python", "python-async", "ai-evals",
    "agent-architecture", "tool-sandboxing", "ai-reliability", "ai-observability",
    "deepswe", "retrieval-evaluation", "enterprise-security", "enterprise-architecture",
    "support-agent", "applied-ai-cases", "customer-communication", "work-mode",
    "dsa-sequences", "dsa-trees-graphs", "dsa-dynamic-programming",
]
REQUIRED = APPLIED + CORE
LESSON_IDS = REQUIRED + FOUNDATIONS + OPTIONAL


class KnowledgeCheck(StrictModel):
    question: str
    options: list[str] = Field(min_length=4, max_length=4)
    answer: int = Field(ge=0, le=3)
    explanation: str


class Lesson(StrictModel):
    id: str
    track: str
    title: str
    stage: str
    minutes: int = Field(ge=5, le=90)
    objectives: list[str] = Field(min_length=1)
    exercises: list[Question] = Field(min_length=2, max_length=4)
    checks: list[KnowledgeCheck] = Field(min_length=3)
    prerequisites: list[str] = Field(default_factory=list)
    required: bool = True


def lessons():
    items = []
    for name in ("applied.json", "lessons.json"):
        content = files("grey_interview").joinpath(f"curriculum/{name}").read_text(encoding="utf-8")
        items.extend(json.loads(content))
    result = [Lesson.model_validate(item) for item in items]
    result.sort(key=lambda lesson: LESSON_IDS.index(lesson.id) if lesson.id in LESSON_IDS else -1)
    if [lesson.id for lesson in result] != LESSON_IDS or any(
        lesson.track not in CORE + OPTIONAL for lesson in result
    ):
        raise ValueError("Curriculum has invalid lesson IDs or tracks.")
    seen = set()
    for lesson in result:
        if (
            not set(lesson.prerequisites) <= seen
            or len(lesson.prerequisites) != len(set(lesson.prerequisites))
            or lesson.required != (lesson.id in REQUIRED)
        ):
            raise ValueError("Curriculum has invalid prerequisites or required lessons.")
        seen.add(lesson.id)
    return result


def load_lesson(lesson_id):
    lesson = next((item for item in lessons() if item.id == lesson_id), None)
    if lesson is None:
        raise ValueError("Unknown lesson. Use 'grey learn --list'.")
    return {**lesson.model_dump(), "guide": guide(lesson_id)}


def guide(lesson_id="welcome"):
    if lesson_id not in ["welcome", *LESSON_IDS]:
        raise ValueError("Unknown guide. Use 'grey learn --list'.")
    return (
        files("grey_interview").joinpath(f"curriculum/{lesson_id}.md").read_text(encoding="utf-8")
    )


def recommended_lesson(sessions):
    completed = {
        s["lesson"]["id"] for s in sessions if s["mode"] == "training" and s["completed_at"]
    }
    return next((lesson_id for lesson_id in REQUIRED if lesson_id not in completed), None)


def checkpoint_version(lesson):
    return hashlib.sha256(json.dumps(lesson["checks"], sort_keys=True).encode()).hexdigest()


def check_answers(lesson, answers):
    if len(answers) != len(lesson["checks"]) or any(
        type(a) is not int or not 0 <= a <= 3 for a in answers
    ):
        raise ValueError("Choose one answer for each knowledge check.")
    results = [
        {
            "correct": selected == check["answer"],
            "selected": selected,
            "answer": check["answer"],
            "explanation": check["explanation"],
        }
        for selected, check in zip(answers, lesson["checks"])
    ]
    percent = round(sum(item["correct"] for item in results) / len(results) * 100)
    return {
        "lesson_id": lesson["id"],
        "version": checkpoint_version(lesson),
        "score": percent,
        "passed": percent >= 80,
        "results": results,
    }


def curriculum_progress(sessions):
    lines = ["Tutorials | completion means exercises reviewed, not mastery"]
    for lesson in lessons():
        matching = [
            s for s in sessions if s["mode"] == "training" and s["lesson"]["id"] == lesson.id
        ]
        if any(s["completed_at"] for s in matching):
            status = "completed"
        elif matching:
            latest = matching[-1]
            graded = sum(
                bool(q["attempts"] and q["attempts"][-1]["evaluation"]) for q in latest["questions"]
            )
            status = f"{graded}/{len(latest['lesson']['exercises'])} reviewed | {latest['id']}"
        else:
            status = "not started"
        optional = "" if lesson.required else " (optional refresher/reference)"
        lines.append(f"{lesson.id}{optional}: {lesson.title} | {status}")
    next_id = recommended_lesson(sessions)
    lines.append(
        f"Next: grey learn --lesson {next_id}"
        if next_id
        else "Core tutorials complete. Try: grey run --tracks coding system-design --turns 2"
    )
    return "\n".join(lines)
