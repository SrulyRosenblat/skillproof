#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const WORKSPACE = '/workspace';

function fail(msg) {
  console.error('FAIL: ' + msg);
  process.exit(1);
}

const serverPagePath = path.join(WORKSPACE, 'server-page.js');
if (!fs.existsSync(serverPagePath)) fail('server-page.js is missing');

const dataSourcePath = path.join(WORKSPACE, 'data-source.js');
if (!fs.existsSync(dataSourcePath)) fail('data-source.js is missing');

let mod;
try {
  mod = require(path.resolve(serverPagePath));
} catch (e) {
  fail('server-page.js threw while loading: ' + e.message);
}

if (!mod || typeof mod.renderPage !== 'function') {
  fail('server-page.js must export a renderPage() function via module.exports');
}

let result;
try {
  result = mod.renderPage();
} catch (e) {
  fail('renderPage() threw an error: ' + e.message);
}

if (!result || typeof result !== 'object') {
  fail('renderPage() must return an object of the shape { component, props }');
}

if (result.component !== 'Dashboard') {
  fail(`renderPage() must return component: "Dashboard" (found: ${JSON.stringify(result.component)})`);
}

const props = result.props;
if (!props || typeof props !== 'object' || Array.isArray(props)) {
  fail('renderPage() must return a props object');
}

// Ground truth for the four users the client directory/active-panel must be
// able to render. Not read from data-source.js so that this check is
// independent of how the solution chooses to source/shape its data.
const EXPECTED_USERS = [
  { id: 1, name: 'Bob', email: 'bob@example.com', active: true },
  { id: 2, name: 'Alice', email: 'alice@example.com', active: false },
  { id: 3, name: 'Cara', email: 'cara@example.com', active: true },
  { id: 4, name: 'Dan', email: 'dan@example.com', active: true },
];
const ALLOWED_USER_FIELDS = ['active', 'email', 'id', 'name'].join(',');

const EXPECTED_PRODUCT = { name: 'Widget Pro', price: 49.99 };

// --- Validate users -------------------------------------------------------

if (!Array.isArray(props.users)) fail('props.users must be an array');
if (props.users.length !== EXPECTED_USERS.length) {
  fail(`props.users must contain exactly ${EXPECTED_USERS.length} users (found ${props.users.length})`);
}

for (const expected of EXPECTED_USERS) {
  const actual = props.users.find((u) => u && u.id === expected.id);
  if (!actual) fail(`props.users is missing the user with id ${expected.id}`);
  if (actual.name !== expected.name) fail(`user ${expected.id} has an incorrect name`);
  if (actual.email !== expected.email) fail(`user ${expected.id} has an incorrect email`);
  if (actual.active !== expected.active) fail(`user ${expected.id} has an incorrect active flag`);

  const keys = Object.keys(actual).sort().join(',');
  if (keys !== ALLOWED_USER_FIELDS) {
    fail(
      `user ${expected.id} must contain exactly the fields id, name, email, active and nothing else ` +
        `(found: ${keys || '(none)'})`
    );
  }
}

// --- Validate top-level prop keys (no extra / duplicate data) -------------

const topKeys = Object.keys(props).sort();
const SHAPE_WITH_PRODUCT_OBJECT = ['product', 'users'];
const SHAPE_WITH_PRODUCT_SCALARS = ['productName', 'productPrice', 'users'];

const isShapeA = JSON.stringify(topKeys) === JSON.stringify(SHAPE_WITH_PRODUCT_OBJECT);
const isShapeB = JSON.stringify(topKeys) === JSON.stringify(SHAPE_WITH_PRODUCT_SCALARS);

if (!isShapeA && !isShapeB) {
  fail(
    'props must contain exactly the fields users + product, OR users + productName + productPrice, ' +
      `and nothing else (found top-level keys: ${topKeys.join(', ')})`
  );
}

// --- Validate product representation --------------------------------------

if (isShapeA) {
  const product = props.product;
  if (!product || typeof product !== 'object' || Array.isArray(product)) {
    fail('props.product must be an object');
  }
  const pkeys = Object.keys(product).sort().join(',');
  if (pkeys !== 'name,price') {
    fail(`props.product must contain exactly the fields name, price and nothing else (found: ${pkeys})`);
  }
  if (product.name !== EXPECTED_PRODUCT.name) fail('props.product.name is incorrect');
  if (product.price !== EXPECTED_PRODUCT.price) fail('props.product.price is incorrect');
}

if (isShapeB) {
  if (props.productName !== EXPECTED_PRODUCT.name) fail('props.productName is incorrect');
  if (props.productPrice !== EXPECTED_PRODUCT.price) fail('props.productPrice is incorrect');
}

console.log('PASS');
process.exit(0);
