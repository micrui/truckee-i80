#!/usr/bin/env python3
"""Poll Caltrans open District 3 feeds for I-80 chain control (Nevada/Placer
counties) and currently active closures; append state CHANGES to
data/conditions/log.jsonl. Caltrans publishes no history of these feeds, so
this log is the history. Standard library only."""
import datetime, json, os, time, urllib.request

UA = "truckee-i80 data project"
CC_URL = "https://cwwp2.dot.ca.gov/data/d3/cc/ccStatusD03.json"
LCS_URL = "https://cwwp2.dot.ca.gov/data/d3/lcs/lcsStatusD03.json"
STATE = "data/conditions/state.json"
LOG = "data/conditions/log.jsonl"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def snapshot():
    snap = {}
    for rec in fetch(CC_URL).get("data", []):
        c = rec["cc"]
        loc = c["location"]
        if loc.get("route") != "I-80" or loc.get("county") not in ("Nevada", "Placer"):
            continue
        key = f'chain:{loc.get("locationName", "?")}:{loc.get("direction", "?")}'
        snap[key] = c.get("statusData", {}).get("status", "?")
    now = time.time()
    for rec in fetch(LCS_URL).get("data", []):
        c = rec["lcs"]
        begin = c["location"]["begin"]
        if begin.get("beginRoute") != "I-80" or begin.get("beginCounty") not in ("Nevada", "Placer"):
            continue
        ts = c.get("closure", {}).get("closureTimestamp", {})
        try:
            start = float(ts.get("closureStartEpoch", 0))
            end = float(ts.get("closureEndEpoch", 0))
        except ValueError:
            continue
        indefinite = ts.get("isClosureEndIndefinite") == "true"
        if start <= now and (indefinite or now <= end):
            cl = c["closure"]
            key = f'closure:{c.get("index", "?")}'
            snap[key] = (f'{cl.get("typeOfClosure", "?")}/{cl.get("typeOfWork", "?")}'
                         f' {begin.get("beginDirection", "?")} PM{begin.get("beginPostmile", "?")}')
    return snap

def main():
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    try:
        new = snapshot()
    except Exception as e:
        print(f"fetch failed: {e}")
        return
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    old = json.load(open(STATE)) if os.path.exists(STATE) else {}
    changes = []
    for k, v in new.items():
        if old.get(k) != v:
            changes.append({"t": now_iso, "key": k, "was": old.get(k), "now": v})
    for k in old:
        if k not in new:
            changes.append({"t": now_iso, "key": k, "was": old[k], "now": None})
    if changes:
        with open(LOG, "a") as f:
            for c in changes:
                f.write(json.dumps(c) + "\n")
    json.dump(new, open(STATE, "w"), indent=1, sort_keys=True)
    print(f"{len(new)} tracked items, {len(changes)} changes")

if __name__ == "__main__":
    main()
