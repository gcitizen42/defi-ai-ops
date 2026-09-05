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
