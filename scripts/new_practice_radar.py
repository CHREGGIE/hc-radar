"""
New Practice Radar - prototype (Phase 0)

Finds ORGANIZATION NPIs (Entity Type 2) in one state that were enumerated recently,
labels specialty via the official NUCC taxonomy, flags likely noise, and writes a CSV + summary.

Input is one or more NPPES V.2 zips: either the monthly full file (recommended; it contains every
active NPI with its enumeration date) or weekly update files. Files are streamed from inside the
zip in chunks, so the ~11 GB monthly CSV is never extracted.

Usage:
    pip install requests pandas
    # monthly full file (download it once into data/; ~1.1 GB zipped)
    python scripts/new_practice_radar.py --file data/nppes_monthly_2026-11.zip --state NY --days 30
    # newest N weekly files, auto-downloaded from the CMS index into data/
    python scripts/new_practice_radar.py --state NY --days 30 --weeks 1

Sources (verified 2026-11-08):
    NPPES: https://download.cms.gov/nppes/NPI_Files.html (public, no key). V.1 files ended 2026-03-03.
    NUCC taxonomy CSV: https://www.nucc.org (Code Sets > Taxonomy > CSV), latin-1 encoded.
"""
import argparse
import glob
import re
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUTPUT = ROOT / "output"

INDEX_URL = "https://download.cms.gov/nppes/NPI_Files.html"
BASE = "https://download.cms.gov/nppes/"
NUCC_INDEX = "https://www.nucc.org/index.php/code-sets-mainmenu-41/provider-taxonomy-mainmenu-40/csv-mainmenu-57"
NUCC_BASE = "https://www.nucc.org"
UA = {"User-Agent": "hc-radar-prototype/0.1 (public data research)"}

# Verified against npidata_pfile_20050523-20261102_fileheader.csv (V.2, 330 columns).
COLS = {
    "NPI": "npi",
    "Entity Type Code": "entity_type",
    "Provider Organization Name (Legal Business Name)": "legal_name",
    "Provider Other Organization Name": "dba_name",
    "Provider Enumeration Date": "enumeration_date",
    "Last Update Date": "last_update",
    "NPI Deactivation Date": "deactivation_date",
    "Provider First Line Business Practice Location Address": "practice_address",
    "Provider Business Practice Location Address City Name": "city",
    "Provider Business Practice Location Address State Name": "state",
    "Provider Business Practice Location Address Postal Code": "zip",
    "Provider Business Practice Location Address Telephone Number": "phone",
    "Provider First Line Business Mailing Address": "mailing_address",
    "Authorized Official First Name": "official_first",
    "Authorized Official Last Name": "official_last",
    "Authorized Official Title or Position": "official_title",
    "Authorized Official Telephone Number": "official_phone",
    "Is Organization Subpart": "is_subpart",
    "Parent Organization LBN": "parent_org",
}
TAXO_CODE = [f"Healthcare Provider Taxonomy Code_{i}" for i in range(1, 16)]
TAXO_SWITCH = [f"Healthcare Provider Primary Taxonomy Switch_{i}" for i in range(1, 16)]
DATE_FMT = "%m/%d/%Y"


# ---------- sources ----------

def download(url, dest):
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    print(f"Downloading {url} ...", file=sys.stderr)
    with requests.get(url, headers=UA, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return dest


def weekly_links():
    html = requests.get(INDEX_URL, headers=UA, timeout=60).text
    links = re.findall(r"""href=['"]([^'"]*Weekly[^'"]*\.zip)['"]""", html, flags=re.I)
    links = [l if l.startswith("http") else BASE + l.lstrip("./") for l in links]
    if not links:
        sys.exit("Could not find weekly files on the CMS page; the page layout may have changed.")
    # As of Nov 2026 the page lists only the newest weekly file, so --weeks > 1 can't be served
    # from the index. Keep weekly zips in data/ as they come out, or use the monthly file.
    return links


def load_taxonomy():
    files = sorted(glob.glob(str(DATA / "nucc_taxonomy_*.csv")),
                   key=lambda p: int(re.search(r"(\d+)\.csv$", p).group(1)))
    if not files:
        html = requests.get(NUCC_INDEX, headers=UA, timeout=60).text
        hrefs = re.findall(r"""href=['"]([^'"]*nucc_taxonomy_(\d+)\.csv)['"]""", html)
        if not hrefs:
            sys.exit("Could not find the NUCC taxonomy CSV link; download it manually into data/.")
        href = max(hrefs, key=lambda h: int(h[1]))[0]
        files = [str(download(NUCC_BASE + href, DATA / Path(href).name))]
    t = pd.read_csv(files[-1], dtype=str, encoding="latin-1")
    t["Code"] = t["Code"].str.strip()
    print(f"Taxonomy: {Path(files[-1]).name} ({len(t)} codes)", file=sys.stderr)
    return t.set_index("Code")


def iter_npi_chunks(zip_path, usecols, chunksize=200_000):
    z = zipfile.ZipFile(zip_path)
    name = next(n for n in z.namelist()
                if n.lower().startswith("npidata_pfile") and "fileheader" not in n.lower())
    with z.open(name) as f:
        yield from pd.read_csv(f, dtype=str, usecols=usecols, chunksize=chunksize, keep_default_na=False)


def load_orgs(zip_paths, state):
    """All Entity Type 2 rows for `state` across the given zips (later files win on duplicate NPI)."""
    wanted = set(COLS) | set(TAXO_CODE) | set(TAXO_SWITCH)
    st_col = "Provider Business Practice Location Address State Name"
    frames = []
    for p in zip_paths:
        print(f"Reading {Path(p).name} ...", file=sys.stderr)
        n = 0
        for chunk in iter_npi_chunks(p, lambda c: c in wanted):
            n += len(chunk)
            frames.append(chunk[(chunk["Entity Type Code"] == "2") & (chunk[st_col].str.upper() == state)])
        print(f"  {n:,} rows scanned", file=sys.stderr)
    df = pd.concat(frames, ignore_index=True).drop_duplicates("NPI", keep="last")
    return df


# ---------- logic ----------

def primary_taxonomy(df):
    out = pd.Series(pd.NA, index=df.index, dtype="object")
    for code, switch in zip(TAXO_CODE, TAXO_SWITCH):
        hit = out.isna() & df[switch].str.upper().eq("Y") & df[code].ne("")
        out[hit] = df.loc[hit, code]
    fallback = out.isna() & df[TAXO_CODE[0]].ne("")
    out[fallback] = df.loc[fallback, TAXO_CODE[0]]
    return out


def norm_addr(s):
    return s.fillna("").str.upper().str.replace(r"[^A-Z0-9 ]", "", regex=True) \
        .str.replace(r"\s+", " ", regex=True).str.strip()


def flags(r):
    out = []
    if str(r.is_subpart).upper() == "Y":
        out.append("subpart of existing org")
    if r.mailing_address.strip() and r.practice_address.strip() \
            and r.mailing_address.strip().upper() != r.practice_address.strip().upper():
        out.append("mailing != practice address")
    if re.search(r"\bP\.?\s?O\.?\s?BOX\b", r.practice_address, re.I):
        out.append("PO box practice address")
    name = str(r.legal_name).upper()
    if any(k in name for k in ["BILLING", "MANAGEMENT", "HOLDINGS", "STAFFING", "SERVICES MSO"]):
        out.append("possible billing/admin entity")
    if r.deactivation_date.strip():
        out.append("deactivated")
    return "; ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="NY")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--file", action="append", help="local NPPES zip (monthly or weekly); repeatable")
    ap.add_argument("--weeks", type=int, default=1, help="if no --file: newest weekly files to download")
    ap.add_argument("--as-of", help="window end date YYYY-MM-DD (default: latest enumeration date in data)")
    ap.add_argument("--out")
    a = ap.parse_args()
    state = a.state.upper()
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)

    if a.file:
        zips = a.file
    else:
        links = weekly_links()[-a.weeks:]
        if len(links) < a.weeks:
            print(f"warning: CMS index lists only {len(links)} weekly file(s)", file=sys.stderr)
        zips = [download(u, DATA / u.rsplit("/", 1)[-1]) for u in links]

    taxonomy = load_taxonomy()
    df = load_orgs(zips, state)
    df["primary_taxonomy_code"] = primary_taxonomy(df)
    df = df.rename(columns=COLS)
    df["enumeration_date"] = pd.to_datetime(df.enumeration_date, format=DATE_FMT, errors="coerce")
    df["zip5"] = df.zip.str[:5]
    df["addr_key"] = norm_addr(df.practice_address) + "|" + df.zip5

    as_of = pd.Timestamp(a.as_of) if a.as_of else df.enumeration_date.max()
    start = as_of - timedelta(days=a.days)
    in_window = (df.enumeration_date > start) & (df.enumeration_date <= as_of)
    new = df[in_window].copy()

    # Informational (not a flag yet): how many OTHER org NPIs enumerated before the window share
    # this practice address. Only meaningful with the monthly full file as input.
    prior_counts = df[df.enumeration_date <= start].addr_key.value_counts()
    new["existing_orgs_at_address"] = new.addr_key.map(prior_counts).fillna(0).astype(int)

    disp = taxonomy["Display Name"].fillna(taxonomy["Classification"])
    new["specialty"] = new.primary_taxonomy_code.map(disp).fillna("Unknown (" + new.primary_taxonomy_code.fillna("?") + ")")
    new["taxonomy_grouping"] = new.primary_taxonomy_code.map(taxonomy["Grouping"])
    new["noise_flags"] = new.apply(flags, axis=1)
    new["likely_real_opening"] = new.noise_flags.eq("")

    keep = ["npi", "enumeration_date", "legal_name", "dba_name", "specialty", "taxonomy_grouping",
            "primary_taxonomy_code", "practice_address", "mailing_address", "city", "zip5", "phone",
            "official_first", "official_last", "official_title", "official_phone", "is_subpart",
            "parent_org", "existing_orgs_at_address", "noise_flags", "likely_real_opening"]
    new = new[keep].sort_values("enumeration_date", ascending=False)
    new["enumeration_date"] = new.enumeration_date.dt.date

    out = a.out or str(OUTPUT / f"new_practices_{state}_{as_of:%Y%m%d}_{a.days}d.csv")
    new.to_csv(out, index=False)

    real = new[new.likely_real_opening]
    print(f"\nWindow: {start.date()} (excl) to {as_of.date()} ({a.days} days); "
          f"{len(df):,} {state} org NPIs in input")
    print(f"{len(new)} new {state} organization NPIs ({len(real)} with no noise flags)\n")
    print("Top specialties (all new):\n", new.specialty.value_counts().head(15).to_string(), "\n")
    print("Top specialties (no flags):\n", real.specialty.value_counts().head(15).to_string(), "\n")
    print("Top cities:\n", new.city.str.title().value_counts().head(10).to_string(), "\n")
    print("Noise flags (a row can have several):\n",
          new.noise_flags.str.split("; ").explode().replace("", pd.NA).dropna().value_counts().to_string(), "\n")
    print("Rows whose address already hosts 1+ older org NPI:",
          int((new.existing_orgs_at_address > 0).sum()),
          f"(of which no-flag: {int((real.existing_orgs_at_address > 0).sum())})")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
