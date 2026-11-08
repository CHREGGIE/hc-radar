# CLAUDE.md — B2B Products Lab

## Who this is for
Greg Grinman, founder of Sharpcom (fractional CMO / SEO / ecommerce / AI consultant, Brooklyn NY).
Greg is exploring software products to sell to B2B companies. This repo holds the research,
specs, and prototypes. Read `HANDOFF.md` first, then `TASKS.md`.

## Working style
- Be critical and direct. No reflexive praise. If an idea or result looks weak, say so with evidence.
- Validate before building. Every phase in the specs has a gate; don't move past a failed gate.
- Prefer small, working increments over big scaffolds. Commit often with clear messages.
- When a fact matters (data field names, file formats, competitor claims), verify it from the source
  rather than from memory, and note the source in the relevant doc.
- Keep `HANDOFF.md` and `TASKS.md` current as work progresses.

## Default stack (Greg's existing tooling)
- Python 3.11+ for ingestion / ETL (pandas, requests; switch to duckdb or polars for the multi-GB monthly file)
- Supabase (Postgres + storage + auth) as the database
- Next.js on Vercel for any web front end
- GitHub for version control
- Claude API for classification and vision tasks

## Hard rules
- Never commit secrets. Use `.env` (gitignored) and document required vars in `.env.example`.
- No patient data (PHI) anywhere in the healthcare project. Provider directory data only.
- Respect source terms of use and rate limits. Identify scrapers with a contact User-Agent.
- In the claims product, never auto-reject or auto-accuse. The system flags; humans decide.
