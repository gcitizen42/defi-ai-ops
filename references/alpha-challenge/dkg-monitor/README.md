# DKG Monitor

This project provides scripts for monitoring and backfilling WalletRegistry DKG events using `ts-node`.

## Updating your local clone

To sync your local checkout with the latest changes pushed to the remote repository, run the following commands from the project root:

```bash
git checkout main        # or the branch you want to update
git pull origin main     # fetch and merge the latest commits
git submodule update --init --recursive  # if the repo uses submodules
```

If you are working on a feature branch, pull the updates for that branch instead of `main`:

```bash
git checkout your-branch
git pull origin your-branch
```

Alternatively, you can fetch first and then rebase to keep a linear history:

```bash
git fetch origin
git rebase origin/main
```

Replace `main` with the appropriate branch name as needed.

## Package scripts

The `package.json` file already includes a script for the unified CLI:

```json
"scripts": {
  "live": "ts-node --esm src/live.ts",
  "history": "ts-node --esm src/history.ts",
  "// note": "Unified CLI (history + live, only getLogs)",
  "dkg": "ts-node --esm src/dkg-cli.ts"
}
```

You can run the unified CLI with:

```bash
npm run dkg -- <command> [options]
```

For example, to launch the polling live monitor:

```bash
RPC_URL=https://your-rpc.example npm run dkg -- live --registry=0x...
```

Refer to the inline usage notes in `src/dkg-cli.ts` for the available commands and flags.
