# Protocol Security Challenge Simulations

This folder is for defensive protocol-security research and simulation only.
Scripts are intended for local forks, Tenderly virtual networks, and historical
analysis. They should not be treated as live transaction playbooks.

## Contents

- `simulate.sh` - Foundry/Anvil simulation entry point for known paths.
- `tenderly_simulate.py` - single-transaction Tenderly simulation helper.
- `tenderly_ask_claim_bundle.py` - Tenderly bundle simulation helper for Ask quest 4.
- `fetch_sources.mjs` - source snapshot extraction helper.
- `generate_vault_candidates.mjs` - vault secret candidate list generator.
- `full_function_sweep.sh` - function sweep helper for local fork analysis.
- `RendererProof.sol` - minimal renderer candidate for Art governance simulations.
- `sources/` - verified/public source snapshots used for analysis.
- `addresses.json` - contract addresses used by the simulations.

## Requirements

- Foundry tools: `cast`, `forge`, and optionally `anvil`
- Node.js 18+
- Python 3.11+
- Optional Tenderly credentials supplied by environment variables or a local env file

Required Tenderly variables:

```text
TENDERLY_ACCOUNT_SLUG=
TENDERLY_PROJECT_SLUG=
TENDERLY_ACCESS_KEY=
```

Keep real values outside this repository.

## Setup

Use a Tenderly vnet RPC:

```bash
export TENDERLY_RPC_URL="https://..."
chmod +x protocol-security-lab/challenge-simulations/simulate.sh
protocol-security-lab/challenge-simulations/simulate.sh state
```

Or use a local Anvil fork:

```bash
anvil --fork-url https://ethereum-rpc.publicnode.com
chmod +x protocol-security-lab/challenge-simulations/simulate.sh
protocol-security-lab/challenge-simulations/simulate.sh state
```

## Safety

- Default usage is simulation-only.
- Do not store RPC keys, Tenderly access keys, private keys, or wallet seed phrases in this folder.
- Re-check live state before attempting to reproduce any historical simulation manually.

## Research Notes

The notes below capture historical simulation paths that were useful for
understanding contract state, accounting edges, and governance gates.

### Bounty Quest 4

Simulation explored buying `Ask` from the steward and claiming bounty quest `4`.

Observed state showed `Ask.price() = 0.01 ETH`, `Ask.ownerOf(1) = steward`, `Bounties.wonBy(4) = 0x0`, and the bounty contract still held enough ETH for three rewards.

### Bounty Quest 9

This path requires holding at least two Fork editions. The fork result confirmed the qualification logic and one-reward-per-address constraint.

### Art Renderer Control Path

The renderer-governance path demonstrated how support thresholds and volume gates affect renderer adoption in a forked environment. `RendererProof.sol` is kept as a minimal renderer interface example for review.

### Bequeath Path

Open bounty quest 2 requires holding Bequeath while not being the steward. Observed state showed Bequeath was still held by the steward, with a public `claim()` time lock observed for `2027-02-28 20:20:59 UTC`.

Simulation entry points remain in `simulate.sh` for reproducible local analysis.

## Extraction Surface Summary

The main ETH surfaces are:

- `Bounties.claim(q)`: externally claimable, but only one reward per address and only if `qualifies(q, msg.sender)` is true.
- `Collectible.pullBeacon(amount)`: steward-only, not available to normal users.
- `Collectible.lifeBalance`: funded by `ProofOfLife.beat()`, intentionally non-withdrawable.
- Sale functions such as `Ask.buy`, `Ratchet.buy`, `Pyre.buy`, `Lineage.buy`, and `Fork.mint`: transfer ETH according to the mechanic, but do not expose a generic public withdrawal.

The main art/NFT surfaces are:

- `Ask.buy(newPrice)`
- `Fork.mint()`
- `Tug.paint(uint24 target)`
- `ProofOfLife.beat()`
- `Ratchet.buy()`
- `Pyre.buy()`
- `Lineage.buy()`
- `ByMe.buy()`
- `Bequeath.bequeath(to)` by current holder, or `Bequeath.claim()` after timeout
