from types import SimpleNamespace

import pytest

from grey_interview.engine import Trainer, adjust, export_state, progress, report
from grey_interview.models import CORE, DIMENSIONS, OPTIONAL, Config
from grey_interview.provider import ProviderError
from grey_interview.store import Store


def evaluation(value=3, confidence="high"):
    return {
        "dimensions": [
            {
                "name": name,
                "score": value,
                "evidence": "Specific evidence",
                "improvement": "Add a concrete edge-case test",
            }
            for name in DIMENSIONS
        ],
        "strengths": ["Clear reasoning"],
        "gaps": ["Missing boundary check"],
        "lesson": "Check boundary conditions.",
        "exercise": "Add boundary tests and explain them.",
        "followup_focus": "Failure handling",
        "confidence": confidence,
    }


class FakeProvider:
    def __init__(self):
        self.calls = []
        self.fail = None

    def request(self, task, schema, payload):
        self.calls.append((task, payload))
        if self.fail == task:
            raise ProviderError("Simulated network failure")
        if task == "question":
            result = {
                "title": f"Generated fixture {len(self.calls)}",
                "prompt": str(len(self.calls)),
                "constraints": [],
                "starter_code": "",
                "acceptance_checks": ["Check edges"],
                "minutes": 15,
                "interviewer_notes": "PRIVATE REFERENCE",
            }
        elif task == "evaluate":
            result = evaluation(4)
        else:
            result = {"reply": "A small nudge"}
        return schema.model_validate(result).model_dump(), {
            "model": "test",
            "response_id": "fixture",
            "usage": {"total_tokens": 50},
        }


@pytest.fixture
def rig(tmp_path):
    provider = FakeProvider()
    store = Store(tmp_path / "progress.sqlite3")
    trainer = Trainer(store, Config(), lambda _: provider)
    return SimpleNamespace(provider=provider, store=store, trainer=trainer)


def test_complete_all_tracks_resume_and_followup(rig):
    sid = rig.trainer.start(tracks=CORE + OPTIONAL, turns=2)["id"]
    for _ in range(16):
        s, q = rig.trainer.next(sid)
        rig.trainer.submit(sid, "My implementation and reasoning")
        assert q["question"]["prompt"]
    s = rig.trainer.finish(sid)
    assert s["completed_at"]
    assert len(s["questions"]) == 16
    assert "Build next:" in report(s)
    assert "My implementation" in export_state(s)
    payloads = [p for task, p in rig.provider.calls if task == "question"]
    assert payloads[1]["previous_round_answers"][0]["attempt"]["answer"]
    assert payloads[1]["difficulty"] == 3
    assert len(Store(rig.store.path).all()) == 1


def test_failure_preserves_answer_and_retry_is_idempotent(rig):
    sid = rig.trainer.start(tracks=["coding"], turns=1)["id"]
    rig.trainer.next(sid)
    rig.provider.fail = "evaluate"
    with pytest.raises(ProviderError):
        rig.trainer.submit(sid, "important work")
    s, _ = rig.store.load(sid)
    assert s["questions"][0]["attempts"][0]["answer"] == "important work"
    with pytest.raises(ValueError, match="not graded"):
        rig.trainer.next(sid)
    rig.provider.fail = None
    rig.trainer.grade(sid)
    calls = len(rig.provider.calls)
    rig.trainer.grade(sid)
    assert len(rig.provider.calls) == calls


def test_mock_never_reveals_feedback_early(rig):
    sid = rig.trainer.start(mode="mock", tracks=["coding"], turns=1)["id"]
    rig.trainer.next(sid)
    rig.trainer.coach(sid, "clarify", "What input type?")
    for kind in ("hint", "review"):
        with pytest.raises(ValueError):
            rig.trainer.coach(sid, kind, "Help")
    s = rig.trainer.submit(sid, "Answer")
    assert "100/100" not in report(s)
    assert "recent average" not in progress(rig.store)
    with pytest.raises(ValueError):
        export_state(s)
    with pytest.raises(ValueError):
        rig.trainer.submit(sid, "Answer 2", revise=True)
    assert "100/100" in report(rig.trainer.finish(sid))


def test_assistance_and_revisions_do_not_inflate_difficulty(rig):
    sid = rig.trainer.start(tracks=["coding"])["id"]
    rig.trainer.next(sid)
    rig.trainer.coach(sid, "hint", "Help")
    s = rig.trainer.submit(sid, "Answer")
    assert s["levels"]["coding"] == 2
    s = rig.trainer.submit(sid, "Improved answer", revise=True)
    assert len(s["questions"][0]["attempts"]) == 2
    assert "coding: not assessed" in progress(rig.store)
    assert rig.trainer.start(tracks=["coding"])["levels"]["coding"] == 2


def test_pending_question_reused_and_failed_generation_does_not_advance(rig):
    sid = rig.trainer.start(tracks=["coding"])["id"]
    rig.provider.fail = "question"
    with pytest.raises(ProviderError):
        rig.trainer.next(sid)
    assert not rig.store.load(sid)[0]["questions"]
    rig.provider.fail = None
    rig.trainer.next(sid)
    calls = len(rig.provider.calls)
    rig.trainer.next(sid)
    assert len(rig.provider.calls) == calls


def test_optimistic_concurrency(rig):
    sid = rig.trainer.start()["id"]
    a, version = rig.store.load(sid)
    b, stale = rig.store.load(sid)
    rig.store.save(a, version)
    with pytest.raises(ValueError, match="another process"):
        rig.store.save(b, stale)


def test_boundaries_and_completion(rig):
    assert adjust(1, evaluation(0)) == 1
    assert adjust(5, evaluation(4)) == 5
    assert adjust(3, evaluation(0, "low")) == 3
    assert adjust(3, evaluation(4), assisted=True) == 3
    sid = rig.trainer.start()["id"]
    with pytest.raises(ValueError):
        rig.trainer.finish(sid)
    with pytest.raises(ValueError):
        rig.trainer.submit(sid, " ")
    with pytest.raises(ValueError):
        rig.trainer.start(tracks=["invalid"])
    with pytest.raises(ValueError):
        rig.trainer.start(turns=5)


def test_cli_roundtrip_config_and_public_question(tmp_path, monkeypatch, capsys):
    from grey_interview import cli

    fake = FakeProvider()
    monkeypatch.setattr(cli, "Provider", lambda _: fake)
    base = ["--home", str(tmp_path)]
    cli.main(base + ["init"])
    capsys.readouterr()
    cli.main(base + ["start", "--tracks", "coding", "--turns", "1"])
    sid = capsys.readouterr().out.strip()
    cli.main(base + ["next", sid])
    assert "PRIVATE" not in capsys.readouterr().out
    path = tmp_path / "answer.txt"
    path.write_text("Implementation", encoding="utf-8")
    cli.main(base + ["answer", sid, "--file", str(path)])
    cli.main(base + ["finish", sid])
    cli.main(base + ["export", sid, "--out", str(tmp_path / "report.md")])
    assert "100/100" in (tmp_path / "report.md").read_text()


def test_cross_session_adaptation_and_no_private_clarification(rig):
    sid = rig.trainer.start(tracks=["coding"], turns=1)["id"]
    rig.trainer.next(sid)
    rig.trainer.coach(sid, "clarify", "What is the contract?")
    coaching_payload = rig.provider.calls[-1][1]
    assert "interviewer_notes" not in coaching_payload["question"]
    rig.trainer.submit(sid, "My answer")
    rig.trainer.finish(sid)
    s = rig.trainer.start(tracks=["coding"], turns=1)
    assert s["levels"]["coding"] == 3
    assert "coding: recent average 100/100" in progress(rig.store)


def test_duplicate_question_does_not_advance(rig):
    sid = rig.trainer.start(tracks=["coding"])["id"]
    rig.trainer.next(sid)
    rig.trainer.submit(sid, "My answer")
    rig.provider.calls.clear()  # Force fixture to repeat its first exact prompt.
    with pytest.raises(ValueError, match="repeated"):
        rig.trainer.next(sid)
    assert len(rig.store.load(sid)[0]["questions"]) == 1


def test_interactive_resume_finishes(tmp_path, monkeypatch, capsys):
    from grey_interview import cli

    fake = FakeProvider()
    monkeypatch.setattr(cli, "Provider", lambda _: fake)
    base = ["--home", str(tmp_path)]
    cli.main(base + ["init"])
    capsys.readouterr()
    cli.main(base + ["start", "--tracks", "coding", "--turns", "1"])
    sid = capsys.readouterr().out.strip()
    answers = iter(["pause"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    cli.main(base + ["run", sid])
    assert len(fake.calls) == 1
    answer = tmp_path / "answer.md"
    answer.write_text("My code", encoding="utf-8")
    answers = iter([f"file {answer}"])
    cli.main(base + ["run", sid])
    assert Store(tmp_path / "progress.sqlite3").load(sid)[0]["completed_at"]
