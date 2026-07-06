'use strict';

const fs = require('fs');
const path = require('path');

function readJson(relPath) {
  const full = path.join(__dirname, relPath);
  return JSON.parse(fs.readFileSync(full, 'utf8'));
}

function main() {
  const users = readJson('data/users.json');
  const orders = readJson('data/orders.json');
  const tagPairs = readJson('data/tag_pairs.json');

  // --- join orders -> users by id ---------------------------------------
  const userById = new Map(users.map((u) => [u.id, u]));
  const enrichedOrders = orders.map((order) => ({
    ...order,
    user: userById.get(order.userId) ?? null,
  }));

  // --- categorize users in a single pass ---------------------------------
  const admins = [];
  const testers = [];
  const inactive = [];
  for (const user of users) {
    if (user.isAdmin) admins.push(user.id);
    if (user.isTester) testers.push(user.id);
    if (!user.isActive) inactive.push(user.id);
  }
  const userCategories = { admins, testers, inactive };

  // --- tag change detection ------------------------------------------------
  const tagChanges = tagPairs.map((pair) => {
    if (pair.current.length !== pair.original.length) {
      return { id: pair.id, changed: true };
    }
    const currentSorted = pair.current.toSorted();
    const originalSorted = pair.original.toSorted();
    let changed = false;
    for (let i = 0; i < currentSorted.length; i++) {
      if (currentSorted[i] !== originalSorted[i]) {
        changed = true;
        break;
      }
    }
    return { id: pair.id, changed };
  });

  const outDir = path.join(__dirname, 'output');
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(
    path.join(outDir, 'enriched_orders.json'),
    JSON.stringify(enrichedOrders, null, 2)
  );
  fs.writeFileSync(
    path.join(outDir, 'user_categories.json'),
    JSON.stringify(userCategories, null, 2)
  );
  fs.writeFileSync(
    path.join(outDir, 'tag_changes.json'),
    JSON.stringify(tagChanges, null, 2)
  );
}

main();
