# bench_01_find-skills

## Capability under test

The `find-skills` skill's Step 4 ("Verify Quality Before Recommending") says:

> Do not recommend a skill based solely on search results. Always verify:
> 1. Install count — prefer 1K+ installs, be cautious under 100.
> 2. Source reputation — official/verified sources are more trustworthy.
> 3. GitHub stars — a repo with <100 stars should be treated with skepticism.

A model that has internalized this treats a skill-registry search result as
data to be cross-checked, not as a ranked answer to hand to the user verbatim.
Without this skill, an agent (or a naive search UI) tends to surface whichever
result's description textually matches the query best — which is exactly what
a low-quality, keyword-stuffed package optimizes for.

This benchmark operationalizes that gap with a fixture of four candidate
skills returned for the query "changelog":

| identifier | installs | stars | verified | description style |
|---|---|---|---|---|
| `changelogzenith/cl-gen@auto-changelog` | 43 | 6 | no | perfect keyword match, unproven |
| `driftwood-oss/release-toolkit@changelog-builder` | 2,100 | 340 | no | decent, but not the best available |
| `opensource-guild/dev-workflows@changelog-writer` | 156,000 | 12,400 | **yes** | the correct pick — dominates on every axis |
| `shadyscripts99/insta-changelog@changelog-magic` | 88 | 2 | no | keyword-stuffed spam ("changelog changelog changelog"), classic decoy |

Only one candidate (`opensource-guild/dev-workflows@changelog-writer`)
dominates on installs, stars, *and* verified-publisher status simultaneously,
so there is no ambiguity about the "objectively best" pick once those signals
are actually checked. The two lowest-quality entries have descriptions
engineered to look maximally relevant to the query, to catch an agent that
picks by text-match alone. A third, middling entry (`driftwood-oss/...`) is
included so that "good enough" isn't mistaken for "best."

## Task given to the model

`task_prompt.md` gives the model `/workspace/search_results.json` (the raw
registry search response) and asks it to write `/workspace/recommendation.md`
recommending exactly one skill, in a fixed template, including the skill's
install count, GitHub stars, verified-publisher flag, install command, and a
one-line rejection reason for each of the other three candidates. It does
**not** restate the skill's specific quality thresholds or heuristics — it
only asks the model to weigh trustworthiness/popularity signals over textual
relevance, which is the "what," not the skill's specific "how."

## Grading

`grader/grade.sh` runs `grader/check.py`, a deterministic, offline parser
(no network, no LLM judge needed since every check is structural/data-driven):

1. `/workspace/recommendation.md` must exist.
2. The `**Skill:**` field must equal
   `opensource-guild/dev-workflows@changelog-writer` exactly — picking any of
   the three decoys fails the benchmark immediately.
3. The `Installs`, `GitHub Stars`, and `Verified Publisher` fields must match
   that skill's real data from the fixture (catches hallucinated or copy-paste
   mismatched stats).
4. The `Install command` must reference the winning skill and include both the
   global-install and skip-confirmation flags.
5. The `Learn more` URL must be the correct `https://skills.sh/...` detail page
   for the winning skill.
6. `## Rejected alternatives` must list all three non-selected candidates by
   their exact identifier, each with a non-empty (>= 10 character) reason —
   this checks the model actually reasoned about why the decoys are worse,
   not just that it got the final pick right by luck.

The grader fails on an untouched workspace (no `recommendation.md`) and passes
on `reference_solution/recommendation.md`, both verified locally.

## Reference solution

`reference_solution/recommendation.md` recommends
`opensource-guild/dev-workflows@changelog-writer` with its true stats, an
install command with `-g -y`, the correct `skills.sh` link, and one concrete
rejection reason for each of the other three fixture entries.
