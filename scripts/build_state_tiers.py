"""Build data/state_tiers_<asof>.csv from a counts TSV produced by
state_tier_scan_singlepass.py (state, count[, dme_excluded]) or state_tier_scan.sh
(state, count, no_noise_flags, dme_excluded).

Tier buckets (SHA-85): A = 400+ new org NPIs / 30 days, B = 150-399, C = <150
(counts are DME-excluded, window pinned to --as-of).

Usage: python scripts/build_state_tiers.py <asof YYYY-MM-DD> [tsv path]
       (default tsv: data/state_tier_counts_<asof>.tsv, falling back to
        data/state_tier_counts_singlepass_<asof>.tsv)
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ASOF = sys.argv[1] if len(sys.argv) > 1 else "2026-11-02"
STAMP = ASOF.replace("-", "")
SOURCE_FILE = "NPPES_Data_Dissemination_November_2026_V2.zip"
RUN_CMD = ("python scripts/new_practice_radar.py --file data/nppes_monthly_2026-11.zip "
           "--state <ST> --days 30 --as-of " + ASOF + " --exclude-dme")


def tier(n: int) -> str:
    return "A" if n >= 400 else ("B" if n >= 150 else "C")


default1 = ROOT / "data" / f"state_tier_counts_{STAMP}.tsv"
default2 = ROOT / "data" / f"state_tier_counts_singlepass_{STAMP}.tsv"
tsv = Path(sys.argv[2]) if len(sys.argv) > 2 else (default1 if default1.exists() else default2)

df = pd.read_csv(tsv, sep="\t", dtype={"state": str})
assert {"state", "count"} <= set(df.columns), f"need state/count columns in {tsv}"
df = df.drop_duplicates("state", keep="last").sort_values("state").reset_index(drop=True)
df = df[["state", "count"] + [c for c in ["dme_excluded"] if c in df.columns]]
df["tier"] = df["count"].map(tier)
df["as_of"] = ASOF
df["source_file"] = SOURCE_FILE
out = ROOT / "data" / f"state_tiers_{STAMP}.csv"
df.to_csv(out, index=False)

print(df.to_string(index=False))
print(f"\nTier totals: {df['tier'].value_counts().sort_index().to_dict()}")
print(f"Territories scanned: {len(df)} (expect 50 states + DC = 51)")
print(f"Input TSV: {tsv}")
print(f"Per-state reproducibility command: {RUN_CMD}")
print(f"Saved {out}")
