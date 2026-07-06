# bench_01_agent-browser: Discover the agent-browser workflow before driving it

## Capability under test

The `agent-browser` skill's `SKILL.md` is explicit that it is a **discovery
stub, not the usage guide**:

> This file is a discovery stub, not the usage guide. Before running any
> `agent-browser` command, load the actual workflow content from the CLI:
> `agent-browser skills get core`

An agent that has internalized this treats an unfamiliar `agent-browser`
binary as a tool whose real command surface is *unknown until queried*, and
queries it (`skills get core`) before attempting any actual navigation/click/
fill actions. An agent that has not internalized this pattern tends to do the
opposite: it pattern-matches the name against generic browser-automation
conventions (Playwright/Selenium-style flags, invented subcommands like
`navigate`/`type`/`--selector`) and starts issuing guessed commands directly,
or gives up/fabricates an answer once those guesses fail.

This benchmark operationalizes that distinction with a small mock
`agent-browser` CLI (`files/bin/agent-browser`) that behaves like the real
tool's stub mechanism: every action subcommand (`open`, `snapshot`, `act`)
unconditionally refuses to run (exit code 1, explicit error pointing at
`skills get core`) until the workflow has been loaded in the current
workspace via `skills get core`. Only after that does the tool expose its
actual command syntax and accessibility-tree/`@eN`-ref interaction model
(mirroring the real agent-browser's snapshot+ref workflow), which the agent
must then use correctly across multiple steps (open a page, read refs from a
snapshot, fill two fields with a value looked up from a data fixture, click
a button, and read a dynamically-generated confirmation code off the
resulting snapshot) to produce the correct output.

Because the confirmation code is computed at runtime by the tool (not stored
anywhere in the static fixtures), it cannot be obtained by reading files
directly — the only way to get the right answer is to actually discover and
correctly drive the tool.

## Task summary

The agent is given:
- `bin/agent-browser` — the mock CLI described above.
- `site/portal.html` — a login form (employee name + access code + submit).
- `data/employee_directory.json` — a lookup table of employee access codes.

It must log in as a named employee (using that employee's access code from
the directory) through `agent-browser`, and write the confirmation code shown
after a successful login to `/workspace/result.json` as
`{"confirmation_code": "..."}`.

## Why this matters for the skill

The whole point of `agent-browser` shipping a "discovery stub" `SKILL.md`
instead of a full usage guide is that the CLI's actual command reference
lives in the binary and is fetched on demand (`skills get core`), so it never
goes stale across versions. An agent that skips this step and guesses at
syntax will fail against the real tool exactly as it fails here: the mock
CLI's action commands are gated and return nothing useful until the workflow
is loaded, so guessed commands just produce errors instead of progress.

## Grading

Grading is fully deterministic and network-free (`grader/grade.sh` →
`grader/check.py`):

1. Confirms `/workspace/result.json` exists, is valid JSON, and contains
   exactly the key `confirmation_code` with a non-empty string value.
2. Confirms the three input fixture directories (`bin/`, `site/`, `data/`)
   are still present (i.e. the agent didn't delete/rename its inputs).
3. Independently computes the expected confirmation code by copying the
   fixtures into a scratch temp directory and *executing* the same
   `agent-browser` tool through the correct sequence
   (`skills get core` → `open site/portal.html` → fill employee name → fill
   the access code looked up from `data/employee_directory.json` → click
   submit → `snapshot`), then parsing the confirmation code out of that
   snapshot's output.
4. Passes only if the agent's `result.json` value exactly matches that
   independently-computed value.

This follows "execute, don't grep": grading never inspects the agent's
transcript or command history, and never string-matches source code: it
only asserts on the produced artifact by re-deriving ground truth through
the same executable tool.

## Reference solution

`reference_solution/result.json` contains the correct confirmation code for
employee `Jordan Blake` (`access_code` `7Q2KD9`, `employee_id` `4471`),
precomputed by actually running `bin/agent-browser` through the full correct
sequence: `9DK2Q7-71` (the access code reversed, joined with the last two
digits of the employee ID — the exact transform used internally by the
mock tool). This is the only file a correct solution needs to add to the
workspace.
