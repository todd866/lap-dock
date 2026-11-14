# Lap Dock

An open-hardware lap tray for a 13-inch M5 MacBook Air that cools the laptop where it is
hot, keeps the lap cool, and carries its own battery. Two identical pads, about 150 Wh
each: one on the lap, one on the charger.

**Status: design and simulation only. Nothing is built yet.** Every performance figure
here comes from a thermal model (good to about ±20%), not from a measurement of the
tray. Phase 1 builds a prototype to check them.

## Read first

- [Design](docs/2026-11-14-lap-dock-design.md)
- [Cooling study](docs/cooling-study.md): where the fan goes, what kind, and what it is
  worth. [Full tables](docs/cooling-study-tables.md).
- [Phase 0 measurements](docs/phase-0-measurements.md) and
  [plan](docs/plans/2026-11-14-phase-0-measure.md)
- [Thermal-pad job sheet](docs/shop-brief.md) for the optional laptop modification

## What the model says so far

Sustained chip power on an unmodified Air at 25 °C:

| Arrangement | Sustained chip power |
|---|---|
| Bare on the lap | 7.7 W |
| 200 mm fan cooling pad | 8.4 W |
| This tray (blower, air along the bare base) | 8.8 W |
| This tray with the optional finned plate | 9.2 W |

A stock Air's bottleneck is inside the laptop, so no tray gains much. The tray is mainly
worth building for the battery and the cooler lap.

## Tools

| Tool | What it does |
|---|---|
| `tools/lapdock_sample.py` | Appends one power and thermal sample to `~/.local/state/lap-dock/draw.csv`. |
| `tools/lapdock_report.py` | Summarises the log: heavy draw, cell count, hours per pad. |
| `tools/throttle_bench.py` | 30-minute full load that reports how much burst speed the Air sustains. It makes the laptop hot and slow while it runs. |
| `sim/` | Thermal model, calibration and the study that produced the tables. |
| `launchd/lapdock-draw-log.plist` | Template that runs the sampler every 20 s. Replace `YOU` and the label, then load it. |

Tests: `python3 -m unittest discover -s tests`

## Safety

- This design contains a lithium-ion pack. Cells are spot-welded, never soldered, and the
  pack needs a protection board. If you have not built one before, buy a finished pack.
- Opening a MacBook and fitting a thermal pad is at your own risk and makes the base too
  hot to hold on a bare lap.
- A lap pad does not by itself protect against lap heat; see the cooling study.

## Licence

- Hardware design: CERN-OHL-P v2 ([text](LICENSES/CERN-OHL-P-2.0.txt))
- Code: MIT ([text](LICENSES/MIT.txt))
- Documentation: CC BY 4.0 ([text](LICENSES/CC-BY-4.0.txt))

Not affiliated with Apple or Klim.
