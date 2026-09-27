import json
from types import SimpleNamespace

import pytest
from test_trainer import FakeProvider

from grey_interview import cli
from grey_interview.curriculum import (
    APPLIED,
    LESSON_IDS,
    REQUIRED,
    curriculum_progress,
    guide,
    lessons,
    recommended_lesson,
)
from grey_interview.engine import Trainer, first_scores, progress, report
from grey_interview.models import Config
from grey_interview.provider import ProviderError
from grey_interview.store import Store


@pytest.fixture
def training(tmp_path):
    provider = FakeProvider()
    store = Store(tmp_path / "progress.sqlite3")
    trainer = Trainer(store, Config(), lambda _: provider)
    return SimpleNamespace(provider=provider, store=store, trainer=trainer)


@pytest.mark.parametrize("lesson_id", LESSON_IDS)
def test_tutorial_complete_and_repeat_without_generation(training, lesson_id):
    for _ in range(2):
        state = training.trainer.start(mode="training", lesson_id=lesson_id)
        track = state["lesson"]["track"]
        sid = state["id"]
        assert state["levels"][track] == 1
        assert len(state["lesson"]["exercises"]) == 2
        for i in range(2):
            _, q = training.trainer.next(sid)
            assert q["question"] == state["lesson"]["exercises"][i]
            calls = len(training.provider.calls)
            assert training.trainer.next(sid)[1] == q
            assert len(training.provider.calls) == calls
            graded = training.trainer.submit(sid, f"My answer {i}")
            assert graded["questions"][-1]["attempts"][-1]["assisted"]
            assert graded["levels"][track] == 1
        finished = training.trainer.finish(sid)
        assert finished["completed_at"]
        assert "guided scores" in report(finished)
        assert not first_scores(training.store.all(), track)
    assert all(task == "evaluate" for task, _ in training.provider.calls)
    assert f"{track}: not assessed" in progress(training.store)
    assert "completed" in curriculum_progress(training.store.all())
    assert training.trainer.start(tracks=[track])["levels"][track] == 2


def test_tutor_receives_public_lesson_and_review_context(training):
    sid = training.trainer.start(mode="training", lesson_id="system-design")["id"]
    _, first = training.trainer.next(sid)
    training.trainer.coach(sid, "explain", "How do I draw the queue?")
    _, payload = training.provider.calls[-1]
    assert "```mermaid" in payload["lesson"]["guide"]
    assert "interviewer_notes" not in json.dumps(payload)
    assert first["question"]["interviewer_notes"] not in json.dumps(payload)
    training.trainer.submit(sid, "My initial design")
    training.trainer.next(sid)
    training.trainer.submit(sid, "My overload extension")
    task, payload = training.provider.calls[-1]
    assert task == "evaluate"
    assert payload["training"]["objectives"]
    assert payload["training"]["previous_exercises"][0]["answer"] == "My initial design"


def test_training_review_failure_preserves_work_and_resume(training):
    sid = training.trainer.start(mode="training", lesson_id="coding")["id"]
    training.trainer.next(sid)
    training.provider.fail = "evaluate"
    with pytest.raises(ProviderError):
        training.trainer.submit(sid, "Unlost work")
    with pytest.raises(ValueError, match="not graded"):
        training.trainer.next(sid)
    saved, _ = training.store.load(sid)
    assert saved["questions"][0]["attempts"][0]["answer"] == "Unlost work"
    training.provider.fail = None
    resumed = Trainer(Store(training.store.path), Config(), lambda _: training.provider)
    resumed.grade(sid)
    calls = len(training.provider.calls)
    resumed.grade(sid)
    assert len(training.provider.calls) == calls
    resumed.submit(sid, "Revised work", revise=True)
    assert len(training.store.load(sid)[0]["questions"][0]["attempts"]) == 2


def test_saved_lesson_survives_curriculum_changes(training, monkeypatch):
    sid = training.trainer.start(mode="training", lesson_id="coding")["id"]
    from grey_interview import engine

    def unavailable(_):
        raise AssertionError("Existing sessions must use their snapshot")

    monkeypatch.setattr(engine, "load_lesson", unavailable)
    state, q = training.trainer.next(sid)
    assert q["question"] == state["lesson"]["exercises"][0]


def test_training_boundaries_and_interview_tutor_restriction(training):
    with pytest.raises(ValueError, match="Unknown lesson"):
        training.trainer.start(mode="training", lesson_id="missing")
    with pytest.raises(ValueError, match="training mode only"):
        training.trainer.start(lesson_id="coding")
    sid = training.trainer.start(mode="training", lesson_id="coding")["id"]
    with pytest.raises(ValueError, match="Complete all"):
        training.trainer.finish(sid)
    sid = training.trainer.start(mode="mock", tracks=["coding"])["id"]
    training.trainer.next(sid)
    with pytest.raises(ValueError, match="training mode only"):
        training.trainer.coach(sid, "explain", "Help")


def test_curriculum_recommendation_ignores_interviews(training):
    assert recommended_lesson([]) == "role-diagnostic"
    assert [lesson.id for lesson in lessons()] == LESSON_IDS
    sid = training.trainer.start(tracks=["coding"], turns=1)["id"]
    training.trainer.next(sid)
    training.trainer.submit(sid, "Answer")
    training.trainer.finish(sid)
    assert recommended_lesson(training.store.all()) == "role-diagnostic"
    for track in REQUIRED:
        sid = training.trainer.start(mode="training", lesson_id=track)["id"]
        for _ in range(2):
            training.trainer.next(sid)
            training.trainer.submit(sid, "Guided answer")
        training.trainer.finish(sid)
    assert recommended_lesson(training.store.all()) is None


def test_applied_path_dependencies_and_legacy_ids():
    catalog = lessons()
    seen = set()
    for lesson in catalog:
        assert set(lesson.prerequisites) <= seen
        assert lesson.required == (lesson.id in REQUIRED)
        assert guide(lesson.id).startswith("# ")
        seen.add(lesson.id)
    assert set(APPLIED) <= seen
    assert {"python-basics", "post-training", "research-engineering"} <= seen


def test_completed_legacy_lesson_does_not_skip_advanced_path(training):
    sid = training.trainer.start(mode="training", lesson_id="python-basics")["id"]
    for _ in range(2):
        training.trainer.next(sid)
        training.trainer.submit(sid, "Legacy answer")
    training.trainer.finish(sid)
    assert recommended_lesson(training.store.all()) == "role-diagnostic"


def test_guides_and_map_available_before_init(tmp_path, capsys):
    for lesson in ["welcome", *LESSON_IDS]:
        cli.main(["guide", lesson])
        assert guide(lesson).strip() in capsys.readouterr().out
    cli.main(["learn", "--list"])
    assert "coding" in capsys.readouterr().out
    assert not (tmp_path / ".grey").exists()


def test_cli_auto_resume_new_attempt_and_progress(tmp_path, capsys):
    base = ["--home", str(tmp_path)]
    cli.main(base + ["init"])
    capsys.readouterr()
    cli.main(base + ["learn", "--start-only"])
    first = capsys.readouterr().out.strip()
    cli.main(base + ["learn", "--start-only"])
    assert capsys.readouterr().out.strip() == first
    cli.main(base + ["learn", "--lesson", "coding", "--new", "--start-only"])
    second = capsys.readouterr().out.strip()
    assert second != first
    cli.main(base + ["learn", "--list"])
    assert second in capsys.readouterr().out
    cli.main(base + ["next", second])
    output = capsys.readouterr().out
    assert "Keep the first occurrence" in output
    assert "expected O(n)" not in output  # Private exercise notes are not printed.
    cli.main(base + ["learn", first, "--start-only"])
    assert capsys.readouterr().out.strip() == first


def test_interactive_final_exercise_allows_review_retry_and_pause(training, monkeypatch, capsys):
    sid = training.trainer.start(mode="training", lesson_id="coding")["id"]
    for _ in range(2):
        training.trainer.next(sid)
        training.trainer.submit(sid, "Initial answer")
    actions = iter(["review Explain the gap", "retry", "pause"])
    monkeypatch.setattr("builtins.input", lambda _: next(actions))
    monkeypatch.setattr(cli, "read_answer", lambda: "Improved final answer")
    cli.interactive(training.trainer, sid)
    state, _ = training.store.load(sid)
    assert not state["completed_at"]
    assert len(state["questions"][-1]["attempts"]) == 2
    assert "Attempt 2" in capsys.readouterr().out
    monkeypatch.setattr("builtins.input", lambda _: "")
    cli.interactive(training.trainer, sid)
    assert training.store.load(sid)[0]["completed_at"]
    assert "system-design" in capsys.readouterr().out


def test_interactive_guide_explanation_and_file_answer(training, monkeypatch, tmp_path, capsys):
    sid = training.trainer.start(mode="training", lesson_id="system-design")["id"]
    answer = tmp_path / "design.md"
    answer.write_text("```mermaid\nflowchart LR\n Client --> API\n```", encoding="utf-8")
    actions = iter(["guide", "explain What is an outbox?", f"file {answer}", "pause"])
    monkeypatch.setattr("builtins.input", lambda _: next(actions))
    cli.interactive(training.trainer, sid)
    state, _ = training.store.load(sid)
    assert "```mermaid" in state["questions"][0]["attempts"][0]["answer"]
    assert state["questions"][0]["coaching"][0]["kind"] == "explain"
    assert "transactional" in capsys.readouterr().out
