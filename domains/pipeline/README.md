# Pipeline — hard tasks at scale, matched to relevant skills

Generates Harbor/SkillsBench-format tasks that a base model **fails but domain
knowledge solves** (so a skill packaging that knowledge can measurably help), and
matches each task to the skills that should help it — without ever letting a skill
shape the task (project rule 1: skills consulted at measurement time, never
selection time; see `../README.md`).

## The one idea that makes "hard" mean the right thing

Raw hardness is the wrong target. A task that's hard for *capability* reasons is
hard in both arms and yields **zero uplift** — it measures the model, not the skill.
What we want is **knowledge/procedure-gated hardness**: the base model fails because
it lacks a specific value, convention, non-default procedure, or edge case that
*exists in the domain*. (This is why brand-guidelines went 0%→42% in skillproof: the
skill held unguessable hex values, not harder reasoning.)

We generate that skill-blind by authoring from the **domain corpus** — the corpus
holds the same class of specialized knowledge a good skill packages, minus the
specific skill under test. The engine has two halves:

- **Prior (cheap, deterministic, at scale):** score corpus chunks by difficulty
  potential and author only from the dense ones. `difficulty.py` — normative rules
  ("must/never"), documented pitfalls (the best seeds: they name the naive wrong
  path), non-default procedures, and unguessable specifics (hex, exact measures,
  identifiers, quoted literals). Verified: pitfall/spec-dense prose scores 18 vs 0
  for generic overview.
- **Filter (expensive, empirical):** the skill-blind headroom probe actually runs a
  base agent and keeps only tasks it fails. The prior exists to raise the probe's
  hit-rate so scarce agent runs aren't wasted authoring from chunks that could only
  ever produce easy tasks.

## Front end: import → cluster → domains

The pool is seeded from real skills, at scale:

```
skills_manifest.yaml
  │  skills_import.import_all      shallow-clone / copy ~100 skill folders
  ▼
imported skills (cache)
  │  skillmap.cluster_into_domains  embed name+description, KMeans+silhouette
  ▼                                  (reads the routing contract, not skill bodies)
DomainMap  (K discovered domains, each = a set of member skills)
```

Verified on the 12 repo skills with real embeddings: coherent domains fall out —
documents (docx, pdf), design (frontend-design, vercel-react, brand-guidelines),
web/browser (agent-browser, webapp-testing, web-artifacts), etc. At ~100 skills
these separate much more finely. The domain map is the taxonomy AND the "relevant
skills" set for matching — both from one clustering.

**Corpus = the domain cluster's skills, minus the one being scored.** With a
skills-first pipeline the per-domain corpus is the aggregate content of the cluster's
member skills. Per-skill uplift stays honest via a **leave-one-out** rule: a task
that will be scored against skill X is seeded from the domain's *other* skills, never
X. So a `documents` task scored on `pdf` was authored from `docx`+`find-skills`
content — X never shaped its own benchmark. This is the reconciliation of "use skills
as raw material at scale" with "metrics disconnected from skills": no single skill
authors the task it's graded on, and many skills per domain dilute any one skill's
fingerprint. (Residual caveat: heavily-overlapping skills within a domain can still
share fingerprints; the headroom probe + skill-tax control surface it.)

## Stages

```
domain corpus (cluster skills, leave-one-out per scored skill)
  │  corpus.load_corpus         chunk (skillproof chunk_markdown)
  ▼
chunks
  │  corpus.select_seeds        difficulty prior + cluster for diversity
  ▼  = difficulty.rank ∘ cluster_chunks ∘ select_dissimilar
TaskSeeds  (diverse, difficulty-dense; carry corpus_refs provenance)
  │  authoring.authoring_prompt   author agent, NO skill in context  ── seam A ──
  ▼  (agent run = skillproof codex _run_codex pattern; Harbor task package out)
Harbor task package  (task.md / environment / oracle / verifier / provenance.yaml)
  │  validate gates 1-4           structure / oracle=1.0 / baseline=0 / determinism
  │  gate 5: headroom probe       run base agent via Harbor, N trials  ── seam B ──
  ▼      ├─ base fails (≤⅓) → ACCEPT, write headroom{} to provenance.yaml
         └─ base passes    → authoring.harden_prompt(transcript) → re-author → re-probe
                                (ratchet; capped rounds; else FAILED.md)
accepted tasks
  │  match.build_plan            skill-blind matching  (fully built)
  ▼
MatchPlan  (per-task with-skill arms ranked by relevance; shared baseline; skill-tax)
  │  Harbor run                  arms × trials  ── seam B ──
  ▼
rewards → uplift / paired deltas / routing validity / skill tax
```

## Matching (built, verified)

`match.py` is **structurally skill-blind**: it only ever embeds a skill's `claim`
(its SKILL.md `description`, quoted in `domain.yaml`), never the skill body. That is
the exact text production skill-routing matches against, so
`relevance = cosine(task_prompt, skill_claim)` is the production-routing analog and
can't tune a task toward a skill.

- `build_plan(domain, tasks, claims, task_domain, embedder)` → **MatchPlan**: each
  task's with-skill arms = the skills claiming its domain, ranked by relevance
  (verified: the design skill ranks above the perf skill on a design task, and vice
  versa); a shared skill-blind baseline (one arm-set per pool, not per skill); and
  sampled **skill-tax** pairs (an off-domain skill injected as a negative control —
  does carrying an irrelevant skill hurt?).
- `classify_to_domain(task_text, domain_refs, embedder)` routes imported/unlabeled
  tasks (e.g. remapping a SkillsBench `category` to our domain taxonomy).
- Relevance is retained per (task, skill) for the **routing-validity** metric: does
  a skill help more on the tasks its own description scores high on?

Production embeddings come from skillproof `get_provider(cfg)`; the module takes any
`Embedder` (inject a stub for tests, as the verifier does).

## Scale

Three levers, in order of leverage:
1. **Prior → hit-rate.** Authoring from difficulty-ranked seeds means a larger
   fraction of probes land on genuinely-hard tasks. This is the main scale lever.
2. **Batch fan-out.** Seeds are independent; author + probe them concurrently
   (the codex harness is single-task, but the loop parallelizes trivially — one task
   dir per worker).
3. **Import + re-probe.** SkillsBench ships 87 externally-authored, verifier-backed
   tasks; importing (strip `environment/skills/`, re-probe against our agents) is
   pure volume with the strongest possible independence. See `../README.md` §
   Interchange. Shares the whole back half (probe → harden → match) with authoring.

## What's built

Every stage is implemented. `scratchpad/verify_pipeline.py` (offline chain) and
`scratchpad/verify_seams.py` (seam logic via a FakeSandbox) are both green, and the
CLI runs end to end (`import-skills` executed for real).

| Module | Role | Verified |
| --- | --- | --- |
| `skills_import.py` | manifest → skills cache | local import round-trip + real CLI run |
| `skillmap.py` | cross-skill clustering → domains | 12 skills, real embeddings |
| `difficulty.py` | difficulty prior (scorer + rank) | hard 18 vs overview 0 |
| `corpus.py` | load / score / select_seeds | diverse hard seeds, easy excluded |
| `match.py` | relevances / build_plan / classify | routing + tax + classify |
| `authoring.py` | Harbor authoring / harden / repair prompts | contracts render |
| `harbor.py` | task load/parse; run verifier/oracle on sandbox | reward parse, structure |
| `validate.py` | gates 1-4 (structure/oracle=1/baseline=0/determinism) | gate flow (FakeSandbox) |
| `eval_runner.py` | **seam B**: headroom probe + arms×trials eval | probe tally, uplift math |
| `author_runner.py` | **seam A**: author→validate→probe→harden loop | control flow |
| `cli.py` | typer CLI wiring all stages | `--help` + `import-skills` run |

Seam A drives `claude -p` via skillproof's `_run_codex` (host-side, subscription
auth); seam B runs Harbor tasks on skillproof's offline Sandbox + `run_agent` and
reads `/logs/verifier/reward.txt` — **no dependency on Harbor the framework.** Tasks
carry `environment/Dockerfile` for interchange; the local runner stages `environment/`
into `/workspace` on the shared image, so authored tasks must use only the shared
image's packages (the authoring contract enforces this).

## Prerequisites to run for real

- **Docker** — required for validate / probe / generate / evaluate (the sandbox).
  Not installed in the current environment; install Docker Desktop and
  `skillproof build-image` once.
- **`OPENROUTER_API_KEY`** — cluster / seed / match (embeddings) and evaluate/probe
  (the agent model). Local sentence-transformers works for embeddings if preferred.
- **`claude` CLI** — authoring (present; uses subscription auth, no key).

## Run order (all stages built)

```
1. curate domains/skills_manifest.yaml toward ~100 (community dirs → pin repos)
2. python -m pipeline.cli import-skills                 → skills cache
3. python -m pipeline.cli cluster                       → domain_map.yaml   [embeddings]
4. python -m pipeline.cli seed <domain> [--holdout X]   → seeds.json        [embeddings]
5. python -m pipeline.cli generate <domain>             → tasks/ (author→gate→probe→harden)  [Docker + model]
6. python -m pipeline.cli match <domain>                → match_plan.json   [embeddings]
7. python -m pipeline.cli evaluate <domain>             → uplift / per-skill [Docker + model]
```

`python -m pipeline.cli` needs `domains/` on `PYTHONPATH` (or run from `domains/`).
Steps 5 and 7 are the Docker+model-gated ones; everything else runs with embeddings.
