# Data sources and access provenance

## Caltrans PeMS (pems.dot.ca.gov)

- Access is through a registered PeMS account held by the site maintainer, created
  2026-08-09 with the Terms of Use reviewed at signup. An archived copy of the policy
  as presented (dated December 7, 2000) is in `sources/pems-use-policy-2000-12-07.txt`.
- The policy states that site content "unless otherwise indicated, is considered in the
  public domain" and prohibits attempts "to defeat or circumvent security features, or
  to utilize this system for other than its intended purposes."
- Use here: one scheduled pull per day (the prior day's District 3 five-minute file,
  one listing request and one download), plus occasional manual pulls for historical
  baselines, all through the account's normal endpoints with an identifying user-agent.
  No circumvention of access controls. Credentials live in GitHub Actions secrets and
  the maintainer's keychain; they are never stored in this repository.

## Caltrans open feeds (no authentication)

- Chain control, lane closures, changeable message signs, and roadside weather:
  District 3 JSON at cwwp2.dot.ca.gov (the QuickMap backend). Polled on a schedule;
  history accumulated in this repository, since Caltrans publishes none.
- Current conditions text: roads.dot.ca.gov/roadinfo/i80
- Annual AADT and truck AADT: Caltrans GIS REST layers (gisdata.dot.ca.gov)

## CHP incidents

- Live traffic incidents (collisions, hazards, fires) via the PeMS CHP Incidents Day
  dataset, statewide, filtered to the I-80 corridor box from Baxter to the Nevada state line (lat 39.2–39.6, lon −120.9 to −119.99), matching the corridor’s chain-control territory. Pulled by the same daily
  job into `data/chp/`. This is the real-time incident feed; TIMS below is the
  adjudicated historical crash record.

## Crash data

- SWITRS via TIMS (tims.berkeley.edu, UC Berkeley SafeTREC), registered access,
  one-time queries for the record pages.

## Truck volumes and weights

- Truck counts by axle class: Caltrans Traffic Census annual "Truck AADT" tables
  (https://dot.ca.gov/programs/traffic-operations/census), statewide Excel files, public.
  Key I-80 rows for this corridor are excerpted in `data/reference/truck-aadt.csv` with the
  source year noted per row.
- Axle weights: the nearest weigh-in-motion instrument to the pass is Caltrans WIM Station 72
  (Bowman, I-80 Placer County postmile R23.4, east of Auburn). Caltrans publishes no per-record
  WIM download; the stated access route is a request to traffic@dot.ca.gov, and pre-2016 weight
  distributions are public through FHWA's VTRIS W-tables (https://fhwaapps.fhwa.dot.gov/vtris-wp/).
  No public source measures axle weights at Donner Pass itself; the CHP scales east of Truckee
  generate enforcement data, not published statistics.
