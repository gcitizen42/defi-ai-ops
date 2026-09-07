# Security Notes

This workspace may interact with trading APIs, wallet analytics APIs, RPC providers, and simulation services. Treat all credentials as private.

## Never Commit

- API keys or access tokens
- Wallet private keys or seed phrases
- `.env` files
- SQLite databases and local market captures
- Generated build artifacts
- Personal CV or identity documents

## Local Secret Locations

Use ignored local folders such as:

```text
market-ops-lab/secrets/
```

Copy the relevant example file into that folder and fill it locally.

## Quick Secret Scan

Run this before every sync:

```bash
rg -n --hidden -g '!.git/**' -g '!**/.venv/**' -g '!**/data/**' -g '!**/secrets/**' -g '!archive/**' -i '(api[_-]?key|secret|token|private[_-]?key|password|mnemonic|access[_-]?key|seed phrase)' .
```

Investigate every match before committing.

## Governance Batches

Treat generated Safe and Timelock batches as unsigned proposals, not approvals. Before proposing one:

- confirm the chain, Safe, Timelock, role members, delay, salt, and operation ID
- decode every grant and revoke payload
- simulate the schedule and execute stages separately
- have another reviewer compare the generated role diff with the intended roster

Never include the schedule and execute calls in the same Safe transaction. The Timelock delay must remain enforceable.
