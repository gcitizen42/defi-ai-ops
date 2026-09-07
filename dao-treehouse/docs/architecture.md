# Architecture

## System Shape

```text
GitHub App -> Repository Scanner -> Address Candidates
                                      |
RPC + verified source -> Chain Adapters -> Evidence Store
                                            |
                                      Control Graph
                                      /           \
                              Explore UI      Action Builder
                                                   |
                                             Simulation Gate
                                                   |
                                      Unsigned export or Safe proposal
```

The discovery and action paths share data but run as separate services. A scan cannot create a proposal, and connecting a wallet does not change scan results.

## Repository Scanner

Start with structured sources:

- Hardhat Deploy files under `deployments/**`
- Foundry broadcast files under `broadcast/**`
- OpenZeppelin network manifests under `.openzeppelin/**`
- JSON and YAML address registries
- TypeScript or Solidity address constants parsed as source text
- documentation tables as low-confidence candidates

The scanner works from a pinned commit. It reads files as untrusted data, enforces size and path limits, rejects symlink escapes, and never runs package scripts, build tools, or repository binaries.

## Chain Discovery

Each candidate is enriched through small, independently testable adapters:

- deployed bytecode and code hash
- EIP-1967 implementation, admin, and beacon slots
- Ownable and Ownable2Step state
- AccessControl interface checks and role event history
- OpenZeppelin Timelock roles, delay, and operation state
- Governor executor and Timelock relationships
- Safe owners, threshold, modules, guard, fallback handler, and version
- ProxyAdmin ownership and UUPS authorization clues
- verified ABI, metadata, and source from Sourcify or a supported explorer

Unknown and custom patterns remain visible as unresolved findings. They are never forced into a familiar contract type.

## Evidence Store

Every observation records:

- project and scan ID
- source URI and repository commit when applicable
- chain ID and block number
- address and code hash
- method, storage slot, event range, or source locator
- raw result hash and normalized result
- confidence and verification time

SQLite is enough for a local single-project prototype. PostgreSQL is the intended shared deployment store. The control graph is derived from evidence so it can be rebuilt after parser changes.

## Control Graph Service

The graph service resolves authority paths, cycles, conflicts, and missing links. It exposes graph-shaped JSON to the UI and keeps evidence available beside every relationship.

The main view is a controller-first tree with a graph toggle for cross-links. Shared controllers and cyclic governance relationships cannot be represented faithfully by a tree alone.

## Action Builder

An action begins as a typed intent, not calldata. An adapter converts the intent into exact calls only after checking the target's current ABI and authority path.

```text
Intent -> Preconditions -> Encoded Calls -> Decoded Review -> Simulation -> Unsigned Output
```

Safe actions use Protocol Kit for transaction construction and API Kit for optional proposal sharing. Timelock schedule and execute payloads are produced as separate artifacts.

## Suggested Implementation Stack

- TypeScript across the web app, workers, and shared packages
- Next.js and React for the dashboard
- `@xyflow/react` for the interactive control graph
- viem for EVM reads, decoding, encoding, and unit conversion
- Zod plus JSON Schema for boundaries and exported manifests
- Reown AppKit with wagmi for external wallet connections
- Safe Protocol Kit and API Kit for Safe-aware workflows
- a fork-capable simulator before any proposal handoff
