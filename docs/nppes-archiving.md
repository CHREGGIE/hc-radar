# Weekly NPPES file archiving (SHA-86)

The CMS index — https://download.cms.gov/nppes/NPI_Files.html (URL is
**case-sensitive**) — lists only the newest weekly dissemination file. Once a
weekly zip rotates off the index it is gone for good, so multi-week backfills
are impossible unless each zip is archived as it is released.

## Script

`scripts/archive_nppes_weekly.py` — fetches the CMS index, finds the current
`NPPES_Data_Dissemination_<MMDDYY>_<MMDDYY>_Weekly_V2.zip`, and downloads it
into `data/` **only if not already present** (idempotent; a second run prints
`SKIP: ... already archived` and exits 0). Downloads go to a `.part` file and are
renamed on completion, so an interrupted run never leaves a corrupt zip.

Run manually:

```bash
cd /opt/data/hc-radar && source .venv/bin/activate
python scripts/archive_nppes_weekly.py            # add --data-dir to override data/
```

## Schedule

Hermes cron job `nppes-weekly-archive` (job id `3e61394ce35c`) — script-only
(no LLM), **every Monday 9:00 AM America/New_York**, with catch-up on return
after downtime. It runs the wrapper
`~/.hermes/../profiles/developer/scripts/archive_nppes_weekly.sh` (also stored
in this repo at `scripts/cron/archive_nppes_weekly.sh` for reference), which
invokes the archive script and only prints output when a new file is archived
or the run fails — silent ticks mean "nothing new".

Manage it with the Hermes `cronjob_manage` tool (`list` to see job state) or:

```bash
hermes cron list
hermes cron run <job_id>
```

Equivalent raw cron entry, if the repo ever moves off Hermes:

```
0 9 * * 1  cd /opt/data/hc-radar && .venv/bin/python scripts/archive_nppes_weekly.py >> data/archive.log 2>&1
```

## Storage rules

- Zips live in `data/` only; `.gitignore` excludes `data/` and `*.zip`, so
  archived files never enter git.
