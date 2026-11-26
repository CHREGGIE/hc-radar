#!/usr/bin/env python3
"""Archive the newest weekly NPPES dissemination file into data/ (SHA-86).

The CMS index (https://download.cms.gov/nppes/NPI_Files.html — case-sensitive)
lists only the NEWEST weekly file. Once it rotates off, multi-week backfills
are impossible, so each weekly zip must be archived as it is released.

Idempotent: if the current weekly zip already exists in data/, it is skipped.
Exits 0 with "already archived" or "archived" status; non-zero on failure.

Usage:
    python scripts/archive_nppes_weekly.py [--data-dir data/]
"""

import argparse
import re
import sys
from pathlib import Path

import requests

INDEX_URL = "https://download.cms.gov/nppes/NPI_Files.html"
WEEKLY_RE = re.compile(r"NPPES_Data_Dissemination_\d{6}_\d{6}_Weekly_V2\.zip")


def find_current_weekly(index_html: str) -> str | None:
    """Return the newest weekly zip filename listed on the CMS index."""
    matches = WEEKLY_RE.findall(index_html)
    return matches[-1] if matches else None


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive the newest weekly NPPES zip")
    parser.add_argument("--data-dir", default="data", help="directory to store zips (default: data/)")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching CMS index: {INDEX_URL}")
    resp = requests.get(INDEX_URL, timeout=60)
    resp.raise_for_status()

    weekly = find_current_weekly(resp.text)
    if not weekly:
        print("ERROR: no weekly NPPES file found on the CMS index", file=sys.stderr)
        return 1

    dest = data_dir / weekly
    if dest.exists():
        print(f"SKIP: {dest} already archived ({dest.stat().st_size:,} bytes)")
        return 0

    url = f"https://download.cms.gov/nppes/{weekly}"
    print(f"Downloading {url} -> {dest}")
    with requests.get(url, stream=True, timeout=300) as dl:
        dl.raise_for_status()
        tmp = dest.with_suffix(".zip.part")
        with open(tmp, "wb") as fh:
            for chunk in dl.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
        tmp.rename(dest)

    print(f"ARCHIVED: {dest} ({dest.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
