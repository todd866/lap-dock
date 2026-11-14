import math
import pathlib
import sys
import unittest
from dataclasses import replace

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sim"))

import airflow  # noqa: E402
import model  # noqa: E402

LAP = model.Laptop(dx=0.005)


class Physics(unittest.TestCase):
    def test_energy_balance(self):
        """All chip heat leaves through the two outer surfaces."""
        sol = model.solve(LAP, model.uniform(LAP, "desk", 6.0, 25.0))
        qb, qt = sol.heat_split()
        self.assertAlmostEqual(qb + qt, 1.0, places=6)

    def test_no_power_sits_at_ambient(self):
        sol = model.solve(LAP, model.uniform(LAP, "desk", 6.0, 25.0), t_amb=25.0)
        self.assertAlmostEqual(sol.base_die, 25.0, places=6)
        self.assertAlmostEqual(float(sol.base_bottom.max()), 25.0, places=6)

    def test_lumped_limit(self):
        """With near-perfect conduction everywhere, rise = P / (total hA)."""
        lap = replace(LAP, kt_bottom=1e4, kt_top=1e4, g_edge=1e4, h_interior=1e4,
                      r_die_spreader=1e-6, g_spreader_top=1e4)
        sol = model.solve(lap, model.uniform(lap, "u", 10.0, 25.0))
        ny, nx = lap.shape
        area = ny * nx * lap.dx ** 2
        expected = 1.0 / ((10.0 + lap.h_top) * area)
        self.assertAlmostEqual(sol.rise_die, expected, delta=expected * 0.01)

    def test_more_cooling_means_more_power(self):
        weak = model.solve(LAP, model.uniform(LAP, "weak", 4.0, 25.0))
        strong = model.solve(LAP, model.uniform(LAP, "strong", 40.0, 25.0))
        self.assertGreater(strong.sustained_power(100)[0], weak.sustained_power(100)[0])

    def test_pad_helps_only_with_base_cooling_available(self):
        cool = model.uniform(LAP, "strong", 40.0, 25.0)
        stock = model.solve(LAP, cool).sustained_power(100)[0]
        padded = model.solve(LAP.with_pad(), cool).sustained_power(100)[0]
        self.assertGreater(padded, stock)

    def test_hot_spot_is_over_the_spreader(self):
        sol = model.solve(LAP.with_pad(), model.uniform(LAP, "desk", 6.0, 25.0))
        iy, ix = np.unravel_index(np.argmax(sol.rise_bottom), sol.rise_bottom.shape)
        self.assertTrue(LAP.mask(LAP.spreader)[iy, ix])

    def test_skin_limit_can_bind(self):
        sol = model.solve(LAP.with_pad(), model.uniform(LAP, "desk", 6.0, 25.0))
        p, which = sol.sustained_power(105, t_skin_limit=45)
        self.assertLessEqual(p, sol.sustained_power(105)[0])
        self.assertIn(which, ("chip", "bottom skin", "top skin"))


class Airflow(unittest.TestCase):
    FAN = airflow.Fan("test 92", 0.092, 0.014, 50 / 3600, 20.0, 20.0, 1.0)

    def test_free_air_when_unrestricted(self):
        q = airflow.operating_flow(self.FAN, 1, a_out=10.0, a_in=10.0)
        self.assertAlmostEqual(q, self.FAN.q_max, delta=self.FAN.q_max * 0.001)

    def test_restriction_cuts_flow(self):
        wide = airflow.operating_flow(self.FAN, 1, a_out=0.004, a_in=0.01)
        tight = airflow.operating_flow(self.FAN, 1, a_out=0.001, a_in=0.01)
        self.assertLess(tight, wide)
        self.assertLess(wide, self.FAN.q_max)

    def test_operating_point_is_on_both_curves(self):
        a_out, a_in = 0.002, 0.004
        q = airflow.operating_flow(self.FAN, 2, a_out, a_in)
        system = 0.5 * airflow.RHO * (2 * q) ** 2 * (1.8 / a_out ** 2 + 1.8 / a_in ** 2)
        self.assertAlmostEqual(self.FAN.pressure(q), system, delta=0.01)

    def test_half_speed_halves_free_flow(self):
        q = airflow.operating_flow(self.FAN, 1, 10.0, 10.0, speed=0.5)
        self.assertAlmostEqual(q, self.FAN.q_max / 2, delta=self.FAN.q_max * 0.001)

    def test_impingement_map(self):
        zone = (0.0, LAP.width, 0.145, LAP.depth)
        c = airflow.impingement(LAP, "t", self.FAN, [(0.152, 0.18)], zone, 0.006, 25.0, 0.01)
        inside = LAP.mask(zone)
        self.assertGreater(c.h[inside].max(), 20.0)
        self.assertTrue(np.all(c.h[~inside] == 4.0))
        self.assertTrue(0 < c.notes["fraction_of_free_flow"] <= 1)
        self.assertTrue(math.isfinite(c.notes["noise_dba"]))


if __name__ == "__main__":
    unittest.main()
