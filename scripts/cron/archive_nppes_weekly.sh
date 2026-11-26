#!/usr/bin/env bash
# Weekly NPPES archive job (SHA-86). Runs the idempotent archive script in
# hc-radar. Prints output ONLY when something happens (new file archived or an
# error) so the no_agent cron stays silent on "already archived" ticks.
set -o pipefail
cd /opt/data/hc-radar || { echo "hc-radar repo missing"; exit 1; }
source .venv/bin/activate
out=$(python scripts/archive_nppes_weekly.py 2>&1)
code=$?
if [ $code -ne 0 ]; then
  echo "NPPES weekly archive FAILED: $out"
  exit $code
elif echo "$out" | grep -q '^ARCHIVED'; then
  echo "$out"
  ls -la data/
fi
