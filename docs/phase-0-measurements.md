# Phase 0: measurements

Where each number the design needs comes from. Published figures and the Mac's own
readings are used wherever they exist; hand measurement is the last resort.

## From published sources (done)

| Item | Value | Source |
|---|---|---|
| Air width × depth × height | 304.1 × 215 × 11.3 mm | Apple tech specs, 13-inch M5 |
| Air weight | 1.23 kg | Apple tech specs |
| Air battery | 53.8 Wh | Apple tech specs |
| Charging | MagSafe 3 or USB-C; 30 W minimum; fast charge from 70 W USB PD | Apple tech specs |
| Klim (KLIM Ultimate) size | 425 × 315 × 43 mm | maker's listing |
| Klim weight | 960 g | maker's listing |
| Klim fan | one 200 mm, 750 rpm | maker's listing |

Not published anywhere found: the Air's foot positions, foot height and corner radius.
Apple's accessory drawings page lists no MacBook Air. The design no longer needs them
(design section 4.2).

## From the Mac itself (automatic)

- **Power draw.** A launchd job logs it every 20 seconds while the Air is awake. After a
  few days that include heavy sessions: `python3 tools/lapdock_report.py`
- **Throttling baseline.** `python3 tools/throttle_bench.py --label klim` loads the Air
  fully for 30 minutes and reports how much of its burst speed it sustains. It makes the
  laptop hot and slow while it runs, so it is started only when the owner says. A second
  run with `--label bare` (Air on a cushion, no pad) shows what the Klim is worth today.

## From simulation and published tests

Where the heat is, where the fans go, how big they are and which cooling scheme wins are
answered by the thermal model in `sim/` and its sources, then confirmed by the Phase 1
prototype. See `docs/cooling-study.md`.

## Only the owner can do

| Question for the repair shop | Answer |
|---|---|
| Do you have a battery spot welder, or do you only solder? | |

If they only solder, the cells are bought with tabs already welded on, or the pack is
ordered from a pack builder.
