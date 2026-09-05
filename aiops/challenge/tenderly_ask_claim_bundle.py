#!/usr/bin/env python3
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ENV_FILE = Path("/Users/Citizen42/Desktop/TdaoUtils/AI-ops/Tenderly_simulations/.env")
USER = "0x3070f20f86fda706ac380f5060d256028a46ec29"
ASK = "0xa0096d95daaa3cf19091c0f0627b3913c2e417ae"
BOUNTY = "0xAAB498e3974F7543724602604f4EC6c44867FC72"
OUT = Path("aiops/challenge/tenderly-ask-claim-result.json")


def read_env():
    values = {}
    if ENV_FILE.exists():
        for raw in ENV_FILE.read_text().splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key] = value.strip().strip('"').strip("'")
    for key, value in os.environ.items():
        if key.startswith("TENDERLY_"):
            values[key] = value
    return values


def calldata(signature, *args):
    return subprocess.check_output(["cast", "calldata", signature, *map(str, args)], text=True).strip()


def main():
    env = read_env()
    missing = [
        key
        for key in ("TENDERLY_ACCOUNT_SLUG", "TENDERLY_PROJECT_SLUG", "TENDERLY_ACCESS_KEY")
        if not env.get(key)
    ]
    if missing:
        raise SystemExit(f"Missing Tenderly env: {', '.join(missing)}")

    buy_input = calldata("buy(uint256)", "10000000000000042")
    claim_input = calldata("claim(uint8)", "4")
    balance_override = "0x8AC7230489E80000"  # 10 ETH, simulation-local only.

    common = {
        "network_id": "1",
        "save": True,
        "save_if_fails": True,
        "simulation_type": "full",
        "from": USER,
        "gas": 1_000_000,
        "gas_price": 0,
        "state_objects": {
            USER: {
                "balance": balance_override,
            }
        },
    }
    payload = {
        "simulations": [
            {
                **common,
                "to": ASK,
                "input": buy_input,
                "value": "10000000000000000",
            },
            {
                **common,
                "to": BOUNTY,
                "input": claim_input,
                "value": "0",
            },
        ]
    }

    url = (
        "https://api.tenderly.co/api/v1/account/"
        f"{env['TENDERLY_ACCOUNT_SLUG']}/project/{env['TENDERLY_PROJECT_SLUG']}/simulate-bundle"
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Access-Key": env["TENDERLY_ACCESS_KEY"],
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as error:
        body = error.read().decode(errors="replace")
        raise SystemExit(f"Tenderly HTTP {error.code}: {body}") from error

    OUT.write_text(json.dumps(data, indent=2))

    sims = data.get("simulations") or data.get("simulation_results") or data.get("transactions") or []
    summary = []
    if isinstance(sims, list):
        for i, item in enumerate(sims, start=1):
            tx = item.get("transaction", item) if isinstance(item, dict) else {}
            summary.append(
                {
                    "step": i,
                    "status": tx.get("status"),
                    "error_message": tx.get("error_message"),
                    "gas_used": tx.get("gas_used") or tx.get("gasUsed"),
                    "id": tx.get("id") or item.get("id") if isinstance(item, dict) else None,
                }
            )
    print(json.dumps({"output": str(OUT), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
