# Security Model

DAO Treehouse is an operations aid, not an autonomous administrator. Its default state is read-only.

## Trust Boundaries

- Repository contents are untrusted input.
- RPC and explorer responses are evidence sources, not absolute truth.
- Browser wallet and Safe signatures stay outside the server.
- Generated calldata is untrusted until decoded, reviewed, and simulated.
- Labels and identities are annotations; addresses and chain state remain primary.

## Secrets

- Never request, import, log, or store seed phrases or private keys.
- Keep GitHub App keys, RPC credentials, and service tokens in managed secret storage.
- Redact credentials from errors, telemetry, job payloads, and exported manifests.
- Use a GitHub App with read-only repository Contents access for scanning.
- Request write access only in a separate future feature that creates an explicit pull request.

## Proposal Gates

An action cannot reach proposal handoff until all gates pass:

1. The repository revision and chain are pinned.
2. Target bytecode and authority state are re-read at a fresh block.
3. Preconditions match the reviewed snapshot.
4. Every call is decoded with the verified ABI or visibly marked unverified.
5. Decimal inputs show their raw integer representation.
6. The full batch is simulated on a fork at the recorded block.
7. Expected state changes and unexpected side effects are shown.
8. The connected wallet is on the intended chain and is eligible to propose.
9. The user explicitly confirms the final transaction hash or Safe transaction hash.

Any state drift invalidates the simulation and returns the action to Prepare mode.

## Timelock Rules

- Discover Admin, Proposer, Executor, and Canceller independently.
- Treat a zero-address Executor as an open execution policy, not an empty role.
- Preserve at least one verified scheduling path and one execution path.
- Grant and verify replacement roles before revoking old roles.
- Keep Proposer and Canceller changes together in the review because they affect both scheduling and denial-of-service risk.
- Keep Admin changes isolated from ordinary actions and require a second reviewer.
- Confirm self-administration before removing an external admin.
- Derive and display operation ID, delay, predecessor, salt, targets, values, and decoded payloads.
- Never combine scheduling and execution in one transaction or bypass the enforced delay.

## Safe Rules

- Show the threshold as both a number and a fraction of current owners.
- Re-read owners, threshold, nonce, modules, and guard before preparing changes.
- Add the replacement owner before removing the old owner when the Safe version and intended threshold permit it.
- Simulate owner and threshold changes together as the final ordered batch.
- Warn when a module or guard can bypass the apparent signer path.
- Do not claim real-world signer identities without a separately verified source.

## Repository Scanner Isolation

The scanner never runs `npm install`, build scripts, shell files, tests, Solidity compilation, or repository-provided executables. Archive extraction, parsing, and source analysis run with strict resource limits and no secret-bearing environment variables.

## Audit Trail

Store immutable scan snapshots, action revisions, simulations, and proposal references. Do not store signatures beyond what the selected wallet or Safe service already publishes.
