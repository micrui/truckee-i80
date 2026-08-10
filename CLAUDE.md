# CLAUDE.md: truckee-i80

Public record of Interstate 80 over Donner Pass at Truckee: traffic volumes, chain control and
closures, incidents, governance, funding, history. Site: https://micrui.github.io/truckee-i80
(GitHub Pages from `/docs`).

## Voice and editorial rules (non-negotiable)

Same rules as truckee-flights:

- Community member writing for neighbors; no side-taking, no outreach voice.
- No highway/traffic jargon in prose ("AADT", "postmile", "R-2" get plain-English glosses on
  first use or a link to the source that defines them).
- **Falsifiability is the admission criterion.** Unfalsifiable claims appear only as attributed
  statements. Political questions (what the corridor should carry, who should pay) stay open;
  the site supplies the record.
- No self-referential neutrality statements, no apologetic framing, no editorializing labels.
- No aphorisms and no imported frames. A sentence may not bring in an image or domain
  (military, conquest, personified laws or records) that the subject itself did not supply.
  Transitions state the topic change plainly. Directness is not softening: state the hard
  fact concretely instead of decorating it or deleting it.
- Narrative prose is drafted in a clean room: a fresh agent receives only the fact sheet
  (from facts.json) and these style rules, never the working conversation. The session
  verifies the draft against the registry and assembles it. Long-context drafting produces
  ornament; clean-context drafting from facts does not.
- No em-dashes anywhere, in site prose or repo docs. Use commas, colons, semicolons,
  parentheses, or a new sentence.
- Every number traces to a linked source. Corrections are dated addenda, never silent.

## Data collection

All jobs are stdlib-only Python run by GitHub Actions:

- `pems_daily.py` (workflow `pems-daily.yml`, daily 19:00 UTC) pulls yesterday's Caltrans PeMS
  5-minute detector file for District 3, filters to the 55 stations in `config/truckee_stations.txt`,
  aggregates to hourly rows in `data/pems/hourly/`. Also pulls the statewide daily CHP incident
  file and filters to the corridor box in `data/chp/`.
- `conditions_poll.py` (workflow `conditions-poll.yml`) polls Caltrans' public cwwp2 feeds for
  chain-control status and lane closures on I-80 in Nevada/Placer counties; appends changes to
  `data/conditions/log.jsonl`. Winter cadence every 30 min, summer every 3 h.
- **Corridor box**: lat 39.2–39.6, lon −120.9 to −119.99, Baxter to the Nevada state line,
  matching the corridor's chain-control territory.

## Credentials policy

- PeMS requires a registered account (created 2026-08-09; terms archived in `sources/`).
  Credentials live **only** in GitHub Actions secrets (`PEMS_USER`, `PEMS_PASS`) and the
  maintainer's keychain. Never in this repository, never in code, never in logs.
- One scheduled pull per day plus occasional manual runs; no circumvention of access controls.
- The cwwp2 feeds are public and unauthenticated.
- Provenance for every source is in `DATA-SOURCES.md`.

## Working discipline

- Hold pushes until the repo is coherent; verify locally; single push.
- Pages are hand-written HTML in `/docs` using the shared CSS token set (light/dark via
  `prefers-color-scheme` + `data-theme` override). No build step, no dependencies.
- Scheduled workflows `git pull --rebase --autostash` before pushing; commit steps must
  tolerate empty data days.

## The fact registry

`facts.json` is the canonical record of every factual claim on the site: status
(verified | sourced | contested | held), sources, method, check date, and the pages that
state it. Pages must never claim what the registry does not hold; corrections fix both,
together, in one commit. `python3 factcheck.py` validates the registry and flags facts
unchecked for 180 days. The `/fact-vet` skill runs the full verification ritual.

## Siblings

truckee-flights (the airport) and truckee-trains (the railroad) follow the same pattern and rules.
