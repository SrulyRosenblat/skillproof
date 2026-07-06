'use strict';
/*
 * Preloaded via `node -r instrument.js solve.js`. Wraps a few Array.prototype
 * methods to count how many times their callback actually runs (i.e. how many
 * elements were scanned), then writes the tally to INSTRUMENT_OUTPUT on exit.
 * This measures algorithmic behavior by execution, not by reading source.
 */
const fs = require('fs');

const counts = {
  findCallbackInvocations: 0,
  filterCallbackInvocations: 0,
  sortInvocations: 0,
};

const origFind = Array.prototype.find;
Array.prototype.find = function (cb, thisArg) {
  const wrapped = function (...args) {
    counts.findCallbackInvocations++;
    return cb.apply(this, args);
  };
  return origFind.call(this, wrapped, thisArg);
};

const origFilter = Array.prototype.filter;
Array.prototype.filter = function (cb, thisArg) {
  const wrapped = function (...args) {
    counts.filterCallbackInvocations++;
    return cb.apply(this, args);
  };
  return origFilter.call(this, wrapped, thisArg);
};

const origSort = Array.prototype.sort;
Array.prototype.sort = function (...args) {
  counts.sortInvocations++;
  return origSort.apply(this, args);
};

if (typeof Array.prototype.toSorted === 'function') {
  const origToSorted = Array.prototype.toSorted;
  Array.prototype.toSorted = function (...args) {
    counts.sortInvocations++;
    return origToSorted.apply(this, args);
  };
}

process.on('exit', () => {
  const out = process.env.INSTRUMENT_OUTPUT;
  if (out) {
    fs.writeFileSync(out, JSON.stringify(counts));
  }
});
