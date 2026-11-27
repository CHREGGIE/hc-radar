#!/usr/bin/env bash
# SHA-85: 50-state volume scan for pricing tiers.
# Runs scripts/new_practice_radar.py per state on the NPPES monthly full file
# (30-day window, pinned --as-of, DME excluded) and appends parsed counts to a TSV.
# Safe to re-run: states already present in the TSV are skipped.
#
# Usage: scripts/state_tier_scan.sh <asof YYYY-MM-DD> <STATE> [<STATE> ...]
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate

ASOF="$1"; shift
SRC="data/nppes_monthly_2026-11.zip"   # == NPPES_Data_Dissemination_November_2026_V2.zip
STAMP="${ASOF//-}"
TSV="data/state_tier_counts_${STAMP}.tsv"
LOGDIR="data/state_tier_scan_logs_${STAMP}"
mkdir -p "$LOGDIR"
touch "$TSV"

for ST in "$@"; do
  if grep -qE "^${ST}	" "$TSV"; then echo "== $ST already done, skipping"; continue; fi
  OUT="data/radar_${ST}_30d_${STAMP}.csv"
  LOG="$LOGDIR/${ST}.log"
  python scripts/new_practice_radar.py --file "$SRC" --state "$ST" --days 30 \
    --as-of "$ASOF" --exclude-dme --out "$OUT" >"$LOG" 2>&1
  COUNT=$(grep -oE "[0-9]+ new ${ST} organization NPIs" "$LOG" | head -1 | grep -oE "^[0-9]+")
  NOFLAG=$(grep -oE "\([0-9]+ with no noise flags\)" "$LOG" | grep -oE "[0-9]+")
  DME=$(grep -oE "Excluding [0-9]+ DME" "$LOG" | grep -oE "[0-9]+")
  if [ -z "${COUNT:-}" ]; then echo "parse failed for $ST; see $LOG"; exit 1; fi
  printf '%s	%s	%s	%s\n' "$ST" "$COUNT" "$NOFLAG" "${DME:-0}" >> "$TSV"
  echo "== $ST: count=$COUNT noflag=$NOFLAG dme_excluded=${DME:-0}"
done
echo "batch done: $(wc -l < "$TSV") states in $TSV"
