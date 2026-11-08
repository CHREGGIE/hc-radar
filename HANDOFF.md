# Handoff — B2B product exploration (Nov 2026)

Summary of a chat session exploring which B2B software products Greg should build:
what was considered, what was learned, and where to pick up.

## Starting point
Greg has built admin panels and CRMs and is building a lead-gen chatbot for law firms.
He asked for product ideas, specifically "blue ocean" ones outside his usual verticals.

## Ideas rejected, and why
- **Gorgias-style helpdesk:** very crowded (Gorgias, Zendesk, Re:amaze, Richpanel, Intercom, Siena AI).
  Heavy infrastructure and high switching cost for buyers. Only viable as an add-on layer on top of
  existing helpdesks, not a replacement.
- **Law-firm intake chatbot:** crowded (Smith.ai, Intaker, LawDroid, Clio Grow). Viable only with a sharp
  differentiator such as state attorney-advertising compliance built in. Not pursued further here.
- **Other first-round ideas** (vertical AI-visibility monitoring, ABA intake, wholesale reorder portal,
  missed-call text-back, Shopify catalog fixer): Greg judged these red ocean.

## Second-round ideas considered
1. Agent-ready catalogs for B2B suppliers
2. Vendor bank-change verification against deepfake fraud
3. Tacit-knowledge capture for retiring business owners
4. Fake-evidence detection for claims (Greg chose to explore; became ClaimProof)
5. SMB overbilling recovery on contingency (Greg liked; parked)
6. AI usage governance for small professional firms
7. Spoken multilingual SOPs for frontline crews

Then Greg asked how to rebuild Shovels.ai and whether the model works for healthcare. That became
New Practice Radar, now the primary project.

## Research findings (web search, Nov 2026)
- **Fake-photo detection for insurers is crowded.** Large insurers (Aviva, MS&AD, IAG, Allianz, PZU) are
  building or deploying their own detectors; startups like VAARHAFT and Sensity sell into insurance.
- **Ecommerce return-photo fraud is filling up fast.** Forter calls AI-doctored damage claims the
  fastest-growing return abuse; UPS-owned Happy Returns is piloting AI return-fraud detection; a Shopify app
  (Veriflied) launched Oct 21, 2026 for AI-generated return photos.
- **Overbilling recovery is an old industry.** Contingency auditors (Auditel, TRI, CBIZ, Cost Analysts) have
  existed for decades, sometimes at ~50% of recovery; Vaudit covers SaaS/cloud/ads. The gap is businesses
  too small for human auditors.
- **B2B damage/shortage claims.** Enterprise deduction tools (HighRadius, Stuut) serve manufacturers vs.
  big-box retailers; delivery-photo apps (e.g., Podfy) cover the driver side. The gap is authenticating the
  claimant's own photos for mid-size distributors whose claims arrive by email.
- **Shovels.ai (reference model).** Aggregates building permits from thousands of jurisdictions,
  AI-classifies them, matches contractors (60–80% contact match), sells via app, API and data feeds.
  Its moat is jurisdiction coverage built over years.
- **Healthcare provider intelligence at enterprise level is crowded** (Definitive Healthcare, IQVIA,
  H1, Veeva). The opening is affordable new-practice signals for small and mid-size vendors.

## Active projects
| Project | Status | Spec |
|---|---|---|
| **New Practice Radar** (healthcare, Shovels-style) | **Primary.** Phase 0 volume measured on the real Nov 2026 NPPES file (NY: ~530 new org NPIs/month, ~365 unflagged). Precision hand-check pending | `specs/new-practice-radar.md`, `research/phase0-results.md` |
| **ClaimProof** (B2B damage-claim verification) | Secondary. Customer interviews first; no product code yet | `specs/claimproof.md` |
| SMB overbilling recovery | Parked. Suggested test: manual audits of 5–10 businesses in one vertical | — |

## Where to pick up
Greg hand-checks `research/phase0-review-sample.csv` (40 rows); then compute precision and the
enumeration-to-opening lag and make the gate call. See `research/phase0-results.md`: overall NY volume
passes, but physician/dental/clinic volume alone looks under 150/month, so multi-state may be needed.

Environment: a personal cloud environment `hc-radar` allows download.cms.gov and nucc.org. The data
lives in `data/` (gitignored). Re-download the monthly zip (~1.1 GB) in a fresh container.
