# Triage Requests for an Agent-Skill Registry Search

Your team has access to a public registry of installable "agent skill" packages
(reusable bundles of instructions/tools that extend what an AI coding agent can do).
The registry can be searched by keyword, and a matching package can then be
installed. Some packages come from source repositories that are especially
well-established and widely adopted by the community — when more than one
plausible source exists, an experienced user would know which source
repositories are the safe, popular bets to check first, rather than picking
an arbitrary or obscure one.

Five colleagues have sent you requests, recorded in `/workspace/requests.json`
(each with an `id`, `from`, and `text`). For each request, decide how you would
search the registry to find a pre-built package that covers it — or, if the
request is too idiosyncratic for a pre-built package to plausibly exist, say so
instead.

Write your triage plan to `/workspace/search_plan.json` as a single JSON object
of the form:

```json
{
  "plans": [
    { "id": "r1", "primary_query": "...", "alternative_query": "...", "check_sources": ["owner/repo", "owner/repo"] },
    { "id": "r2", "primary_query": "...", "alternative_query": "...", "check_sources": ["owner/repo", "owner/repo"] },
    { "id": "r3", "primary_query": "...", "alternative_query": "...", "check_sources": ["owner/repo", "owner/repo"] },
    { "id": "r4", "primary_query": "...", "alternative_query": "...", "check_sources": ["owner/repo", "owner/repo"] },
    { "id": "r5", "no_match_response": "..." }
  ]
}
```

Rules for each entry:

- Include exactly one entry per request id (`r1`-`r5`), in any order.
- For a request where a pre-built package plausibly exists (this applies to at
  least four of the five requests):
  - `primary_query`: the keyword search you'd run first. It must be specific
    enough to the request's actual subject matter to surface targeted results
    — a single generic word describing the general field is not enough on its
    own.
  - `alternative_query`: a different search you'd try using different
    terminology, in case the first search comes up empty. It must not be
    identical to `primary_query`, and must still be relevant to the request.
  - `check_sources`: one or two `"owner/repo"` strings naming the specific
    GitHub source repositories that a knowledgeable user of this registry
    would check first, because they are known to host an especially large,
    popular, well-maintained collection of packages across many topics (not
    just one narrow topic).
- For a request where no pre-built package plausibly exists because the need
  is too specific/one-off to this team, instead provide a single
  `no_match_response` string containing the message you'd send back to that
  colleague. That message must:
  1. Clearly tell them no existing package was found for this.
  2. Offer to help them accomplish the underlying task directly, right now.
  3. Give one concrete, actionable suggestion for the specific command or
     workflow they could use with this same registry tool to package up and
     save this as a reusable capability for next time, so they don't lose the
     work.

Write only `/workspace/search_plan.json`. Do not modify `requests.json`.
