# Tenderly Ask Quest 4 Bundle Simulation

Simulation type:

```text
Tenderly simulate-bundle API
```

Transactions:

```text
1. Ask.buy(uint256 newPrice)
2. Bounties.claim(uint8 q)
```

Target wallet:

```text
0x3070f20f86fda706ac380f5060d256028a46ec29
```

## Step 1: Ask.buy

Contract:

```text
0xa0096d95daaa3cf19091c0f0627b3913c2e417ae
```

Input:

```text
newPrice = 10000000000000042
msg.value = 10000000000000000 wei
```

Tenderly result:

```text
status = true
gas_used = 93282
```

Important state changes:

```text
Ask.price:
  10000000000000000 -> 10000000000000042

Ask._ownerOf[1]:
  0x3567dBd98fe316408C7ebAB6Ac6B12a0F27A7ed5
  -> 0x3070f20f86fda706ac380f5060d256028a46ec29

Ask balance:
  user: 0 -> 1
  steward: 1 -> 0
```

## Step 2: Bounties.claim

Contract:

```text
0xAAB498e3974F7543724602604f4EC6c44867FC72
```

Input:

```text
q = 4
msg.value = 0
```

Tenderly result:

```text
status = true
gas_used = 88518
```

Important state and balance changes:

```text
Bounties.claimed[user]:
  false -> true

Bounties.wonBy[4]:
  0x0000000000000000000000000000000000000000
  -> 0x3070f20f86fda706ac380f5060d256028a46ec29

User ETH balance:
  9.990000000000000000 -> 9.992500000000000000

Bounties ETH balance:
  0.007500000000000000 -> 0.005000000000000000
```

Raw JSON:

```text
archive/aiops-challenge-results/tenderly-ask-claim-result.json
```

The raw JSON is local-only and intentionally ignored by git. Keep this summary in
the repository instead of publishing the full simulation payload.
