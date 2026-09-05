# Puzzle Plan

Objective: find challenge-intended call sequences that move ETH or ownership to
`0x3070f20f86fda706ac380f5060d256028a46ec29`, then document the exact evidence
and Etherscan calls.

This is not a generic security audit. The working method is:

1. Identify every public/external function that can change ownership, balances,
   bounty state, renderer state, or recorded volume.
2. Classify each function as direct claim, paid acquisition, governance action,
   time-gated action, or steward-only action.
3. Simulate the cheapest currently-open paths first.
4. For any suspicious mechanic, write a minimal transaction sequence and check
   final owner/balance deltas.
5. Keep only paths that work from a normal externally-owned address or a small
   helper contract deployable by the wallet.

## Current Working Priorities

1. `Ask.buy(newPrice)` then `Bounties.claim(4)`.
   This is currently the lowest-cost successful bounty path.

2. `Fork.mint()` twice then `Bounties.claim(9)`.
   This works but costs more and still only claims one bounty per address.

3. `Fork.mint()` enough for voting majority, `Lineage.buy()` until
   `Art.volume() >= 10 ETH`, then `Art.propose(candidate)` and
   `Art.endorse(candidate)`.
   Confirmed on a fresh fork at block `25874289`: two Fork mints plus 25
   Lineage buys made `Art.renderer()` equal the target address.

4. `Vault.unlock(secret, to)`.
   This is the main unresolved ETH extraction path. The function is public and
   sends the full vault balance to `to`, but it requires the preimage for the
   stored `SEAL`.

5. Helper-contract callback tests around sale functions.
   Targets: `Ask.buy`, `Ratchet.buy`, `Pyre.buy`, `Lineage.buy`.
   Reason: these functions call `_move(...)` then perform external ETH transfers.
   The puzzle question is whether a receiving contract can re-enter a public
   method and end with unexpected ownership or payout.

6. `Bequeath.claim()` time gate.
   Currently not live-callable until `2027-02-28 20:20:59 UTC` unless the steward
   gifts it and resets the timer.

## Non-Starters From Current Source

- `pullBeacon(amount)` is steward-only.
- `lifeBalance` is intentionally non-withdrawable.
- `Bounties.withdraw()` is steward-only.
- `ByMe.buy()` is currently priced near `1,000,000 ETH`, so it is not a practical
  immediate path.
- `Vault.unlock(...)` is not a non-starter, but brute forcing the preimage is not
  practical unless the thread/source/transaction history reveals a small
  candidate set.

## Tenderly Credential Location

Credentials exist in:

```text
/Users/Citizen42/Desktop/TdaoUtils/AI-ops/Tenderly_simulations/.env
```

Expected keys:

```text
TENDERLY_ACCOUNT_SLUG
TENDERLY_PROJECT_SLUG
TENDERLY_ACCESS_KEY
```

Do not copy the secret values into this folder.
