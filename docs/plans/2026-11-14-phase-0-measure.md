# Lap Dock Phase 0 (measure) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the design's estimates with measurements: the Air's real power draw in heavy sessions, a throttling baseline, and the physical facts only the owner can measure.

**Architecture:** A tiny sampler run by launchd every 20 s appends one CSV row of power and thermal readings. A report script turns the CSV into the numbers the design needs (heavy draw, hours per pad, cell count). A benchmark script records sustained performance over 30 minutes, run only when the owner says. A checklist covers the hands-on measurements.

**Tech Stack:** Python 3 standard library only, `unittest`, launchd, `ioreg`, `notifyutil`.

**Spec:** `docs/2026-11-14-lap-dock-design.md` (sections 3, 4.4 and 6). Later phases get their own plans once these numbers exist.

## Global Constraints

- Data lives in `~/.local/state/lap-dock/`, never in a temp directory.
- No third-party Python packages. No admin rights (`powermetrics` is out).
- The sampler must cost almost nothing: one `ioreg` and one `notifyutil` call per sample.
- The benchmark is never started automatically; this laptop stays cool while the owner works.
- Pack figures from the spec: 8 cells deliver 122 Wh, 10 cells deliver 153 Wh; 10 cells when heavy draw is above 40 W; goal is at least 3 hours per pad.
- Nothing is pushed or published.

## Review Focus

- The Mac sleeps mid-session: a gap in samples must break a rolling window, not be averaged across.
- `ioreg` reports negative currents as huge unsigned numbers: they must be read as signed.
- The CSV is being appended while the report reads it: a truncated last line must be skipped.
- Too little data: the report says so instead of recommending a cell count from ten minutes of idling.
- Draw while the Air charges its own battery overstates what the pad must supply: the report uses system load, not power in.

---

### Task 1: Sampler

**Files:**
- Create: `tools/lapdock_sample.py`, `tests/test_sample.py`, `tests/fixtures/ioreg_battery.txt`

**Interfaces:**
- Produces: `parse_ioreg(text: str) -> dict` with keys `load_w`, `power_in_w`, `battery_w` (negative when discharging), `battery_pct`, `adapter_w`, `external` (bool); missing values are `None`.
- Produces: `FIELDS: list[str]` = `["ts", "load_w", "power_in_w", "battery_w", "battery_pct", "adapter_w", "external", "thermal_level"]`; `ts` is UTC ISO 8601 with a `Z`.
- Produces: CLI `lapdock_sample.py [--out PATH]`, default `~/.local/state/lap-dock/draw.csv`, writes the header once and appends one row.

- [ ] Step 1: Save a real `ioreg -rn AppleSmartBattery -w0` capture as the fixture.
- [ ] Step 2: Write failing tests: `test_parses_load_and_power_in` (fixture gives `load_w` and `power_in_w` within 0.01 of the captured milliwatt values / 1000); `test_unsigned_wraparound_is_negative` (`"BatteryPower"=18446744073709548543` gives `battery_w == -3.073`); `test_missing_keys_are_none` (empty text gives all `None`); `test_append_writes_header_once` (two appends give one header and two rows).
- [ ] Step 3: Run `python3 -m unittest discover -s tests -v`; expect failures.
- [ ] Step 4: Implement.
- [ ] Step 5: Run the tests; expect pass. Run the CLI once against a temp path and read the row.
- [ ] Step 6: Commit.

### Task 2: Report

**Files:**
- Create: `tools/lapdock_report.py`, `tests/test_report.py`

**Interfaces:**
- Consumes: the CSV and `FIELDS` from Task 1.
- Produces: `load_rows(path) -> list[dict]` (skips malformed lines); `rolling_means(rows, window_s=1800, max_gap_s=90) -> list[float]` (mean `load_w` of every window fully covered by samples no further apart than `max_gap_s`); `summarise(rows) -> dict` with `hours_logged`, `median_w`, `p90_w`, `heavy_w` (the highest 30-minute rolling mean, or `None`), `cells`, `hours_per_pad`; `recommend_cells(heavy_w: float) -> int`.
- CLI prints the summary as a short table; with under 2 hours logged or no complete window it prints "not enough data yet" and no recommendation.

- [ ] Step 1: Write failing tests: `test_recommend_cells` (40.0 gives 8, 40.1 gives 10); `test_hours_per_pad` (30 W on 8 cells gives 4.07 to two places; 45 W on 10 cells gives 3.4); `test_gap_breaks_window` (25 minutes at 50 W, a 10-minute gap, 25 minutes at 50 W gives no window); `test_steady_window` (40 minutes at 30 W gives `heavy_w == 30.0`); `test_truncated_last_line_skipped`; `test_not_enough_data` (`heavy_w is None`, `cells is None`).
- [ ] Step 2: Run; expect failures.
- [ ] Step 3: Implement.
- [ ] Step 4: Run; expect pass.
- [ ] Step 5: Commit.

### Task 3: Install the sampler

**Files:**
- Create: `launchd/lapdock-draw-log.plist` (`StartInterval` 20, runs the Task 1 CLI with `/opt/homebrew/bin/python3`, logs to `~/.local/state/lap-dock/sampler.log`)
- Record the job wherever this Mac's background jobs are listed.

- [ ] Step 1: Write the plist; `plutil -lint` it.
- [ ] Step 2: Install: copy to `~/Library/LaunchAgents` and `launchctl bootstrap gui/$UID` it.
- [ ] Step 3: Verify: after a minute the CSV has at least two rows with different timestamps and the log is empty of errors.
- [ ] Step 4: Commit.

### Task 4: Throttle benchmark

**Files:**
- Create: `tools/throttle_bench.py`, `tests/test_bench.py`

**Interfaces:**
- Produces: CLI `throttle_bench.py --minutes 30 --label NAME`; runs one SHA-256 worker per performance core, records work done per 10-second slice and the thermal level, writes `~/.local/state/lap-dock/bench/<label>-<UTC>.csv`, and prints first-minute rate, last-five-minute rate and their ratio ("sustained fraction").
- Produces: `sustained_fraction(slices: list[float], slice_s=10) -> float`.

- [ ] Step 1: Write failing tests: `test_sustained_fraction_flat` (constant slices give 1.0); `test_sustained_fraction_throttled` (first minute at 100, the rest at 60 gives 0.6); `test_too_short_raises` (under 6 minutes of slices raises `ValueError`).
- [ ] Step 2: Run; expect failures. Implement. Run; expect pass.
- [ ] Step 3: Smoke-run for `--minutes 0.2 --label smoke` only (12 seconds), confirm the file and the "too short for a sustained figure" message.
- [ ] Step 4: Commit. The real runs (bare, on the Klim) wait for the owner.

### Task 5: Hands-on checklist

**Files:**
- Create: `docs/phase-0-measurements.md`, `README.md`

- [ ] Step 1: Write the checklist with a blank table for each: Air outline and foot positions and height; Klim thickness and noise; the hot-spot map (a grid over the underside, read after the benchmark has run 15 minutes, with what instrument); the two shop questions (spot welder, thermal-pad modification). Each item says what the number decides in the design.
- [ ] Step 2: Write a short README: what the project is, where the design and plan are, how to read the report.
- [ ] Step 3: Commit.
