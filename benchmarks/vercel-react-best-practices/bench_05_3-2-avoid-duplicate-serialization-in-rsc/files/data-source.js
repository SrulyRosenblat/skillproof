'use strict';

function fetchUsers() {
  return [
    {
      id: 1,
      name: 'Bob',
      email: 'bob@example.com',
      active: true,
      role: 'admin',
      joinedAt: '2020-01-01',
      lastLoginAt: '2024-03-01',
      phone: '555-0101',
      address: '12 Elm St',
      department: 'Engineering',
      managerId: null,
    },
    {
      id: 2,
      name: 'Alice',
      email: 'alice@example.com',
      active: false,
      role: 'member',
      joinedAt: '2021-05-12',
      lastLoginAt: '2024-01-15',
      phone: '555-0102',
      address: '88 Oak Ave',
      department: 'Sales',
      managerId: 1,
    },
    {
      id: 3,
      name: 'Cara',
      email: 'cara@example.com',
      active: true,
      role: 'member',
      joinedAt: '2019-11-23',
      lastLoginAt: '2024-02-20',
      phone: '555-0103',
      address: '4 Pine Rd',
      department: 'Support',
      managerId: 1,
    },
    {
      id: 4,
      name: 'Dan',
      email: 'dan@example.com',
      active: true,
      role: 'member',
      joinedAt: '2022-07-04',
      lastLoginAt: '2024-03-10',
      phone: '555-0104',
      address: '9 Birch Ln',
      department: 'Engineering',
      managerId: 1,
    },
  ];
}

function fetchProduct() {
  return {
    id: 'p-001',
    name: 'Widget Pro',
    price: 49.99,
    description: 'A very fine widget for all your widget needs.',
    sku: 'WGT-PRO-001',
    inventoryCount: 128,
    supplierId: 'sup-42',
    warehouseLocation: 'Aisle 12',
  };
}

module.exports = { fetchUsers, fetchProduct };
