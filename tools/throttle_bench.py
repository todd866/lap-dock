#!/usr/bin/env python3
"""Measure how much of its burst speed this Mac sustains under a long load.

Runs one hashing worker per performance core, records work done in each
10-second slice, and reports the sustained fraction: the rate over the last five
minutes divided by the rate over the first minute. 1.0 means no throttling.

This loads the machine fully and makes it hot. Start it deliberately.
"""
import argparse
import csv
import datetime
import hashlib
import multiprocessing as mp
import pathlib
import subprocess
import time

SLICE_S = 10
DEFAULT_DIR = pathlib.Path.home() / ".local/state/lap-dock/bench"


def sustained_fraction(slices, slice_s=SLICE_S):
    """Last-five-minute rate over first-minute rate. Needs six minutes of slices."""
    if len(slices) * slice_s < 360:
        raise ValueError("too short for a sustained figure: need at least 6 minutes")
    first = slices[: 60 // slice_s]
    last = slices[-(300 // slice_s):]
    burst = sum(first) / len(first)
    if burst <= 0:
        raise ValueError("no work recorded in the first minute")
    return (sum(last) / len(last)) / burst


def performance_cores():
    try:
        out = subprocess.run(["sysctl", "-n", "hw.perflevel0.physicalcpu"],
                             capture_output=True, text=True, timeout=5).stdout
        return max(1, int(out.strip()))
    except (OSError, ValueError, subprocess.SubprocessError):
        return mp.cpu_count()


def thermal_level():
    try:
        out = subprocess.run(
            ["notifyutil", "-g", "com.apple.system.thermalpressurelevel"],
            capture_output=True, text=True, timeout=5).stdout
        return int(out.split()[-1])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return ""


def _worker(counter, stop):
    block = b"\0" * (1 << 20)
    while not stop.is_set():
        hashlib.sha256(block).digest()
        counter.value += 1  # single writer per counter


def run(minutes, label, out_dir=DEFAULT_DIR):
    n = performance_cores()
    stop = mp.Event()
    counters = [mp.Value("Q", 0, lock=False) for _ in range(n)]
    procs = [mp.Process(target=_worker, args=(c, stop), daemon=True) for c in counters]
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{label}-{stamp}.csv"
    slices = []
    for p in procs:
        p.start()
    try:
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["elapsed_s", "mb_hashed", "thermal_level"])
            start = time.monotonic()
            prev, k = 0, 0
            while (k + 1) * SLICE_S <= minutes * 60 + 1e-9:
                k += 1
                time.sleep(max(0.0, start + k * SLICE_S - time.monotonic()))
                total = sum(c.value for c in counters)
                slices.append(float(total - prev))
                prev = total
                w.writerow([k * SLICE_S, int(slices[-1]), thermal_level()])
                f.flush()
    finally:
        stop.set()
        for p in procs:
            p.join(timeout=5)
            if p.is_alive():
                p.terminate()
    return path, slices, n


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--minutes", type=float, default=30.0)
    ap.add_argument("--label", required=True, help="e.g. bare, klim, pad-v1")
    args = ap.parse_args()
    path, slices, n = run(args.minutes, args.label)
    print(f"workers   {n}")
    print(f"saved     {path}")
    try:
        frac = sustained_fraction(slices)
    except ValueError as e:
        print(f"sustained {e}")
        return
    first = sum(slices[:6]) / 6 / SLICE_S
    last = sum(slices[-30:]) / 30 / SLICE_S
    print(f"first minute       {first:.0f} MB/s")
    print(f"last five minutes  {last:.0f} MB/s")
    print(f"sustained fraction {frac:.2f}")


if __name__ == "__main__":
    mp.set_start_method("spawn")
    main()
