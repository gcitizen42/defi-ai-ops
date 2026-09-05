#!/usr/bin/env bash
set -euo pipefail

SEAL="${SEAL:-0x68f7c7cd0e11695dd28fccbc84dd8e04f016cf5e3d379d518aba6059d429c5c9}"
CANDIDATES="${1:-aiops/challenge/vault-candidates.txt}"

if [[ ! -f "$CANDIDATES" ]]; then
  echo "missing candidates file: $CANDIDATES" >&2
  exit 2
fi

matches=0
while IFS= read -r candidate || [[ -n "$candidate" ]]; do
  [[ -n "$candidate" ]] || continue
  [[ "$candidate" =~ ^# ]] && continue

  text_hash="$(cast keccak "$(cast from-utf8 "$candidate")")"
  if [[ "$text_hash" == "$SEAL" ]]; then
    echo "MATCH text: $candidate"
    matches=$((matches + 1))
  fi

  if [[ "$candidate" =~ ^0x[0-9a-fA-F]+$ ]] && (( (${#candidate} - 2) % 2 == 0 )); then
    hex_hash="$(cast keccak "$candidate")"
    if [[ "$hex_hash" == "$SEAL" ]]; then
      echo "MATCH hex: $candidate"
      matches=$((matches + 1))
    fi
  fi
done < "$CANDIDATES"

echo "matches=$matches"
