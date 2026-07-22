"""Authoring contract — drive an agent to write a Harbor/SkillsBench task package
from a difficulty-dense corpus seed, with NO skill in context.

Differences from skillproof's benchmark contract (codex/prompts.py), all forced by
this project's rules:
  - Output is the upstream Harbor layout (task.md / environment / oracle / verifier),
    not skillproof's benchmark.yaml layout.
  - DETERMINISTIC VERIFIER ONLY. There is no LLM judge in this format; a task that
    can't be checked with programmatic assertions doesn't ship.
  - The author sees the corpus excerpts, never any SKILL.md. The task must state
    WHAT to achieve, never HOW — and must never name or allude to a skill.
  - Difficulty is the explicit target: the seed's rationale names why its chunks
    gate on domain knowledge; the task must make the naive approach fail the tests.

The agent invocation reuses skillproof.codex.harness._run_codex verbatim (headless
`claude -p`, cwd = task dir, Bash tool, acceptEdits). Only the prompt + the output
layout + the validation gates differ, so harness.py's author→validate→repair loop
is the model to copy; this module supplies the prompts and (later) the gate calls.
"""

from __future__ import annotations

from .models import TaskSeed

CONTRACT = """\
## Output contract — create EXACTLY this Harbor task layout in the current directory

```
task.md                     # YAML frontmatter (schema_version '1.3') + prompt body
environment/
  Dockerfile                # self-contained; bake task inputs in via COPY. NO skills/.
  <input files>
oracle/
  solve.sh                  # COMPUTES the solution (never hardcodes); reaches reward 1.0
verifier/
  test.sh                   # runs pytest, writes 0|1 to /logs/verifier/reward.txt, exits 0
  test_outputs.py           # deterministic, outcome-based assertions
provenance.yaml             # domain, origin: authored, corpus_refs: {chunk_ids}
```

### task.md
Strict upstream schema 1.3. Frontmatter fields: `schema_version: '1.3'`;
`metadata` (author_name, author_email, difficulty [easy|medium|hard],
difficulty_explanation, category, subcategory, category_confidence,
task_type[], modality[], interface[], skill_type[], tags[]); `verifier`
(type: test-script, timeout_sec); `agent` (timeout_sec); `environment`
(network_mode: no-network unless the task truly needs the network, build_timeout_sec,
os: linux, cpus, memory_mb, storage_mb, gpus: 0). Then the prompt body — exactly
what the agent under test sees.

### verifier (deterministic ONLY)
- `verifier/test.sh`: `mkdir -p /logs/verifier`, run `pytest /verifier/test_outputs.py`,
  write `1` to `/logs/verifier/reward.txt` on pass else `0`, and ALWAYS `exit 0`
  (the reward file is the verdict).
- The sandbox is **OFFLINE**. Use ONLY packages preinstalled in the image (listed in
  the inventory below); pytest/numpy/pandas/pypdf/pyyaml/etc. are present. Any
  `pip install` must be non-fatal (`... || true`) — it cannot reach the network.
- Mount points available in the container: `/verifier`, `/oracle`, `/logs/verifier`,
  and the working dir `/workspace`.
- `verifier/test_outputs.py`: 4-10 focused, deterministic assertions on the produced
  artifacts. EXECUTE the artifacts and assert on what they produce; never grep the
  solution's source. Property-based checks over byte-exact when several outputs are
  correct. Numeric tolerances where appropriate. NO LLM judging, no network, no clock,
  no ordering dependence — same workspace in, same reward out.

### oracle/solve.sh
Runs in the built environment and COMPUTES the solution from the task inputs
(hardcoded answers are rejected). Running it then the verifier must yield reward 1.0.

## Difficulty is the target (why this task exists)
The corpus excerpts below were selected because they gate on specific domain
knowledge a strong model does NOT apply by default:
    {rationale}
Design the task so the obvious/naive attempt FAILS a deterministic check — encode the
exact value, non-default procedure, convention, or edge case the excerpts describe as
a hard verifier assertion. A base model with no domain knowledge should fail; a model
that knows this slice of the domain should pass.

## Anti-leakage / fairness (hard rules)
- The prompt states WHAT to achieve, never HOW. Do not restate the excerpts' method,
  values, or step order in the prompt — that gap is what the benchmark measures.
- Never name a skill, never assume a specific tool/script only one packaging provides.
  The verifier judges outcomes, not toolchains.
- No `environment/skills/` — skills are injected by the run harness per arm.
- Baseline must fail: the verifier on the untouched environment must yield reward 0.
"""


def authoring_prompt(seed: TaskSeed, domain_title: str, packages_note: str = "") -> str:
    excerpts = "\n\n---\n\n".join(
        f"[corpus chunk {cid}]\n{text}" for cid, text in zip(seed.chunk_ids, seed.excerpts)
    )
    contract = CONTRACT.format(rationale=seed.rationale, chunk_ids=seed.chunk_ids)
    return f"""\
You are authoring ONE deterministic Harbor task in the domain "{domain_title}".
You have NO access to any "skill" — author only from the corpus excerpts below.

# Domain corpus excerpts (the knowledge this task should gate on)
<corpus_excerpts>
{excerpts}
</corpus_excerpts>

{contract}

{packages_note}

Work step by step: design a task whose naive solution fails; build the environment
and inputs; write the deterministic verifier; write oracle/solve.sh and confirm it
reaches reward 1.0 while the untouched environment reaches reward 0; then write
provenance.yaml and task.md. Create all files in the CURRENT directory.
"""


def harden_prompt(base_transcript_summary: str) -> str:
    """Adversarial repair: the headroom probe's base agent SOLVED the task unaided.
    Tighten the task so that path fails — capability-framed, never skill-framed."""
    return f"""\
The headroom probe ran a base agent (no skill) on your task and it PASSED — the task
is too easy, so it can't measure skill uplift. Here is how the base agent solved it:

{base_transcript_summary}

Tighten the task IN PLACE so that exact path no longer earns reward 1.0, while your
oracle still does. Prefer: demand the precise value/convention/edge-case the base
agent guessed or skipped; add a deterministic assertion the naive output fails; remove
any hint in the prompt that revealed the approach. Do NOT make it merely longer or
add unrelated capability difficulty — the goal is knowledge-gated hardness, not raw
hardness. Keep the same task id and layout. Re-verify oracle=1.0, baseline=0 locally.
"""


def repair_prompt(validation_report: str) -> str:
    return f"""\
Your task FAILED automated validation. Fix it IN PLACE, keeping the same id/layout.

# Validation failures
{validation_report}

# Reminders
- oracle check: running oracle/solve.sh then the verifier must yield reward 1.0.
- baseline check: the untouched environment must yield reward 0.
- determinism: two identical verifier runs must agree.
- verifier is deterministic and offline; no LLM judge exists in this format.
Re-verify locally before finishing.
"""
