import hashlib
import json
import uuid
from datetime import datetime, timezone

from .curriculum import curriculum_progress, load_lesson
from .models import COMPETENCIES, CORE, OPTIONAL, Coaching, Config, Evaluation, Question, score


def now():
    return datetime.now(timezone.utc).isoformat()


def adjust(level, evaluation, assisted=False):
    if assisted or evaluation["confidence"] == "low":
        return level
    value = score(evaluation)
    return min(5, level + 1) if value >= 80 else max(1, level - 1) if value < 50 else level


def first_scores(sessions, track):
    return [
        q["attempts"][0]["evaluation"]
        for s in sessions
        if s["mode"] != "training"
        for q in s["questions"]
        if q["track"] == track
        and q["attempts"]
        and q["attempts"][0].get("evaluation")
        and not q["attempts"][0]["assisted"]
    ]


class Trainer:
    def __init__(self, store, config, provider_factory):
        self.store, self.config, self.provider_factory = store, config, provider_factory

    def start(self, mode="practice", tracks=None, turns=None, lesson_id=None):
        lesson = None
        if mode == "training":
            lesson = load_lesson(lesson_id)
            tracks, turns = [lesson["track"]], len(lesson["exercises"])
        elif lesson_id is not None:
            raise ValueError("Lessons are available in training mode only.")
        tracks = CORE if tracks is None else tracks
        if (
            mode not in ("practice", "mock", "training")
            or not tracks
            or any(t not in CORE + OPTIONAL for t in tracks)
            or len(set(tracks)) != len(tracks)
        ):
            raise ValueError("Choose practice/mock and unique valid tracks.")
        turns = self.config.turns_per_round if turns is None else turns
        if not 1 <= turns <= 4:
            raise ValueError("Turns per round must be 1-4.")
        previous = self.store.all()
        levels = {}
        for track in tracks:
            results = first_scores(previous, track)
            levels[track] = 1 if lesson else self.config.initial_difficulty
            for result in [] if lesson else results[-3:]:
                levels[track] = adjust(levels[track], result)
        state = {
            "schema_version": 1,
            "id": uuid.uuid4().hex[:12],
            "created_at": now(),
            "mode": mode,
            "config": self.config.model_dump(),
            "tracks": tracks,
            "turns_per_round": turns,
            "levels": levels,
            "questions": [],
            "completed_at": None,
            "calls": [],
        }
        if lesson:
            state["lesson"] = lesson
        self.store.create(state)
        return state

    def call(self, state, task, schema, payload):
        provider = self.provider_factory(Config.model_validate(state["config"]))
        result, metadata = provider.request(task, schema, payload)
        state["calls"].append({"task": task, "at": now(), **metadata})
        return result

    def next(self, sid, remediate=False):
        state, revision = self.store.load(sid)
        if state["completed_at"]:
            raise ValueError("Session complete. Start a new session for more practice.")
        if state["questions"] and not state["questions"][-1]["attempts"]:
            return state, state["questions"][-1]
        if state["questions"] and not state["questions"][-1]["attempts"][-1].get("evaluation"):
            raise ValueError("Answer saved but not graded. Run 'grey grade SESSION'.")
        index = len(state["questions"])
        if index >= len(state["tracks"]) * state["turns_per_round"]:
            raise ValueError("All turns answered. Run 'grey finish SESSION' for the report.")
        track = state["tracks"][index // state["turns_per_round"]]
        if remediate and state["mode"] != "practice":
            raise ValueError("Remediation is available in practice mode.")
        previous = [q for q in state["questions"] if q["track"] == track]
        recent = [s for s in self.store.all() if s["mode"] != "training"][-20:]
        history = [
            {"question": q["question"]["prompt"], "attempt": q["attempts"][-1]}
            for q in previous
            if q["attempts"]
        ]
        past_gaps = [e["gaps"] for e in first_scores(recent, track)[-5:]]
        payload = {
            "profile": state["config"],
            "track": track,
            "competency": COMPETENCIES[track],
            "difficulty": state["levels"][track],
            "turn": len(previous) + 1,
            "previous_round_answers": history,
            "recent_gaps": past_gaps,
            "remediation": remediate,
            "avoid_titles": [q["question"]["title"] for s in recent for q in s["questions"]][-100:],
            "variation_seed": uuid.uuid4().hex,
        }
        question = (
            state["lesson"]["exercises"][index]
            if state["mode"] == "training"
            else self.call(state, "question", Question, payload)
        )
        normalized = " ".join(question["prompt"].lower().split())
        fingerprint = hashlib.sha256(normalized.encode()).hexdigest()
        if state["mode"] != "training" and any(
            q["fingerprint"] == fingerprint
            for s in self.store.all()
            if s["mode"] != "training"
            for q in s["questions"]
        ):
            raise ValueError("Generator repeated a question. Retry 'next' for a fresh task.")
        entry = {
            "track": track,
            "difficulty": state["levels"][track],
            "question": question,
            "fingerprint": fingerprint,
            "opened_at": now(),
            "attempts": [],
            "coaching": [],
        }
        state["questions"].append(entry)
        self.store.save(state, revision)
        return state, entry

    def submit(self, sid, answer, revise=False):
        if not answer.strip() or len(answer) > 60000:
            raise ValueError("Answer must contain 1-60,000 characters.")
        state, revision = self.store.load(sid)
        if state["completed_at"] or not state["questions"]:
            raise ValueError("Start an active question with 'next' first.")
        q = state["questions"][-1]
        if q["attempts"]:
            if not q["attempts"][-1].get("evaluation"):
                raise ValueError("A saved answer awaits grading. Use 'grade' to retry.")
            if not revise or state["mode"] == "mock":
                raise ValueError("Already answered. Use 'next', or --revise in practice/training.")
        elif revise:
            raise ValueError("No previous answer to revise.")
        q["attempts"].append(
            {
                "answer": answer,
                "submitted_at": now(),
                "evaluation": None,
                "assisted": bool(
                    state["mode"] == "training"
                    or q["attempts"]
                    or any(c["kind"] == "hint" for c in q["coaching"])
                ),
                "elapsed_seconds": max(
                    0,
                    int(
                        (
                            datetime.now(timezone.utc) - datetime.fromisoformat(q["opened_at"])
                        ).total_seconds()
                    ),
                ),
            }
        )
        self.store.save(state, revision)  # Commit the user's work before the network call.
        return self.grade(sid)

    def grade(self, sid):
        state, revision = self.store.load(sid)
        if not state["questions"] or not state["questions"][-1]["attempts"]:
            raise ValueError("No submitted answer to grade.")
        q = state["questions"][-1]
        attempt = q["attempts"][-1]
        if attempt["evaluation"]:
            return state
        evaluation = self.call(
            state,
            "evaluate",
            Evaluation,
            {
                "track": q["track"],
                "competency": COMPETENCIES[q["track"]],
                "difficulty": q["difficulty"],
                "question": q["question"],
                "answer": attempt["answer"],
                "assisted": attempt["assisted"],
                "coaching": q["coaching"],
                "training": {
                    "title": state["lesson"]["title"],
                    "stage": state["lesson"]["stage"],
                    "objectives": state["lesson"]["objectives"],
                    "previous_exercises": [
                        {
                            "prompt": entry["question"]["prompt"],
                            "answer": entry["attempts"][-1]["answer"],
                        }
                        for entry in state["questions"][:-1]
                        if entry["attempts"]
                    ],
                }
                if state["mode"] == "training"
                else None,
            },
        )
        attempt["evaluation"] = evaluation
        if len(q["attempts"]) == 1:
            state["levels"][q["track"]] = adjust(q["difficulty"], evaluation, attempt["assisted"])
        self.store.save(state, revision)
        return state

    def coach(self, sid, kind, message):
        state, revision = self.store.load(sid)
        if not state["questions"] or state["completed_at"]:
            raise ValueError("No active question.")
        if kind not in ("hint", "clarify", "review", "explain") or not message.strip():
            raise ValueError("Supply a coaching request.")
        if kind == "explain" and state["mode"] != "training":
            raise ValueError("Tutor explanations are available in training mode only.")
        if state["mode"] == "mock" and kind != "clarify":
            raise ValueError("Mock mode allows requirement clarifications only.")
        q = state["questions"][-1]
        if kind == "review" and (not q["attempts"] or not q["attempts"][-1]["evaluation"]):
            raise ValueError("Submit and grade an answer before discussing feedback.")
        public = {k: v for k, v in q["question"].items() if k != "interviewer_notes"}
        reply = self.call(
            state,
            "coach",
            Coaching,
            {
                "kind": kind,
                "message": message,
                "question": public,
                "coaching": q["coaching"],
                "attempts": q["attempts"] if kind == "review" else [],
                "lesson": {
                    "title": state["lesson"]["title"],
                    "objectives": state["lesson"]["objectives"],
                    "guide": state["lesson"]["guide"],
                }
                if state["mode"] == "training"
                else None,
            },
        )
        q["coaching"].append(
            {"kind": kind, "message": message, "reply": reply["reply"], "at": now()}
        )
        self.store.save(state, revision)
        return reply["reply"]

    def finish(self, sid):
        state, revision = self.store.load(sid)
        if len(state["questions"]) != len(state["tracks"]) * state["turns_per_round"] or any(
            not q["attempts"] or not q["attempts"][-1]["evaluation"] for q in state["questions"]
        ):
            raise ValueError("Complete all scheduled turns before finishing.")
        if not state["completed_at"]:
            state["completed_at"] = now()
            self.store.save(state, revision)
        return state


def report(state):
    graded = sum(
        bool(q["attempts"] and q["attempts"][-1]["evaluation"]) for q in state["questions"]
    )
    lines = [
        f"Grey Interview | {state['id']} | {state['mode']}",
        (f"Progress: {graded}/{len(state['tracks']) * state['turns_per_round']} turns graded"),
    ]
    if state["mode"] == "training":
        lines.append(
            f"Tutorial: {state['lesson']['title']} | guided scores are not interview readiness"
        )
    if state["mode"] == "mock" and not state["completed_at"]:
        return "\n".join(lines + ["Feedback unlocks after all rounds. Continue with next/answer."])
    for i, q in enumerate(state["questions"], 1):
        lines.append(
            f"\n{i}. {q['track']} | difficulty {q['difficulty']}/5 | {q['question']['title']}"
        )
        for n, a in enumerate(q["attempts"], 1):
            e = a["evaluation"]
            if e is None:
                lines.append("Answer saved; grading pending.")
                continue
            label = "assisted/revision" if a["assisted"] else "unassisted"
            lines.append(f"Attempt {n}: {score(e)}/100 ({label}); confidence {e['confidence']}")
            for d in e["dimensions"]:
                lines.append(
                    f"  {d['name']}: {d['score']}/4 - {d['evidence']} Next: {d['improvement']}"
                )
            lines.extend(
                [
                    "Strengths: " + "; ".join(e["strengths"]),
                    "Gaps: " + "; ".join(e["gaps"]),
                    "Learn: " + e["lesson"],
                    "Build next: " + e["exercise"],
                ]
            )
    lines.append("\nPractice estimates, not hiring predictions. Code was reviewed, not executed.")
    return "\n".join(lines)


def progress(store):
    # Active mocks cannot reveal indirect grades through aggregate statistics.
    sessions = [s for s in store.all() if s["mode"] != "mock" or s["completed_at"]]
    lines = ["Progress | unassisted first attempts only"]
    priorities = []
    for track in CORE + OPTIONAL:
        evaluations = first_scores(sessions, track)
        if not evaluations:
            lines.append(f"{track}: not assessed")
            priorities.append((0, track))
            continue
        values = [score(e) for e in evaluations[-5:]]
        average = round(sum(values) / len(values))
        lines.append(
            f"{track}: recent average {average}/100 | {len(evaluations)} attempts | {values}"
        )
        priorities.append((average, track))
    lines.append(
        "Suggested core practice: "
        + ", ".join(t for _, t in sorted(p for p in priorities if p[1] in CORE)[:2])
    )
    tokens = sum(c.get("usage", {}).get("total_tokens", 0) for s in store.all() for c in s["calls"])
    lines.append(
        f"Recorded successful model calls: {sum(len(s['calls']) for s in store.all())}; tokens: {tokens}"
    )
    lines.extend(["", curriculum_progress(store.all())])
    return "\n".join(lines)


def export_state(state):
    if state["mode"] == "mock" and not state["completed_at"]:
        raise ValueError("Finish the mock before exporting its transcript.")
    return json.dumps(state, indent=2, ensure_ascii=False)
