#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const root = new URL(".", import.meta.url).pathname;
const outDir = path.join(root, "sources");
const addresses = JSON.parse(fs.readFileSync(path.join(root, "addresses.json"), "utf8"));

const contracts = {
  art: addresses.art,
  bounties: addresses.bounties,
  bequeath: addresses.pieces.bequeath,
  ratchet: addresses.pieces.ratchet,
  fork: addresses.pieces.fork,
  pyre: addresses.pieces.pyre,
  ask: addresses.pieces.ask,
  lineage: addresses.pieces.lineage,
  tug: addresses.pieces.tug,
  byMe: addresses.pieces.byMe,
  proofOfLife: addresses.pieces.proofOfLife,
  verb: addresses.pieces.verb,
  vault: addresses.vault
};

async function fetchStandardJson(address) {
  const url = `https://etherscan.io/address/${address}#code`;
  const response = await fetch(url, { headers: { "user-agent": "Mozilla/5.0" } });
  if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
  const html = await response.text();
  const marker = "var editor_contractJsonData = ";
  const start = html.indexOf(marker);
  const end = html.indexOf("\n        EtherEditor.init", start);
  if (start < 0 || end < 0) throw new Error(`${address}: verified source JSON not found`);
  let literal = html.slice(start + marker.length, end).trim();
  if (literal.endsWith(";")) literal = literal.slice(0, -1);
  return JSON.parse(eval(literal));
}

function safePath(name) {
  return name.replace(/[^a-zA-Z0-9_.-]/g, "_");
}

fs.mkdirSync(outDir, { recursive: true });

for (const [name, address] of Object.entries(contracts)) {
  try {
    const standardJson = await fetchStandardJson(address);
    const contractDir = path.join(outDir, safePath(name));
    fs.mkdirSync(contractDir, { recursive: true });
    fs.writeFileSync(path.join(contractDir, "standard-json.json"), JSON.stringify(standardJson, null, 2) + "\n");
    for (const [sourcePath, source] of Object.entries(standardJson.sources || {})) {
      const target = path.join(contractDir, sourcePath);
      fs.mkdirSync(path.dirname(target), { recursive: true });
      fs.writeFileSync(target, source.content);
    }
    console.log(`${name}: saved ${Object.keys(standardJson.sources || {}).length} files`);
  } catch (error) {
    console.log(`${name}: ${error.message}`);
  }
}
