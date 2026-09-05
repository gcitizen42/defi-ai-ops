#!/usr/bin/env node
import fs from "node:fs";

const out = new Set();
const add = (x) => {
  if (x !== undefined && x !== null && String(x).length) out.add(String(x));
};

const names = [
  "Bequeath", "Ratchet", "Fork", "Pyre", "Ask", "Lineage", "Tug",
  "By Me", "Proof of Life", "Verb", "Vault", "Lost", "Found", "Art"
];
const fragments = [
  "read the hands", "read the hands that fill it", "hands that fill it",
  "one of a set", "whoever wants the rest follows the hands that fill it",
  "a pool that only grows", "sealed by a hash", "its preimage opens it once"
];
const addresses = [
  "0x92E5D4582d2DaAeC18a8ebCa7ED5341f4183557a",
  "0x6b77136442bBd008fF2E185Bda819cD7ba367e96",
  "0x3567dBd98fe316408C7ebAB6Ac6B12a0F27A7ed5",
  "0x4f33E5AA6D6c83E0bD32887b3A65A6d26e28B57b",
  "0x7392197B936a0b3d3E3734a48acA3C9b2682098F",
  "0x0596702Ae60A2b27593a89F2E69855817E1f2CC2"
];
const nums = ["25870436", "25870442", "25871204", "25871543", "0.01", "0.20", "0.21"];

for (const n of names) {
  add(n); add(n.toLowerCase()); add(n.replaceAll(" ", "")); add(n.replaceAll(" ", "-").toLowerCase());
}
for (const f of fragments) add(f);
for (const a of addresses) { add(a); add(a.toLowerCase()); add(a.slice(2)); add(a.toLowerCase().slice(2)); }
for (const n of nums) add(n);

for (const left of [...names, ...fragments]) {
  for (const right of [...names, ...addresses, ...nums]) {
    add(`${left}:${right}`);
    add(`${left}-${right}`);
    add(`${left} ${right}`);
    add(`${left}${right}`);
    add(`${left.toLowerCase()}:${String(right).toLowerCase()}`);
  }
}

for (const a of addresses) {
  for (const b of addresses) {
    if (a !== b) {
      add(`${a}${b}`);
      add(`${a.toLowerCase()}${b.toLowerCase()}`);
      add(`${a}:${b}`);
      add(`${a.toLowerCase()}:${b.toLowerCase()}`);
    }
  }
}

fs.writeFileSync("protocol-security-lab/challenge-simulations/vault-candidates.generated.txt", [...out].join("\n") + "\n");
console.log(`wrote ${out.size} candidates`);
