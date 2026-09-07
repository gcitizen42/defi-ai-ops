# Product Requirements

## Product Goal

Give DAO contributors one place to answer three questions:

1. What contracts make up this project?
2. Who can change each contract, directly or indirectly?
3. What reviewed proposal is required to make an intended change?

## Required for the First Usable Release

| Area | Requirement |
| --- | --- |
| Project intake | Accept a GitHub URL, branch or commit, and selected EVM networks. |
| Repository scan | Parse common deployment and address files without installing dependencies or executing repository code. |
| Chain verification | Confirm chain ID, deployed bytecode, current implementation, ownership, roles, and observation block. |
| Control map | Show direct and indirect authority paths with source, confidence, and last verification. |
| Safe inspection | Show version, owners, threshold, enabled modules, guard, and fallback handler where available. |
| Timelock inspection | Show minimum delay and Admin, Proposer, Executor, and Canceller membership, including open roles granted to the zero address. |
| Proxy inspection | Detect EIP-1967 implementation, admin, and beacon slots; identify Transparent and UUPS authority paths. |
| Contract details | Show verified source status, ABI, current controller, dependencies, and unresolved checks. |
| Findings | Flag conflicting sources, stale deployments, unknown controllers, unsafe role posture, and incomplete evidence. |
| Snapshot export | Export a deterministic, machine-readable project manifest. |

## Action Preparation

The first action release prepares unsigned output only.

- Ownable and Ownable2Step ownership changes
- AccessControl grants and revokes
- Timelock role rotations
- Safe owner and threshold changes
- ProxyAdmin ownership changes
- Transparent and UUPS implementation upgrades
- Governor proposal payloads
- Generic ABI calls with an advanced raw-calldata view

Every action must include its target chain, target address, decoded call, expected current state, expected next state, evidence, and simulation result.

## Human-Friendly Inputs

- Use labels and checksummed addresses together.
- Use dropdowns for known contracts, roles, enum values, and approved controllers.
- Resolve token decimals on chain and show both the decimal value and raw integer.
- Show timestamps as dates while preserving the raw Unix value.
- Explain bytes and hashes by purpose, but never hide their exact value.
- Display a clear warning when an ABI field cannot be safely simplified.

## Operating Modes

| Mode | Wallet | Allowed work |
| --- | --- | --- |
| Explore | Not required | Scan, verify, browse, compare, and export snapshots. |
| Prepare | Optional | Build an unsigned action intent and run simulations. |
| Review | Required only to propose | Re-verify state, sign or propose through the user's wallet, and track approvals. |

## Later Scope

- GitHub organization portfolios and scheduled rescans
- Diamond proxies, minimal proxies, custom permission managers, and non-EVM networks
- Change alerts and governance runbooks
- Team comments, policy checks, and approval workflows
- Privy authentication or embedded wallets for audiences that do not already use external wallets

## Not in Scope

- Custodying private keys
- Automatic transaction execution
- Treating source files as authoritative without chain verification
- Running arbitrary scripts from scanned repositories
- Claiming that a zero owner address proves a contract is immutable
