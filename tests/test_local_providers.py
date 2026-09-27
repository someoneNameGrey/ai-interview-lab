import asyncio
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import create_autospec

import pytest
from openai_codex import ApprovalMode, AsyncCodex, AsyncThread, Sandbox
from openai_codex.generated.v2_all import TurnStatus
from pydantic import ValidationError
from test_trainer import evaluation

from grey_interview import cli, provider
from grey_interview.models import Coaching, Config, Evaluation
from grey_interview.provider import Provider, ProviderError
from grey_interview.store import Store


@pytest.fixture
def codex(monkeypatch):
    client = create_autospec(AsyncCodex, instance=True)
    thread = create_autospec(AsyncThread, instance=True)
    thread.id = "thread-test"
    client.thread_start.return_value = thread
    thread.run.return_value = SimpleNamespace(
        status=TurnStatus.completed,
        final_response='{"reply":"Ready"}',
        id="turn-test",
        usage=None,
    )
    factory = create_autospec(AsyncCodex, return_value=client)
    monkeypatch.setattr(provider, "AsyncCodex", factory)
    monkeypatch.setattr(provider.shutil, "which", lambda _: "/local/codex")
    return SimpleNamespace(client=client, thread=thread, factory=factory)


def test_codex_sdk_contract_and_cleanup(codex, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GREY_CODEX_BIN", "/custom/codex")
    result, meta = Provider(Config(model="question-model")).request(
        "coach",
        Coaching,
        {"message": "Hello 世界"},
    )
    assert result == {"reply": "Ready"}
    assert meta["provider"] == "codex"
    assert meta["response_id"] == "turn-test"
    assert meta["model"] == "question-model"
    launch = codex.factory.call_args.args[0]
    assert launch.codex_bin == "/custom/codex"
    assert not Path(launch.cwd).exists()
    start = codex.client.thread_start.call_args.kwargs
    assert start["sandbox"] == Sandbox.read_only
    assert start["approval_mode"] == ApprovalMode.deny_all
    assert start["ephemeral"] is True
    assert start["model"] == "question-model"
    assert json.loads(codex.thread.run.call_args.args[0]) == {"message": "Hello 世界"}
    assert codex.thread.run.call_args.kwargs["output_schema"] == Coaching.model_json_schema()
    codex.client.close.assert_awaited_once()


def test_codex_evaluator_and_usage(codex):
    codex.thread.run.return_value.final_response = json.dumps(evaluation())
    codex.thread.run.return_value.usage = SimpleNamespace(
        total=SimpleNamespace(model_dump=lambda: {"total_tokens": 123}),
    )
    _, meta = Provider(Config(model="questions", evaluator_model="reviews")).request(
        "evaluate",
        Evaluation,
        {},
    )
    assert codex.client.thread_start.call_args.kwargs["model"] == "reviews"
    assert meta["usage"]["total_tokens"] == 123


@pytest.mark.parametrize("mode", ["failed", "empty", "invalid", "exception", "duplicate"])
def test_codex_failed_output_is_safe_and_closed(codex, mode):
    schema = Coaching
    if mode == "failed":
        codex.thread.run.return_value.status = TurnStatus.failed
    elif mode == "empty":
        codex.thread.run.return_value.final_response = None
    elif mode == "invalid":
        codex.thread.run.return_value.final_response = '{"PRIVATE":1}'
    elif mode == "exception":
        codex.thread.run.side_effect = RuntimeError("PRIVATE")
    else:
        schema = Evaluation
        data = evaluation()
        data["dimensions"][1]["name"] = data["dimensions"][0]["name"]
        codex.thread.run.return_value.final_response = json.dumps(data)
    with pytest.raises(ProviderError) as error:
        Provider(Config()).request("evaluate" if mode == "duplicate" else "coach", schema, {})
    assert "PRIVATE" not in str(error.value)
    codex.client.close.assert_awaited_once()


def test_codex_timeout_closes_client(codex, monkeypatch):
    original_wait = asyncio.wait_for

    async def short_wait(awaitable, timeout):
        assert timeout == 90
        return await original_wait(awaitable, timeout=0.01)

    async def slow_run(*args, **kwargs):
        await asyncio.sleep(10)

    monkeypatch.setattr(provider.asyncio, "wait_for", short_wait)
    codex.thread.run.side_effect = slow_run
    with pytest.raises(ProviderError, match="Codex timed out"):
        Provider(Config()).request("coach", Coaching, {})
    codex.client.close.assert_awaited_once()


def test_claude_structured_output_and_model(monkeypatch):
    calls = []
    monkeypatch.setattr(provider.shutil, "which", lambda _: "/local/claude")

    def run(command, **kwargs):
        calls.append((command, kwargs))
        assert Path(kwargs["cwd"]).is_dir()
        return SimpleNamespace(
            stdout=json.dumps(
                {
                    "subtype": "success",
                    "is_error": False,
                    "session_id": "claude-test",
                    "structured_output": evaluation(),
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 20,
                        "cache_read_input_tokens": 5,
                    },
                }
            )
        )

    monkeypatch.setattr(provider.subprocess, "run", run)
    result, meta = Provider(
        Config(provider="claude", model="sonnet", evaluator_model="opus")
    ).request(
        "evaluate",
        Evaluation,
        {"answer": "Private answer"},
    )
    command, options = calls[0]
    assert result == evaluation()
    assert command[command.index("--model") + 1] == "opus"
    assert command[command.index("--tools") + 1] == ""
    assert json.loads(command[command.index("--json-schema") + 1]) == Evaluation.model_json_schema()
    assert "Private answer" not in " ".join(command)
    assert json.loads(options["input"]) == {"answer": "Private answer"}
    assert options["timeout"] == 90
    assert not Path(options["cwd"]).exists()
    assert meta["usage"]["total_tokens"] == 35
    assert meta["provider"] == "claude"


@pytest.mark.parametrize(
    "output",
    [
        "not json",
        "[]",
        '{"is_error":true,"result":"PRIVATE"}',
        '{"subtype":"error_max_turns"}',
        '{"subtype":"success","structured_output":{}}',
    ],
)
def test_claude_rejects_bad_output(monkeypatch, output):
    monkeypatch.setattr(provider.shutil, "which", lambda _: "/local/claude")
    monkeypatch.setattr(provider.subprocess, "run", lambda *a, **kw: SimpleNamespace(stdout=output))
    with pytest.raises(ProviderError) as error:
        Provider(Config(provider="claude")).request("coach", Coaching, {})
    assert "PRIVATE" not in str(error.value)


@pytest.mark.parametrize(
    "error",
    [
        subprocess.TimeoutExpired("claude", 90, stderr="PRIVATE"),
        subprocess.CalledProcessError(1, "claude", stderr="PRIVATE"),
    ],
)
def test_claude_process_failure(monkeypatch, error):
    monkeypatch.setattr(provider.shutil, "which", lambda _: "/local/claude")

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(provider.subprocess, "run", fail)
    with pytest.raises(ProviderError) as caught:
        Provider(Config(provider="claude")).request("coach", Coaching, {})
    assert "PRIVATE" not in str(caught.value)


def test_claude_missing_executable(monkeypatch):
    monkeypatch.setattr(provider.shutil, "which", lambda _: None)
    with pytest.raises(ProviderError, match="Install Claude Code"):
        Provider(Config(provider="claude")).request("coach", Coaching, {})


def test_environment_switch_clears_incompatible_saved_models(monkeypatch):
    config = Config(model="gpt-example", evaluator_model="gpt-review")
    monkeypatch.setenv("GREY_LLM_PROVIDER", "claude")
    resolved = config.with_environment()
    assert resolved.provider == "claude"
    assert resolved.model_for("question") is None
    assert resolved.model_for("evaluate") is None
    monkeypatch.setenv("GREY_LLM_MODEL", "sonnet")
    assert config.with_environment().model_for("evaluate") == "sonnet"
    monkeypatch.setenv("GREY_LLM_EVALUATOR_MODEL", "opus")
    assert config.with_environment().model_for("evaluate") == "opus"
    monkeypatch.setenv("GREY_LLM_PROVIDER", "invalid")
    with pytest.raises(ValidationError):
        config.with_environment()


def test_cli_dotenv_precedence_and_snapshot(tmp_path, monkeypatch, capsys):
    (tmp_path / ".env").write_text(
        "GREY_LLM_PROVIDER=claude\nGREY_LLM_MODEL=sonnet\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GREY_LLM_MODEL", "opus")
    base = ["--home", str(tmp_path / "state")]
    cli.main(base + ["init"])
    capsys.readouterr()
    cli.main(base + ["start", "--tracks", "coding"])
    sid = capsys.readouterr().out.strip()
    state, _ = Store(tmp_path / "state" / "progress.sqlite3").load(sid)
    assert state["config"]["provider"] == "claude"
    assert state["config"]["model"] == "opus"
    # A resumed session can explicitly select a different model without losing state.
    monkeypatch.setenv("GREY_LLM_MODEL", "sonnet")
    assert Provider(Config.model_validate(state["config"])).config.model == "sonnet"


@pytest.mark.parametrize("backend", ["codex", "claude", "openai"])
def test_doctor_offline_reports_selected_provider(tmp_path, monkeypatch, capsys, backend):
    monkeypatch.setenv("GREY_LLM_PROVIDER", backend)
    monkeypatch.setenv("GREY_LLM_MODEL", "selected-model")
    base = ["--home", str(tmp_path)]
    cli.main(base + ["init"])
    cli.main(base + ["doctor"])
    output = capsys.readouterr().out
    assert f"provider: {backend}" in output
    assert "selected-model" in output


@pytest.mark.parametrize(
    "task,expected", [("coach", "medium"), ("question", "medium"), ("evaluate", "high")]
)
def test_codex_effort_routing(codex, task, expected):
    _, meta = Provider(Config(effort="medium", evaluator_effort="high")).request(task, Coaching, {})
    assert codex.thread.run.call_args.kwargs["effort"].value == expected
    assert meta["effort"] == expected


def test_codex_default_effort_is_omitted(codex):
    _, meta = Provider(Config()).request("coach", Coaching, {})
    assert "effort" not in codex.thread.run.call_args.kwargs
    assert meta["effort"] is None


@pytest.mark.parametrize(
    "task,effort,expected",
    [
        ("coach", "medium", "medium"),
        ("evaluate", "medium", "high"),
        ("coach", None, None),
    ],
)
def test_claude_effort_routing(monkeypatch, task, effort, expected):
    calls = []
    monkeypatch.setattr(provider.shutil, "which", lambda _: "/local/claude")

    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(
            stdout=json.dumps(
                {
                    "subtype": "success",
                    "structured_output": {"reply": "Ready"},
                }
            )
        )

    monkeypatch.setattr(provider.subprocess, "run", run)
    _, meta = Provider(Config(provider="claude", effort=effort, evaluator_effort="high")).request(
        task,
        Coaching,
        {},
    )
    if expected:
        assert calls[0][calls[0].index("--effort") + 1] == expected
    else:
        assert "--effort" not in calls[0]
    assert meta["effort"] == expected


def test_effort_environment_overrides(monkeypatch):
    config = Config(effort="low", evaluator_effort="high")
    assert config.effort_for("evaluate") == "high"
    monkeypatch.setenv("GREY_LLM_EFFORT", " medium ")
    resolved = config.with_environment()
    assert resolved.effort_for("coach") == "medium"
    assert resolved.effort_for("evaluate") == "medium"
    monkeypatch.setenv("GREY_LLM_EVALUATOR_EFFORT", "xhigh")
    assert config.with_environment().effort_for("evaluate") == "xhigh"
    monkeypatch.setenv("GREY_LLM_EFFORT", "invalid")
    with pytest.raises(ValidationError):
        config.with_environment()


def test_provider_switch_clears_saved_efforts(monkeypatch):
    monkeypatch.setenv("GREY_LLM_PROVIDER", "claude")
    resolved = Config(effort="ultra", evaluator_effort="minimal").with_environment()
    assert resolved.effort_for("coach") is None
    assert resolved.effort_for("evaluate") is None


def test_tutor_model_and_effort_overrides_do_not_change_interviews(monkeypatch, codex):
    monkeypatch.setenv("GREY_LLM_MODEL", "gpt-5.6-sol")
    monkeypatch.setenv("GREY_LLM_EVALUATOR_MODEL", "gpt-5.6-sol")
    monkeypatch.setenv("GREY_LLM_EFFORT", "high")
    monkeypatch.setenv("GREY_LLM_EVALUATOR_EFFORT", "high")
    monkeypatch.setenv("GREY_LLM_TUTOR_MODEL", "gpt-5.6-luna")
    monkeypatch.setenv("GREY_LLM_TUTOR_EFFORT", "max")
    config = Config().with_environment()
    for task in ("question", "evaluate"):
        assert config.model_for(task) == "gpt-5.6-sol"
        assert config.effort_for(task) == "high"
    for task in ("tutor", "coach"):
        Provider(config).request(task, Coaching, {"message": "Hello"})
        assert codex.client.thread_start.call_args.kwargs["model"] == "gpt-5.6-luna"
        assert codex.thread.run.call_args.kwargs["effort"].value == "max"


def test_recursion_diagnostics_do_not_log_private_values(codex, caplog):
    codex.thread.run.side_effect = RecursionError("PRIVATE QUESTION OR CREDENTIAL")
    with pytest.raises(ProviderError, match="RecursionError"):
        Provider(Config()).request("tutor", Coaching, {"message": "PRIVATE QUESTION"})
    assert "RecursionError" in caplog.text
    assert "provider.py" in caplog.text
    assert "PRIVATE" not in caplog.text
    codex.client.close.assert_awaited_once()


@pytest.mark.parametrize(
    "detail,expected",
    [
        (
            "stream disconnected before completion: error sending request for url PRIVATE",
            "could not connect",
        ),
        ("401 unauthorized PRIVATE", "login needs attention"),
        ("unsupported model PRIVATE", "cannot use the selected model"),
        ("quota exceeded PRIVATE", "usage is currently limited"),
    ],
)
def test_codex_errors_provide_safe_actionable_reason(codex, detail, expected):
    codex.thread.run.side_effect = RuntimeError(detail)
    with pytest.raises(ProviderError, match=expected) as error:
        Provider(Config()).request("tutor", Coaching, {"message": "PRIVATE"})
    assert "PRIVATE" not in str(error.value)
