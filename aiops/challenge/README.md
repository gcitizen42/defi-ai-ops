# 0xFlorent Challenge Simulation Notes

This folder is for simulation only. The script refuses to send transactions to
Ethereum mainnet unless `ALLOW_MAINNET=1` is set.

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
chmod +x aiops/challenge/simulate.sh
aiops/challenge/simulate.sh state
```

Or use a local Anvil fork:

```bash
anvil --fork-url https://ethereum-rpc.publicnode.com
chmod +x aiops/challenge/simulate.sh
aiops/challenge/simulate.sh state
```

## Safety

- Default usage is simulation-only.
- Do not store RPC keys, Tenderly access keys, private keys, or wallet seed phrases in this folder.
- Re-check live state before attempting to reproduce any historical simulation manually.

## Where I Would Start

Start with open bounty quest 4:

1. Buy `Ask` from the steward at its current price.
2. Claim bounty quest `4`.

Reason: it is the simplest live open path. Current state showed `Ask.price() =
0.01 ETH`, `Ask.ownerOf(1) = steward`, `Bounties.wonBy(4) = 0x0`, and the bounty
contract still held enough ETH for three rewards.

Simulation:

```bash
TENDERLY_RPC_URL="$TENDERLY_RPC_URL" aiops/challenge/simulate.sh ask-q4
```

Observed fork result:

```text
Ask.buy(...) success
Bounties.claim(4) success
Ask.ownerOf(1) = 0x3070f20f86fDa706Ac380F5060D256028a46eC29
Bounties.wonBy(4) = 0x3070f20f86fDa706Ac380F5060D256028a46eC29
Bounties balance moved from 0.0075 ETH to 0.005 ETH
```

## Second Path

Open bounty quest 9 requires holding at least two Fork editions.

Simulation:

```bash
TENDERLY_RPC_URL="$TENDERLY_RPC_URL" aiops/challenge/simulate.sh fork-q9
```

This is not profitable by itself. It spends the current Fork mint price plus the
next increased price and claims only `0.0025 ETH`, but it leaves the address with
two Fork NFTs.

Observed fork result from a fresh fork:

```text
Fork.mint() at 0.011 ETH success, minted token id 2
Fork.mint() at 0.0121 ETH success, minted token id 3
Bounties.claim(9) success
Fork.balanceOf(user) = 2
Bounties.wonBy(9) = 0x3070f20f86fDa706Ac380F5060D256028a46eC29
Bounties balance moved from 0.0075 ETH to 0.005 ETH
```

Do not run quest 4 and quest 9 from the same address if the objective is claiming
both bounties. `Bounties.claimed(address)` allows only one reward per address.

## Art Renderer Control Path

`Art.endorse(candidate)` can adopt a renderer when both gates are true:

- `Fork.balanceOf(voter) > 0`
- total support is a strict majority of `Fork.totalSupply()`
- `Art.volume() >= 10 ETH`

Fresh-fork simulation at block `25874289` showed this path works from
`0x3070f20f86fda706ac380f5060d256028a46ec29`:

```bash
TENDERLY_RPC_URL="$TENDERLY_RPC_URL" aiops/challenge/simulate.sh art-control
```

Observed result:

```text
Fork.mint() twice for voting majority
Lineage.buy() 25 times to push Art.volume() over 10 ETH
Art.propose(user) success
Art.endorse(user) success
Art.volume() = 10.4132 ETH
Fork.balanceOf(user) = 2
Lineage.ownerOf(1) = 0x3070f20f86fDa706Ac380F5060D256028a46eC29
Art.renderer() = 0x3070f20f86fDa706Ac380F5060D256028a46eC29
```

This proves art governance control. Setting the renderer to an EOA proves state
control, but for a cleaner public win, deploy a tiny renderer contract first and
endorse that contract address instead. The renderer candidate should implement
the expected `render(address piece, uint256 id)` interface used by `Art`.
Use `RendererProof.sol` in this folder as a minimal candidate contract.

## Bequeath Path

Open bounty quest 2 requires holding Bequeath while not being the steward.
Current state showed Bequeath is still held by the steward. Public `claim()` is
time-locked until `2027-02-28 20:20:59 UTC`, unless the holder moves it and
resets `lastMove`.

Simulation:

```bash
TENDERLY_RPC_URL="$TENDERLY_RPC_URL" aiops/challenge/simulate.sh bequeath-q2
```

## Etherscan Write Calls To Replicate A Successful Simulation

These are the direct write functions a normal wallet can trigger on Etherscan.
Only use them after confirming live state has not changed.

### Claim Ask Bounty Quest 4

Contract: `Ask` at `0xa0096d95daaa3cf19091c0f0627b3913c2e417ae`

Function: `buy(uint256 newPrice)`

Inputs:

```text
newPrice = 10000000000000000
msg.value = current Ask.price(), currently 10000000000000000 wei if unchanged
```

Then:

Contract: `Bounties` at `0xAAB498e3974F7543724602604f4EC6c44867FC72`

Function: `claim(uint8 q)`

Inputs:

```text
q = 4
```

### Claim Fork Collector Bounty Quest 9

Contract: `Fork` at `0x4f33e5aa6d6c83e0bd32887b3a65a6d26e28b57b`

Function: `mint()`

Call once with `msg.value = current Fork.price()`, then call again with the new
`Fork.price()` after the first mint. Then call:

Contract: `Bounties` at `0xAAB498e3974F7543724602604f4EC6c44867FC72`

Function: `claim(uint8 q)`

Inputs:

```text
q = 9
```

### Take Renderer Governance Control

First deploy a renderer candidate, for example
`aiops/challenge/RendererProof.sol`, with constructor argument:

```text
claimant_ = 0x3070f20f86fda706ac380f5060d256028a46ec29
```

Contract: `Fork` at `0x4f33e5aa6d6c83e0bd32887b3a65a6d26e28b57b`

Function: `mint()`

Call repeatedly until your wallet has strict majority voting weight:

```text
your Fork balance * 2 > Fork.totalSupply()
msg.value = current Fork.price() for each mint
```

At the observed state, two mints were enough because only one Fork existed before
the simulation.

Contract: `Lineage` at `0x7392197b936a0b3d3e3734a48aca3c9b2682098f`

Function: `buy()`

Repeat until:

```text
Art.volume() >= 10000000000000000000
msg.value = current Lineage.price() for each buy
```

At the observed state, 25 Lineage buys after the two Fork mints reached the
volume gate. Re-read `Lineage.price()` before every buy, because the price moves
after each call.

Contract: `Art` at `0xa01a0386b0fb47296C52d5d2492Fbe01BfDa85B8`

Functions:

```text
propose(address candidate)
endorse(address candidate)
```

Use your deployed renderer contract as `candidate`. If the only goal is proving
state control in a simulation, the wallet address itself can be used as
`candidate`, as in the fork run above.

### Bequeath Bounty Quest 2

Contract: `Bequeath` at `0x4332bd627c7712718d5373ce9d6c6bced6338a0e`

Function: `claim()`

This is only callable after `lastMove + 182 days`. Current observed unlock was
`2027-02-28 20:20:59 UTC`. If the current holder calls `bequeath(address to)`,
that timer resets.

Then call `Bounties.claim(2)`.

## Extraction Surface Summary

The main ETH surfaces are:

- `Bounties.claim(q)`: externally claimable, but only one reward per address and
  only if `qualifies(q, msg.sender)` is true.
- `Collectible.pullBeacon(amount)`: steward-only, not available to normal users.
- `Collectible.lifeBalance`: funded by `ProofOfLife.beat()`, intentionally
  non-withdrawable.
- Sale functions such as `Ask.buy`, `Ratchet.buy`, `Pyre.buy`, `Lineage.buy`,
  and `Fork.mint`: transfer ETH according to the mechanic, but do not expose a
  generic public withdrawal.

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
