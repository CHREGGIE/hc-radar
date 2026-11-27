"""SHA-85: single-pass all-state volume scan (count logic mirrors new_practice_radar.py).

Streams the NPPES monthly full zip ONCE, keeping only org NPIs (Entity Type Code 2) for
counting: NPI, state, enumeration date, primary taxonomy code. Then applies the same
pipeline as scripts/new_practice_radar.py: NPI dedupe keep-last, window
(as_of - days, as_of], DME exclusion (NUCC classification
"Durable Medical Equipment & Medical Supplies", i.e. 332B* codes).

Validated against per-state new_practice_radar.py runs before use (see SHA-85 notes).

Usage:
    python scripts/state_tier_scan_singlepass.py \
        --file data/nppes_monthly_2026-11.zip --days 30 --as-of 2026-11-02 \
        --out data/state_tier_counts_singlepass_20261102.tsv
Output TSV: state, count, dme_excluded (all states + DC, even count 0).
"""
import argparse
import sys
import zipfile
from datetime import timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TAXO_CODE = [f"Healthcare Provider Taxonomy Code_{i}" for i in range(1, 16)]
TAXO_SWITCH = [f"Healthcare Provider Primary Taxonomy Switch_{i}" for i in range(1, 16)]
ST_COL = "Provider Business Practice Location Address State Name"
USECOLS = {"NPI", "Entity Type Code", "Provider Enumeration Date", ST_COL, *TAXO_CODE, *TAXO_SWITCH}
DATE_FMT = "%m/%d/%Y"


def primary_taxonomy(df):
    """Same function as new_practice_radar.primary_taxonomy (per-row, order-independent)."""
    out = pd.Series(pd.NA, index=df.index, dtype="object")
    for code, switch in zip(TAXO_CODE, TAXO_SWITCH):
        hit = out.isna() & df[switch].str.upper().eq("Y") & df[code].ne("")
        out[hit] = df.loc[hit, code]
    fallback = out.isna() & df[TAXO_CODE[0]].ne("")
    out[fallback] = df.loc[fallback, TAXO_CODE[0]]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="NPPES monthly zip")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--as-of", required=True, help="window end YYYY-MM-DD (pinned)")
    ap.add_argument("--taxonomy", default=str(ROOT / "data" / "nucc_taxonomy_261.csv"))
    ap.add_argument("--out", required=True, help="output TSV: state, count, dme_excluded")
    a = ap.parse_args()

    as_of = pd.Timestamp(a.as_of)
    start = as_of - timedelta(days=a.days)

    tax = pd.read_csv(a.taxonomy, dtype=str, encoding="latin-1")
    tax["Code"] = tax["Code"].str.strip()
    dme_codes = set(tax.loc[tax["Classification"].eq("Durable Medical Equipment & Medical Supplies"), "Code"])
    print(f"DME codes: {sorted(dme_codes)}", file=sys.stderr)

    z = zipfile.ZipFile(a.file)
    name = next(n for n in z.namelist()
                if n.lower().startswith("npidata_pfile") and "fileheader" not in n.lower())
    print(f"Scanning {a.file} :: {name} (single pass)", file=sys.stderr)

    frames = []
    with z.open(name) as f:
        for i, chunk in enumerate(pd.read_csv(f, dtype=str, usecols=lambda c: c in USECOLS,
                                             chunksize=200_000, keep_default_na=False)):
            orgs = chunk[chunk["Entity Type Code"].eq("2")]
            if len(orgs):
                keep = orgs[["NPI", ST_COL, "Provider Enumeration Date"]].copy()
                keep["primary_taxonomy_code"] = primary_taxonomy(orgs)
                frames.append(keep)
            if i % 25 == 0:
                print(f"  chunk {i}", file=sys.stderr)

    df = pd.concat(frames, ignore_index=True)
    print(f"{len(df):,} org NPI rows", file=sys.stderr)
    df = df.drop_duplicates("NPI", keep="last")
    df["enumeration_date"] = pd.to_datetime(df["Provider Enumeration Date"],
                                            format=DATE_FMT, errors="coerce")
    df["state"] = df[ST_COL].str.upper()

    new = df[(df.enumeration_date > start) & (df.enumeration_date <= as_of)].copy()
    codes = new["primary_taxonomy_code"].fillna("")
    is_dme = codes.isin(dme_codes) | codes.str.startswith("332B")
    n_dme = int(is_dme.sum())
    new = new[~is_dme]

    counts = new.groupby("state").size()
    window_all = df[(df.enumeration_date > start) & (df.enumeration_date <= as_of)]
    all_codes = window_all["primary_taxonomy_code"].fillna("")
    dme_counts = window_all.assign(is_dme=all_codes.isin(dme_codes)
                                   | all_codes.str.startswith("332B")) \
        .groupby(["state", "is_dme"]).size()

    states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID",
              "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO",
              "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA",
              "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
    print(f"\nWindow: {start.date()} (excl) to {as_of.date()} ({a.days} days); "
          f"{len(df):,} org NPIs in input; {len(new):,} new, {n_dme} DME excluded\n")
    with open(a.out, "w") as f:
        f.write("state\tcount\tdme_excluded\n")
        for st in states:
            c = int(counts.get(st, 0))
            d = int(dme_counts.get((st, True), 0))
            f.write(f"{st}\t{c}\t{d}\n")
            print(f"{st}: {c} (dme_excluded={d})")
    print(f"\nSaved {a.out}")


if __name__ == "__main__":
    main()
