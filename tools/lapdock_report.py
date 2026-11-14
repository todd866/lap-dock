#!/usr/bin/env python3
"""Turn the draw log into the numbers the design needs.

Heavy draw is the highest 30-minute average of system load. System load is used,
not power in, so that charging the Air's own battery does not inflate it.
"""
import argparse
import csv
import datetime
import pathlib
import statistics

DEFAULT_LOG = pathlib.Path.home() / ".local/state/lap-dock/draw.csv"

# From the design, section 4.4: energy delivered to the Air after losses.
DELIVERED_WH = {8: 122.0, 10: 153.0}
TEN_CELLS_ABOVE_W = 40.0
MIN_HOURS_LOGGED = 2.0


def load_rows(path):
    """Rows as {"t": epoch seconds, "load_w": float}; malformed lines skipped."""
    rows = []
    try:
        f = pathlib.Path(path).open(newline="")
    except OSError:
        return rows
    with f:
        for rec in csv.DictReader(f):
            try:
                t = datetime.datetime.strptime(rec["ts"], "%Y-%m-%dT%H:%M:%SZ")
                t = t.replace(tzinfo=datetime.timezone.utc).timestamp()
                level = rec.get("thermal_level") or ""
                rows.append({"t": t, "load_w": float(rec["load_w"]),
                             "thermal": int(level) if level.strip() else None})
            except (KeyError, TypeError, ValueError):
                continue
    rows.sort(key=lambda r: r["t"])
    return rows


def _runs(rows, max_gap_s):
    """Split rows into runs with no gap longer than max_gap_s."""
    run = []
    for row in rows:
        if run and row["t"] - run[-1]["t"] > max_gap_s:
            yield run
            run = []
        run.append(row)
    if run:
        yield run


def rolling_means(rows, window_s=1800, max_gap_s=90):
    """Mean load of every window_s window that lies wholly inside one run."""
    means = []
    for run in _runs(rows, max_gap_s):
        if run[-1]["t"] - run[0]["t"] < window_s:
            continue
        start, total = 0, 0.0
        for end, row in enumerate(run):
            total += row["load_w"]
            while row["t"] - run[start]["t"] > window_s:
                total -= run[start]["load_w"]
                start += 1
            if row["t"] - run[0]["t"] >= window_s:
                means.append(round(total / (end - start + 1), 3))
    return means


def logged_seconds(rows, max_gap_s=90):
    return sum(run[-1]["t"] - run[0]["t"] for run in _runs(rows, max_gap_s))


def recommend_cells(heavy_w):
    return 10 if heavy_w > TEN_CELLS_ABOVE_W else 8


def hours_per_pad(heavy_w, cells):
    return DELIVERED_WH[cells] / heavy_w


def summarise(rows):
    hours = logged_seconds(rows) / 3600.0
    loads = [r["load_w"] for r in rows]
    out = {
        "samples": len(rows),
        "hours_logged": hours,
        "median_w": statistics.median(loads) if loads else None,
        "p90_w": statistics.quantiles(loads, n=10)[-1] if len(loads) >= 10 else None,
        "heavy_w": None, "cells": None, "hours_per_pad": None,
    }
    levels = [r.get("thermal") for r in rows if r.get("thermal") is not None]
    out["throttled_fraction"] = (sum(1 for v in levels if v > 0) / len(levels)) if levels else None
    out["peak_thermal_level"] = max(levels) if levels else None
    means = rolling_means(rows)
    if hours >= MIN_HOURS_LOGGED and means:
        out["heavy_w"] = max(means)
        out["cells"] = recommend_cells(out["heavy_w"])
        out["hours_per_pad"] = hours_per_pad(out["heavy_w"], out["cells"])
    return out


def _fmt(v, unit=""):
    return "-" if v is None else f"{v:.1f}{unit}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("log", nargs="?", default=str(DEFAULT_LOG))
    args = ap.parse_args()
    s = summarise(load_rows(args.log))
    print(f"logged          {_fmt(s['hours_logged'], ' h')}  ({s['samples']} samples)")
    print(f"median load     {_fmt(s['median_w'], ' W')}")
    print(f"90th percentile {_fmt(s['p90_w'], ' W')}")
    if s["throttled_fraction"] is not None:
        print(f"thermal pressure {s['throttled_fraction']:.1%} of samples above nominal "
              f"(peak level {s['peak_thermal_level']})")
    if s["heavy_w"] is None:
        print(f"heavy draw      not enough data yet (need {MIN_HOURS_LOGGED:.0f} h logged "
              "and one unbroken 30-minute stretch)")
        return
    print(f"heavy draw      {_fmt(s['heavy_w'], ' W')}  (highest 30-minute average)")
    print(f"cells           {s['cells']}  ({DELIVERED_WH[s['cells']]:.0f} Wh delivered)")
    print(f"hours per pad   {_fmt(s['hours_per_pad'], ' h')}  (goal: 3.0 h or more)")


if __name__ == "__main__":
    main()
