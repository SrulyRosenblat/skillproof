"""Configuration: skillproof.yaml merged with environment (secrets only via env)."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    provider: str = "openrouter"  # "openrouter" | "openai" | "local"
    model: str = "google/gemini-embedding-2"


class ClusteringConfig(BaseModel):
    k_benchmarks: int = 5
    k_range: tuple[int, int] = (2, 10)
    min_chunk_tokens: int = 150
    max_chunk_tokens: int = 1500


class CodexConfig(BaseModel):
    """Benchmark-authoring agent. backend 'codex' (OpenAI Codex CLI) or 'claude'
    (Claude Code CLI, headless)."""

    backend: str = "codex"  # codex | claude
    binary: str = "codex"  # path/name of the codex CLI
    claude_binary: str = "claude"  # path/name of the claude CLI
    model: str | None = None  # None -> backend default (claude backend: sonnet)
    max_attempts: int = 3
    timeout_seconds: int = 900


class SandboxConfig(BaseModel):
    image: str = "skillproof-sandbox:latest"
    dockerfile_dir: str = "docker"  # auto-rebuild source if the image goes missing
    mem_limit: str = "2g"
    cpus: float = 2.0
    pids_limit: int = 256
    output_limit_bytes: int = 50_000


class JudgeConfig(BaseModel):
    """LLM judge panel for grader yes/no questions (vision-capable, via OpenRouter).

    Each model in the panel answers every question once; majority vote decides.
    Diverse families reduce correlated blind spots.
    """

    models: list[str] = Field(
        default_factory=lambda: [
            "openai/gpt-5-nano",
            "google/gemini-2.5-flash-lite",
            "qwen/qwen3-vl-30b-a3b-instruct",
        ]
    )
    max_questions: int = 10  # per grading run


class ProviderPin(BaseModel):
    order: list[str] = Field(default_factory=list)
    allow_fallbacks: bool = True


class EvalConfig(BaseModel):
    models: list[str] = Field(default_factory=lambda: ["openai/gpt-4.1-mini"])
    trials: int = 3
    max_turns: int = 30
    agent_wall_seconds: int = 600
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 8192
    api_retries: int = 5
    error_policy: str = "fail"  # "fail" | "exclude"
    provider: ProviderPin | None = None
    parallel: int = 1


class Config(BaseModel):
    seed: int = 42
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    clustering: ClusteringConfig = Field(default_factory=ClusteringConfig)
    codex: CodexConfig = Field(default_factory=CodexConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    judge: JudgeConfig = Field(default_factory=JudgeConfig)
    eval: EvalConfig = Field(default_factory=EvalConfig)
    benchmarks_dir: Path = Path("benchmarks")
    results_dir: Path = Path("results")

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Config":
        """Load YAML config; also loads .env from cwd for API keys."""
        load_dotenv()
        p = Path(path) if path else Path("skillproof.yaml")
        if p.is_file():
            data = yaml.safe_load(p.read_text()) or {}
            return cls.model_validate(data)
        if path and str(path) != "skillproof.yaml":
            raise FileNotFoundError(f"config file not found: {p}")
        return cls()

    # ----- secrets (env only, never in YAML) -----

    @staticmethod
    def openrouter_api_key() -> str:
        key = os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set (env or .env). Required to run evaluations."
            )
        return key

    @staticmethod
    def openai_api_key() -> str:
        key = os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set (env or .env). Required for the 'openai' "
                "embedding provider; alternatively set embedding.provider: local "
                "(requires `pip install skillproof[local-embeddings]`)."
            )
        return key
