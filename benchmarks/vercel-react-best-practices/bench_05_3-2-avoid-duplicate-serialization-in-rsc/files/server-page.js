'use strict';

/**
 * Simulates a Next.js React Server Component page.
 *
 * `renderPage()` represents the server component's render logic: it loads
 * data on the server and returns the exact `props` payload that gets sent
 * across the network to the client component `Dashboard`.
 */
const { fetchUsers, fetchProduct } = require('./data-source');

function renderPage() {
  const users = fetchUsers();
  const product = fetchProduct();

  const activeUsersSorted = users
    .filter((u) => u.active)
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((u) => u.name);

  return {
    component: 'Dashboard',
    props: {
      users,
      activeUsersSorted,
      product,
      productName: product.name,
      productPrice: product.price,
    },
  };
}

module.exports = { renderPage };
