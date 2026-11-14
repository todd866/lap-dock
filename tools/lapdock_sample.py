#!/usr/bin/env python3
"""Append one power and thermal sample for this Mac to a CSV.

Run every 20 seconds by launchd. Needs no admin rights and no packages.
"""
import argparse
import csv
import datetime
import pathlib
import re
import subprocess

FIELDS = ["ts", "load_w", "power_in_w", "battery_w", "battery_pct",
          "adapter_w", "external", "thermal_level"]
DEFAULT_OUT = pathlib.Path.home() / ".local/state/lap-dock/draw.csv"


def _number(text, key):
    """First integer value of `key` in ioreg output, read as signed 64-bit."""
    m = re.search(r'"%s"\s*=\s*(\d+)' % re.escape(key), text)
    if not m:
        return None
    n = int(m.group(1))
    return n - (1 << 64) if n >= (1 << 63) else n


def _milli(text, key):
    n = _number(text, key)
    return None if n is None else n / 1000.0


def parse_ioreg(text):
    """Readings from `ioreg -rn AppleSmartBattery -w0`. Missing values are None.

    load_w is what the system is consuming, power_in_w what the charger supplies,
    battery_w the battery's contribution (negative when discharging).
    """
    ext = re.search(r'"ExternalConnected"\s*=\s*(Yes|No)', text)
    return {
        "load_w": _milli(text, "SystemLoad"),
        "power_in_w": _milli(text, "SystemPowerIn"),
        "battery_w": _milli(text, "BatteryPower"),
        "battery_pct": _number(text, "CurrentCapacity"),
        "adapter_w": _number(text, "Watts"),
        "external": None if ext is None else ext.group(1) == "Yes",
    }


def thermal_level():
    """macOS thermal pressure level (0 is nominal), or None."""
    try:
        out = subprocess.run(
            ["notifyutil", "-g", "com.apple.system.thermalpressurelevel"],
            capture_output=True, text=True, timeout=5).stdout
        return int(out.split()[-1])
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return None


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_sample():
    text = subprocess.run(["ioreg", "-rn", "AppleSmartBattery", "-w0"],
                          capture_output=True, text=True, timeout=10).stdout
    row = parse_ioreg(text)
    row["ts"] = utc_now()
    row["thermal_level"] = thermal_level()
    return row


def append_row(path, row):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: ("" if row.get(k) is None else row[k]) for k in FIELDS})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    append_row(args.out, read_sample())


if __name__ == "__main__":
    main()
