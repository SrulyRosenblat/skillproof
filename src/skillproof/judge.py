"""Host-side LLM judge for grader yes/no questions.

Graders run offline in Docker. When a check can't be verified deterministically
(visual rendering, reading order, layout), the grader writes strictly-binary
questions to /workspace/.judge/questions.json and exits with code 3. The harness
answers them here — outside the sandbox, so no network or API key ever enters the
container — writes /workspace/.judge/answers.json back, and re-runs the grader.

Question format (list under key "questions"):
    {"id": "q1", "question": "...? ", "image": "/workspace/out/page1.png"}  # or
    {"id": "q2", "question": "...?", "text": "content to judge"}

Answer format written back: {"answers": {"q1": true, "q2": false}}
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field

from openai import OpenAI

from .config import Config, JudgeConfig

QUESTIONS_PATH = "/workspace/.judge/questions.json"
ANSWERS_PATH = "/workspace/.judge/answers.json"
JUDGE_EXIT_CODE = 3

_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".gif": "image/gif", ".webp": "image/webp"}

_SYSTEM = (
    "You are a strict, literal grading judge. You will be asked a single yes/no "
    "question about the provided content. Judge exactly what is asked — no "
    "leniency, no inferring intent. If the question contains multiple conditions, "
    "answer YES only if EVERY condition is fully met; if any condition is not met, "
    "is only partially met, or cannot be verified from the provided content, answer "
    "NO. When in doubt, answer NO. Reply with exactly one word: YES or NO."
)


@dataclass
class JudgeRecord:
    id: str
    question: str
    answer: bool
    votes: dict[str, str] = field(default_factory=dict)  # model -> YES/NO/ERROR


class JudgeError(RuntimeError):
    pass


def _image_part(sandbox, path: str) -> dict:
    ext = "." + path.rsplit(".", 1)[-1].lower()
    mime = _MIME.get(ext)
    if not mime:
        raise JudgeError(f"unsupported judge image type: {path}")
    data = sandbox.get_file(path)
    if len(data) > 8_000_000:
        raise JudgeError(f"judge image too large ({len(data)} bytes): {path}")
    b64 = base64.b64encode(data).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


def answer_questions(sandbox, cfg: JudgeConfig) -> list[JudgeRecord]:
    """Read questions from the sandbox, answer via the judge model, write answers back."""
    raw = json.loads(sandbox.get_file(QUESTIONS_PATH).decode("utf-8"))
    questions = raw.get("questions", [])
    if not questions:
        raise JudgeError(".judge/questions.json contains no questions")
    if len(questions) > cfg.max_questions:
        raise JudgeError(
            f"grader asked {len(questions)} judge questions (max {cfg.max_questions})"
        )

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=Config.openrouter_api_key(),
        timeout=120.0,
    )

    records: list[JudgeRecord] = []
    for q in questions:
        qid, question = str(q["id"]), str(q["question"])
        content: list[dict] = [{"type": "text", "text": question}]
        if q.get("image"):
            content.append(_image_part(sandbox, str(q["image"])))
        if q.get("text"):
            content[0]["text"] += "\n\n<content>\n" + str(q["text"])[:20_000] + "\n</content>"

        votes: dict[str, str] = {}
        for model in cfg.models:
            messages = [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": content},
            ]
            try:
                try:
                    resp = client.chat.completions.create(
                        model=model, messages=messages, temperature=0.0, max_tokens=2000
                    )
                except Exception as e:
                    if "temperature" not in str(e).lower():
                        raise
                    # reasoning models that only accept default temperature
                    resp = client.chat.completions.create(
                        model=model, messages=messages, max_tokens=2000
                    )
                text = (resp.choices[0].message.content or "").strip().upper()
                first = text.split()[0].strip(".,!:;") if text.split() else ""
                votes[model] = "YES" if first == "YES" else "NO"
            except Exception as e:  # one flaky panelist must not sink the panel
                votes[model] = f"ERROR: {str(e)[:120]}"
        cast = [v for v in votes.values() if v in ("YES", "NO")]
        if not cast:
            raise JudgeError(f"all judge models errored for question {qid}: {votes}")
        answer = cast.count("YES") > len(cast) / 2
        records.append(JudgeRecord(id=qid, question=question, answer=answer, votes=votes))

    payload = json.dumps({"answers": {r.id: r.answer for r in records}}).encode()
    sandbox.put_file(ANSWERS_PATH, payload)
    return records
