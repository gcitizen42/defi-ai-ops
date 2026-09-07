# Timelock Role Manager

Builds minimal Safe Transaction Builder batches for OpenZeppelin `TimelockController` role rotations.

The tool reads current role state, compares it with the desired state, and generates:

- `plan.json` with the verified role diff and safety checks
- `schedule.json` for the Safe to schedule the atomic rotation
- `execute.json` for the Safe to execute it after the delay

It does not sign, propose, or execute transactions.

## Safety Rules

| Role | Purpose | Rule |
| --- | --- | --- |
| `PROPOSER_ROLE` | Schedules operations | Proposers and cancellers must be reviewed together. |
| `EXECUTOR_ROLE` | Executes ready operations | An open executor requires explicit acknowledgement. |
| `CANCELLER_ROLE` | Cancels pending operations | At least one canceller must remain. |
| Admin roles | Grant and revoke roles | This general-purpose tool refuses to rotate them. |

Every grant is ordered before every revoke. The tool also verifies the chain, Safe contract, on-chain delay, operation ID, Timelock self-administration, and the Safe's ability to schedule and execute.

## Run

From `onchain-ops-toolkit/`:

```bash
cp timelock-role-manager/.env.example timelock-role-manager/.env
cp timelock-role-manager/config.example.json timelock-role-manager/config.json
# Fill in the RPC URL and public addresses, then run:
npm run start --workspace timelock-role-manager -- timelock-role-manager/config.json
```

Generated files are written to `timelock-role-manager/generated/` and are ignored by git.

To rotate proposers, provide both `proposers` and `cancellers` in `roles`. Omitted role groups are preserved. Setting the zero address as an executor requires `"allowOpenExecutor": true`. Acknowledging an external admin requires `"allowExternalAdmin": true`.

## Threshold Deployments

| Network | Timelock | Governance Safe | Delay |
| --- | --- | --- | --- |
| Ethereum mainnet | [`0x92f2...4913D`](https://etherscan.io/address/0x92f2d8b72a7F6a551Be60b9aa4194248E9B4913D) | `0x9F6e...C2F5f` | 24 hours |
| Arbitrum One | [`0x6614...114e`](https://arbiscan.io/address/0x6614Ee0374A9EaD7cff8D6929829c4B2B035114e) | `0x9F6e...C2F5f` | 24 hours |

The complete addresses, deployment blocks, and deployment transactions are in [`deployments/threshold.json`](deployments/threshold.json). They were cross-checked against the local deployment artifacts and live chain state on 2026-09-07. The manager still verifies every value when it runs.

## Required Review

Check `plan.json`, decode every payload, and simulate both stages before proposing them. The execute batch can only succeed after the on-chain minimum delay.

The state-diff approach is inspired by [GNSPS Safe Owner Manager](https://github.com/GNSPS/safe-owner-manager). Timelock role discovery uses event history because standard `AccessControl` does not expose a complete member list.
