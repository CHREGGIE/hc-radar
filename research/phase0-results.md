# Phase 0 results — New Practice Radar (NY)

**Status:** volume measured on real data; precision **not yet measured** (needs Greg's hand-check of
`research/phase0-review-sample.csv`). Gate decision is pending.

Run date: 2026-11-08. Data: NPPES V.2 monthly full file, November 2026
(`NPPES_Data_Dissemination_November_2026_V2.zip`, built 2026-11-02, 9,891,116 NPI rows).
Taxonomy: NUCC v26.1 (`nucc_taxonomy_261.csv`, 883 codes).

## What changed in the script, and why
| Finding | Fix |
|---|---|
| All 19 `COLS` names and 30 taxonomy columns **match** the real V.2 header (330 cols). | None needed. |
| CMS page uses single-quoted `href='...'`; the old regex (double quotes only) found nothing and exited. | Regex accepts both quote styles. |
| CMS page lists **only the newest** weekly file, and that file (`..._102626_110126_Weekly_V2.zip`) returned **404** on 2026-11-08. `--weeks 4` cannot be served from the index. | Added `--file` for local zips. Used the monthly full file instead: it holds every active NPI with its enumeration date, so "enumerated in the last N days" is exact. |
| V.1 files were retired 2026-03-03. | Script targets V.2. |
| Deactivated NPIs have a blank Entity Type, so the `entity_type == "2"` filter drops them; the "deactivated" flag can never fire. | Left as is (harmless). Phase 1 should use the deactivation file. |
| Window used `datetime.now()`, so results drifted with run day. | `--as-of` (defaults to latest enumeration date in data). |
| Hard-coded 34-code TAXONOMY dict. | Joined to NUCC CSV (auto-downloads into `data/`). |
| ~11 GB CSV read in one shot. | Chunked streaming from the zip; full scan ≈ 95 s, low memory. |
| — | New informational column `existing_orgs_at_address`: count of older NY org NPIs at the same normalized address + ZIP5. Not yet a flag. |

## Volume (NY, organization NPIs)
Command: `python scripts/new_practice_radar.py --file data/nppes_monthly_2026-11.zip --state NY --days 30`

| Window | New org NPIs | No noise flags |
|---|---|---|
| 30 days (10/03–11/02) | **532** | **366** |
| 90 days (08/05–11/02), per month avg | 526 | 365 |

Weekly volume is steady at ~100–145 (no seasonality visible over 13 weeks).

**Top specialties, 30 days (all / no-flag):** DME & Medical Supplies 56/44, Clinical Social Worker 37/24,
Mental Health Counselor 30/21, Psych NP 30/21, Retail Pharmacy 19/13, Urgent Care 19/11,
Internal Medicine 13/8, Physical Therapist 13/11, Behavioral Health Agency 13/8, Behavior Analyst 12/10.

**Top cities, 30 days:** New York 88, Brooklyn 71, Bronx 18, Staten Island 15, Rochester 14, Jamaica 11,
Albany 11, Flushing 10, Buffalo 8, Valley Stream 8. NYC's five boroughs ≈ 40% of the state.

**Noise flags, 30 days:** mailing ≠ practice address 150, subpart 11, billing/admin name 9, PO box 0.

## Critical read (before hand-check)
1. **Raw volume clears the 150/month bar easily, but the mix is the problem.** Per month (90-day avg,
   no-flag rows): agencies/transport/other 90, suppliers (DME, pharmacy) 79, behavioral health 64,
   clinics/facilities 34, chiro/PT/eye/podiatry 30, physician groups 30, NP/PA 25, **dental 13**.
   The buyers in the spec (supply distributors, EHR, buildout, leasing) mostly want physician, dental,
   and clinic openings. Those together are only ~75–80 no-flag rows/month in all of NY.
2. **Many "likely real" rows are solo clinicians incorporating, not new locations.** Of 1,094 no-flag
   rows (90 days), 147 have an apartment-style practice address and 157 carry a personal credential in
   the legal name (LCSW, LMHC, NP, MD, DDS...). Excluding both leaves ~270/month, about half in
   agencies/suppliers. Behavioral health and NP/PA drop by half or more.
3. **The "mailing ≠ practice" flag looks too blunt.** It is 88% of all flags, and examples include
   plausible real practices that just use a home or accountant mailing address (e.g., a new pediatrics
   PLLC with a street practice address and a residential mailing address). The hand-check will
   show whether flagged rows are really worse.
4. **`existing_orgs_at_address` is a promising noise signal.** 193 of 532 new rows (130 no-flag) share
   an address with at least one older NY org NPI: billing offices, large medical buildings, or an
   existing group adding an entity. Score it in Phase 1. It needs care, since a large medical office
   building legitimately hosts many orgs.
5. **DME is the largest single category.** NY DME enrollments are historically fraud-prone, and few target
   buyers sell to DME suppliers. Consider excluding by default.

**Implication for the gate:** at 366 no-flag rows/month, 60% precision gives ~220 real openings/month,
so volume passes for "any organization". For the core buyer specialties (physician, dental, clinic),
NY alone is likely **under** 150/month even at 100% precision. Expect to need multi-state or a narrower
buyer focus for those segments.

## Hand-check (pending, for Greg)
File: `research/phase0-review-sample.csv`, 40 rows (30 no-flag + 10 flagged, seed 42) from the 30-day run.
Rows are shuffled; `sample_group` (far right) shows which bucket each came from. Hide it while reviewing.
Fill in:
- `has_website`, `has_google_listing`: Y/N
- `is_new_location`: Y = a new physical place where patients will be seen; N = billing entity,
  re-registration, existing location, home office/telehealth only; ? = can't tell
- `opened_on`: best-evidence opening date (site launch, Google "opened" date, press), else blank
- `notes`

Then compute: precision = Y / (Y + N) within `likely_real`, the same for `flagged`, and the median
(`opened_on` − `enumeration_date`). With n=30 the 95% interval on precision is about ±17 points, so treat
a result between 45% and 75% as inconclusive and draw another 30 rows.

## Gate
- Volume ≥150 real openings/month: **likely pass overall; likely fail for physician/dental/clinic only.**
- Precision ≥60% on likely-real: **unknown until hand-check.**
