import csv
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import lapdock_sample as s  # noqa: E402

FIXTURE = (ROOT / "tests" / "fixtures" / "ioreg_battery.txt").read_text()


class ParseIoreg(unittest.TestCase):
    def test_parses_load_and_power_in(self):
        d = s.parse_ioreg(FIXTURE)
        self.assertAlmostEqual(d["load_w"], 21.929, places=3)
        self.assertAlmostEqual(d["power_in_w"], 7.216, places=3)
        self.assertEqual(d["battery_pct"], 78)
        self.assertEqual(d["adapter_w"], 8)
        self.assertIs(d["external"], True)

    def test_fixture_battery_power_is_negative(self):
        self.assertAlmostEqual(s.parse_ioreg(FIXTURE)["battery_w"], -14.713, places=3)

    def test_unsigned_wraparound_is_negative(self):
        d = s.parse_ioreg('"BatteryPower"=18446744073709548543')
        self.assertAlmostEqual(d["battery_w"], -3.073, places=3)

    def test_missing_keys_are_none(self):
        d = s.parse_ioreg("")
        for key in ("load_w", "power_in_w", "battery_w", "battery_pct", "adapter_w", "external"):
            self.assertIsNone(d[key], key)


class Append(unittest.TestCase):
    def test_append_writes_header_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "sub" / "draw.csv"
            row = dict.fromkeys(s.FIELDS, 1)
            s.append_row(out, row)
            s.append_row(out, row)
            lines = out.read_text().splitlines()
            self.assertEqual(lines[0], ",".join(s.FIELDS))
            self.assertEqual(len(lines), 3)
            with out.open() as f:
                self.assertEqual(len(list(csv.DictReader(f))), 2)

    def test_timestamp_is_utc_with_z(self):
        self.assertRegex(s.utc_now(), r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


if __name__ == "__main__":
    unittest.main()
