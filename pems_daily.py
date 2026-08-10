#!/usr/bin/env python3
"""Daily PeMS pull: yesterday's District 3 five-minute station file, filtered to
the I-80 Truckee/Donner segment and aggregated to hourly per-station rows.

Runs from GitHub Actions with a registered PeMS account (see DATA-SOURCES.md).
Credentials via environment: PEMS_USER, PEMS_PASS. One listing request, one
file download per day. Standard library only.
"""
import csv, datetime, gzip, io, json, os, sys, urllib.request, urllib.parse
from http.cookiejar import CookieJar

BASE = "https://pems.dot.ca.gov"
UA = "truckee-i80 data project (registered user)"
TZ = datetime.timezone(datetime.timedelta(hours=-8))  # PeMS files are local standard time days

def opener_with_login():
    cj = CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", UA)]
    data = urllib.parse.urlencode({
        "redirect": "", "username": os.environ["PEMS_USER"],
        "password": os.environ["PEMS_PASS"], "login": "Login",
    }).encode()
    with op.open(BASE + "/", data, timeout=60) as r:
        body = r.read().decode(errors="replace")
    if "Logout" not in body and "logout" not in body:
        sys.exit("PeMS login failed")
    return op

def find_file(op, district, ftype, want):
    url = (f"{BASE}/?srq=clearinghouse&district_id={district}&geotag=null"
           f"&yy={want[-14:-10]}&type={ftype}&returnformat=text")
    with op.open(url, timeout=60) as r:
        listing = json.load(r)
    for month in (listing.get("data") or {}).values():
        for e in month:
            if e.get("file_name") == want:
                return e["url"]
    return None

def download(op, href):
    with op.open(BASE + href, timeout=300) as r:
        return r.read()

TRUCKEE_BOX = (39.2, 39.6, -120.6, -120.0)  # lat_min, lat_max, lon_min, lon_max

def in_box(lat, lon):
    a, b, c, d = TRUCKEE_BOX
    return a <= lat <= b and c <= lon <= d

def pull_chp(op, day):
    """CHP incidents are statewide; filter to the Truckee I-80 box."""
    import zipfile, gzip, csv as _csv
    want = f"all_text_chp_incidents_day_{day.strftime('%Y_%m_%d')}.txt.zip"
    href = find_file(op, "all", "chp_incidents_day", want)
    if not href:
        print("CHP file not posted yet")
        return
    z = zipfile.ZipFile(io.BytesIO(download(op, href)))
    inner = z.read([n for n in z.namelist() if "det" not in n][0])
    text = gzip.decompress(inner).decode(errors="replace") if inner[:2] == b"\x1f\x8b" else inner.decode(errors="replace")
    rows = []
    for r in _csv.reader(text.splitlines()):
        try:
            lat, lon, fwy = float(r[9]), float(r[10]), r[14]
        except (ValueError, IndexError):
            continue
        if fwy == "80" and in_box(lat, lon):
            rows.append([r[3], r[4], r[5], r[15] if len(r) > 15 else "", r[9], r[10]])
    if not rows:
        print("no I-80 Truckee-box incidents that day")
        return
    out = f"data/chp/{day.isoformat()}.csv"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["datetime", "description", "location", "direction", "lat", "lon"])
        w.writerows(rows)
    print(f"wrote {out}: {len(rows)} incidents")

def main():
    day = (datetime.datetime.now(TZ) - datetime.timedelta(days=1)).date()
    out_path = f"data/pems/hourly/{day.isoformat()}.csv"
    if os.path.exists(out_path):
        print(f"{out_path} already exists; nothing to do")
        return
    ids = set(open("config/truckee_stations.txt").read().split())
    op = opener_with_login()
    try:
        pull_chp(op, day)
    except Exception as e:
        print(f"CHP pull skipped: {e}")
    want = f"d03_text_station_5min_{day.strftime('%Y_%m_%d')}.txt.gz"
    href = find_file(op, "3", "station_5min", want)
    if not href:
        print(f"5-min file for {day} not posted yet; exiting cleanly")
        return
    raw = download(op, href)
    print(f"downloaded {len(raw):,} bytes")
    # aggregate: (station, direction, lane_type, hour) -> [veh, flow-weighted speed sum]
    agg = {}
    for line in gzip.open(io.BytesIO(raw), "rt"):
        p = line.split(",")
        if p[1] not in ids:
            continue
        hour = p[0][11:13]
        flow = float(p[9]) if p[9] else 0.0
        speed = float(p[11]) if len(p) > 11 and p[11] else None
        key = (p[1], p[4], p[5], hour)
        a = agg.setdefault(key, [0.0, 0.0, 0.0])
        a[0] += flow
        if speed is not None and flow > 0:
            a[1] += speed * flow
            a[2] += flow
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "station", "dir", "lane_type", "hour", "vehicles", "avg_speed_mph"])
        for (sid, d, lt, hr), (veh, spsum, spflow) in sorted(agg.items()):
            w.writerow([day.isoformat(), sid, d, lt, hr, int(veh),
                        round(spsum / spflow, 1) if spflow else ""])
    print(f"wrote {out_path}: {len(agg)} station-hour rows")

if __name__ == "__main__":
    main()
