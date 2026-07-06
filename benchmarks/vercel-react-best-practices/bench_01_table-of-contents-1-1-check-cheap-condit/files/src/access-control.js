'use strict';

/**
 * Access-control and request-handling helpers for an internal admin panel.
 *
 * Each exported function receives a `deps` object containing the functions it
 * needs to do its job. Some of those dependency functions are cheap, purely
 * synchronous checks on data the caller already has in memory. Others are
 * expensive asynchronous calls that hit a remote feature-flag service, a
 * user-data API, a permissions service, or a database (they are simulated
 * here as async functions, since in production they involve real network or
 * database round trips).
 */

// 1. Feature-flag gated access check.
//
// A user should be treated as having access to `featureName` only if BOTH:
//   - `user.isBetaTester` is true, AND
//   - the remote feature flag for `featureName` is enabled.
async function checkFeatureAccess(deps, user, featureName) {
  const flag = await deps.getFeatureFlag(featureName);

  if (flag && user.isBetaTester) {
    return true;
  }
  return false;
}

// 2. Request handler with an early-out.
//
// If `skipProcessing` is true, the handler should immediately return
// `{ skipped: true }` without doing any further work. Otherwise, it should
// fetch the user's data and hand it off to `processUserData`, returning
// whatever that produces.
async function handleRequest(deps, userId, skipProcessing) {
  const userData = await deps.fetchUserData(userId);

  if (skipProcessing) {
    return { skipped: true };
  }

  return deps.processUserData(userData);
}

// 3. Resource update with validation.
//
// Looks up the resource and the requesting user's permissions, then:
//   - if the resource doesn't exist, returns `{ error: 'Not found' }`
//   - if the user lacks edit permission, returns `{ error: 'Forbidden' }`
//   - otherwise, applies the update and returns the result of
//     `deps.updateResourceData(resource, permissions)`
async function updateResource(deps, resourceId, userId) {
  const permissions = await deps.fetchPermissions(userId);
  const resource = await deps.getResource(resourceId);

  if (!resource) {
    return { error: 'Not found' };
  }

  if (!permissions.canEdit) {
    return { error: 'Forbidden' };
  }

  return deps.updateResourceData(resource, permissions);
}

module.exports = { checkFeatureAccess, handleRequest, updateResource };
