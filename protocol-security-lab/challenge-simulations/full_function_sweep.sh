#!/usr/bin/env bash
set -u

RPC_URL="${TENDERLY_RPC_URL:-${RPC_URL:-http://127.0.0.1:8545}}"
USER_ADDR="${USER_ADDR:-0x3070f20f86fda706ac380f5060d256028a46ec29}"
STEWARD="0x3567dBd98fe316408C7ebAB6Ac6B12a0F27A7ed5"
OUT="${OUT:-protocol-security-lab/challenge-simulations/function-sweep.md}"

ART="0xa01a0386b0fb47296C52d5d2492Fbe01BfDa85B8"
BOUNTY="0xAAB498e3974F7543724602604f4EC6c44867FC72"
VAULT="0x0596702Ae60A2b27593a89F2E69855817E1f2CC2"
BEQUEATH="0x4332bd627c7712718d5373ce9d6c6bced6338a0e"
RATCHET="0x792ebdc632bbd4d41f2521ffb502d2424b1f2338"
FORK="0x4f33e5aa6d6c83e0bd32887b3a65a6d26e28b57b"
PYRE="0x8423322212ac399750c59de51b22ed7d77048150"
ASK="0xa0096d95daaa3cf19091c0f0627b3913c2e417ae"
LINEAGE="0x7392197b936a0b3d3e3734a48aca3c9b2682098f"
TUG="0x6c6fc769cd751632accc23f9335a72c26a7551df"
BYME="0x7c5f5c915f44924400649a18bdaf1f9dad68ea2c"
LIFE="0x4ab5E5DFB8D1B6C7ca94E5cd35Eaa2f4a6f3B0f8"
VERB="0x5cFC192ecA0d530E9ec6a8c8Ca7b33d8E35D2A07"

run() {
  local title="$1"
  shift
  {
    echo
    echo "#### $title"
    echo
    echo '```text'
    echo "$ $*"
  } >> "$OUT"
  "$@" >> "$OUT" 2>&1
  local status=$?
  {
    echo "exit=$status"
    echo '```'
  } >> "$OUT"
  return 0
}

call() {
  cast call "$@" --rpc-url "$RPC_URL"
}

send_user() {
  cast send "$@" --from "$USER_ADDR" --unlocked --rpc-url "$RPC_URL"
}

send_steward() {
  cast send "$@" --from "$STEWARD" --unlocked --rpc-url "$RPC_URL"
}

uint_call() {
  call "$@" | awk '{print $1}'
}

fund_and_impersonate() {
  cast rpc anvil_setBalance "$USER_ADDR" 0x21E19E0C9BAB2400000 --rpc-url "$RPC_URL" >/dev/null 2>&1
  cast rpc anvil_setBalance "$STEWARD" 0x21E19E0C9BAB2400000 --rpc-url "$RPC_URL" >/dev/null 2>&1
  cast rpc anvil_impersonateAccount "$USER_ADDR" --rpc-url "$RPC_URL" >/dev/null 2>&1
  cast rpc anvil_impersonateAccount "$STEWARD" --rpc-url "$RPC_URL" >/dev/null 2>&1
}

snapshot() {
  cast rpc evm_snapshot --rpc-url "$RPC_URL" | tr -d '"'
}

revert_to() {
  cast rpc evm_revert "$1" --rpc-url "$RPC_URL" >/dev/null
}

state_block() {
  {
    echo
    echo "#### State: $1"
    echo
    echo '```text'
    echo "user_eth=$(cast balance "$USER_ADDR" --ether --rpc-url "$RPC_URL")"
    echo "steward_eth=$(cast balance "$STEWARD" --ether --rpc-url "$RPC_URL")"
    echo "bounty_eth=$(cast balance "$BOUNTY" --ether --rpc-url "$RPC_URL")"
    echo "vault_eth=$(cast balance "$VAULT" --ether --rpc-url "$RPC_URL")"
    echo "art_volume=$(call "$ART" 'volume()(uint256)')"
    echo "art_renderer=$(call "$ART" 'renderer()(address)')"
    echo "ask_owner=$(call "$ASK" 'ownerOf(uint256)(address)' 1)"
    echo "ask_price=$(call "$ASK" 'price()(uint256)')"
    echo "bequeath_owner=$(call "$BEQUEATH" 'ownerOf(uint256)(address)' 1)"
    echo "fork_minted=$(call "$FORK" 'minted()(uint256)')"
    echo "fork_price=$(call "$FORK" 'price()(uint256)')"
    echo "fork_user_balance=$(call "$FORK" 'balanceOf(address)(uint256)' "$USER_ADDR")"
    echo "lineage_owner=$(call "$LINEAGE" 'ownerOf(uint256)(address)' 1)"
    echo "lineage_price=$(call "$LINEAGE" 'price()(uint256)')"
    echo "ratchet_owner=$(call "$RATCHET" 'ownerOf(uint256)(address)' 1)"
    echo "ratchet_last=$(call "$RATCHET" 'last()(uint256)')"
    echo "pyre_owner=$(call "$PYRE" 'ownerOf(uint256)(address)' 1)"
    echo "pyre_cost=$(call "$PYRE" 'cost()(uint256)')"
    echo "tug_owner=$(call "$TUG" 'ownerOf(uint256)(address)' 1)"
    echo "tug_color=$(call "$TUG" 'color()(uint24)')"
    echo "life_owner=$(call "$LIFE" 'ownerOf(uint256)(address)' 1)"
    echo "verb_owner=$(call "$VERB" 'ownerOf(uint256)(address)' 1)"
    echo "verb_witness_count=$(call "$VERB" 'witnessCount()(uint256)')"
    for q in 0 1 2 3 4 5 6 7 8 9; do
      echo "bounty_wonBy_$q=$(call "$BOUNTY" 'wonBy(uint8)(address)' "$q")"
      echo "bounty_qualifies_user_$q=$(call "$BOUNTY" 'qualifies(uint8,address)(bool)' "$q" "$USER_ADDR")"
    done
    echo '```'
  } >> "$OUT"
}

scenario() {
  local title="$1"
  shift
  local snap
  snap="$(snapshot)"
  {
    echo
    echo "### $title"
  } >> "$OUT"
  state_block "before $title"
  "$@"
  state_block "after $title"
  revert_to "$snap"
}

scenario_tug() {
  run "Tug.paint(uint24)" send_user "$TUG" 'paint(uint24)' 16711680
  run "Bounties.claim(0)" send_user "$BOUNTY" 'claim(uint8)' 0
}

scenario_life() {
  run "ProofOfLife.beat()" send_user "$LIFE" 'beat()' --value 1000000000000000
  run "Bounties.claim(1)" send_user "$BOUNTY" 'claim(uint8)' 1
}

scenario_bequeath() {
  run "Bequeath.claim() before timeout" send_user "$BEQUEATH" 'claim()'
  run "Bequeath.bequeath(user) as steward holder" send_steward "$BEQUEATH" 'bequeath(address)' "$USER_ADDR"
  run "Bounties.claim(2)" send_user "$BOUNTY" 'claim(uint8)' 2
}

scenario_fork() {
  local p
  p="$(uint_call "$FORK" 'price()(uint256)')"
  run "Fork.mint() first" send_user "$FORK" 'mint()' --value "$p"
  run "Bounties.claim(3)" send_user "$BOUNTY" 'claim(uint8)' 3
  p="$(uint_call "$FORK" 'price()(uint256)')"
  run "Fork.mint() second" send_user "$FORK" 'mint()' --value "$p"
  run "Bounties.claim(9)" send_user "$BOUNTY" 'claim(uint8)' 9
}

scenario_ask() {
  run "Ask.setPrice(uint256) before owning" send_user "$ASK" 'setPrice(uint256)' 20000000000000000
  local p
  p="$(uint_call "$ASK" 'price()(uint256)')"
  run "Ask.buy(uint256)" send_user "$ASK" 'buy(uint256)' 10000000000000000 --value "$p"
  run "Ask.setPrice(uint256) after owning" send_user "$ASK" 'setPrice(uint256)' 20000000000000000
  run "Bounties.claim(4)" send_user "$BOUNTY" 'claim(uint8)' 4
}

scenario_lineage() {
  local p
  p="$(uint_call "$LINEAGE" 'price()(uint256)')"
  run "Lineage.buy()" send_user "$LINEAGE" 'buy()' --value "$p"
  run "Bounties.claim(5)" send_user "$BOUNTY" 'claim(uint8)' 5
}

scenario_ratchet() {
  local last value
  last="$(uint_call "$RATCHET" 'last()(uint256)')"
  value="$(python3 - "$last" <<'PY'
import sys
print(int(sys.argv[1]) + 1)
PY
)"
  run "Ratchet.buy()" send_user "$RATCHET" 'buy()' --value "$value"
  run "Bounties.claim(6)" send_user "$BOUNTY" 'claim(uint8)' 6
}

scenario_pyre() {
  local cost value
  cost="$(uint_call "$PYRE" 'cost()(uint256)')"
  value="$(python3 - "$cost" <<'PY'
import sys
print(int(sys.argv[1]) + 1)
PY
)"
  run "Pyre.buy()" send_user "$PYRE" 'buy()' --value "$value"
  run "Bounties.claim(7)" send_user "$BOUNTY" 'claim(uint8)' 7
}

scenario_verb() {
  run "Verb.echo()" send_user "$VERB" 'echo()'
  run "Bounties.claim(8)" send_user "$BOUNTY" 'claim(uint8)' 8
  run "Verb.allPieces()" call "$VERB" 'allPieces()(address[])'
}

scenario_byme() {
  local p
  p="$(uint_call "$BYME" 'price()(uint256)')"
  run "ByMe.price()" call "$BYME" 'price()(uint256)'
  run "ByMe.buy()" send_user "$BYME" 'buy()' --value "$p"
}

scenario_art_control() {
  local p target buys
  p="$(uint_call "$FORK" 'price()(uint256)')"
  run "Fork.mint() for vote 1" send_user "$FORK" 'mint()' --value "$p"
  p="$(uint_call "$FORK" 'price()(uint256)')"
  run "Fork.mint() for vote 2" send_user "$FORK" 'mint()' --value "$p"
  target=10000000000000000000
  buys=0
  while python3 - "$ART" "$target" "$RPC_URL" <<'PY'
import subprocess, sys
art, target, rpc = sys.argv[1:]
out = subprocess.check_output(["cast", "call", art, "volume()(uint256)", "--rpc-url", rpc], text=True)
sys.exit(0 if int(out.split()[0]) < int(target) else 1)
PY
  do
    p="$(uint_call "$LINEAGE" 'price()(uint256)')"
    run "Lineage.buy() volume pump $((buys + 1))" send_user "$LINEAGE" 'buy()' --value "$p"
    buys=$((buys + 1))
  done
  run "Art.propose(user)" send_user "$ART" 'propose(address)' "$USER_ADDR"
  run "Art.endorse(user)" send_user "$ART" 'endorse(address)' "$USER_ADDR"
}

scenario_vault() {
  run "Vault.state()" call "$VAULT" 'state()(string)'
  run "Vault.balance()" call "$VAULT" 'balance()(uint256)'
  run "Vault.unlock(wrong,to)" send_user "$VAULT" 'unlock(bytes,address)' 0x6c6f7374 "$USER_ADDR"
  run "Direct fund Vault receive()" send_user "$VAULT" --value 1000000000000000
}

scenario_bounty_admin() {
  run "Bounties.withdraw() as user" send_user "$BOUNTY" 'withdraw()'
  run "Bounties.withdraw() as steward" send_steward "$BOUNTY" 'withdraw()'
}

scenario_collectible_admin() {
  run "Ask.seedBeacon() as user" send_user "$ASK" 'seedBeacon()' --value 1000000000000000
  run "Ask.seedBeacon() as steward" send_steward "$ASK" 'seedBeacon()' --value 1000000000000000
  run "Ask.pullBeacon(uint256) as user" send_user "$ASK" 'pullBeacon(uint256)' 1000000000000000
  run "Ask.pullBeacon(uint256) as steward" send_steward "$ASK" 'pullBeacon(uint256)' 1000000000000000
  run "Ask.pulse() as user" send_user "$ASK" 'pulse()' --value 1000000000000000
}

main() {
  fund_and_impersonate
  {
    echo "# Function Sweep"
    echo
    echo "Fork-only execution report."
    echo
    echo "- RPC: $RPC_URL"
    echo "- User: $USER_ADDR"
    echo "- Steward: $STEWARD"
    echo "- Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  } > "$OUT"

  state_block "baseline"
  scenario "Tug" scenario_tug
  scenario "ProofOfLife" scenario_life
  scenario "Bequeath" scenario_bequeath
  scenario "Fork" scenario_fork
  scenario "Ask" scenario_ask
  scenario "Lineage" scenario_lineage
  scenario "Ratchet" scenario_ratchet
  scenario "Pyre" scenario_pyre
  scenario "Verb" scenario_verb
  scenario "ByMe" scenario_byme
  scenario "Art renderer control via Fork and Lineage" scenario_art_control
  scenario "Vault" scenario_vault
  scenario "Bounties admin" scenario_bounty_admin
  scenario "Collectible admin/life hooks on Ask" scenario_collectible_admin

  {
    echo
    echo "## Short Interpretation"
    echo
    echo "- Public ETH claim path is \`Bounties.claim(q)\`, but each quest can be taken once and each address can claim once."
    echo "- Public vault drain path is only \`Vault.unlock(secret,to)\`; no other contract proxies into it."
    echo "- Fork and Lineage fund the Vault, and Lineage can raise \`Art.volume()\` cheaply relative to gross volume because repeat buys refund the previous paid amount."
    echo "- \`Art.renderer\` changes collection metadata rendering only. It does not create withdrawal rights."
    echo "- Steward-only paths are \`Bounties.withdraw()\`, \`seedBeacon()\`, and \`pullBeacon()\`."
  } >> "$OUT"
}

main "$@"
