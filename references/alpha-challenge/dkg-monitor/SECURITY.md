# Security Notes

The DKG monitor reads blockchain events from RPC endpoints and writes local output files. It should not require wallet private keys.

## Keep Local

- `.env`
- paid or private RPC URLs
- generated `out/` files
- any downstream analysis containing private addresses or notes

## Safe Setup

Copy `.env.example` to `.env`, fill values locally, and keep `.env` out of git.

```bash
cp .env.example .env
```

Use read-only RPC credentials whenever possible.
