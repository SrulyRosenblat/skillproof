'use strict';

// Loads /workspace/src/access-control.js and exercises each exported
// function with instrumented (spy) dependencies across a matrix of inputs.
// Asserts both:
//   (a) correctness: return values match the documented contract exactly
//   (b) laziness: expensive dependency functions are only invoked when their
//       result can actually affect the returned value
//
// Exit 0 = all checks passed, exit 1 = at least one check failed.

const path = require('path');
const fs = require('fs');

// grade.sh always invokes this script with cwd set to the workspace root.
const modPath = path.join(process.cwd(), 'src', 'access-control.js');

if (!fs.existsSync(modPath)) {
  console.error(`Missing file: ${modPath}`);
  process.exit(1);
}

delete require.cache[require.resolve(modPath)];
const mod = require(modPath);

const failures = [];

function makeSpy(fn) {
  const spy = (...args) => {
    spy.calls += 1;
    return fn(...args);
  };
  spy.calls = 0;
  return spy;
}

function expectEqual(actual, expected, message) {
  const a = JSON.stringify(actual);
  const e = JSON.stringify(expected);
  if (a !== e) {
    failures.push(`${message}: expected ${e}, got ${a}`);
  }
}

function expectCalls(spy, expected, message) {
  if (spy.calls !== expected) {
    failures.push(`${message}: expected ${expected} call(s), got ${spy.calls}`);
  }
}

async function checkRequiredExports() {
  for (const name of ['checkFeatureAccess', 'handleRequest', 'updateResource']) {
    if (typeof mod[name] !== 'function') {
      failures.push(`Module must export a function named "${name}"`);
    }
  }
}

async function testCheckFeatureAccess() {
  if (typeof mod.checkFeatureAccess !== 'function') return;

  {
    const getFeatureFlag = makeSpy(async () => true);
    const result = await mod.checkFeatureAccess({ getFeatureFlag }, { isBetaTester: false }, 'new-editor');
    expectEqual(result, false, 'checkFeatureAccess(isBetaTester=false, flag=true) return value');
    expectCalls(getFeatureFlag, 0, 'checkFeatureAccess(isBetaTester=false): getFeatureFlag call count');
  }
  {
    const getFeatureFlag = makeSpy(async () => false);
    const result = await mod.checkFeatureAccess({ getFeatureFlag }, { isBetaTester: false }, 'new-editor');
    expectEqual(result, false, 'checkFeatureAccess(isBetaTester=false, flag=false) return value');
    expectCalls(getFeatureFlag, 0, 'checkFeatureAccess(isBetaTester=false, flag=false): getFeatureFlag call count');
  }
  {
    const getFeatureFlag = makeSpy(async () => true);
    const result = await mod.checkFeatureAccess({ getFeatureFlag }, { isBetaTester: true }, 'new-editor');
    expectEqual(result, true, 'checkFeatureAccess(isBetaTester=true, flag=true) return value');
    expectCalls(getFeatureFlag, 1, 'checkFeatureAccess(isBetaTester=true, flag=true): getFeatureFlag call count');
  }
  {
    const getFeatureFlag = makeSpy(async () => false);
    const result = await mod.checkFeatureAccess({ getFeatureFlag }, { isBetaTester: true }, 'new-editor');
    expectEqual(result, false, 'checkFeatureAccess(isBetaTester=true, flag=false) return value');
    expectCalls(getFeatureFlag, 1, 'checkFeatureAccess(isBetaTester=true, flag=false): getFeatureFlag call count');
  }
}

async function testHandleRequest() {
  if (typeof mod.handleRequest !== 'function') return;

  {
    const fetchUserData = makeSpy(async () => ({ id: 'u1', name: 'Ada' }));
    const processUserData = makeSpy((data) => ({ processed: data.id }));
    const result = await mod.handleRequest({ fetchUserData, processUserData }, 'u1', true);
    expectEqual(result, { skipped: true }, 'handleRequest(skipProcessing=true) return value');
    expectCalls(fetchUserData, 0, 'handleRequest(skipProcessing=true): fetchUserData call count');
    expectCalls(processUserData, 0, 'handleRequest(skipProcessing=true): processUserData call count');
  }
  {
    const fetchUserData = makeSpy(async () => ({ id: 'u2', name: 'Grace' }));
    const processUserData = makeSpy((data) => ({ processed: data.id }));
    const result = await mod.handleRequest({ fetchUserData, processUserData }, 'u2', false);
    expectEqual(result, { processed: 'u2' }, 'handleRequest(skipProcessing=false) return value');
    expectCalls(fetchUserData, 1, 'handleRequest(skipProcessing=false): fetchUserData call count');
    expectCalls(processUserData, 1, 'handleRequest(skipProcessing=false): processUserData call count');
  }
}

async function testUpdateResource() {
  if (typeof mod.updateResource !== 'function') return;

  {
    const fetchPermissions = makeSpy(async () => ({ canEdit: true }));
    const getResource = makeSpy(async () => null);
    const updateResourceData = makeSpy(async () => ({ updated: true }));
    const result = await mod.updateResource(
      { fetchPermissions, getResource, updateResourceData },
      'r1',
      'u1'
    );
    expectEqual(result, { error: 'Not found' }, 'updateResource(resource missing) return value');
    expectCalls(getResource, 1, 'updateResource(resource missing): getResource call count');
    expectCalls(fetchPermissions, 0, 'updateResource(resource missing): fetchPermissions call count');
    expectCalls(updateResourceData, 0, 'updateResource(resource missing): updateResourceData call count');
  }
  {
    const fetchPermissions = makeSpy(async () => ({ canEdit: false }));
    const getResource = makeSpy(async () => ({ id: 'r2' }));
    const updateResourceData = makeSpy(async () => ({ updated: true }));
    const result = await mod.updateResource(
      { fetchPermissions, getResource, updateResourceData },
      'r2',
      'u2'
    );
    expectEqual(result, { error: 'Forbidden' }, 'updateResource(canEdit=false) return value');
    expectCalls(getResource, 1, 'updateResource(canEdit=false): getResource call count');
    expectCalls(fetchPermissions, 1, 'updateResource(canEdit=false): fetchPermissions call count');
    expectCalls(updateResourceData, 0, 'updateResource(canEdit=false): updateResourceData call count');
  }
  {
    const fetchPermissions = makeSpy(async () => ({ canEdit: true }));
    const getResource = makeSpy(async () => ({ id: 'r3' }));
    const updateResourceData = makeSpy(async (resource, permissions) => ({
      updated: true,
      id: resource.id,
      canEdit: permissions.canEdit,
    }));
    const result = await mod.updateResource(
      { fetchPermissions, getResource, updateResourceData },
      'r3',
      'u3'
    );
    expectEqual(
      result,
      { updated: true, id: 'r3', canEdit: true },
      'updateResource(canEdit=true) return value'
    );
    expectCalls(getResource, 1, 'updateResource(canEdit=true): getResource call count');
    expectCalls(fetchPermissions, 1, 'updateResource(canEdit=true): fetchPermissions call count');
    expectCalls(updateResourceData, 1, 'updateResource(canEdit=true): updateResourceData call count');
  }
}

async function run() {
  await checkRequiredExports();
  if (failures.length > 0) {
    console.error('FAILURES:');
    for (const f of failures) console.error(` - ${f}`);
    process.exit(1);
  }

  await testCheckFeatureAccess();
  await testHandleRequest();
  await testUpdateResource();

  if (failures.length > 0) {
    console.error('FAILURES:');
    for (const f of failures) console.error(` - ${f}`);
    process.exit(1);
  }

  console.log('All checks passed.');
  process.exit(0);
}

run().catch((err) => {
  console.error(`ERROR: ${(err && err.stack) || err}`);
  process.exit(1);
});
