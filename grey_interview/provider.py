import asyncio
import json
import logging
import os
import shutil
import subprocess
import traceback
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

from openai import OpenAI, OpenAIError
from openai_codex import ApprovalMode, AsyncCodex, CodexConfig, CodexError, Sandbox
from openai_codex.generated.v2_all import ReasoningEffort, TurnStatus
from pydantic import ValidationError

from .models import DIMENSIONS, Config, Evaluation


class ProviderError(RuntimeError):
    pass


def codex_failure_message(exc):
    """Classify known CLI failures without returning raw errors or user data."""
    detail = str(exc).lower()
    if isinstance(exc, asyncio.TimeoutError):
        return "Codex timed out. Check your connection or increase timeout_seconds in .grey/config.json."
    if any(
        token in detail
        for token in ("not logged in", "unauthorized", "401", "refresh token", "authentication")
    ):
        return "Codex login needs attention. Run 'codex login' in PowerShell, then retry."
    if any(
        token in detail
        for token in (
            "model is not supported",
            "model not found",
            "unsupported model",
            "does not support the model",
        )
    ):
        return "The local Codex CLI cannot use the selected model. Check model access and update the CLI."
    if any(token in detail for token in ("usage limit", "quota exceeded", "rate limit", "429")):
        return "Codex usage is currently limited. Check your account limits before retrying."
    if any(
        token in detail
        for token in (
            "error sending request",
            "stream disconnected",
            "connection refused",
            "dns",
            "certificate",
        )
    ):
        return (
            "Codex could not connect to its model service. Check your internet, VPN/proxy and firewall. "
            "If this server was started inside Codex, stop it and run '.\\.venv\\Scripts\\grey.exe web' "
            "from a normal PowerShell window in the project folder, then retry."
        )
    return None


class Provider:
    def __init__(self, config: Config, client=None):
        self.config = config.with_environment()
        if self.config.provider == "openai" and client is None and not os.getenv("OPENAI_API_KEY"):
            raise ProviderError(
                "Set OPENAI_API_KEY in your environment, then retry. Progress is saved."
            )
        self.client = client
        if self.config.provider == "openai" and client is None:
            self.client = OpenAI(timeout=config.timeout_seconds, max_retries=2)

    def request(self, task, schema, payload):
        prompt = files("grey_interview").joinpath(f"prompts/{task}.md").read_text(encoding="utf-8")
        model = self.config.model_for(task)
        effort = self.config.effort_for(task)
        try:
            if self.config.provider == "codex":
                parsed, metadata = asyncio.run(self._codex(prompt, schema, payload, model, effort))
            elif self.config.provider == "claude":
                parsed, metadata = self._claude(prompt, schema, payload, model, effort)
            else:
                parsed, metadata = self._openai(prompt, schema, payload, model, effort)
            if isinstance(parsed, Evaluation) and sorted(
                d.name for d in parsed.dimensions
            ) != sorted(DIMENSIONS):
                raise ProviderError(
                    "Evaluator returned duplicate/missing dimensions. Retry grading."
                )
            return parsed.model_dump(), {
                "provider": self.config.provider,
                "effort": effort,
                **metadata,
            }
        except ProviderError:
            raise
        except (
            OpenAIError,
            CodexError,
            ValidationError,
            ValueError,
            OSError,
            RuntimeError,
            asyncio.TimeoutError,
            subprocess.SubprocessError,
        ) as exc:
            # Record locations only: exception messages and source lines may contain private data.
            frames = " -> ".join(
                f"{Path(frame.filename).name}:{frame.lineno}:{frame.name}"
                for frame in traceback.extract_tb(exc.__traceback__)[-12:]
            )
            logging.getLogger(__name__).error(
                "%s %s failed (%s): %s", self.config.provider, task, type(exc).__name__, frames
            )
            if self.config.provider == "codex":
                message = codex_failure_message(exc)
                if message:
                    raise ProviderError(message + " Progress is saved.") from exc
            # Never echo SDK/CLI errors: they may contain submitted answers or credentials.
            raise ProviderError(
                f"{self.config.provider} request failed ({type(exc).__name__}). "
                "Check login, CLI version, model access, network, quota or timeout, then retry. "
                "Progress is saved."
            ) from exc

    async def _codex(self, prompt, schema, payload, model, effort):
        with TemporaryDirectory(prefix="grey-codex-") as cwd:
            client = AsyncCodex(
                CodexConfig(
                    codex_bin=os.getenv("GREY_CODEX_BIN") or shutil.which("codex"),
                    cwd=cwd,
                )
            )

            async def run():
                thread = await client.thread_start(
                    model=model,
                    cwd=cwd,
                    ephemeral=True,
                    sandbox=Sandbox.read_only,
                    approval_mode=ApprovalMode.deny_all,
                    base_instructions=prompt
                    + (
                        "\nUse only the supplied interview data. Do not use tools, read files, "
                        "run commands, or delegate work. Return only the requested JSON."
                    ),
                )
                result = await thread.run(
                    json.dumps(payload, ensure_ascii=False),
                    output_schema=schema.model_json_schema(),
                    **({"effort": ReasoningEffort(effort)} if effort else {}),
                )
                if result.status != TurnStatus.completed or not result.final_response:
                    raise ProviderError(
                        "Codex returned an incomplete response. Retry; state is safe."
                    )
                parsed = schema.model_validate_json(result.final_response)
                return parsed, {
                    "model": model or "codex-default",
                    "response_id": result.id,
                    "thread_id": thread.id,
                    "usage": result.usage.total.model_dump() if result.usage else {},
                }

            try:
                return await asyncio.wait_for(run(), timeout=self.config.timeout_seconds)
            finally:
                await client.close()

    def _claude(self, prompt, schema, payload, model, effort):
        executable = shutil.which(os.getenv("GREY_CLAUDE_BIN") or "claude")
        if not executable:
            raise ProviderError("Install Claude Code and run 'claude auth login', then retry.")
        command = [
            executable,
            "--print",
            "--output-format",
            "json",
            "--no-session-persistence",
            "--tools",
            "",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--disable-slash-commands",
            "--settings",
            '{"disableAllHooks":true}',
            "--system-prompt",
            prompt,
            "--json-schema",
            json.dumps(schema.model_json_schema()),
        ]
        if model:
            command.extend(["--model", model])
        if effort:
            command.extend(["--effort", effort])
        with TemporaryDirectory(prefix="grey-claude-") as cwd:
            result = subprocess.run(
                command,
                input=json.dumps(payload, ensure_ascii=False),
                capture_output=True,
                text=True,
                encoding="utf-8",
                cwd=cwd,
                timeout=self.config.timeout_seconds,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        response = json.loads(result.stdout)
        if (
            not isinstance(response, dict)
            or response.get("is_error")
            or response.get("subtype") != "success"
            or "structured_output" not in response
        ):
            raise ProviderError("Claude returned an incomplete response. Retry; state is safe.")
        usage = response.get("usage") or {}
        return schema.model_validate(response["structured_output"]), {
            "model": model or "claude-default",
            "response_id": response.get("session_id"),
            "usage": {
                **usage,
                "total_tokens": sum(
                    usage.get(key, 0)
                    for key in (
                        "input_tokens",
                        "output_tokens",
                        "cache_creation_input_tokens",
                        "cache_read_input_tokens",
                    )
                ),
            },
        }

    def _openai(self, prompt, schema, payload, model, effort):
        response = self.client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            text_format=schema,
            max_output_tokens=self.config.max_output_tokens,
            store=False,
            **({"reasoning": {"effort": effort}} if effort else {}),
        )
        parsed = response.output_parsed
        if response.status != "completed" or parsed is None:
            raise ProviderError(
                "Model refused or returned an incomplete response. Retry; state is safe."
            )
        return parsed, {
            "model": response.model,
            "response_id": response.id,
            "usage": response.usage.model_dump() if response.usage else {},
        }
