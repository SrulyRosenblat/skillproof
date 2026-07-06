# Benchmark: Check Cheap Conditions Before Async Flags / Defer Await Until Needed

## Capability under test

This benchmark targets skill rules `async-cheap-condition-before-await` (1.1)
and `async-defer-await` (1.2) from `vercel-react-best-practices`:

- **1.1 Check Cheap Conditions Before Async Flags**: when a branch depends on
  `await someAsyncFlag() && cheapSyncCondition`, evaluate the cheap
  synchronous condition first so the async call is skipped whenever it can't
  matter.
- **1.2 Defer Await Until Needed**: move `await` calls into the branch that
  actually uses their result, including the "early return optimization"
  pattern where an expensive fetch is deferred until a cheaper, earlier
  check (e.g. existence) has already ruled out the need for it.

An agent that has internalized this part of the skill will recognize the
same shape in unfamiliar code — an `await` performed unconditionally before
a branch, or before an independent cheap check — and reorder the code so the
expensive call is skipped on paths where it cannot influence the result. An
agent without this knowledge is likely to focus only on preserving return
values (which naive reordering can also achieve) without noticing *that
call ordering / laziness is the actual point*, or may "fix" the code in a
way that changes behavior.

## Task

`files/src/access-control.js` contains three async functions, each modeled
directly on an example from the skill's waterfall-elimination rules, but
rewritten with dependency-injected `deps` functions so the whole thing is a
plain, offline-testable Node.js module (no real network/DB required):

1. `checkFeatureAccess` — mirrors the `flag && cheapCondition` shape from
   rule 1.1. The starting code awaits the remote flag unconditionally before
   checking the cheap `user.isBetaTester` flag.
2. `handleRequest` — mirrors the `skipProcessing` early-return shape from
   rule 1.2. The starting code awaits `fetchUserData` before checking
   whether the result will even be used.
3. `updateResource` — mirrors the "early return optimization" example from
   rule 1.2, where an expensive permissions fetch happens before an even
   more decisive existence check.

The agent is asked to refactor all three functions so that (a) return values
are unchanged for every input, and (b) each expensive `deps` function is
only invoked when its result can actually affect the output. The prompt
never uses the words "await ordering", "waterfall", or names the rule —
it frames the requirement purely in terms of observable behavior (return
values) and call efficiency (don't call expensive dependencies when their
result is moot).

## Why this is hard without the skill

Simply reading the current code and confirming "it works" isn't enough —
the existing code is already functionally correct in the sense of returning
the right values. The fix requires noticing that a specific `await` is
unconditionally on the hot path before a cheaper, independent (or
outcome-determining) check, and reordering the code without altering
observable behavior. This is exactly the pattern rules 1.1/1.2 name and
give worked examples for. Agents unfamiliar with this pattern often miss
that call-count reduction (not just return-value preservation) is a
requirement, since nothing in the prompt says "avoid extra network calls
using X technique" — they have to derive the fix themselves from the
"only call it when needed" requirement.

## Grading

Grading is fully deterministic and executes the produced module directly
(no string/AST matching on source code):

1. `grader/grade.sh` (run with cwd `/workspace`) checks that
   `src/access-control.js` exists, then runs `grader/check.js` with Node.

2. `grader/check.js` does `require('/workspace/src/access-control.js')` and
   calls each of the three exported functions multiple times with
   instrumented (call-counting) spy implementations of every `deps`
   function, covering every relevant branch:
   - `checkFeatureAccess`: `isBetaTester` × flag value (4 cases)
   - `handleRequest`: `skipProcessing` true/false (2 cases)
   - `updateResource`: resource missing / found-but-forbidden /
     found-and-editable (3 cases)

   For each case it asserts:
   - the **return value** exactly matches the documented contract, and
   - each expensive dependency's **call count** matches what's required for
     a lazy implementation (e.g. `getFeatureFlag` must be called 0 times
     when `isBetaTester` is false, `fetchPermissions` must be called 0
     times when the resource doesn't exist, etc).

   Any mismatch on either axis is a failure, and the script prints exactly
   which assertion(s) failed.

3. Exit code 0 = pass, 1 = fail.

This design catches two distinct failure modes: an agent that reorders code
incorrectly and breaks a return value, and an agent that leaves the
wasteful unconditional `await`s in place (return values still correct, but
extra calls still happen).

## Reference solution

`reference_solution/src/access-control.js` reorders each function exactly
per the skill's guidance:

- `checkFeatureAccess` checks `user.isBetaTester` first and returns `false`
  immediately if it's falsy, only calling `deps.getFeatureFlag` on the
  remaining path.
- `handleRequest` checks `skipProcessing` first and returns immediately,
  only calling `deps.fetchUserData` on the remaining path.
- `updateResource` fetches the resource first and returns `Not found`
  immediately if missing, only calling `deps.fetchPermissions` once the
  resource is confirmed to exist.

Running `bash grader/grade.sh` against the reference solution's file passes;
running it against the unmodified `files/` fixture (the starting point given
to the agent) fails, since the starting code calls every expensive
dependency unconditionally.
