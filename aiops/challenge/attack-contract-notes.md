# Historical Attack Contract Notes

Contract:

```text
0x6b77136442bBd008fF2E185Bda819cD7ba367e96
```

Historical transaction:

```text
0x32e93bd9a8094e1e190e5b234696e285754047da7065e0827727212bb5db4323
```

Observed public selectors/getters:

```text
attack() selector: 0x9e5faafc
controller() = 0x38c40EAd3D0Fe7959eb9DFE8337B3c4929884d2c
lineage() = 0x7392197B936a0b3d3E3734a48acA3C9b2682098F
seedAmount() = 200000000000000000
lastFee() = 0
```

What it did:

- The controller called `attack()` with `0.2 ETH`.
- The transaction used WETH and the Balancer Vault.
- The helper bought `Lineage` repeatedly.
- Each `Lineage.buy()` sent a `0.01 ETH` increment into `Vault`.
- The helper became the Lineage holder and claimed bounty quest `5`.

Fork reuse test:

```text
cast send 0x6b77136442bBd008fF2E185Bda819cD7ba367e96 'attack()' \
  --from 0x38c40EAd3D0Fe7959eb9DFE8337B3c4929884d2c \
  --unlocked \
  --value 200000000000000000
```

Result on current fork state:

```text
execution reverted
```

Interpretation:

- It is evidence for the intended `Lineage` mechanism: use capital briefly,
  repeatedly buy the same piece, raise gross collection volume, and fund `Vault`
  only by the `0.01 ETH` increment each time.
- It does not expose `Vault.unlock`.
- It is not a proxy or privileged router for the rest of the collection.
- It is not directly reusable for an open bounty, because quest `5` is already
  claimed and the helper is controller-specific.
