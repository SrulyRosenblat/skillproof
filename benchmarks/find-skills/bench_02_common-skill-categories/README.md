# bench_02_common-skill-categories

## Capability tested

This benchmark targets the "Common Skill Categories" section of the `find-skills`
skill, specifically the **Tips for Effective Searches** and **When No Skills Are
Found** guidance:

1. **Use specific keywords** — a search query should combine the specific subject
   of the request (a tool/technology name) with the task, not just the bare
   generic category word (e.g. "react testing" rather than "testing").
2. **Try alternative terms** — a second query using different terminology should
   be proposed in case the first search returns nothing.
3. **Check popular sources** — when picking which source repositories to trust,
   an experienced user of this registry knows to check the specific well-known,
   broad, multi-topic hub repositories first (`vercel-labs/agent-skills` and
   `ComposioHQ/awesome-claude-skills`), rather than an arbitrary narrowly-scoped
   repo.
4. **When no skill is found** — acknowledge that nothing was found, offer to
   help directly right now, and suggest the specific command for scaffolding a
   new reusable skill (`npx skills init <name>`).

None of these four specifics (the exact multi-word query pattern, the two named
source repos, and the `skills init` scaffolding command) are derivable from
general knowledge or from the task prompt — they come only from having
internalized this part of the skill. A capable agent without the skill will
still produce a plausible-looking JSON plan, but it will reach for generic
narrowly-scoped GitHub repos it already knows about (e.g. `microsoft/playwright`)
instead of the two specific broad skill-hub repos, and it will invent its own
generic suggestion ("save it as a script") instead of the actual CLI command
for creating a new skill package.

## Task given to the model

The model sees five colleague requests in `/workspace/requests.json` (four map
to common, plausible-to-exist domains — testing, DevOps, code review,
changelog generation — and one, a personalized-haiku generator, does not). It
must write `/workspace/search_plan.json` with, for each of the four domain
requests, a specific `primary_query`, a distinct `alternative_query`, and 1-2
`check_sources` repos; and for the one-off request, a `no_match_response`
string satisfying the three-part fallback contract.

The prompt explains the general existence and shape of the registry/CLI (so
the task is well-posed) but never states the tips, the category table, the two
source-repo names, or the `skills init` command — that gap is exactly what the
benchmark measures.

## Grading

`grader/grade.sh` runs `grader/check.py`, a pure deterministic Python script
(no network, no LLM judge needed since everything here is objectively
checkable from the text):

1. `search_plan.json` must exist, parse as JSON, and contain exactly one plan
   entry for each of `r1`-`r5`.
2. For `r1`-`r4` (the domain requests):
   - `primary_query` must be multi-word and contain the request's specific
     subject-matter anchor term (e.g. "playwright" for r1, "kubernetes"/"k8s"
     for r2, "review" for r3, "changelog" for r4).
   - `alternative_query` must differ from `primary_query` and still contain a
     term relevant to the request.
   - `check_sources` must include (case-insensitively) `vercel-labs/agent-skills`
     or `ComposioHQ/awesome-claude-skills`.
3. For `r5` (the no-match request):
   - `no_match_response` must contain language acknowledging no existing
     package was found, language offering to help directly/right now, and the
     substring `skills init` (from the concrete scaffolding command it should
     recommend).

Any failed check exits non-zero with a message identifying exactly which
requirement was not met. The grader was verified locally to:
- **Pass** on `reference_solution/` overlaid on `files/`.
- **Fail** on `files/` alone (untouched workspace — no `search_plan.json`).
- **Fail** on a plausible skill-unaware baseline plan (correct-looking queries
  but generic/narrow source repos and a generic "save it as a script" fallback
  instead of `skills init`).

## Reference solution

`reference_solution/search_plan.json` gives specific multi-word queries with
distinct alternates for each domain request, cites both known hub repos as
`check_sources`, and for the haiku request gives a `no_match_response` that
acknowledges no package was found, offers to build it directly right now, and
recommends `npx skills init birthday-haiku` to save the work as a reusable
skill.
