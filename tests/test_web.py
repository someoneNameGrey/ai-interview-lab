import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest
from pydantic import ValidationError
from test_trainer import FakeProvider

from grey_interview.curriculum import APPLIED, FOUNDATIONS, lessons, load_lesson
from grey_interview.provider import ProviderError
from grey_interview.web import WebApp, make_server, readiness


@pytest.fixture
def app(tmp_path):
    provider = FakeProvider()
    result = WebApp(tmp_path, lambda _: provider)
    result.provider = provider
    return result


def start(app, **kwargs):
    state = app.post("/api/sessions", kwargs)
    path = "/api/sessions/" + state["id"]
    return path, app.post(path + "/next", {})


@pytest.mark.parametrize("lesson_id", FOUNDATIONS + APPLIED)
def test_lesson_exercises_use_correct_track(app, lesson_id):
    path, state = start(app, mode="training", lesson_id=lesson_id)
    assert state["tracks"] == [load_lesson(lesson_id)["track"]]
    assert "interviewer_notes" not in json.dumps(state)
    assert "checks" not in state["lesson"]
    assert app.provider.calls == []
    for i in range(2):
        app.post(path + "/answer", {"answer": f"Answer {i}"})
        if i == 0:
            app.post(path + "/next", {})
    assert app.post(path + "/finish", {})["completed_at"]
    assert readiness(app.store)[0]["independent_attempts"] == 0


def test_checkpoint_redaction_validation_and_persistence(app):
    lesson = app.get("/api/lessons/python-basics")
    assert all(set(c) == {"question", "options"} for c in lesson["checks"])
    answers = [c["answer"] for c in load_lesson("python-basics")["checks"]]
    with pytest.raises(ValidationError):
        app.post("/api/checkpoints/python-basics", {"answers": [True, 0, 1]})
    with pytest.raises(ValueError):
        app.post("/api/checkpoints/python-basics", {"answers": [4, 0, 1]})
    result = app.post("/api/checkpoints/python-basics", {"answers": answers})
    assert result["passed"] and result["score"] == 100
    restored = WebApp(app.home).bootstrap()
    saved = next(item for item in restored["lessons"] if item["id"] == "python-basics")
    assert saved["checkpoint"]["score"] == 100
    assert restored["readiness"][0]["independent_attempts"] == 0


def test_mock_feedback_is_locked_until_finished(app):
    path, state = start(app, mode="mock", tracks=["coding"], turns=1)
    assert "PRIVATE REFERENCE" not in json.dumps(state)
    state = app.post(path + "/answer", {"answer": "My answer"})
    attempt = state["questions"][0]["attempts"][0]
    assert attempt["evaluation"] is None and attempt["score"] is None
    assert app.bootstrap()["readiness"][0]["independent_attempts"] == 0
    state = app.post(path + "/finish", {})
    assert state["questions"][0]["attempts"][0]["score"] == 100


def test_failed_review_retains_answer_for_retry(app):
    path, _ = start(app, mode="training", lesson_id="python-basics")
    app.provider.fail = "evaluate"
    with pytest.raises(ProviderError):
        app.post(path + "/answer", {"answer": "def solution():\n    return 42"})
    state = app.get(path)
    assert state["questions"][0]["attempts"][0]["answer"].endswith("return 42")
    app.provider.fail = None
    assert app.post(path + "/grade", {})["questions"][0]["attempts"][0]["graded"]


def test_http_assets_and_cross_origin_protection(app):
    server = make_server(app, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        for path in ["/", "/app.css", "/assets/app.js", "/api/bootstrap"]:
            with urlopen(base + path) as response:
                assert response.status == 200
                assert response.headers["Content-Security-Policy"]
        for headers in [{}, {"X-Grey-Token": app.token, "Origin": "https://example.com"}]:
            request = Request(
                base + "/api/sessions",
                data=b"{}",
                headers={"Content-Type": "application/json", **headers},
            )
            with pytest.raises(HTTPError) as error:
                urlopen(request)
            assert error.value.code == 403
        request = Request(
            base + "/api/sessions",
            data=json.dumps({"mode": "training", "lesson_id": "python-basics"}).encode(),
            headers={"Content-Type": "application/json", "X-Grey-Token": app.token},
        )
        with urlopen(request) as response:
            assert json.load(response)["mode"] == "training"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_readiness_requires_checks_and_fresh_independent_results(app):
    lesson_ids = [lesson.id for lesson in lessons() if lesson.track == "coding" and lesson.required]
    for lesson_id in lesson_ids:
        answers = [c["answer"] for c in load_lesson(lesson_id)["checks"]]
        app.post("/api/checkpoints/" + lesson_id, {"answers": answers})
    assert readiness(app.store)[0]["status"] == "Try independent practice"
    path, _ = start(app, mode="practice", tracks=["coding"], turns=2)
    app.post(path + "/answer", {"answer": "First independent answer"})
    assert readiness(app.store)[0]["status"] == "Try independent practice"
    app.post(path + "/next", {})
    app.post(path + "/answer", {"answer": "Second independent answer"})
    assert readiness(app.store)[0]["status"] == "Ready for a mock"
    checkpoint = app.store.checkpoints()["coding"]
    checkpoint["version"] = "stale"
    app.store.save_checkpoint(checkpoint)
    assert readiness(app.store)[0]["status"] == "Continue learning"


def test_advanced_bootstrap_and_optional_refreshers(app):
    data = app.bootstrap()
    assert data["recommended_lesson"] == "role-diagnostic"
    assert data["lessons"][0]["id"] == "role-diagnostic"
    assert not next(x for x in data["lessons"] if x["id"] == "python-basics")["required"]
    lesson = app.get("/api/lessons/deepswe")
    assert lesson["prerequisites"] == ["ai-observability"]
    assert "interviewer_notes" not in json.dumps(lesson)
    assert all(set(c) == {"question", "options"} for c in lesson["checks"])
    for lesson_id in FOUNDATIONS:
        answers = [c["answer"] for c in load_lesson(lesson_id)["checks"]]
        app.post("/api/checkpoints/" + lesson_id, {"answers": answers})
    assert readiness(app.store)[0]["status"] == "Continue learning"


def test_tutor_remembers_history_and_only_receives_public_lesson(app):
    result = app.post(
        "/api/tutor", {"message": "What is a list?", "lesson_id": "python-collections"}
    )
    assert result["messages"][0]["reply"]
    task, payload = app.provider.calls[-1]
    assert task == "tutor"
    assert set(payload["lesson"]) == {"title", "guide", "objectives"}
    app.post("/api/tutor", {"message": "How is a set different?"})
    assert app.provider.calls[-1][1]["history"][0]["message"] == "What is a list?"
    assert len(WebApp(app.home).get("/api/tutor")["messages"]) == 2


def test_tutor_session_help_marks_practice_assisted(app):
    path, state = start(app, mode="practice", tracks=["coding"], turns=1)
    app.post("/api/tutor", {"message": "Help me start", "session_id": state["id"]})
    assert app.provider.calls[-1][1]["kind"] == "hint"
    result = app.post(path + "/answer", {"answer": "My answer"})
    assert result["questions"][0]["attempts"][0]["assisted"]


def test_tutor_mock_uses_only_clarification_and_no_private_context(app):
    _, state = start(app, mode="mock", tracks=["coding"], turns=1)
    app.post("/api/tutor", {"message": "Explain the requirements", "session_id": state["id"]})
    payload = app.provider.calls[-1][1]
    assert payload["kind"] == "clarify"
    assert "PRIVATE REFERENCE" not in json.dumps(payload)
    assert payload["attempts"] == []


def test_tutor_failure_releases_lock_and_rejects_blank(app):
    with pytest.raises(ValueError):
        app.post("/api/tutor", {"message": "   "})
    app.provider.fail = "tutor"
    with pytest.raises(ProviderError):
        app.post("/api/tutor", {"message": "What is Python?"})
    assert app.get("/api/tutor")["messages"] == []
    app.provider.fail = None
    assert app.post("/api/tutor", {"message": "What is Python?"})["messages"]
