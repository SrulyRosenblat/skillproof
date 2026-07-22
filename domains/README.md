# Domain pools — skill-independent benchmarks in the SkillsBench/Harbor format

A **new, standalone project** (currently parked inside the skillproof repo; designed
to lift out into its own repository unchanged). It measures skill uplift on
skill-independent task pools, one pool per *domain*, with tasks in the
**[SkillsBench](https://arxiv.org/abs/2602.12670) task format** — the
[Harbor](https://github.com/harbor-framework/harbor)-based layout used by
[benchflow-ai/skillsbench](https://github.com/benchflow-ai/skillsbench) (87 tasks ×
8 categories, deterministic verifiers). A task directory here can be copied into
their `tasks/` and vice versa; interchange is `cp -r`, not a converter.

This project deliberately does **not** use skillproof's task format or harness.
skillproof remains the sibling "syllabus track" (tasks generated from a skill's own
content, answering "does the skill deliver its own claims?"). This project answers
the question skillproof structurally cannot: **does a skill help on independently
sampled work in the domain it claims?**

## Design rules

1. **A skill may be consulted at measurement time, never at selection time.**
   No task authoring input, validation gate, repair objective, or acceptance
   criterion may depend on any skill's content or on the with-skill arm's outcome.
   Positive uplift must never be true by construction.
2. **Provenance or it didn't happen.** Every task traces to committed corpus
   sources (or to an upstream benchmark task id). The corpus is committed and
   auditable.
3. **Tasks are skill-blind on disk.** Task packages carry **no skills** —
   `environment/skills/` does not exist in this repo's tasks. Skills are injected
   by the run harness per arm (see Evaluation). This is the on-disk enforcement of
   rule 1, and it is the one deliberate difference from upstream SkillsBench
   packages, resolved at export/import time (see Interchange).

## Directory layout

```
domains/                        # project root (name is a placeholder; becomes the repo root)
├── README.md                   # this file
├── tasks/                      # flat, SkillsBench-format task dirs — the interchange surface
│   ├── _template/              # annotated format reference (never run)
│   └── <task-id>/
│       ├── task.md             # YAML frontmatter (upstream schema 1.3) + prompt body
│       ├── environment/
│       │   ├── Dockerfile      # per-task environment; inputs baked in; NO skills/
│       │   └── <bundled inputs>
│       ├── oracle/
│       │   └── solve.sh        # computes the solution; must reach reward 1.0
│       ├── verifier/
│       │   ├── test.sh         # runs pytest, writes 0|1 to /logs/verifier/reward.txt, exits 0
│       │   └── test_outputs.py # deterministic outcome-based tests
│       └── provenance.yaml     # OUR sidecar: domain, corpus refs, headroom, validation
└── <domain>/                   # e.g. web-ui/
    ├── domain.yaml             # manifest: skill claims, task membership, probe config
    └── corpus/                 # committed source material + SOURCES.json
```

Layout decisions that keep interchange trivial:

- `tasks/` is **flat** with kebab-case ids, exactly like upstream. Domain membership
  lives in `domain.yaml` (and `metadata.category/subcategory` in the frontmatter),
  never in directory nesting — so a task dir moves between repos without
  restructuring.
- `task.md` stays **strictly upstream schema 1.3**. Everything this project needs
  beyond it lives in the `provenance.yaml` sidecar, which upstream tooling ignores
  and export can drop. No custom frontmatter keys that could trip their CI
  (`bench tasks check` / taxonomy lint).

## Task format (upstream contract, verbatim)

Verified against the SkillsBench
[CONTRIBUTING.md](https://github.com/benchflow-ai/skillsbench/blob/main/CONTRIBUTING.md)
and a real task (`tasks/edit-pdf/`):

- **`task.md`** — YAML frontmatter with `schema_version: '1.3'`, `metadata.*`
  (author, difficulty easy|medium|hard, category/subcategory from their
  `taxonomy.yaml`, task_type/modality/interface/skill_type lists, tags),
  `verifier.type: test-script` + `verifier.timeout_sec`, `agent.timeout_sec`,
  `environment.*` (network_mode, cpus, memory_mb, storage_mb, os). Body = the
  prompt the agent sees.
- **`verifier/test.sh`** — installs test deps, runs
  `pytest /verifier/test_outputs.py`, writes `1` or `0` to
  `/logs/verifier/reward.txt`, **always exits 0** (the reward file is the verdict).
  Tests are deterministic, outcome-based (4–10 focused assertions, numeric
  tolerances where appropriate), and test results, not process.
- **`oracle/solve.sh`** — human/agent-authored reference that **computes** the
  solution (hardcoded answers are rejected upstream) and must achieve reward 1.0.
- **`environment/Dockerfile`** — self-contained task environment with inputs baked
  in. Harbor builds it, drops the agent in, then mounts and runs the verifier.

There is **no LLM judge** in this format. Verification is deterministic or the task
doesn't ship. (Consequence for visual domains: see Open questions.)

## `provenance.yaml` sidecar

Everything project-specific, kept out of `task.md`:

```yaml
domain: web-ui
origin: authored              # authored | imported
imported_from: null           # "skillsbench:<task-id>@<commit>" when origin: imported
corpus_refs:                  # authored tasks: corpus chunks this task derives from
  - corpus/example-source.md#heading
authoring: {}                 # backend/model/tokens/cost, set by the authoring harness
validation:
  oracle_reward: null         # must be 1.0
  baseline_reward: null       # verifier on untouched environment; must be 0.0
  determinism_checked: false
  validated_at: null
headroom:                     # stage-5 skill-blind probe (see Validation)
  probe_agent: null           # harbor agent + model, e.g. "terminus:moonshotai/kimi-k2.7-code"
  trials: 0
  base_passes: 0
  probed_at: null
pool_version: 0               # bumped if the task changes after the pool freezes
```

## `domain.yaml` manifest

One per domain — the **only** place skills and tasks are associated. Domains and
their member-skill sets can be **discovered** by clustering ~100 imported skills
(`pipeline/skillmap.py` → `DomainMap.as_yaml_stub()`) rather than hand-authored; the
generator then authors each domain's tasks leave-one-out (a task scored against a
skill is never seeded from that skill). See `pipeline/README.md`.

- `skills[]` — skills claiming this domain; each `claim` quotes the skill's
  `SKILL.md description` frontmatter verbatim (the same text that routes skill
  selection in production). Skill packages themselves live outside the task tree
  (for now, the skillproof repo's `skills/`; a standalone deployment vendors them).
- `tasks[]` — explicit list of task ids in this pool (flat `tasks/` needs an
  explicit membership list; auditable in review).
- `headroom_probe` — probe agent/model and acceptance threshold.
- `interchange` — this domain's `metadata.category`/`subcategory` mapping into the
  upstream taxonomy, and the pinned upstream `schema_version`.
- `frozen` / `pool.version` — once published, the pool freezes; changes bump the
  version. A moving pool destroys the fixed-yardstick property.

## Corpus rules

1. **Independence.** Nothing in `corpus/` may be authored by, derived from, or
   paraphrased out of any skill under test. If in doubt, exclude.
2. **Need/spec level, not how-to level.** Format specs, official platform docs,
   real user requests. Material describing *what people need done*, not *how to do
   it*.
3. **Committed and attributed.** Every corpus file has a `SOURCES.json` entry
   (origin URL, license, retrieval date).
4. **Knowledge/policy domains use the ground-truth source.** Where the domain has
   no public existence (brand rules, house style), the corpus is the underlying
   ground-truth document; a skill is one *packaging* of it, and competing packagings
   compete on the same pool.

## Authoring tasks

- The authoring agent receives the domain brief + corpus cluster excerpts. **No
  SKILL.md, from any skill, ever appears in its context.**
- Prompt states *what*, never *how*. No dependence on any one skill's bundled
  scripts (fairness rule — the verifier judges outcomes, not toolchains).
- Repair objectives are capability-framed only ("the probe agent solved it unaided
  via <transcript> — change the task so that path fails"), never "make skill X
  matter more".
- Environment policy: default `network_mode: no-network` (upstream allows `public`;
  we accept it only where the domain genuinely demands network access, because
  offline determinism is what makes baselines trustworthy).
- Pool size target: 15–25 tasks per domain. Cross-skill comparison on 5 tasks is
  noise.

## Validation gates

1. **Structural** — upstream layout + `task.md` schema (upstream `bench tasks
   check` once available locally; a thin local linter until then), plus sidecar
   parses and `environment/skills/` is absent.
2. **Oracle** — `oracle/solve.sh` in the task environment reaches reward 1.0.
3. **Baseline-fails** — verifier on the untouched environment yields reward 0
   (no trivially-passable tasks).
4. **Determinism** — repeated verification gives the same reward.
5. **Headroom probe (skill-blind)** — run the strongest base agent config unaided,
   `trials` times; accept iff `base_passes/trials ≤ max_base_pass_rate` (default ⅓).
   Recorded in the sidecar; failures feed the repair loop with the passing
   transcript. Two deliberate choices, carried over from the design discussions:
   **cap, don't zero** (uplift ≥ −base; a 0%-base pool makes harmful skills
   mathematically invisible), and **the with-skill arm is never probed** (floors
   ship as findings, not filtered as defects — that is what keeps this from being
   PR for skills).

Imported tasks pass the same gates — including re-probing headroom against *our*
agent configs; upstream difficulty was calibrated on different agents and does not
transfer. Only the tasks transfer.

## Evaluation

Run harness: **Harbor**, with agent scaffolds it supports (Claude Code, Codex CLI,
Gemini CLI, terminus, custom). An evaluation is a matrix over
`(task, skill-arm, agent config, trial)`:

- **without-skill arm** — the task environment exactly as committed (skill-blind by
  construction). Shared across all skills in the pool: N skills cost N+1 arm-sets,
  not 2N, and every skill is compared against the *identical* baseline.
- **with-skill arm** — the harness materializes the task with the claiming skill
  injected at `environment/skills/<name>/` (folder copy at image build), which is
  exactly SkillsBench's curated-skills condition. One arm per claiming skill.
- **Skill-tax control** — sampled cells where an *off-domain* skill is injected;
  measures whether carrying an irrelevant skill hurts. Fully skill-disconnected
  honesty metric.
- Verdicts are the binary rewards; uplift = with − without pass rate per
  (skill, agent config), over the pool.

Metrics: pool uplift; **paired per-task deltas between skills on the same pool**
(the statistic the syllabus track can never provide); skill tax; routing validity
(uplift restricted to tasks matching the skill's own claim); probe-time vs eval-time
base rates (divergence = the headroom filter overfit to the probe agent).

## Interchange

- **Import** (`skillsbench tasks/<id>` → here): copy the dir; **delete
  `environment/skills/`** (arm control belongs to the harness — a baked-in skill
  would leak into the baseline arm and corrupt uplift); add `provenance.yaml` with
  `origin: imported` and upstream id@commit; record upstream license in the domain's
  `SOURCES.json`; run gates 1–5. Because Harbor runs per-task Dockerfiles natively,
  there is no shared-image dependency constraint — their environments run as-is.
- **Export** (here → upstream PR): copy the dir; inject the relevant skill(s) at
  `environment/skills/`; drop `provenance.yaml`; fill `metadata.category/subcategory`
  from the domain's `interchange` mapping; follow their PR checklist (oracle reward
  1.0, agent runs with/without skills, pass rates in the PR).

## What is intentionally dropped from skillproof

- Its task format (`benchmark.yaml`/`task_prompt.md`/`grader/grade.sh`), harness
  (OpenRouter agent loop, shared sandbox image), and the exit-3 **LLM-judge
  protocol** — this project is deterministic-verifier-only, per the upstream
  contract.
- `skill_files_read` telemetry (skillproof's agent loop tracked which skill files
  the agent opened; Harbor scaffolds don't report this). Known loss, noted in
  reporting.
- The existing 35 skill-derived benchmarks. They stay in skillproof as the syllabus
  track and are **not migrated**: their topic distribution was chosen by the
  incumbent skills' headings, which would structurally favor incumbents on a shared
  pool.

## Build-out checklist

1. Local lint: structural gate + sidecar schema (until upstream `bench` CLI is
   wired in).
2. Harbor run configs: arm materialization (skill injection at build), shared
   baseline, trial matrix, results collection.
3. Headroom probe runner (gate 5) + repair-loop prompts (capability-framed).
4. Authoring pipeline: corpus chunk/cluster (skillproof's `chunking.py`/
   `clustering.py` logic is reusable as library code) → author → gates.
5. Import tooling + first import batch: upstream tasks overlapping our domains
   (their `office-white-collar`/pdf-editing category overlaps skillproof's pdf/docx
   skills; several web tasks, e.g. `data-to-d3`, `fix-visual-stability`, are web-ui
   candidates — audit per task).
6. Aggregation + report (uplift, paired deltas, skill tax; small — rewards are
   binary files on disk).
7. Seed the web-ui corpus and author the first 15 tasks.

## Open questions

- **Visual quality without an LLM judge.** The deterministic-only contract means
  web-ui tasks must verify structure/behavior/performance (DOM assertions, computed
  styles, bundle behavior under node) rather than aesthetics. Either accept that
  scope for web-ui, or pilot the exchange on a naturally deterministic domain
  (documents) and keep aesthetic evaluation out of v0.
- **Network policy.** Upstream allows `network_mode: public` (their `edit-pdf` uses
  it, and their verifiers pip-install at verify time). Default here is no-network;
  do we accept public-network imports as-is or vendor their deps into the image?
- **Licensing.** Confirm the skillsbench repo license permits redistributing
  imported task content before committing any; record per-task license regardless.
- **Upstream drift.** `schema_version` (pinned 1.3) and `taxonomy.yaml` are moving
  targets; the local linter should fail loudly when the pin goes stale.
- **Probe agent choice.** Headroom filtering is against one agent config; report
  probe-vs-eval divergence and revisit if it overfits.
