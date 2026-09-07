# Control Graph

## Direction

Control edges normally point from the authority to the object it can affect. For example:

```text
Safe --OWNS--> BridgeGovernance --GOVERNS--> Bridge
Safe --PROPOSES_TO--> Timelock --OWNS--> Contract
Implementation --IMPLEMENTS--> Proxy
Signer --SIGNER_OF--> Safe
```

Implementation and dependency edges are structural rather than authority claims. The UI must style them differently.

## Node Types

| Type | Meaning |
| --- | --- |
| Project | Repository and declared deployment scope. |
| Contract | A deployed contract without a more specific classification. |
| Proxy | A contract delegating behavior to an implementation or beacon. |
| Implementation | Logic used by a proxy. |
| ProxyAdmin | Authority for one or more Transparent proxies. |
| Safe | Safe smart account with owners, threshold, modules, and guards. |
| Timelock | Delayed executor with role-based scheduling and execution. |
| Governor | Proposal and voting contract whose executor may be a Timelock. |
| Role | Named or hashed permission on a target contract. |
| Module | Contract able to act through a Safe or permission manager. |
| EOA | Externally owned account; identity is unknown unless separately verified. |
| Unknown | Valid address whose control behavior is not yet classified. |

## Edge Types

| Edge | Meaning |
| --- | --- |
| `OWNS` | Source is the current Ownable controller of target. |
| `PENDING_OWNER_OF` | Source must accept an Ownable2Step transfer. |
| `GOVERNS` | Source can invoke a target's custom governance surface. |
| `ADMINISTERS` | Source can change target permissions or configuration. |
| `UPGRADES` | Source can change target implementation. |
| `IMPLEMENTS` | Source is the implementation currently used by target. |
| `BEACON_FOR` | Source beacon supplies target's implementation. |
| `PROPOSES_TO` | Source can schedule Timelock operations. |
| `EXECUTES_FOR` | Source can execute ready Timelock operations. |
| `CANCELS_FOR` | Source can cancel Timelock operations. |
| `SIGNER_OF` | Source is a current Safe owner. |
| `MODULE_OF` | Source is enabled as a Safe module. |
| `GUARDS` | Source is the Safe guard. |
| `FALLBACK_HANDLER_OF` | Source is the Safe fallback handler. |
| `HAS_ROLE_ON` | Source holds a custom AccessControl role on target. |
| `DEPENDS_ON` | Structural relationship without an authority claim. |

## Evidence and Confidence

Each node and edge has one of these confidence levels:

- `verified`: observed directly from chain state at a recorded block
- `corroborated`: supported by two independent sources, including chain data
- `reported`: present in a repository or registry but not yet checked on chain
- `inferred`: derived from code, bytecode, or transaction behavior
- `conflict`: credible sources disagree
- `unresolved`: the system cannot yet classify the relationship

No edge is displayed as current without an observation block. Historical views keep old edges instead of overwriting them.

## Resolving Effective Control

For every contract, walk all reachable authority routes:

1. Read explicit owner and pending owner functions when supported.
2. Check AccessControl roles and their role admins.
3. Read proxy implementation, admin, and beacon slots.
4. Inspect ProxyAdmin ownership and UUPS authorization logic.
5. Detect custom governance pointers and executor contracts.
6. Expand Timelock proposers, executors, cancellers, admins, and delay.
7. Expand Safe owners, threshold, modules, guard, and fallback handler.
8. Continue until each route reaches a human signer set, open role, immutable boundary, or unresolved node.

Cycles are valid. A self-administered Timelock is a meaningful cycle and must not be removed during graph simplification.

## Zero Address Rule

`owner() == 0x0000000000000000000000000000000000000000` means only that the Ownable path is disabled. It does not prove immutability.

The graph still checks roles, proxy administration, UUPS authorization, governors, Timelocks, modules, upgrade beacons, and custom privileged functions. The contract is labelled `no-known-authority` only when all supported routes have been checked; otherwise it remains `unresolved`.

The zero address also has pattern-specific meanings. An Executor role granted to zero on OpenZeppelin TimelockController means permissionless execution of already scheduled operations, not missing control.
