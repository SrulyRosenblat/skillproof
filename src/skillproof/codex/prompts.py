"""Prompt templates for driving Codex to author benchmarks."""

from __future__ import annotations

from pathlib import Path

from ..models import Chunk, Cluster, Skill

_PACKAGES_FILE = Path(__file__).resolve().parents[3] / "docker" / "packages.txt"


def _sandbox_packages() -> str:
    # repo layout: <root>/docker/packages.txt ; fall back gracefully if moved
    for candidate in [
        _PACKAGES_FILE,
        Path.cwd() / "docker" / "packages.txt",
    ]:
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    return "(packages.txt not found — assume python3.12 with pytest, numpy, pypdf, pyyaml)"


CONTRACT = """\
## Output contract — create EXACTLY these files in the current directory

1. `benchmark.yaml` — metadata, matching this template exactly (fill every field):
```yaml
schema_version: 1
id: {bench_id}
skill_name: {skill_name}
title: "<short human title>"
capability: "<one sentence: the specific capability this benchmark tests>"
difficulty: medium        # easy | medium | hard
provenance:
  cluster_id: {cluster_id}
  cluster_label: "{cluster_label}"
  chunk_ids: {chunk_ids}
timeouts:
  agent_wall_seconds: 600
  grader_seconds: 120
limits:
  max_turns: 30
grader:
  entrypoint: grader/grade.sh
skill_assets_needed: {skill_assets_needed}
validation:
  reference_passed: false
  baseline_failed: false
```
2. `README.md` — documentation: what capability is tested, why it matters for this
   skill, exactly how grading works, and how the reference solution satisfies it.
3. `task_prompt.md` — the task given to the model under test. It must be
   self-contained (the model may NOT see the skill), reference input files by their
   paths in `/workspace`, and state precisely which output files must exist and in
   what format. Do NOT mention the grader or reveal grading internals.
4. `files/` — input fixtures. Copied to `/workspace` before the agent starts.
   Generate fixtures with a script if needed (you may run code), but commit only the
   resulting files. If the task needs no input files, create `files/.gitkeep`.
5. `grader/grade.sh` — grading entrypoint, run as `bash /grader/grade.sh` with
   cwd=/workspace AFTER the agent finishes. Exit 0 = pass, non-zero = fail.
   It may invoke `pytest /grader/test_*.py` or plain python/bash checks.
6. `reference_solution/` — the exact end-state files a correct solution would leave
   in `/workspace` (excluding the input fixtures, which are overlaid automatically).

## Hard rules for the grader
- DETERMINISTIC FIRST: same workspace in, same verdict out. No randomness, no
  clock, no network (the container has networking disabled), no ordering
  dependence. Use the LLM judge (below) only for what code cannot verify.
- Judge ONLY produced artifacts in /workspace. Never inspect transcripts or
  processes.
- EXECUTE, DON'T GREP: verify behavior by running the produced artifacts (execute
  the solution script against the fixtures, parse/render the output files) and
  asserting on what they produce. String-matching the solution's source code is
  FORBIDDEN unless task_prompt.md explicitly mandates that exact token. If a
  property is visual (rendering, layout, styling), verify it via rendered output
  (e.g. `pdftoppm` a PDF page to PNG) plus the LLM judge — never by grepping for
  the API calls that would normally produce it.
- Prefer PROPERTY-BASED checks (parse the output, assert on content/structure)
  over byte-exact comparisons whenever multiple correct outputs are possible.
- The grader must fail on an untouched workspace (this is checked automatically).
- The grader must pass on your reference_solution (also checked automatically).
- Only use packages listed in the sandbox inventory below.
- TRACEABILITY: every grader assertion must be traceable to an explicit statement
  in task_prompt.md. Never fail a solution that satisfies everything the task
  prompt actually asked for.
- For writing/prose outputs: structure checks alone are too weak (skeleton text
  passes). Add substance checks — facts that must be extracted from fixtures,
  cross-consistency between outputs, negative checks (banned filler/placeholder
  text), and/or LLM-judge questions about whether the text fulfills the stated
  purpose.

## LLM judge (for checks code cannot do — visual rendering, reading order, "does
## this fulfill X")
The harness provides a panel of vision-capable LLM judges that answer STRICT
yes/no questions. Protocol:
1. Run all deterministic checks first; if any fail, exit non-zero immediately.
2. If judge questions are needed, write /workspace/.judge/questions.json:
   {{"questions": [{{"id": "q1", "question": "<self-contained yes/no question>",
                   "image": "/workspace/.grading/page1.png"}},   // optional image
                  {{"id": "q2", "question": "...", "text": "<content to judge>"}}]}}
   and exit with code 3. Generate any images yourself first (e.g.
   `pdftoppm -png -r 100` for PDF pages) into /workspace/.grading/.
3. The harness answers (majority vote of 3 models, strict — any unmet condition
   means NO) into /workspace/.judge/answers.json: {{"answers": {{"q1": true, ...}}}}.
   On the re-run, read the answers and produce the final exit code.
Rules: max 10 questions; each must be binary, self-contained, and crisp enough
that two careful humans would agree (ambiguous questions flip between validation
runs and fail the determinism check); phrase multi-part checks as separate
questions; PREFER deterministic checks wherever possible.

## Hard rules for the task prompt (anti-leakage)
- task_prompt.md must state WHAT to achieve, never HOW the skill says to achieve
  it. Do NOT restate the skill's guidance, workflows, API names, magic values, or
  pitfalls — the gap between the prompt and the skill content is exactly what the
  benchmark measures. A model without the skill should find the task meaningfully
  harder.
- Never copy skill files (guides, references, scripts) into files/ fixtures.

## Hard rules for the task
- Solvable inside the sandbox by a competent coding agent in <= 30 tool calls.
- Must exercise the target capability described in the cluster excerpts — someone
  who has internalized that part of the skill should do noticeably better.
- No network access, no interactive input, no GUI.
"""


def authoring_prompt(
    skill: Skill,
    cluster: Cluster,
    chunks: list[Chunk],
    bench_id: str,
) -> str:
    chunk_text = "\n\n---\n\n".join(
        f"[chunk {c.id}]\n{c.text}" for c in chunks
    )
    contract = CONTRACT.format(
        bench_id=bench_id,
        skill_name=skill.name,
        cluster_id=cluster.cluster_id,
        cluster_label=cluster.label,
        chunk_ids=[c.id for c in chunks],
        skill_assets_needed="true" if skill.script_files else "false",
    )
    return f"""\
You are authoring ONE deterministic benchmark that tests whether an AI coding agent
has mastered a specific capability of the skill "{skill.name}".

# The skill (full SKILL.md, for context)
<skill_md>
{skill.skill_md}
</skill_md>

# The capability to test (cluster "{cluster.label}")
These excerpts from the skill define the SPECIFIC capability your benchmark must
target. The benchmark should be hard to complete correctly without the knowledge in
these excerpts, and straightforward with it:
<capability_excerpts>
{chunk_text}
</capability_excerpts>

{contract}

## Sandbox environment inventory (the ONLY available dependencies)
<packages>
{_sandbox_packages()}
</packages>

Work step by step: design the task, generate fixtures, write the grader, produce the
reference solution, verify locally that `bash grader/grade.sh` passes when run in a
directory containing files/ + reference_solution/ contents and fails on files/ alone,
then write README.md and benchmark.yaml. Create all files in the CURRENT directory.
"""


def repair_prompt(validation_report: str) -> str:
    return f"""\
Your previously generated benchmark (in the current directory) FAILED automated
validation. Fix it IN PLACE. Do not start over unless necessary; keep the same
benchmark id and file layout.

# Validation failures
{validation_report}

# Reminders
- reference check: fixtures + reference_solution/ overlaid into /workspace must make
  `bash grader/grade.sh` exit 0.
- baseline check: fixtures alone must make it exit non-zero.
- The grader runs with cwd=/workspace and the grader directory mounted at /grader,
  offline, deterministic.
Verify your fix locally before finishing.
"""
