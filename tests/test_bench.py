import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import throttle_bench as b  # noqa: E402


class SustainedFraction(unittest.TestCase):
    def test_flat(self):
        self.assertEqual(b.sustained_fraction([50.0] * 180), 1.0)

    def test_throttled(self):
        slices = [100.0] * 6 + [60.0] * 174
        self.assertAlmostEqual(b.sustained_fraction(slices), 0.6, places=6)

    def test_too_short_raises(self):
        with self.assertRaises(ValueError):
            b.sustained_fraction([50.0] * 35)

    def test_exactly_six_minutes_is_enough(self):
        self.assertEqual(b.sustained_fraction([50.0] * 36), 1.0)

    def test_zero_first_minute_raises(self):
        with self.assertRaises(ValueError):
            b.sustained_fraction([0.0] * 6 + [10.0] * 30)


if __name__ == "__main__":
    unittest.main()
