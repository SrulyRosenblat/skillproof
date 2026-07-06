# Benchmark: Choose the Right Internal Comms Guide

This benchmark tests whether an agent can recognize the type of internal communication it has been asked to write, select the correct guide from several available options, and produce an output that follows that guide instead of a superficially similar one.

That matters for `internal-comms` because the skill is not just about writing clearly. It requires the agent to classify the request first, then load the matching guidance file. The benchmark is designed so that the request is clearly in scope for the skill, but it does not match one of the specialized guides. A correct agent must fall back to the general guide.

## Task shape

The workspace contains:

- `examples/` with four communication guides
- `request.md` with a concrete leadership update request and the facts that must be reflected

The model under test must create:

- `selection.json`
- `response.md`

## How grading works

The grader is fully deterministic and only inspects artifacts left in `/workspace`.

It checks that:

- both required output files exist and parse correctly
- `selection.json` names the correct guide path: `examples/general-comms.md`
- the markdown follows the structure required by the general guide
- the response includes the specific facts from `request.md`
- the response avoids placeholders and obvious wrong-guide formats such as 3P, FAQ, or newsletter layouts

The grader fails an untouched fixture-only workspace because the required outputs are missing.

## Why the reference solution passes

The reference solution:

- identifies the request as a leadership update
- selects `examples/general-comms.md`
- formats the response with the exact sections and list structure required by that guide
- includes the incident facts, schedule impact, and leadership decision request from the briefing
