"""Minimal model-agnostic agent loop over OpenRouter's OpenAI-compatible API.

The model gets bash/write_file/read_file tools that execute inside the Docker
sandbox. Arm A ("with_skill") injects the skill text into the system prompt and
mounts the skill's scripts at /skill; arm B runs bare.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from openai import APIError, APITimeoutError, OpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from ..config import Config
from ..models import Skill
from ..sandbox.container import SKILL_MOUNT, Sandbox
from .tools import TOOL_SCHEMAS, dispatch
from .transcript import Transcript

SYSTEM_PREAMBLE = """\
You are an autonomous coding agent working in a Linux sandbox. Your working
directory is /workspace; input files (if any) are already there. You have no
network access and no human to ask — complete the task fully on your own.

Use the provided tools to inspect files, write code, and run commands. Verify your
work before finishing (e.g., run your code, check output files exist and are valid).
When the task is complete, reply with a short summary WITHOUT calling any tools —
that ends the session. Only the final file state of /workspace is evaluated.
"""

SKILL_BLOCK_TEMPLATE = """

A skill has been invoked for this task. Its instructions follow; apply them
wherever relevant.

<skill name="{name}" description="{description}">
{skill_md}
</skill>

The skill's supporting files are available read-only at {mount}:
{file_listing}

When the skill instructions point to a reference document or script, read or run
it from {mount} (e.g. read_file {mount}/REFERENCE.md, or bash `python3
{mount}/scripts/tool.py`) instead of guessing its contents.
"""


@dataclass
class AgentOutcome:
    turns_used: int
    stop_reason: str  # "completed" | "max_turns" | "wall_clock" | "api_error"
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float | None = None
    error: str | None = None
    skill_files_read: list[str] | None = None


def build_skill_injection(skill: Skill) -> str:
    """Claude Code-style invocation: SKILL.md body enters context; reference files
    and scripts stay on disk at /skill for the agent to read on demand."""
    listed = sorted(
        list(skill.reference_files) + skill.script_files + skill.asset_files
    )
    file_listing = "\n".join(f"- {SKILL_MOUNT}/{p}" for p in listed) or "(none)"
    return SKILL_BLOCK_TEMPLATE.format(
        mount=SKILL_MOUNT,
        name=skill.name,
        description=skill.description.replace('"', "'"),
        skill_md=skill.skill_md,
        file_listing=file_listing,
    )


def mount_skill(sandbox: Sandbox, skill: Skill) -> None:
    """Copy the skill folder (scripts/assets included) read-only into /skill."""
    sandbox.put_dir(skill.path, SKILL_MOUNT)


def _make_client(cfg: Config) -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=Config.openrouter_api_key(),
        timeout=180.0,
    )


def _truncate_old_tool_results(messages: list[dict], keep_last: int = 6) -> None:
    """On context overflow, replace old tool results with a stub in place."""
    tool_indices = [i for i, m in enumerate(messages) if m.get("role") == "tool"]
    for i in tool_indices[:-keep_last]:
        if len(messages[i].get("content") or "") > 200:
            messages[i]["content"] = "[tool output elided to fit context]"


def run_agent(
    task_prompt: str,
    skill: Skill | None,
    sandbox: Sandbox,
    model: str,
    cfg: Config,
    transcript: Transcript,
) -> AgentOutcome:
    client = _make_client(cfg)

    system = SYSTEM_PREAMBLE
    if skill is not None:
        system += build_skill_injection(skill)
        mount_skill(sandbox, skill)

    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user", "content": task_prompt},
    ]
    transcript.event("meta", model=model, arm="with_skill" if skill else "without_skill",
                     temperature=cfg.eval.temperature, seed=cfg.seed)

    # usage.include=true makes OpenRouter attach the credit cost to each response
    extra_body: dict = {"usage": {"include": True}}
    if cfg.eval.provider and cfg.eval.provider.order:
        extra_body["provider"] = {
            "order": cfg.eval.provider.order,
            "allow_fallbacks": cfg.eval.provider.allow_fallbacks,
        }

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
        stop=stop_after_attempt(cfg.eval.api_retries),
        wait=wait_exponential_jitter(initial=2, max=60),
        reraise=True,
    )
    def _call():
        return client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            temperature=cfg.eval.temperature,
            top_p=cfg.eval.top_p,
            seed=cfg.seed,
            max_tokens=cfg.eval.max_tokens,
            extra_body=extra_body,
        )

    tokens_in = tokens_out = 0
    cost_usd: float | None = None
    skill_accesses: set[str] = set()
    started = time.monotonic()

    def _outcome(turns: int, reason: str, error: str | None = None) -> AgentOutcome:
        reads = sorted(skill_accesses) if skill is not None else None
        if reads is not None:
            transcript.event("skill_files_read", files=reads)
        return AgentOutcome(turns, reason, tokens_in, tokens_out, cost_usd, error, reads)

    for turn in range(1, cfg.eval.max_turns + 1):
        if time.monotonic() - started > cfg.eval.agent_wall_seconds:
            transcript.event("stop", reason="wall_clock", turn=turn)
            return _outcome(turn - 1, "wall_clock")

        try:
            resp = _call()
        except Exception as e:
            msg = str(e)
            if "context" in msg.lower() and "length" in msg.lower():
                _truncate_old_tool_results(messages)
                try:
                    resp = _call()
                except Exception as e2:
                    transcript.event("stop", reason="api_error", error=str(e2), turn=turn)
                    return _outcome(turn - 1, "api_error", str(e2))
            else:
                transcript.event("stop", reason="api_error", error=msg, turn=turn)
                return _outcome(turn - 1, "api_error", msg)

        if resp.usage:
            tokens_in += resp.usage.prompt_tokens or 0
            tokens_out += resp.usage.completion_tokens or 0
            # OpenRouter extension field (requested via usage.include)
            turn_cost = getattr(resp.usage, "cost", None)
            if turn_cost is None and getattr(resp.usage, "model_extra", None):
                turn_cost = resp.usage.model_extra.get("cost")
            if turn_cost is not None:
                cost_usd = (cost_usd or 0.0) + float(turn_cost)

        choice = resp.choices[0]
        assistant = choice.message
        transcript.event(
            "assistant",
            turn=turn,
            content=assistant.content,
            tool_calls=[
                {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}
                for tc in (assistant.tool_calls or [])
            ],
            finish_reason=choice.finish_reason,
        )

        if not assistant.tool_calls:
            transcript.event("stop", reason="completed", turn=turn)
            return _outcome(turn, "completed")

        messages.append(
            {
                "role": "assistant",
                "content": assistant.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant.tool_calls
                ],
            }
        )
        for tc in assistant.tool_calls:
            result = dispatch(tc.function.name, tc.function.arguments, sandbox,
                              skill_accesses if skill is not None else None)
            transcript.event("tool_result", turn=turn, tool=tc.function.name,
                             call_id=tc.id, result=result[:20_000])
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    transcript.event("stop", reason="max_turns", turn=cfg.eval.max_turns)
    return _outcome(cfg.eval.max_turns, "max_turns")
