#!/usr/bin/env python3
"""Render docs/data.html from the accumulated data files.

Run by both scheduled workflows after their pulls, and by hand. Stdlib only.
"""
import csv
import glob
import json
import os
import datetime

OUT = "docs/data.html"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_incidents():
    rows = []
    for f in sorted(glob.glob("data/chp/*.csv")):
        with open(f) as fh:
            rows.extend(csv.DictReader(fh))
    return rows


def load_volumes():
    """Per-day, per-direction vehicle counts at the busiest mainline detector."""
    days = {}
    for f in sorted(glob.glob("data/pems/hourly/*.csv")):
        date = os.path.basename(f)[:10]
        with open(f) as fh:
            for r in csv.DictReader(fh):
                if r["lane_type"] != "ML":
                    continue
                key = (r["station"], r["dir"])
                days.setdefault(date, {}).setdefault(key, [0] * 24)
                days[date][key][int(r["hour"])] += int(r["vehicles"])
    if not days:
        return {}, {}, None
    totals = {}
    for d in days.values():
        for k, hours in d.items():
            totals[k] = totals.get(k, 0) + sum(hours)
    best = {}
    for (st, dr), tot in totals.items():
        if dr not in best or tot > totals[(best[dr], dr)]:
            best[dr] = st
    series = {dr: {} for dr in best}
    for date, d in days.items():
        for dr, st in best.items():
            if (st, dr) in d:
                series[dr][date] = sum(d[(st, dr)])
    latest = max(days)
    profile = {dr: days[latest].get((st, dr), [0] * 24) for dr, st in best.items()}
    return series, profile, (latest, best)


def load_truck_years():
    rows = []
    path = "data/reference/truck-aadt.csv"
    if os.path.exists(path):
        with open(path) as fh:
            for r in csv.DictReader(fh):
                if r["postmile"] == "14.164" and r["leg"] == "ahead":
                    rows.append((int(r["year"]), int(r["truck_aadt"])))
    return sorted(rows)


def load_conditions():
    state, changes = {}, []
    if os.path.exists("data/conditions/state.json"):
        state = json.load(open("data/conditions/state.json"))
    if os.path.exists("data/conditions/log.jsonl"):
        with open("data/conditions/log.jsonl") as fh:
            changes = [json.loads(l) for l in fh if l.strip()]
    return state, changes


def bar_chart(pairs, width=860, height=210, color="var(--accent)", fmt="{:,}"):
    """Simple SVG bar chart from [(label, value)]."""
    if not pairs:
        return "<p>No data yet.</p>"
    top = max(v for _, v in pairs) or 1
    n = len(pairs)
    pad_l, pad_b, pad_t = 46, 26, 12
    plot_w, plot_h = width - pad_l - 10, height - pad_b - pad_t
    bw = plot_w / n
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" '
             f'style="width:100%;height:auto;font-family:ui-monospace,Menlo,monospace">']
    for frac in (0, 0.5, 1.0):
        y = pad_t + plot_h * (1 - frac)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width-10}" y2="{y:.1f}" '
                     f'stroke="var(--grid)" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l-6}" y="{y+4:.1f}" text-anchor="end" font-size="10" '
                     f'fill="var(--muted)">{fmt.format(int(top*frac))}</text>')
    for i, (label, v) in enumerate(pairs):
        x = pad_l + i * bw
        h = plot_h * v / top
        parts.append(f'<rect x="{x+bw*0.15:.1f}" y="{pad_t+plot_h-h:.1f}" '
                     f'width="{bw*0.7:.1f}" height="{h:.1f}" rx="2" fill="{color}"/>')
        if n <= 26 or i % max(1, n // 13) == 0:
            parts.append(f'<text x="{x+bw/2:.1f}" y="{height-8}" text-anchor="middle" '
                         f'font-size="10" fill="var(--muted)">{label}</text>')
    parts.append("</svg>")
    return "".join(parts)


def render():
    incidents = load_incidents()
    vol_series, profile, vol_meta = load_volumes()
    trucks = load_truck_years()
    state, changes = load_conditions()
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # incidents by month
    by_month = {}
    for r in incidents:
        by_month[int(r["datetime"][:2])] = by_month.get(int(r["datetime"][:2]), 0) + 1
    month_pairs = [(MONTHS[m - 1], by_month[m]) for m in sorted(by_month)]
    latest_inc = sorted(incidents, key=lambda r: (r["datetime"][6:10], r["datetime"][:5]))[-8:]

    # daily volume series chart, per direction
    vol_html = "<p>Collection began August 2026; this chart grows one point per day.</p>"
    if vol_series:
        latest, best = vol_meta
        rows = []
        dates = sorted({d for s in vol_series.values() for d in s})
        for dr in sorted(vol_series):
            pairs = [(d[5:], vol_series[dr].get(d, 0)) for d in dates]
            rows.append(f"<h3>{'Eastbound' if dr=='E' else 'Westbound'} "
                        f"(detector {best[dr]})</h3>" + bar_chart(pairs, height=170))
        prof_rows = []
        for dr, hours in profile.items():
            pairs = [(f"{h:02d}", v) for h, v in enumerate(hours)]
            prof_rows.append(f"<h3>{'Eastbound' if dr=='E' else 'Westbound'}, {latest}, by hour</h3>"
                             + bar_chart(pairs, height=170, color="var(--ink-2)"))
        vol_html = "".join(rows) + "".join(prof_rows)

    truck_html = bar_chart([(str(y), v) for y, v in trucks]) if trucks else ""

    chains = {k: v for k, v in state.items() if k.startswith("chain:")}
    active = {k: v for k, v in chains.items() if v not in ("R-0", "")}
    closures = {k: v for k, v in state.items() if k.startswith("closure:")}
    cond_html = (f"<p>Chain control stations tracked: {len(chains)}. "
                 f"Active controls now: {len(active)}. Active lane closures logged: {len(closures)}. "
                 f"Changes recorded since collection began: {len(changes)}.</p>")
    if active:
        cond_html += "<ul>" + "".join(
            f"<li>{k.split(':',1)[1]}: {v}</li>" for k, v in sorted(active.items())) + "</ul>"

    inc_rows = "".join(
        f"<tr><td class=num>{r['datetime'][:16]}</td><td>{r['description']}</td>"
        f"<td>{r['location']}</td></tr>" for r in reversed(latest_inc))

    html = f"""<meta charset="utf-8">
<title>truckee-i80: the corridor in numbers</title>
<style>
  :root {{
    color-scheme: light;
    --page: #f6f7f9; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e;
    --muted: #898781; --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10); --accent: #2a78d6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) {{
      color-scheme: dark;
      --page: #0c0e11; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
      --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10); --accent: #3987e5;
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --page: #0c0e11; --surface: #1a1a19; --ink: #ffffff; --ink-2: #c3c2b7;
    --muted: #898781; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,0.10); --accent: #3987e5;
  }}
  :root[data-theme="light"] {{
    color-scheme: light;
    --page: #f6f7f9; --surface: #fcfcfb; --ink: #0b0b0b; --ink-2: #52514e;
    --muted: #898781; --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,0.10); --accent: #2a78d6;
  }}
  body {{ background: var(--page); color: var(--ink); font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    line-height: 1.6; margin: 0; padding: 48px 20px 72px; }}
  .wrap {{ max-width: 880px; margin: 0 auto; }}
  .eyebrow {{ font-size: 12px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted);
    margin: 0 0 10px; font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  .eyebrow a {{ color: inherit; }}
  h1 {{ font-size: clamp(26px, 4vw, 38px); font-weight: 700; letter-spacing: -0.02em; margin: 0 0 14px; }}
  .standfirst {{ font-size: 15.5px; color: var(--ink-2); max-width: 66ch; margin: 0 0 30px; }}
  h2 {{ font-size: 19px; font-weight: 700; letter-spacing: -0.01em; margin: 40px 0 8px; }}
  h3 {{ font-size: 13px; font-weight: 650; color: var(--ink-2); margin: 18px 0 4px;
    font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  p {{ max-width: 70ch; font-size: 15px; margin: 0 0 12px; }}
  ul {{ max-width: 70ch; font-size: 14.5px; padding-left: 22px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 13px; margin: 10px 0 6px; }}
  th {{ text-align: left; font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted);
    font-weight: 600; padding: 6px 12px 6px 0; border-bottom: 1px solid var(--axis); }}
  td {{ padding: 5px 12px 5px 0; border-bottom: 1px solid var(--grid); vertical-align: top;
    font-variant-numeric: tabular-nums; }}
  td.num {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; white-space: nowrap; }}
  .src {{ font-size: 12px; color: var(--muted); margin: 4px 0 0; max-width: 70ch; }}
  .src a {{ color: var(--muted); }}
  .table-scroll {{ overflow-x: auto; }}
  a {{ color: var(--accent); }}
  .foot {{ margin-top: 44px; padding-top: 16px; border-top: 1px solid var(--grid); color: var(--muted);
    font-size: 12.5px; max-width: 74ch; }}
</style>
<div class="wrap">
  <p class="eyebrow"><a href="./">truckee-i80</a> · data</p>
  <h1>The corridor in numbers</h1>
  <p class="standfirst">
    Rendered automatically from the data this site collects: CHP incidents, Caltrans detector
    volumes, chain control status, and the annual truck census. Every underlying file is in the
    <a href="https://github.com/micrui/truckee-i80">repository</a>. Last rendered {now}.
  </p>

  <h2>Incidents by month, 2026</h2>
  {bar_chart(month_pairs, color="#e05252")}
  <p class="src">CHP dispatch incidents on I-80 between Baxter and the state line. Categories and
  the year-to-date table are on the <a href="safety.html">safety page</a>.</p>

  <h2>Most recent incidents</h2>
  <div class="table-scroll"><table>
    <thead><tr><th>Logged</th><th>Type</th><th>Location</th></tr></thead>
    <tbody>{inc_rows}</tbody>
  </table></div>

  <h2>Traffic through Truckee, day by day</h2>
  {vol_html}
  <p class="src">Vehicles per day at the highest-volume mainline detector in each direction,
  from the daily Caltrans performance measurement system pull. The hourly profile shows the
  most recent day.</p>

  <h2>Trucks per day at Truckee, year by year</h2>
  {truck_html}
  <p class="src">Truck traffic at the SR-89 South junction (eastbound leg) from the Caltrans
  annual truck census, 2013 through 2024. The department carries classification splits forward
  between periodic counts; see the
  <a href="https://github.com/micrui/truckee-i80/blob/main/data/reference/README.md">series notes</a>.</p>

  <h2>Chain control and closures</h2>
  {cond_html}
  <p class="src">From Caltrans' public District 3 feeds, polled on a winter/summer cadence.
  The complete change log accumulates in the repository.</p>

  <div class="foot">
    <p>This page is regenerated by the same scheduled jobs that collect the data.
    Corrections welcome via <a href="https://github.com/micrui/truckee-i80">GitHub</a>.</p>
  </div>
</div>
"""
    with open(OUT, "w") as f:
        f.write(html)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    render()
