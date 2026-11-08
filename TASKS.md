# TASKS

## Setup
- [x] `git init`, add `.gitignore` (Python, Node, `.env`, `data/`), create `.env.example`.
- [x] Create `data/` for downloaded files (gitignored; NPPES files are large).

## New Practice Radar — Phase 0: prove the signal (DO FIRST)
- [x] Download one current NPPES weekly zip. Open its `*_fileheader.csv` and confirm every column name
      used in `scripts/new_practice_radar.py` (the COLS dict and the taxonomy columns). Fix mismatches.
      The script was only tested on mock data.
      *Done 2026-11-08: all columns match V.2. Weekly link 404'd and the index lists only the newest week,
      so ran on the Nov monthly full file instead. Link regex fixed. See research/phase0-results.md.*
- [x] Run: `python scripts/new_practice_radar.py --file data/nppes_monthly_2026-11.zip --state NY --days 30`
- [x] Record total new NY organization NPIs, count with no noise flags, top specialties, top cities.
- [x] Replace the hard-coded TAXONOMY dict with a join to the official NUCC taxonomy CSV (nucc.org).
- [x] Write `scripts/sample_for_review.py`: random 30 "likely real" rows + 10 flagged rows into a review CSV
      with blank columns `has_website`, `has_google_listing`, `is_new_location`, `notes`.
- [ ] **(Greg, next)** Hand-check `research/phase0-review-sample.csv`. Compute precision of `likely_real_opening` and estimate the typical
      gap between NPI enumeration and actual opening.
- [~] Write findings to `research/phase0-results.md` (volume done; precision pending hand-check).
- [ ] **Gate:** go to Phase 1 only if roughly 150+ real openings/month in the target geography and 60%+
      precision on "likely real" rows. Otherwise stop and report options to Greg
      (multi-state, narrower specialties, second confirming signal).

## New Practice Radar — Phase 1: pipeline
See `specs/new-practice-radar.md`, Phase 1. Don't start until the Phase 0 gate passes.

## ClaimProof — validation only
- [ ] Turn the ClaimProof section of `research/interview-guides.md` into a one-page printable guide.
- [ ] No product code until Greg reports interview results.
