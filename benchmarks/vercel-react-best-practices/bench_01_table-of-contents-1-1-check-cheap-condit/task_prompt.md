# Task: Reduce unnecessary async calls in an admin-panel helper module

The file `/workspace/src/access-control.js` contains three exported async
functions used by an internal admin panel:

- `checkFeatureAccess(deps, user, featureName)`
- `handleRequest(deps, userId, skipProcessing)`
- `updateResource(deps, resourceId, userId)`

Each function receives a `deps` object containing the functions it needs.
Some of these dependency functions are cheap, purely synchronous checks on
data the caller already has (e.g. a boolean already present on an in-memory
object). Others are expensive asynchronous calls that simulate a round trip
to a remote feature-flag service, a user-data API, a permissions service, or
a database. In this codebase they're all modeled as functions on `deps` so
they can be swapped out in tests, but in production the async ones carry
real network/database latency and, in some cases, real monetary cost per
call.

Read the file to see the current behavior contract for each function (it's
documented in the comments above each one, and the current code already
implements that contract correctly in terms of return values).

**The problem:** several of these functions call one or more of the
expensive `deps` async functions even in situations where the call's result
can't possibly change what gets returned. That wasted work adds latency (and
sometimes cost) for no benefit.

**Your task:** refactor `checkFeatureAccess`, `handleRequest`, and
`updateResource` in `/workspace/src/access-control.js` so that:

1. For every combination of inputs, each function still returns *exactly*
   the same value it does today (the documented behavior contract must not
   change).
2. Each expensive async `deps` function is invoked *only* when its result is
   actually necessary to determine the final return value. If a function's
   outcome is already fully determined by cheaper information available
   earlier, the expensive call must be skipped entirely on that path.
3. You must not change the exported function names, their parameter order,
   or the shape/names of the `deps` object each one expects — only the
   internal logic and call ordering.
4. Do not add new dependency functions, remove existing ones, or change
   what each dependency function is called with in the cases where it *is*
   still called (e.g. `updateResourceData` must still be called with the
   same `(resource, permissions)` it receives today).

Your solution will be checked by importing the module and calling each
exported function directly with a variety of inputs and instrumented
`deps` implementations, verifying both the returned values and which
dependency functions were actually invoked for each input combination.

When you're done, `/workspace/src/access-control.js` should be a valid
Node.js CommonJS module (`module.exports = { checkFeatureAccess,
handleRequest, updateResource }`) that can be `require()`-d directly.
