# skillproof

**Automatic benchmark generation and skill-uplift measurement for [Agent Skills](https://github.com/anthropics/skills).**

Agent skills are folders of instructions (`SKILL.md` + reference docs + scripts) that get injected into an AI agent's context. Everyone ships them; almost nobody measures whether they help. skillproof answers that question automatically:

> **Skill uplift** = pass rate *with* the skill − pass rate *without* it, on deterministic benchmarks generated from the skill's own content.

```
SKILL.md folder ──► chunk & cluster ──► author & validate ──► evaluate uplift ──► report + website
                    (embeddings,        (Codex / Claude        (N models × 2 arms
                     k-means, max-min    writes task, fixtures,  × N trials, Docker
                     dissimilar picks)   grader; auto-checked)   sandbox, LLM judge)
```

Because uplift is a *differential* measure — same model, same benchmark, same grader in both arms — author bias, grader quirks, and model quirks largely cancel out.

## Results at a glance

12 real skills benchmarked (from Anthropic's and Vercel Labs' public repos), 31 auto-generated benchmarks, ~700 trials across 3 OpenRouter models:

| Skill | Mean uplift | What it revealed |
|---|---:|---|
| brand-guidelines | **+33pp** | Proprietary knowledge (brand hex values) lifts every model |
| docx | **+13pp** | Uplift comes from the skill's bundled scripts, not its prose |
| find-skills | +17pp | Registry-triage benchmark discriminates; the other ceilings |
| internal-comms | +7pp | Prose skills need LLM-judge grading; substring graders floor everything |
| slack-gif-creator | +7pp | One grader punished the skill's own workflow (−100pp) until regenerated |
| pdf, vercel-react, agent-browser | ~0 | Ceilings: the knowledge is already in the models |
| frontend-design | **−38pp** | The skill's boldness guidance defeats its own restraint requirements |

The cross-skill pattern: **uplift concentrates where model capability runs out** — and injected guidance can go *negative* when it distracts from task constraints.

Open `site/index.html` for the full interactive report: every benchmark's task prompt, grader source, reference solution, fixtures, per-trial transcripts, judge votes, and costs.

## How it stays trustworthy

Every generated benchmark must survive an automated gate before it's used:

1. **Structure** — required files exist, `benchmark.yaml` parses against the schema
2. **Reference check** — the bundled reference solution must make the grader **pass**
3. **Baseline check** — an untouched workspace must make the grader **fail** (no trivially-passable benchmarks)
4. **Determinism** — repeated grading gives the same verdict

Failures feed back to the authoring agent verbatim for up to 3 repair rounds; unfixable benchmarks get a `FAILED.md` and are excluded. The authoring contract (in `src/skillproof/codex/prompts.py`) additionally enforces, learned the hard way from adversarial audits:

- **Execute, don't grep** — graders judge produced artifacts, never string-match solution source
- **Traceability** — every grader assertion must trace to an explicit task-prompt statement
- **Anti-leakage** — task prompts state *what*, never the skill's *how*; the prompt/skill gap is what's being measured
- **LLM judge protocol** — for properties code can't verify (visual rendering, semantics of prose), the grader writes strict yes/no questions and exits with code 3; the harness answers them with a **3-model vision judge panel** (majority vote, any-unmet-condition-means-NO) and re-runs the grader. The sandbox stays offline; API keys never enter a container.

## Requirements

- Python ≥ 3.11, a running Docker daemon
- `OPENROUTER_API_KEY` in `.env` (evaluation, embeddings, judge panel)
- An authoring agent CLI: [Claude Code](https://claude.com/claude-code) (`claude`, default) or [OpenAI Codex](https://github.com/openai/codex) (`codex`) — configured under `codex:` in `skillproof.yaml`

## Quickstart

```bash
pip install -e .
cp .env.example .env            # add OPENROUTER_API_KEY
skillproof build-image          # build the Docker sandbox

skillproof all skills/pdf       # full pipeline: cluster → generate → run → report
```

Or step by step:

```bash
skillproof cluster  skills/pdf                 # → benchmarks/pdf/clusters.json
skillproof generate skills/pdf                 # author + validate (skips already-validated)
skillproof validate benchmarks/pdf/bench_01_*  # re-check one benchmark
skillproof run      skills/pdf --trials 3 --parallel 4
skillproof report   results/pdf/<run_id>       # regenerate report.md
```

Interrupted? Everything is resumable: `skillproof run ... --resume <RUN_ID>` keeps graded verdicts and retries infra-errored trials; `skillproof generate` skips validated benchmarks (`--force` to re-author, `--only <id>` for one).

## What a benchmark looks like

```
benchmarks/<skill>/bench_NN_<slug>/
├── benchmark.yaml        # metadata, provenance (cluster + chunks), limits, validation record, authoring cost
├── README.md             # what capability is tested, why, how grading works
├── task_prompt.md        # exactly what the model-under-test sees
├── files/                # input fixtures, copied to /workspace
├── grader/grade.sh       # exit 0 = pass; runs offline in a fresh container; exit 3 = judge questions
└── reference_solution/   # known-good end state (proves solvability)
```

Trials run in fresh `network_mode=none` containers (fixed env, resource limits); the agent's `/workspace` is snapshotted and graded in a *second* fresh container. Per trial we record pass/fail, turns, tokens in/out, cost (OpenRouter-reported), stop reason, judge Q&A with per-model votes, and **which `/skill` files the agent actually read** — the last one tells skill authors which parts of their skill carry the weight.

## Repo layout

```
src/skillproof/        the pipeline
├── chunking.py        heading-based markdown chunking
├── clustering.py      k-means + silhouette + greedy max-min dissimilar selection
├── codex/             authoring harness (prompts/contract, backend drivers, validation)
├── sandbox/           Docker lifecycle + grading
├── agent/             OpenRouter agent loop, tools, transcripts
├── eval/              trial orchestration, resume, uplift aggregation
├── judge.py           3-model yes/no judge panel
└── report/            markdown reports
skills/                skills under test (SOURCES.json maps each to its origin repo)
benchmarks/<skill>/    generated benchmarks (committable, human-auditable)
results/<skill>/<run>/ results.json, report.md, per-trial JSONL transcripts
site/index.html        self-contained interactive report of everything
docker/                sandbox image; packages.txt is the dependency inventory quoted to authors
```

## Honest limitations

- **Best-case measurement**: benchmarks are generated from the skill's own documentation, so they sample the task distribution the skill's author imagined. Read uplift as "does the skill deliver what it promises" (spec conformance), not field performance.
- **No discrimination probe yet**: validation proves consistency, not that a benchmark separates models — ceilings ship (a strong model may pass without the skill). The fix is AutoBencher-style measure-then-search: probe trials during validation, feeding measured difficulty back to the author.
- **Environment-bound skills don't fit**: anything needing a live browser, network, or external service (e.g. agent-browser) can only be tested via offline proxies, which proved too easy. Those need a different harness.
- Provider nondeterminism is mitigated (temp 0, seeds, pinning, N trials) but not eliminated — treat single-trial cells as noise; 3+ trials per arm minimum.

## Tests

```bash
pytest -m "not docker"   # pure unit tests
pytest -m docker         # requires the built sandbox image
```
