"""
Draw a hand-check sample from a new_practice_radar.py output CSV.

Takes N random "likely real" rows (no noise flags) and M random flagged rows,
and writes a review CSV with blank columns for Greg to fill in:
    has_website, has_google_listing, is_new_location, opened_on, notes

`opened_on` (best guess at actual opening date, from website / Google / press) is used to
estimate the gap between NPI enumeration and opening.

Usage:
    python scripts/sample_for_review.py output/new_practices_NY_20261108.csv
    python scripts/sample_for_review.py in.csv --real 30 --flagged 10 --seed 42 --out review.csv
"""
import argparse
import sys
import urllib.parse
from pathlib import Path

import pandas as pd

REVIEW_COLS = ["has_website", "has_google_listing", "is_new_location", "opened_on", "notes"]


def search_url(r):
    q = " ".join(str(x) for x in [r.get("legal_name"), r.get("practice_address"), r.get("city")]
                 if isinstance(x, str) and x)
    return "https://www.google.com/search?q=" + urllib.parse.quote_plus(q)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--real", type=int, default=30, help="likely-real rows to sample")
    ap.add_argument("--flagged", type=int, default=10, help="flagged rows to sample")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out")
    a = ap.parse_args()

    df = pd.read_csv(a.csv, dtype=str, keep_default_na=False)
    real_mask = df.likely_real_opening.str.lower().eq("true")
    real, flagged = df[real_mask], df[~real_mask]
    if len(real) < a.real or len(flagged) < a.flagged:
        print(f"warning: only {len(real)} likely-real and {len(flagged)} flagged rows available",
              file=sys.stderr)

    sample = pd.concat([
        real.sample(min(a.real, len(real)), random_state=a.seed).assign(sample_group="likely_real"),
        flagged.sample(min(a.flagged, len(flagged)), random_state=a.seed).assign(sample_group="flagged"),
    ])
    # Shuffle so the reviewer doesn't know which group a row came from (reduces bias).
    sample = sample.sample(frac=1, random_state=a.seed).reset_index(drop=True)
    sample.insert(0, "review_id", range(1, len(sample) + 1))
    sample["search_url"] = sample.apply(search_url, axis=1)
    for c in REVIEW_COLS:
        sample[c] = ""

    lead = ["review_id", "legal_name", "dba_name", "specialty", "practice_address", "city", "zip5",
            "phone", "enumeration_date", "search_url"] + REVIEW_COLS
    rest = [c for c in sample.columns if c not in lead]
    sample = sample[lead + rest]  # sample_group stays at the far right; hide it while reviewing

    out = a.out or str(Path(a.csv).with_name(Path(a.csv).stem + "_review.csv"))
    sample.to_csv(out, index=False)
    print(f"Wrote {len(sample)} rows ({(sample.sample_group == 'likely_real').sum()} likely real, "
          f"{(sample.sample_group == 'flagged').sum()} flagged) to {out}")


if __name__ == "__main__":
    main()
