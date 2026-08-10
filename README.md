# truckee-i80

Independent, reproducible data about Interstate 80 through Truckee and Donner Pass.
Sibling of [truckee-flights](https://github.com/micrui/truckee-flights). Site pages
to come; the data collection runs first.

- `pems_daily.py`: daily pull of Caltrans PeMS detector data for the 55 stations on
  the Truckee/Donner segment, aggregated to station-hours in `data/pems/hourly/`.
- `conditions_poll.py`: polls Caltrans' open District 3 feeds for I-80 chain control
  and closures, logging state changes to `data/conditions/log.jsonl`. Caltrans
  publishes no history of these; this log accumulates one.
- `DATA-SOURCES.md`: access provenance, including the PeMS account and archived
  terms of use.

License: MIT.
