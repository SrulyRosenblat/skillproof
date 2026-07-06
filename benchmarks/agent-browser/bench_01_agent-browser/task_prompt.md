# Employee Portal Login

Your workspace (`/workspace`) contains:

- `bin/agent-browser` — a command-line browser automation tool. Invoke it from
  `/workspace` as:
  ```
  python3 bin/agent-browser <args...>
  ```
- `site/portal.html` — a local employee portal login page.
- `data/employee_directory.json` — a directory of employees, each with an
  `employee_id` and `access_code`.

## Goal

Using the `agent-browser` tool, log into the portal at `site/portal.html` as the
employee named exactly `Jordan Blake`, entering the access code recorded for
that employee in `data/employee_directory.json`. Once logged in successfully,
the portal displays a confirmation code — retrieve its exact text.

`agent-browser` is a real tool with its own command syntax; it does not accept
arbitrary or guessed arguments, so you'll need to figure out how it actually
works before you can drive it successfully.

## Required output

Write your result to `/workspace/result.json`. It must be valid JSON containing
exactly one key:

```json
{"confirmation_code": "<the confirmation code you retrieved>"}
```

The value must be the exact confirmation code text produced by a successful
login through the tool — not a guessed, fabricated, or manually-derived value.
