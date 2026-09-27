import argparse
import os
import shutil
import sqlite3
import sys
from importlib.metadata import version
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from .curriculum import LESSON_IDS, curriculum_progress, guide, recommended_lesson
from .engine import Trainer, export_state, progress, report
from .models import CORE, OPTIONAL, Coaching, Config
from .provider import Provider, ProviderError
from .store import Store


def show_question(state, q):
    question = q["question"]
    print(
        f"\n{len(state['questions'])}/{len(state['tracks']) * state['turns_per_round']} | "
        f"{q['track']} | difficulty {q['difficulty']}/5 | {question['minutes']} minutes"
    )
    print(f"\n{question['title']}\n\n{question['prompt']}")
    if question["constraints"]:
        print("\nConstraints:\n" + "\n".join("- " + c for c in question["constraints"]))
    if question["starter_code"]:
        print("\nStarter code:\n" + question["starter_code"])
    print("\nAcceptance checks:\n" + "\n".join("- " + c for c in question["acceptance_checks"]))


def read_answer(path=None):
    if path:
        p = Path(path)
        if p.stat().st_size > 240000:
            raise ValueError("Answer file is too large (maximum 240 KB).")
        return p.read_text(encoding="utf-8-sig")
    if not sys.stdin.isatty():
        return sys.stdin.read(60001)
    print("Enter your answer. Finish with .done on its own line; .cancel discards this input.")
    lines = []
    while True:
        line = input()
        if line == ".done":
            return "\n".join(lines)
        if line == ".cancel":
            raise ValueError("Input cancelled; the question remains saved.")
        lines.append(line)


def parser():
    p = argparse.ArgumentParser(description="Grey's production AI engineering interview trainer")
    p.add_argument(
        "--home",
        type=Path,
        default=Path(os.getenv("GREY_HOME", ".grey")),
        help="Local config and progress directory (default: .grey)",
    )
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="Create editable candidate config")
    web = sub.add_parser("web", help="Open the local learning workspace in your browser")
    web.add_argument("--port", type=int, default=8765)
    web.add_argument("--no-browser", action="store_true")
    tutorial = sub.add_parser("guide", help="Read a tutorial without a model call")
    tutorial.add_argument("lesson", nargs="?", default="welcome", choices=["welcome", *LESSON_IDS])
    learn = sub.add_parser("learn", help="Guided lessons and exercises")
    learn.add_argument("session", nargs="?", help="Resume a training session")
    learn.add_argument("--lesson", choices=LESSON_IDS)
    learn.add_argument("--list", action="store_true", help="Show curriculum progress")
    learn.add_argument("--new", action="store_true", help="Start a fresh attempt at a lesson")
    learn.add_argument(
        "--start-only", action="store_true", help="Print a session ID without interaction"
    )
    doctor = sub.add_parser("doctor", help="Check config and provider installation")
    doctor.add_argument(
        "--live", action="store_true", help="Test a generation (uses provider quota)"
    )
    for name in ("start", "run"):
        cmd = sub.add_parser(
            name, help="Create a session" if name == "start" else "Interactive interview"
        )
        if name == "run":
            cmd.add_argument("session", nargs="?", help="Resume an existing session")
        cmd.add_argument("--mode", choices=["practice", "mock"], default="practice")
        cmd.add_argument("--tracks", nargs="+", choices=CORE + OPTIONAL, default=CORE)
        cmd.add_argument("--turns", type=int, help="Turns per round, 1-4")
    for name in (
        "next",
        "show",
        "answer",
        "grade",
        "hint",
        "clarify",
        "review",
        "explain",
        "finish",
        "report",
        "export",
    ):
        cmd = sub.add_parser(name)
        cmd.add_argument("session")
        if name == "next":
            cmd.add_argument("--remediate", action="store_true")
        if name == "answer":
            cmd.add_argument("--file", type=Path)
            cmd.add_argument("--revise", action="store_true")
        if name in ("hint", "clarify", "review", "explain"):
            cmd.add_argument(
                "message", nargs="?", default="Give me one small hint." if name == "hint" else None
            )
        if name == "export":
            cmd.add_argument("--out", type=Path, required=True)
            cmd.add_argument("--format", choices=["json", "markdown"], default="markdown")
    sub.add_parser("sessions", help="List saved sessions")
    sub.add_parser("progress", help="Show recent performance and suggested practice")
    return p


def interactive(trainer, sid):
    state, _ = trainer.store.load(sid)
    training = state["mode"] == "training"
    command = "learn" if training else "run"
    print(f"Session: {sid}. Resume anytime with: grey {command} {sid}")
    if training:
        print(state["lesson"]["guide"])
    while True:
        state, _ = trainer.store.load(sid)
        if state["completed_at"]:
            print(report(state))
            if training:
                print(curriculum_progress(trainer.store.all()))
            return
        if state["questions"] and state["questions"][-1]["attempts"]:
            if not state["questions"][-1]["attempts"][-1]["evaluation"]:
                print("Retrying the saved answer's evaluation...")
                state = trainer.grade(sid)
            if training:
                print(report(state))
                action = training_feedback(trainer, sid)
                if action == "pause":
                    return
                if action == "retry":
                    q = state["questions"][-1]
                    show_question(state, q)
                    trainer.submit(sid, read_answer(), revise=True)
                    continue
            if len(state["questions"]) == len(state["tracks"]) * state["turns_per_round"]:
                print(report(trainer.finish(sid)))
                if training:
                    print(curriculum_progress(trainer.store.all()))
                return
        state, q = trainer.next(sid)
        show_question(state, q)
        while True:
            extras = " | guide | explain TEXT" if training else ""
            action = input(
                f"\n[enter] answer | file PATH | hint | clarify TEXT{extras} | pause > "
            ).strip()
            if action == "pause":
                return
            if training and action == "guide":
                print(state["lesson"]["guide"])
                continue
            if (
                action == "hint"
                or action.startswith("clarify ")
                or (training and action.startswith("explain "))
            ):
                kind = action.split(" ", 1)[0]
                try:
                    print(
                        trainer.coach(
                            sid,
                            kind,
                            "One small hint." if kind == "hint" else action.split(" ", 1)[1],
                        )
                    )
                except ValueError as exc:
                    print(str(exc))
                continue
            if action and not action.startswith("file "):
                print("Choose answer, file PATH, hint, clarify TEXT, or pause.")
                continue
            answer = read_answer(
                action[5:].strip().strip('"') if action.startswith("file ") else None
            )
            state = trainer.submit(sid, answer)
            if not training:
                print(report(state) if state["mode"] == "practice" else "Answer recorded.")
            break


def training_feedback(trainer, sid):
    """Keep revisions and tutor discussion available before the next exercise."""
    while True:
        action = input("\n[enter] continue | retry | review TEXT | pause > ").strip()
        if action in ("", "retry", "pause"):
            return action
        if action.startswith("review "):
            print(trainer.coach(sid, "review", action[7:]))
        else:
            print("Choose continue, retry, review TEXT, or pause.")


def learn(trainer, args):
    if args.session and (args.lesson or args.new):
        raise ValueError("Choose a session ID to resume, or --lesson/--new to start.")
    if args.new and not args.lesson:
        raise ValueError("Use --new with --lesson to repeat a tutorial.")
    sessions = trainer.store.all()
    sid = args.session
    if sid:
        state, _ = trainer.store.load(sid)
        if state["mode"] != "training":
            raise ValueError("Use 'grey run SESSION' to resume an interview.")
    else:
        pending = [
            s
            for s in sessions
            if s["mode"] == "training"
            and not s["completed_at"]
            and (not args.lesson or s["lesson"]["id"] == args.lesson)
        ]
        if pending and not args.new:
            sid = pending[-1]["id"]
        else:
            lesson_id = args.lesson or recommended_lesson(sessions)
            if not lesson_id:
                print(curriculum_progress(sessions))
                return
            state = trainer.start(mode="training", lesson_id=lesson_id)
            sid = state["id"]
            if not args.start_only:
                print(guide())
    if args.start_only:
        print(sid)
    else:
        interactive(trainer, sid)


def main(argv=None):
    load_dotenv(Path.cwd() / ".env", override=False)
    args = parser().parse_args(argv)
    try:
        home = args.home.resolve()
        config_path = home / "config.json"
        if args.command == "web":
            from .web import serve

            serve(home, args.port, open_browser=not args.no_browser)
            return
        if args.command == "guide":
            print(guide(args.lesson))
            return
        if args.command == "learn" and args.list:
            db = home / "progress.sqlite3"
            print(curriculum_progress(Store(db).all() if db.exists() else []))
            return
        if args.command == "init":
            home.mkdir(parents=True, exist_ok=True)
            if config_path.exists():
                print(f"Config already exists: {config_path}")
            else:
                config_path.write_text(Config().model_dump_json(indent=2) + "\n", encoding="utf-8")
                print(
                    f"Created {config_path}. Start with 'grey learn', or interview with 'grey run'."
                )
            return
        if not config_path.exists():
            raise ValueError("Run 'grey init' first.")
        config = Config.model_validate_json(
            config_path.read_text(encoding="utf-8-sig")
        ).with_environment()
        store = Store(home / "progress.sqlite3")
        trainer = Trainer(store, config, Provider)
        cmd = args.command
        if cmd == "doctor":
            print(f"Python {sys.version.split()[0]} | provider: {config.provider}")
            print(
                f"Model: {config.model_for('question') or 'CLI default'} | "
                f"evaluator: {config.model_for('evaluate') or 'CLI default'} | State: {home}"
            )
            print(
                f"Effort: {config.effort_for('question') or 'provider default'} | "
                f"review effort: {config.effort_for('evaluate') or 'provider default'}"
            )
            if config.provider == "openai":
                print(
                    f"OpenAI SDK {version('openai')} | OPENAI_API_KEY: "
                    f"{'present' if os.getenv('OPENAI_API_KEY') else 'missing'}"
                )
            elif config.provider == "codex":
                executable = os.getenv("GREY_CODEX_BIN") or "codex"
                resolved = shutil.which(executable)
                runtime = resolved or (
                    "missing (check GREY_CODEX_BIN)"
                    if os.getenv("GREY_CODEX_BIN")
                    else "SDK bundled runtime"
                )
                print(f"Codex SDK {version('openai-codex')} | executable: {runtime}")
                print("Login: run 'codex login status'; test with 'grey doctor --live'.")
            else:
                executable = os.getenv("GREY_CLAUDE_BIN") or "claude"
                print(f"Claude executable: {shutil.which(executable) or 'missing'}")
                print("Login: run 'claude auth status'; test with 'grey doctor --live'.")
            if args.live:
                result, meta = Provider(config).request(
                    "coach",
                    Coaching,
                    {
                        "kind": "clarify",
                        "message": "Reply with 'Connection ready'.",
                        "question": {},
                    },
                )
                print(result["reply"])
                print(f"Live response: {meta['response_id']} | {meta['model']}")
        elif cmd == "learn":
            learn(trainer, args)
        elif cmd in ("start", "run"):
            sid = getattr(args, "session", None)
            if not sid:
                sid = trainer.start(args.mode, args.tracks, args.turns)["id"]
            if cmd == "start":
                print(sid)
            else:
                interactive(trainer, sid)
        elif cmd == "sessions":
            for s in store.all():
                print(
                    f"{s['id']} | {s['mode']} | {'complete' if s['completed_at'] else 'in progress'}"
                    f" | {', '.join(s['tracks'])} | {s['created_at']}"
                )
        elif cmd == "progress":
            print(progress(store))
        elif cmd == "next":
            state, q = trainer.next(args.session, args.remediate)
            show_question(state, q)
        elif cmd == "show":
            state, _ = store.load(args.session)
            if not state["questions"]:
                raise ValueError("No question yet. Use 'next'.")
            show_question(state, state["questions"][-1])
        elif cmd == "answer":
            print(report(trainer.submit(args.session, read_answer(args.file), args.revise)))
        elif cmd == "grade":
            print(report(trainer.grade(args.session)))
        elif cmd in ("hint", "clarify", "review", "explain"):
            print(trainer.coach(args.session, cmd, args.message or ""))
        elif cmd == "finish":
            print(report(trainer.finish(args.session)))
        elif cmd in ("report", "export"):
            state, _ = store.load(args.session)
            if cmd == "report":
                print(report(state))
            else:
                transcript = export_state(state)  # Enforce mock feedback boundary for both formats.
                content = transcript if args.format == "json" else report(state)
                with args.out.open("x", encoding="utf-8") as out:
                    out.write(content + "\n")
                print(f"Exported {args.out.resolve()}")
    except (ValueError, OSError, sqlite3.Error, ProviderError, ValidationError) as exc:
        # Pydantic errors may echo input values; keep configuration failures concise.
        print(
            "Error: "
            + (
                "Invalid configuration or structured output."
                if isinstance(exc, ValidationError)
                else str(exc)
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)
    except (KeyboardInterrupt, EOFError):
        print("\nPaused. Saved answers and questions are available through 'grey sessions'.")


if __name__ == "__main__":
    main()
