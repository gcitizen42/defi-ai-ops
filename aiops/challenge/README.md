# 0xFlorent Challenge Simulation Notes

Simulation-only notes and helper scripts for the 0xFlorent challenge work.

## Contents

- `simulate.sh` - Foundry/Anvil simulation entry point for known paths.
- `tenderly_simulate.py` - single-transaction Tenderly simulation helper.
- `tenderly_ask_claim_bundle.py` - Tenderly bundle simulation helper.
- `RendererProof.sol` - minimal renderer candidate for Art governance simulations.
- `sources/` - verified/public source snapshots used for analysis.
- `addresses.json` - contract addresses used by the simulations.

## Requirements

- Foundry tools: `cast`, `forge`, and optionally `anvil`
- Node.js 18+
- Python 3.11+
- Optional Tenderly credentials supplied by environment variables or a local env file

## Safety

- Default usage is simulation-only.
- Do not store RPC keys, Tenderly access keys, private keys, or wallet seed phrases in this folder.
- Re-check live state before attempting to reproduce any historical simulation manually.
