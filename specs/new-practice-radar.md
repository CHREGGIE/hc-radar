# Spec — New Practice Radar

## One-liner
A weekly feed of newly forming healthcare practices in a territory, sold to the small and mid-size
vendors who need to reach practices in their first 90 days.

## Customer
**Buyers:** vendors selling to new practices who can't afford enterprise provider databases.
Examples: medical and dental supply distributors, EHR and billing companies, equipment leasing,
malpractice insurance agents, healthcare staffing, IT and phone systems, buildout and signage,
healthcare marketing agencies, payroll.

**Job to be done:** "Tell me about new practices in my territory before my competitors find them."

**Price hypothesis:** $150–400 per month per territory or specialty bundle. To be tested.

## Data sources
| Source | Signal | Access | Phase |
|---|---|---|---|
| CMS NPPES weekly update file | New organization NPIs (Entity Type 2) with enumeration date, specialty code, practice address, authorized official | Free bulk download, download.cms.gov/nppes | 0–1 |
| CMS NPPES monthly full file | Baseline for change detection (address moves, new locations of existing groups) | Free, multi-GB | 1 |
| NPPES deactivation file | Remove closed entities | Free | 1 |
| NUCC taxonomy code set | Specialty names for codes | Free CSV, nucc.org | 0 |
| State license boards (NY first) | New clinician licenses | Varies by state | 2 |
| Certificate of Need filings (states that require CON) | Planned facilities, often far ahead | State health dept sites | 2 |
| State facility licensing (ASCs, urgent care, home health, labs) | New facility approvals | State health dept | 2 |
| Building permits for medical office buildouts | Physical clinic under construction | Shovels API or city open data | 3 |
| Business registrations | Entity formed, earliest signal | Secretary of State | 3 |

**Known limits of NPPES:** self-reported data; a new organization NPI is not always a new physical
location (billing entities, re-registrations, solo providers incorporating, subparts of existing
groups). Filtering this noise is the core value of the product.

## Phase 0 — prove the signal (current)
Goal: measure volume and precision before building anything else.
- Validate `scripts/new_practice_radar.py` against the real file header.
- Run for NY, last 30 days, 4 weekly files.
- Hand-check a sample (see TASKS.md).

**Gate to Phase 1:** roughly 150+ real openings per month in the target geography and 60%+ precision
on rows flagged as likely real. If it fails, options: expand to multi-state, focus on specialties with
better precision, or add a second confirming signal before launch.

## Phase 1 — pipeline
- Scheduled weekly job (GitHub Actions cron or Supabase scheduled function) that downloads the newest
  weekly file, loads raw rows to a staging table, and upserts into normalized tables.
- Monthly baseline load of the full file into DuckDB locally; push only needed columns and states to Supabase.
- Change detection: new NPI, practice address change, new specialty, deactivation.
- Noise scoring v2: replace boolean flags with a 0–100 "likely real opening" score. Features:
  subpart flag, PO box, mailing ≠ practice address, admin-sounding name, address shared by many
  existing org NPIs (e.g., a billing company's office), authorized official matching an existing
  individual NPI at the same address (solo provider incorporating).
- Use Claude for ambiguous business names only, with cached results and a cost cap.

### Proposed tables
- `npi_org` — npi (pk), legal_name, dba_name, enumeration_date, last_update, deactivation_date,
  primary_taxonomy, practice address fields, zip5, phone, official name/title/phone, is_subpart, parent_org
- `npi_event` — id, npi, event_type (new | moved | specialty_added | deactivated), detected_on, old_value, new_value
- `taxonomy` — code (pk), grouping, classification, specialization, display_name
- `opening_score` — npi, score, reasons (jsonb), model_version, scored_on
- `territory` — id, customer_id, zips[] or counties[], specialties[]
- `customer`, `alert_log`

## Phase 2 — enrichment and second signals
- Web presence check: website domain guess, Google Business listing lookup (respect API terms).
- NY state license and facility data as confirming signals; boost score when two sources agree.
- Contact enrichment: start with the authorized official from NPPES; evaluate one paid enrichment
  vendor only after Phase 0 shows demand.

## Phase 3 — product
- Next.js app on Vercel: territory setup (ZIPs/counties + specialties), feed of new practices with
  score and reasons, CSV export, saved searches.
- Weekly email digest per territory.
- CRM push (HubSpot first) as a paid add-on.
- Public SEO pages ("New dental practices in Brooklyn, Nov 2026"), similar to Shovels' content, for lead gen.

## Open questions
- Which specialties have the best precision and the most motivated vendor buyers?
- Is a single state enough volume, or must launch be multi-state?
- How fresh is NPPES enumeration relative to actual opening day? (Measure in Phase 0 hand-checks.)
- Compliance: customers' outreach must follow telemarketing and anti-spam rules; publish an acceptable-use policy.
