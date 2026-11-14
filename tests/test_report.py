import datetime
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import lapdock_report as r  # noqa: E402
import lapdock_sample as s  # noqa: E402

T0 = datetime.datetime(2026, 11, 14, 1, 0, 0, tzinfo=datetime.timezone.utc)


def run(start_min, minutes, watts, step_s=20):
    """Samples every step_s seconds for `minutes`, starting start_min after T0."""
    rows = []
    for i in range(int(minutes * 60 / step_s) + 1):
        t = T0 + datetime.timedelta(minutes=start_min, seconds=i * step_s)
        rows.append({"t": t.timestamp(), "load_w": float(watts)})
    return rows


class Cells(unittest.TestCase):
    def test_recommend_cells(self):
        self.assertEqual(r.recommend_cells(40.0), 8)
        self.assertEqual(r.recommend_cells(40.1), 10)

    def test_hours_per_pad(self):
        self.assertEqual(round(r.hours_per_pad(30.0, 8), 2), 4.07)
        self.assertEqual(round(r.hours_per_pad(45.0, 10), 2), 3.4)


class Rolling(unittest.TestCase):
    def test_gap_breaks_window(self):
        rows = run(0, 25, 50) + run(35, 25, 50)
        self.assertEqual(r.rolling_means(rows), [])

    def test_steady_window(self):
        rows = run(0, 40, 30)
        means = r.rolling_means(rows)
        self.assertTrue(means)
        self.assertEqual(max(means), 30.0)

    def test_peak_window_found(self):
        rows = run(0, 40, 10) + run(40, 40, 36)[1:] + run(80, 40, 10)[1:]
        self.assertAlmostEqual(max(r.rolling_means(rows)), 36.0, places=1)


class Summary(unittest.TestCase):
    def test_not_enough_data(self):
        out = r.summarise(run(0, 10, 12))
        self.assertIsNone(out["heavy_w"])
        self.assertIsNone(out["cells"])
        self.assertIsNone(out["hours_per_pad"])

    def test_enough_data(self):
        out = r.summarise(run(0, 150, 30))
        self.assertEqual(out["heavy_w"], 30.0)
        self.assertEqual(out["cells"], 8)
        self.assertEqual(round(out["hours_per_pad"], 2), 4.07)
        self.assertAlmostEqual(out["hours_logged"], 2.5, places=1)

    def test_long_but_broken_log_gives_no_recommendation(self):
        rows = []
        for k in range(12):
            rows += run(k * 30, 15, 20)
        out = r.summarise(rows)
        self.assertIsNone(out["heavy_w"])
        self.assertIsNone(out["cells"])


class Thermal(unittest.TestCase):
    def test_throttled_fraction(self):
        rows = run(0, 10, 12)
        for i, row in enumerate(rows):
            row["thermal"] = 2 if i < len(rows) // 4 else 0
        out = r.summarise(rows)
        self.assertAlmostEqual(out["throttled_fraction"], (len(rows) // 4) / len(rows))
        self.assertEqual(out["peak_thermal_level"], 2)

    def test_no_thermal_data(self):
        out = r.summarise(run(0, 10, 12))
        self.assertIsNone(out["throttled_fraction"])
        self.assertIsNone(out["peak_thermal_level"])


class Load(unittest.TestCase):
    def test_truncated_last_line_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "draw.csv"
            good = dict.fromkeys(s.FIELDS, "")
            good.update(ts="2026-11-14T01:00:00Z", load_w=12.5)
            s.append_row(p, good)
            with p.open("a") as f:
                f.write("2026-11-14T01:00:2")
            rows = r.load_rows(p)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["load_w"], 12.5)
            self.assertIsNone(rows[0]["thermal"])

    def test_rows_without_load_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "draw.csv"
            blank = dict.fromkeys(s.FIELDS, "")
            blank.update(ts="2026-11-14T01:00:00Z")
            s.append_row(p, blank)
            self.assertEqual(r.load_rows(p), [])

    def test_missing_file_is_empty(self):
        self.assertEqual(r.load_rows(pathlib.Path("/nonexistent/draw.csv")), [])


if __name__ == "__main__":
    unittest.main()
