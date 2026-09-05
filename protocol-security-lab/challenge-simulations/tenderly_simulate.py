#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_ENV_FILE = Path(__file__).with_name("tenderly.env")


def read_env(path):
    values = {}
    p = Path(path)
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key] = value.strip().strip("\"").strip("'")
    values.update({k: v for k, v in os.environ.items() if k.startswith("TENDERLY_")})
    return values


def cast_calldata(signature, *args):
    cmd = ["cast", "calldata", signature, *args]
    return subprocess.check_output(cmd, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description="Run a transaction in a Tenderly simulation project.")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--from", dest="sender", required=True)
    parser.add_argument("--to", required=True)
    parser.add_argument("--input", help="Raw calldata. If omitted, --vault-secret is used.")
    parser.add_argument("--value", default="0")
    parser.add_argument("--gas", type=int, default=1_000_000)
    parser.add_argument("--save", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--vault-secret", help="Text secret candidate for Vault.unlock(bytes,address).")
    parser.add_argument("--vault-secret-hex", help="Hex bytes secret candidate for Vault.unlock(bytes,address).")
    parser.add_argument("--recipient", help="Recipient for Vault.unlock; defaults to --from.")
    args = parser.parse_args()

    env = read_env(args.env_file)
    required = ["TENDERLY_ACCOUNT_SLUG", "TENDERLY_PROJECT_SLUG", "TENDERLY_ACCESS_KEY"]
    missing = [key for key in required if not env.get(key)]
    if missing:
        raise SystemExit(f"Missing Tenderly keys: {', '.join(missing)}")

    tx_input = args.input
    if not tx_input:
        if args.vault_secret is not None:
            secret_hex = subprocess.check_output(["cast", "from-utf8", args.vault_secret], text=True).strip()
        elif args.vault_secret_hex is not None:
            secret_hex = args.vault_secret_hex
        else:
            raise SystemExit("Provide --input, --vault-secret, or --vault-secret-hex")
        tx_input = cast_calldata("unlock(bytes,address)", secret_hex, args.recipient or args.sender)

    payload = {
        "save": args.save,
        "save_if_fails": True,
        "simulation_type": "full",
        "network_id": "1",
        "from": args.sender,
        "to": args.to,
        "input": tx_input,
        "gas": args.gas,
        "gas_price": 0,
        "value": args.value,
    }

    url = (
        "https://api.tenderly.co/api/v1/account/"
        f"{env['TENDERLY_ACCOUNT_SLUG']}/project/{env['TENDERLY_PROJECT_SLUG']}/simulate"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Access-Key": env["TENDERLY_ACCESS_KEY"],
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as error:
        body = error.read().decode(errors="replace")
        raise SystemExit(f"Tenderly HTTP {error.code}: {body}") from error

    tx = data.get("transaction", {})
    result = {
        "status": tx.get("status"),
        "error_message": tx.get("error_message"),
        "gas_used": tx.get("gas_used"),
        "simulation_id": data.get("simulation", {}).get("id") or tx.get("id"),
        "transaction_id": tx.get("id"),
        "from": args.sender,
        "to": args.to,
        "value": args.value,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
