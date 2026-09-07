# Threshold tBTC v2 Case Study

This is the first DAO Treehouse control-map seed. It covers selected Ethereum and Arbitrum One authority paths, not the full tBTC system.

Snapshot time: `2026-09-07T20:05:45Z`

| Network | Observation block | Governance Safe | Threshold | Timelock |
| --- | ---: | --- | ---: | --- |
| Ethereum | `25927757` | `0x9F6e...C2F5f` | 6 of 9 | `0x92f2...4913D` |
| Arbitrum One | `502787406` | `0x9F6e...C2F5f` | 6 of 9 | `0x6614...114e` |

The same Safe address exists on both networks, but its owner roster is not the same. DAO Treehouse treats addresses as chain-specific identities.

## Confirmed Paths

Ethereum:

```text
Governance Safe -> TBTCVault -> TBTC
Governance Safe -> Bank
Governance Safe -> BridgeGovernance -> Bridge proxy -> current implementation
Governance Safe -> RebateStaking proxy -> current implementation
Governance Safe -> RedemptionWatchtower proxy -> current implementation
Governance Safe -> proposer, executor, and canceller roles on Timelock
Timelock -> self-administered Timelock -> owns ProxyAdmin -> upgrades the three proxies
```

Arbitrum One:

```text
Governance Safe -> ArbitrumTBTC proxy -> current implementation
Governance Safe -> ArbitrumWormholeGateway proxy -> current implementation
Governance Safe -> proposer, executor, and canceller roles on Timelock
Timelock -> self-administered Timelock -> owns ProxyAdmin -> upgrades both proxies
```

Neither Timelock had its Executor role granted to the zero address at the observation blocks.

## Source Conflicts Kept as Tests

- The current tBTC repository artifact declares `0xaaC4...b71F` as the ArbitrumWormholeGateway implementation, while the live EIP-1967 slot returned `0x7Ff0...b9a5`.
- A legacy local registry listed `0xf286...0b45` for BridgeGovernance, while the current repository artifact and live `Bridge.governance()` returned `0xcBCF...c0Cf`.

These are not silently corrected. They remain findings so the future scanner and UI can prove how conflicts are handled.

## Evidence

- Repository: `threshold-network/tbtc-v2` main at `502cd3982b5b2dc3ff0e1e6085a24502f78cfe26`
- Live Ethereum and Arbitrum RPC reads at the recorded blocks
- EIP-1967 implementation slot reads
- Safe `getOwners`, `getThreshold`, `VERSION`, and module pagination calls
- Timelock role and `hasRole` calls

The full seed is in [`project.json`](project.json). It must be refreshed before operational use.
