'use strict';

const { fetchUsers, fetchProduct } = require('./data-source');

function renderPage() {
  const users = fetchUsers().map(({ id, name, email, active }) => ({
    id,
    name,
    email,
    active,
  }));
  const product = fetchProduct();

  return {
    component: 'Dashboard',
    props: {
      users,
      productName: product.name,
      productPrice: product.price,
    },
  };
}

module.exports = { renderPage };
