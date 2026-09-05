#!/usr/bin/env bash
set -euo pipefail

RPC_URL="${TENDERLY_RPC_URL:-${RPC_URL:-http://127.0.0.1:8545}}"
USER_ADDR="${USER_ADDR:-0x3070f20f86fda706ac380f5060d256028a46ec29}"
ALLOW_MAINNET="${ALLOW_MAINNET:-0}"

ART="0xa01a0386b0fb47296C52d5d2492Fbe01BfDa85B8"
BOUNTY="0xAAB498e3974F7543724602604f4EC6c44867FC72"
ASK="0xa0096d95daaa3cf19091c0f0627b3913c2e417ae"
FORK="0x4f33e5aa6d6c83e0bd32887b3a65a6d26e28b57b"
BEQUEATH="0x4332bd627c7712718d5373ce9d6c6bced6338a0e"
LINEAGE="0x7392197b936a0b3d3e3734a48aca3c9b2682098f"

chain_id="$(cast chain-id --rpc-url "$RPC_URL")"
is_local=0
case "$RPC_URL" in
  http://127.0.0.1:*|http://localhost:*) is_local=1 ;;
esac

if [[ "$chain_id" == "1" && "$is_local" != "1" && "$ALLOW_MAINNET" != "1" ]]; then
  echo "Refusing to send transactions to Ethereum mainnet. Use a Tenderly vnet or local Anvil fork."
  exit 1
fi

call() {
  cast call "$@" --rpc-url "$RPC_URL"
}

uint_call() {
  call "$@" | awk '{print $1}'
}

wei_lt() {
  python3 - "$1" "$2" <<'PY'
import sys
sys.exit(0 if int(sys.argv[1]) < int(sys.argv[2]) else 1)
PY
}

send_from_user() {
  cast send "$@" --from "$USER_ADDR" --unlocked --rpc-url "$RPC_URL"
}

fund_user_if_supported() {
  cast rpc tenderly_setBalance "$USER_ADDR" 0x8AC7230489E80000 --rpc-url "$RPC_URL" >/dev/null 2>&1 && return 0
  cast rpc anvil_setBalance "$USER_ADDR" 0x8AC7230489E80000 --rpc-url "$RPC_URL" >/dev/null 2>&1 && return 0
  true
}

impersonate_user_if_supported() {
  cast rpc tenderly_impersonateAccount "$USER_ADDR" --rpc-url "$RPC_URL" >/dev/null 2>&1 && return 0
  cast rpc anvil_impersonateAccount "$USER_ADDR" --rpc-url "$RPC_URL" >/dev/null 2>&1 && return 0
  true
}

state() {
  echo "chain_id=$chain_id"
  echo "user=$USER_ADDR"
  echo "bounty_balance=$(cast balance "$BOUNTY" --ether --rpc-url "$RPC_URL") ETH"
  echo "art_volume_wei=$(call "$ART" 'volume()(uint256)')"
  echo "ask_price_wei=$(call "$ASK" 'price()(uint256)')"
  echo "ask_owner=$(call "$ASK" 'ownerOf(uint256)(address)' 1)"
  echo "fork_price_wei=$(call "$FORK" 'price()(uint256)')"
  echo "fork_balance_user=$(call "$FORK" 'balanceOf(address)(uint256)' "$USER_ADDR")"
  echo "lineage_price_wei=$(call "$LINEAGE" 'price()(uint256)')"
  echo "lineage_owner=$(call "$LINEAGE" 'ownerOf(uint256)(address)' 1)"
  echo "art_renderer=$(call "$ART" 'renderer()(address)')"
  echo "bequeath_owner=$(call "$BEQUEATH" 'ownerOf(uint256)(address)' 1)"
  for q in 0 1 2 3 4 5 6 7 8 9; do
    echo "bounty_wonBy_$q=$(call "$BOUNTY" 'wonBy(uint8)(address)' "$q")"
  done
}

ask_q4() {
  fund_user_if_supported
  impersonate_user_if_supported
  p="$(uint_call "$ASK" 'price()(uint256)')"
  echo "Simulating Ask.buy(newPrice=0.01 ether) with value=$p, then Bounties.claim(4)"
  send_from_user "$ASK" 'buy(uint256)' 10000000000000000 --value "$p"
  send_from_user "$BOUNTY" 'claim(uint8)' 4
  state
}

fork_q9() {
  fund_user_if_supported
  impersonate_user_if_supported
  first="$(uint_call "$FORK" 'price()(uint256)')"
  echo "Minting first Fork at $first wei"
  send_from_user "$FORK" 'mint()' --value "$first"
  second="$(uint_call "$FORK" 'price()(uint256)')"
  echo "Minting second Fork at $second wei, then Bounties.claim(9)"
  send_from_user "$FORK" 'mint()' --value "$second"
  send_from_user "$BOUNTY" 'claim(uint8)' 9
  state
}

bequeath_q2() {
  echo "Quest 2 requires owning Bequeath while not steward."
  echo "On current state, only steward can bequeath it, and public claim is locked until 2027-02-28 20:20:59 UTC unless it moves."
  state
}

art_control() {
  fund_user_if_supported
  impersonate_user_if_supported

  echo "Minting two Fork editions for majority voting weight."
  for _ in 1 2; do
    fp="$(uint_call "$FORK" 'price()(uint256)')"
    send_from_user "$FORK" 'mint()' --value "$fp" >/dev/null
  done

  echo "Buying Lineage until Art.volume() reaches the 10 ETH adoption gate."
  target=10000000000000000000
  buys=0
  while wei_lt "$(uint_call "$ART" 'volume()(uint256)')" "$target"; do
    lp="$(uint_call "$LINEAGE" 'price()(uint256)')"
    send_from_user "$LINEAGE" 'buy()' --value "$lp" >/dev/null
    buys=$((buys + 1))
  done

  echo "Lineage buys executed: $buys"
  echo "Endorsing user address as renderer candidate to prove voting control."
  send_from_user "$ART" 'propose(address)' "$USER_ADDR" >/dev/null
  send_from_user "$ART" 'endorse(address)' "$USER_ADDR"
  state
}

case "${1:-state}" in
  state) state ;;
  ask-q4) ask_q4 ;;
  fork-q9) fork_q9 ;;
  bequeath-q2) bequeath_q2 ;;
  art-control) art_control ;;
  *) echo "usage: $0 [state|ask-q4|fork-q9|bequeath-q2|art-control]" >&2; exit 2 ;;
esac
