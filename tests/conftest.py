import pytest


@pytest.fixture(autouse=True)
def isolate_provider_environment(monkeypatch, tmp_path):
    for name in (
        "GREY_LLM_PROVIDER",
        "GREY_LLM_MODEL",
        "GREY_LLM_EVALUATOR_MODEL",
        "GREY_LLM_EFFORT",
        "GREY_LLM_EVALUATOR_EFFORT",
        "GREY_CODEX_BIN",
        "GREY_CLAUDE_BIN",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)  # Never load the developer's .env during CLI tests.
