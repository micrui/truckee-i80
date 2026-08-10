# truckee-i80

An independent public record of Interstate 80 through Truckee and Donner Pass:
history, governance, funding, safety, and accumulating traffic data, every claim
traceable to its source. Sibling of
[truckee-flights](https://github.com/micrui/truckee-flights) (the airport) and
[truckee-trains](https://github.com/micrui/truckee-trains) (the railroad).

**Site: https://micrui.github.io/truckee-i80**

- How the road got here: a sourced timeline from the 1864 wagon road to the
  current rehabilitation projects.
- Who governs the freeway: what Caltrans, the CHP, and federal law each control,
  with statute citations.
- How the freeway is paid for: fuel taxes, truck fees, corridor project costs,
  and the federal cost-allocation record.
- Accidents and incidents: the corridor's incident record from CHP dispatch data,
  plus the adjudicated crash databases.
- The corridor in numbers: charts rendered automatically from the data below.

## Data collection (runs on schedule, accumulates in the open)

- `pems_daily.py` (daily): pulls Caltrans PeMS detector data for the 55 stations
  on the Truckee/Donner segment into `data/pems/hourly/`, and the statewide CHP
  incident file filtered to the Baxter-to-stateline corridor into `data/chp/`
  (backfilled to January 2026).
- `conditions_poll.py` (every 3 hours in summer, every 30 minutes in winter):
  polls Caltrans' open District 3 feeds for I-80 chain control and closures,
  logging state changes to `data/conditions/log.jsonl`. Caltrans publishes no
  history of these; this log accumulates one.
- `render_site.py`: regenerates the data page from the files above; both
  scheduled jobs run it after their pulls.
- `data/reference/truck-aadt.csv`: annual truck traffic at the Truckee count
  points, 2013 through 2024, extracted from the Caltrans truck census with
  per-row source URLs.
- `DATA-SOURCES.md`: access provenance for every source, including the PeMS
  account and archived terms of use. Credentials live only in GitHub Actions
  secrets; nothing sensitive is in this repository.

Stdlib-only Python; no dependencies, no build step. Corrections welcome via
issues.

License: MIT.
