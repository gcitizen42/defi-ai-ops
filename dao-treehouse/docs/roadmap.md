# Roadmap

## Stage 0: Foundation

- define requirements, graph model, safety rules, and integration choices
- create the Threshold tBTC v2 seed manifest
- record known source conflicts as test cases

## Stage 1: Read-Only Scanner

- scan one GitHub repository at a pinned commit
- parse Hardhat Deploy and registry JSON files
- verify Ethereum and Arbitrum addresses and EIP-1967 implementations
- export a schema-valid project snapshot
- add fixture-based tests using the Threshold case study

## Stage 2: Control Map

- add Ownable, AccessControl, Timelock, Safe, Governor, and ProxyAdmin adapters
- render controller-first tree and graph views
- show evidence and conflicts beside every node and edge
- add search, network filters, and historical snapshot comparison

## Stage 3: Action Workbench

- build typed intents and ABI-derived forms
- add decimal and timestamp formatting
- generate unsigned Safe and Timelock artifacts
- enforce fresh-state checks and fork simulation

## Stage 4: Safe Handoff

- connect external wallets with Reown AppKit
- run inside or alongside Safe Wallet
- submit reviewed proposals through Safe API Kit
- track signatures and execution without holding keys

## Stage 5: Project Operations

- scheduled rescans and control-change alerts
- multi-project portfolio view
- contributor comments, policies, and review assignments
- additional proxy, permission-manager, and governance patterns
