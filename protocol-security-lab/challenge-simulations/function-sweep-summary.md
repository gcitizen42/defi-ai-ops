# Function Sweep Summary

Full raw fork output:

```text
protocol-security-lab/challenge-simulations/function-sweep.md
```

Fork block:

```text
25874351
```

Target wallet:

```text
0x3070f20f86fda706ac380f5060d256028a46ec29
```

## Confirmed User-Callable Outcomes

| Contract | Function | Result | Gain |
| --- | --- | --- | --- |
| Tug | `paint(uint24)` | succeeds | owns Tug, but quest 0 already taken |
| ProofOfLife | `beat()` | succeeds with 0.001 ETH | owns Life, but quest 1 already taken |
| Fork | `mint()` | succeeds | owns Fork NFT; funds Vault |
| Fork + Bounties | two `mint()` calls then `claim(9)` | succeeds | wins open 0.0025 ETH bounty quest 9 |
| Ask | `buy(uint256)` | succeeds | owns Ask |
| Ask | `setPrice(uint256)` after buying | succeeds | can set Ask display price |
| Ask + Bounties | `buy(...)` then `claim(4)` | succeeds | wins open 0.0025 ETH bounty quest 4 |
| Lineage | `buy()` | succeeds | owns Lineage; funds Vault increment; quest 5 already taken |
| Pyre | `buy()` | succeeds | owns Pyre; quest 7 already taken |
| Art | Fork majority + Lineage volume + `endorse()` | succeeds | sets `Art.renderer` |
| Vault | direct ETH transfer | succeeds | only increases Vault balance |
| Collectible | `pulse()` | succeeds | only increases non-withdrawable life balance |

## Confirmed Reverts Or Blocked Paths

| Contract | Function | Reason |
| --- | --- | --- |
| Bequeath | `claim()` | locked until `lastMove + 182 days` |
| Bequeath | `bequeath(address)` as user | only current holder can call |
| Ratchet | `buy()` | currently reverts with `pay`; current holder cannot receive payout |
| Verb | `echo()` | currently `too soon` |
| ByMe | `buy()` | current price is too high for practical execution |
| Bounties | `claim(0/1/3/5/6/7/8)` | quests already taken |
| Bounties | `withdraw()` as user | steward only |
| Vault | `unlock(wrongSecret,to)` | wrong key |
| Collectible | `seedBeacon()` / `pullBeacon()` as user | steward only |

## Open Bounties At Sweep Time

```text
quest 2: Bequeath holder, open but requires steward gift or timeout
quest 4: Ask holder, open and user-callable
quest 9: two Fork editions, open and user-callable
```

`Bounties.claimed(address)` means the same wallet can only claim one reward.
Use separate wallets if the challenge goal is to claim multiple open bounties.

## Contract Link Map

```text
Art
  - knows Fork for voting weight
  - knows all pieces for volume()
  - renderer affects tokenURI metadata only

Each piece
  - calls Art.rendering(id) from tokenURI(id)
  - reports piece volume to Art
  - inherits steward-only seedBeacon/pullBeacon
  - inherits public pulse(), which is non-withdrawable accounting

Fork
  - mint() sends mint price to Vault
  - Fork balance is voting power in Art

Lineage
  - buy() refunds previous paid amount to current holder
  - sends only the increment to Vault
  - still records gross price as volume, so repeat buys can raise Art.volume()

Bounties
  - checks ownership/witness state across pieces
  - pays fixed 0.0025 ETH reward for open quests
  - no proxy into Vault or piece balances

Vault
  - accepts ETH from Fork/Lineage/direct sends
  - only sends ETH out through unlock(secret,to)
```

## Main Conclusion

There is no proxy-style contract in the verified set that lets a normal wallet
withdraw all ETH. The actual movement surfaces are separate:

- `Bounties.claim(q)` for small open rewards.
- `Vault.unlock(secret,to)` for the Vault, if the hash preimage is discovered.
- Piece buy/mint functions for ownership and collection volume.
- `Art.endorse(candidate)` for metadata/art control after Fork majority and
  volume threshold.
