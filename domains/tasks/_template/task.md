---
# Upstream SkillsBench task.md — schema 1.3, verified against tasks/edit-pdf/.
# Keep this file STRICTLY upstream-valid: no custom keys (project metadata goes in
# provenance.yaml). category/subcategory must match upstream taxonomy.yaml.
schema_version: '1.3'
metadata:
  author_name: TODO
  author_email: todo@example.com
  difficulty: medium            # easy | medium | hard
  difficulty_explanation: TODO — why this difficulty, in one or two sentences.
  category: TODO                # from upstream taxonomy.yaml (via domain.yaml interchange mapping)
  subcategory: TODO
  category_confidence: medium   # high | medium | low
  task_type:
    - TODO                      # e.g. analysis, calculation, transformation, formatting
  modality:
    - TODO                      # e.g. document, spreadsheet, terminal
  interface:
    - terminal
  skill_type:
    - TODO                      # e.g. domain-procedure, file-format-knowledge, tool-workflow
  tags:
    - TODO
verifier:
  type: test-script
  timeout_sec: 600.0
agent:
  timeout_sec: 1800.0
environment:
  network_mode: no-network      # project default; `public` only where the domain demands it
  build_timeout_sec: 600.0
  os: linux
  cpus: 2
  memory_mb: 2048
  storage_mb: 10240
  gpus: 0
---

(Template — replace this body. It is exactly what the agent sees, in every arm. It
must state the required outcome and deliverable paths, and must never restate any
skill's technique or name any skill. State the *what*, never the *how*.)

Produce the following deliverables:

- `<path>` — description of the required end state, verifiable by the tests from
  the artifact alone.
