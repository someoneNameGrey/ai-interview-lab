"""Loopback-only browser interface for the existing trainer and local provider."""

import copy
import json
import re
import secrets
import sqlite3
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, StrictInt, ValidationError

from .curriculum import check_answers, checkpoint_version, lessons, load_lesson, recommended_lesson
from .engine import Trainer, first_scores, now
from .models import CORE, OPTIONAL, Coaching, Config, StrictModel, score
from .provider import Provider, ProviderError
from .store import Store


class StartRequest(StrictModel):
    mode: Literal["training", "practice", "mock"] = "training"
    lesson_id: str | None = None
    tracks: list[str] | None = None
    turns: int = Field(default=2, ge=1, le=4)


class AnswerRequest(StrictModel):
    answer: str = Field(min_length=1, max_length=60000)
    revise: bool = False


class CoachRequest(StrictModel):
    kind: Literal["hint", "clarify", "review", "explain"]
    message: str = Field(min_length=1, max_length=6000)


class TutorRequest(StrictModel):
    message: str = Field(min_length=1, max_length=6000)
    lesson_id: str | None = None
    session_id: str | None = None


class CheckpointRequest(StrictModel):
    answers: list[StrictInt] = Field(min_length=3, max_length=20, strict=True)


def public_session(state):
    """Never ship reference notes or locked mock feedback to a browser."""
    result = copy.deepcopy(state)
    result["language"] = state["config"].get("language", "Python")
    result.pop("config")
    result.pop("calls")
    result.pop("levels")
    locked = state["mode"] == "mock" and not state["completed_at"]
    result["feedback_locked"] = locked
    if "lesson" in result:
        result["lesson"] = {
            key: result["lesson"][key] for key in ("id", "title", "guide", "objectives")
        }
    for q in result["questions"]:
        q["question"].pop("interviewer_notes", None)
        for attempt in q["attempts"]:
            evaluation = attempt["evaluation"]
            attempt["graded"] = evaluation is not None
            attempt["score"] = score(evaluation) if evaluation and not locked else None
            if locked:
                attempt["evaluation"] = None
    return result


def readiness(store):
    sessions = [s for s in store.all() if s["mode"] != "mock" or s["completed_at"]]
    checks = store.checkpoints()
    curriculum = lessons()
    result = []
    for track in CORE + OPTIONAL:
        required = [
            lesson for lesson in curriculum
            if lesson.track == track and (lesson.required or track in OPTIONAL)
        ]
        passed = sum(
            checks.get(lesson.id, {}).get("passed", False)
            and checks[lesson.id].get("version") == checkpoint_version(lesson.model_dump())
            for lesson in required
        )
        attempts = first_scores(sessions, track)[-2:]
        independent = len(attempts) == 2 and all(
            score(e) >= 75
            and e["confidence"] != "low"
            and all(d["score"] >= 2 for d in e["dimensions"])
            for e in attempts
        )
        status = (
            "Ready for a mock"
            if independent and passed == len(required)
            else ("Try independent practice" if passed == len(required) else "Continue learning")
        )
        result.append(
            {
                "track": track,
                "status": status,
                "checks_passed": passed,
                "checks_total": len(required),
                "independent_attempts": len(attempts),
                "recent_scores": [score(e) for e in attempts],
            }
        )
    return result


class WebApp:
    def __init__(self, home, provider_factory=Provider):
        self.home = Path(home)
        self.home.mkdir(parents=True, exist_ok=True)
        path = self.home / "config.json"
        if not path.exists():
            path.write_text(Config().model_dump_json(indent=2) + "\n", encoding="utf-8")
        self.store = Store(self.home / "progress.sqlite3")
        self.provider_factory = provider_factory
        self.token = secrets.token_urlsafe(32)
        self.tutor_lock = threading.Lock()

    def config(self):
        return Config.model_validate_json(
            (self.home / "config.json").read_text(encoding="utf-8-sig")
        ).with_environment()

    def trainer(self):
        return Trainer(self.store, self.config(), self.provider_factory)

    def bootstrap(self):
        config = self.config()
        sessions = self.store.all()
        checks = self.store.checkpoints()
        courses = []
        for lesson in lessons():
            matching = [s for s in sessions if s.get("lesson", {}).get("id") == lesson.id]
            active = next((s for s in reversed(matching) if not s["completed_at"]), None)
            checkpoint = checks.get(lesson.id)
            if checkpoint and checkpoint.get("version") != checkpoint_version(lesson.model_dump()):
                checkpoint = None
            courses.append(
                {
                    "id": lesson.id,
                    "track": lesson.track,
                    "title": lesson.title,
                    "stage": lesson.stage,
                    "minutes": lesson.minutes,
                    "objectives": lesson.objectives,
                    "prerequisites": lesson.prerequisites,
                    "required": lesson.required,
                    "completed": any(s["completed_at"] for s in matching),
                    "active_session": active["id"] if active else None,
                    "checkpoint": checkpoint,
                }
            )
        return {
            "token": self.token,
            "lessons": courses,
            "recommended_lesson": recommended_lesson(sessions),
            "draft_namespace": str(self.home.resolve()),
            "provider": config.provider,
            "model": config.model_for("question") or "CLI default",
            "effort": config.effort_for("question") or "provider default",
            "tutor_model": config.model_for("tutor") or "CLI default",
            "tutor_effort": config.effort_for("tutor") or "provider default",
            "tracks": CORE + OPTIONAL,
            "readiness": readiness(self.store),
            "sessions": [
                {
                    "id": s["id"],
                    "mode": s["mode"],
                    "tracks": s["tracks"],
                    "title": s.get("lesson", {}).get("title") or " / ".join(s["tracks"]),
                    "completed": bool(s["completed_at"]),
                    "created_at": s["created_at"],
                }
                for s in reversed(sessions)
            ],
        }

    def chat(self, request):
        if not request.message.strip():
            raise ValueError("Enter a question for your tutor.")
        if not self.tutor_lock.acquire(blocking=False):
            raise ValueError("Your tutor is still replying. Please wait.")
        try:
            context = "General learning"
            if request.session_id:
                state, _ = self.store.load(request.session_id)
                if state["questions"] and not state["completed_at"]:
                    q = state["questions"][-1]
                    reviewed = q["attempts"] and q["attempts"][-1]["evaluation"]
                    kind = (
                        "clarify"
                        if state["mode"] == "mock"
                        else "review"
                        if reviewed
                        else "explain"
                        if state["mode"] == "training"
                        else "hint"
                    )
                    reply = self.trainer().coach(state["id"], kind, request.message)
                    context = q["question"]["title"]
                    item = {
                        "message": request.message,
                        "reply": reply,
                        "context": context,
                        "at": now(),
                    }
                    self.store.save_tutor_message(item)
                    return {"messages": self.store.tutor_messages()}
                context = state.get("lesson", {}).get("title", "Interview preparation")
            lesson = None
            if request.lesson_id:
                raw = load_lesson(request.lesson_id)
                lesson = {key: raw[key] for key in ("title", "guide", "objectives")}
                context = raw["title"]
            reply, metadata = self.provider_factory(self.config()).request(
                "tutor",
                Coaching,
                {
                    "message": request.message,
                    "lesson": lesson,
                    "history": self.store.tutor_messages()[-12:],
                },
            )
            self.store.save_tutor_message(
                {
                    "message": request.message,
                    "reply": reply["reply"],
                    "context": context,
                    "at": now(),
                    "call": metadata,
                }
            )
            return {"messages": self.store.tutor_messages()}
        finally:
            self.tutor_lock.release()

    def get(self, path):
        if path == "/api/tutor":
            return {"messages": self.store.tutor_messages()}
        if path == "/api/bootstrap":
            return self.bootstrap()
        if path.startswith("/api/lessons/"):
            lesson = load_lesson(path.removeprefix("/api/lessons/"))
            lesson.pop("exercises")
            lesson["checks"] = [
                {"question": c["question"], "options": c["options"]} for c in lesson["checks"]
            ]
            return lesson
        if re.fullmatch(r"/api/sessions/[a-f0-9]{12}", path):
            return public_session(self.store.load(path.rsplit("/", 1)[1])[0])
        raise ValueError("Page not found.")

    def post(self, path, payload):
        if path == "/api/tutor":
            return self.chat(TutorRequest.model_validate(payload))
        if path == "/api/sessions":
            request = StartRequest.model_validate(payload)
            return public_session(self.trainer().start(**request.model_dump()))
        if path.startswith("/api/checkpoints/"):
            request = CheckpointRequest.model_validate(payload)
            result = check_answers(load_lesson(path.rsplit("/", 1)[1]), request.answers)
            result["at"] = now()
            self.store.save_checkpoint(result)
            return result
        match = re.fullmatch(r"/api/sessions/([a-f0-9]{12})/(next|answer|grade|coach|finish)", path)
        if not match:
            raise ValueError("Action not found.")
        sid, action = match.groups()
        trainer = self.trainer()
        if action == "answer":
            trainer.submit(sid, **AnswerRequest.model_validate(payload).model_dump())
        elif action == "coach":
            trainer.coach(sid, **CoachRequest.model_validate(payload).model_dump())
        else:
            if payload:
                raise ValueError("This action does not accept extra fields.")
            getattr(trainer, action)(sid)
        return public_session(self.store.load(sid)[0])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Submitted content and session identifiers do not belong in access logs.
        pass

    def send_content(self, status, content, content_type="application/json; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        )
        self.end_headers()
        self.wfile.write(content)

    def dispatch(self, write=False):
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        if host not in hosts:
            self.send_content(403, b'{"error":"Use the local workspace URL."}')
            return
        if write and (
            not secrets.compare_digest(self.headers.get("X-Grey-Token", ""), self.server.app.token)
            or self.headers.get("Origin", f"http://{host}") != f"http://{host}"
            or self.headers.get("Sec-Fetch-Site") == "cross-site"
        ):
            self.send_content(403, b'{"error":"Reload the workspace before submitting."}')
            return
        try:
            path = urlsplit(self.path).path
            if write:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 260000:
                    self.send_content(413, b'{"error":"Request is empty or too large."}')
                    return
                if self.headers.get_content_type() != "application/json":
                    raise ValueError("Expected a JSON request.")
                self.connection.settimeout(15)
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict):
                    raise ValueError("Expected a JSON object.")
                result = self.server.app.post(path, payload)
            elif path.startswith("/api/"):
                result = self.server.app.get(path)
            else:
                name = {"/": "index.html", "/app.css": "app.css"}.get(path)
                if re.fullmatch(r"/assets/[\w.-]+\.(js|css|txt)", path):
                    name = path.removeprefix("/")
                if not name:
                    self.send_content(404, b'{"error":"Page not found."}')
                    return
                asset = files("grey_interview").joinpath(f"static/{name}")
                if not asset.is_file():
                    self.send_content(404, b'{"error":"Asset missing. Run npm run build."}')
                    return
                mime = {
                    ".html": "text/html",
                    ".js": "text/javascript",
                    ".css": "text/css",
                    ".txt": "text/plain",
                }
                self.send_content(
                    200, asset.read_bytes(), mime[Path(name).suffix] + "; charset=utf-8"
                )
                return
            self.send_content(200, json.dumps(result, ensure_ascii=False).encode("utf-8"))
        except ValidationError:
            self.send_content(
                400, b'{"error":"Invalid settings or answer. Check the fields and retry."}'
            )
        except (ValueError, ProviderError) as exc:
            self.send_content(400, json.dumps({"error": str(exc)}).encode("utf-8"))
        except (OSError, sqlite3.Error):
            self.send_content(
                500, b'{"error":"Local operation failed. Your saved work is retained."}'
            )

    def do_GET(self):
        self.dispatch()

    def do_POST(self):
        self.dispatch(write=True)


def make_server(app, port=8765):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.app = app
    return server


def serve(home, port=8765, open_browser=True):
    if not 0 <= port <= 65535:
        raise ValueError("Choose a port from 0 to 65535.")
    with make_server(WebApp(home), port) as server:
        url = f"http://127.0.0.1:{server.server_port}"
        print(
            f"Grey learning workspace: {url}\nKeep this terminal open. Ctrl+C stops the server.",
            flush=True,
        )
        if open_browser:
            webbrowser.open(url)
        server.serve_forever()
