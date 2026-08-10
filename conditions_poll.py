#!/usr/bin/env python3
"""Poll Caltrans open District 3 feeds for I-80 Nevada County chain control and
lane closures; append state CHANGES to data/conditions/log.jsonl. Caltrans
publishes no history, so this log is the history. Standard library only."""
import datetime, json, os, urllib.request

UA = "truckee-i80 data project"
FEEDS = {
    "chain": "https://cwwp2.dot.ca.gov/data/d3/cc/ccStatusD03.json",
    "closure": "https://cwwp2.dot.ca.gov/data/d3/lcs/lcsStatusD03.json",
}
STATE = "data/conditions/state.json"
LOG = "data/conditions/log.jsonl"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def snapshot():
    snap = {}
    cc = fetch(FEEDS["chain"])
    for item in cc.get("data", []):
        s = item.get("cc", {})
        loc = s.get("location", {})
        if s.get("route") != "SR-80" and "80" not in str(s.get("route", "")):
            continue
        key = f"chain:{s.get('recordName') or loc.get('locationName', '?')}"
        snap[key] = s.get("statusData", {}).get("status") or s.get("status") or "?"
    lcs = fetch(FEEDS["closure"])
    for item in lcs.get("data", []):
        c = item.get("lcs", {})
        loc = c.get("location", {}) or {}
        begin = loc.get("begin", {}) or {}
        route = begin.get("beginRoute") or ""
        county = begin.get("beginCounty") or ""
        if "80" not in str(route) or county not in ("NEV", "PLA", ""):
            continue
        idx = c.get("closure", {}).get("index") or c.get("index") or begin.get("beginNearby") or "?"
        typ = c.get("closure", {}).get("typeOfClosure") or "?"
        snap[f"closure:{idx}"] = typ
    return snap

def main():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    try:
        new = snapshot()
    except Exception as e:
        print(f"fetch failed: {e}")
        return
    old = json.load(open(STATE)) if os.path.exists(STATE) else {}
    changes = []
    for k, v in new.items():
        if old.get(k) != v:
            changes.append({"t": now, "key": k, "was": old.get(k), "now": v})
    for k in old:
        if k not in new:
            changes.append({"t": now, "key": k, "was": old[k], "now": None})
    if changes:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a") as f:
            for c in changes:
                f.write(json.dumps(c) + "\n")
    json.dump(new, open(STATE, "w"), indent=1)
    print(f"{len(new)} tracked items, {len(changes)} changes")

if __name__ == "__main__":
    main()
