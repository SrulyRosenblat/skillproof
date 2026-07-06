"""Embedding provider abstraction: OpenAI API (default) or local sentence-transformers."""

from __future__ import annotations

import time
from typing import Protocol

import numpy as np

from .config import Config


class EmbeddingProvider(Protocol):
    name: str
    model: str

    def embed(self, texts: list[str]) -> np.ndarray: ...


def _l2_normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


class OpenAIEmbeddings:
    name = "openai"

    def __init__(self, model: str, api_key: str, base_url: str | None = None):
        from openai import OpenAI

        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors: list[list[float]] = []
        batch_size = 128
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = self._client.embeddings.create(model=self.model, input=batch)
            vectors.extend(item.embedding for item in resp.data)
        return _l2_normalize(np.asarray(vectors, dtype=np.float64))


class LocalEmbeddings:
    name = "local"

    def __init__(self, model: str):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise RuntimeError(
                "Local embeddings require: pip install 'skillproof[local-embeddings]'"
            ) from e
        self.model = model
        self._model = SentenceTransformer(model)

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return _l2_normalize(np.asarray(vectors, dtype=np.float64))


class OpenRouterEmbeddings:
    """OpenRouter's /embeddings endpoint via raw HTTP.

    Deliberately not the OpenAI SDK: the SDK always sends encoding_format=base64,
    which some OpenRouter providers (e.g. google/gemini-embedding-2) reject with
    "No embedding data received".
    """

    name = "openrouter"

    def __init__(self, model: str, api_key: str):
        import httpx

        self.model = model
        self._client = httpx.Client(
            base_url="https://openrouter.ai/api/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120.0,
        )

    def embed(self, texts: list[str]) -> np.ndarray:
        # One text per request: batched requests can route to providers blocked by
        # the account's data policy (observed with google/gemini-embedding-2).
        vectors = [self._embed_one(t) for t in texts]
        return _l2_normalize(np.asarray(vectors, dtype=np.float64))

    def _embed_one(self, text: str) -> list[float]:
        last_err: Exception | None = None
        for attempt in range(4):
            resp = self._client.post(
                "/embeddings", json={"model": self.model, "input": [text]}
            )
            data = resp.json() if resp.headers.get("content-type", "").startswith(
                "application/json"
            ) else {}
            if resp.status_code == 200 and data.get("data"):
                return data["data"][0]["embedding"]
            last_err = RuntimeError(
                f"OpenRouter embeddings error (HTTP {resp.status_code}): "
                f"{str(data)[:300]}"
            )
            time.sleep(1.5 * (attempt + 1))
        raise last_err  # type: ignore[misc]


def get_provider(cfg: Config) -> EmbeddingProvider:
    if cfg.embedding.provider == "openrouter":
        return OpenRouterEmbeddings(cfg.embedding.model, Config.openrouter_api_key())
    if cfg.embedding.provider == "openai":
        return OpenAIEmbeddings(cfg.embedding.model, Config.openai_api_key())
    if cfg.embedding.provider == "local":
        model = cfg.embedding.model
        if model.startswith("text-embedding"):  # openai default doesn't apply locally
            model = "all-MiniLM-L6-v2"
        return LocalEmbeddings(model)
    raise ValueError(f"Unknown embedding provider: {cfg.embedding.provider}")
