"""Fit the model's internal thermal paths to published measurements of the M5 Air.

Target: Notebookcheck's 13-inch M5 review, maximum load, 21.5 C ambient, laptop on a
desk. Nine surface temperatures on each side, about 8.5 W sustained in the chip, about
24 W at the wall, chip settling near 100 C (the last figure is from M3 reporting).
"""
import json
import pathlib
from dataclasses import replace

import numpy as np
from scipy.optimize import least_squares

import model

T_AMB = 21.5
P_CHIP = 8.5
T_DIE = 100.0
# Rows from the hinge edge to the front edge; columns left to right as the user sees
# the open laptop. The published bottom grid is shown from underneath, so it is mirrored.
TOP = np.array([[42.7, 44.1, 40.1], [38.2, 39.9, 34.7], [32.9, 29.8, 31.5]])
BOTTOM_AS_PUBLISHED = np.array([[40.3, 42.4, 41.6], [36.9, 41.1, 38.4], [32.7, 33.2, 33.3]])
BOTTOM = BOTTOM_AS_PUBLISHED[:, ::-1]
OUT = pathlib.Path(__file__).with_name("calibration.json")

NAMES = ["h_desk", "h_top", "g_edge", "h_interior", "g_spreader_top", "h_gap",
         "xc", "half_w", "y0", "q_other", "board_frac"]
START = [7.0, 9.0, 8.0, 3.0, 0.35, 22.0, 0.135, 0.06, 0.150, 8.0, 0.7]
# Bounds carry the physics the 18 surface readings cannot identify on their own:
# - h_top: natural convection plus radiation from an upward-facing warm plate, 9-13.
# - h_gap: the shield-to-case air gap is 1.0-1.5 mm (both pad thicknesses make contact),
#   so conduction through still air plus a little radiation gives 19-28 W/m2K.
# - q_other: wall power settles near 24 W; less charger loss, the display and the chip,
#   6-11 W is left for everything else.
LOW = [3.0, 9.0, 0.5, 1.0, 0.02, 19.0, 0.08, 0.025, 0.110, 6.0, 0.2]
HIGH = [14.0, 13.0, 60.0, 15.0, 8.0, 28.0, 0.20, 0.11, 0.185, 11.0, 1.0]


def sectors(field):
    """3x3 sector means, row 0 at the hinge edge."""
    ny, nx = field.shape
    out = np.zeros((3, 3))
    for r in range(3):
        for c in range(3):
            ys = slice(ny - (r + 1) * ny // 3, ny - r * ny // 3)
            xs = slice(c * nx // 3, (c + 1) * nx // 3)
            out[r, c] = field[ys, xs].mean()
    return out


def build(p, dx=0.005):
    v = dict(zip(NAMES, p))
    lap = model.Laptop(
        dx=dx, h_top=v["h_top"], g_edge=v["g_edge"], h_interior=v["h_interior"],
        g_spreader_top=v["g_spreader_top"], h_gap=v["h_gap"],
        spreader=(v["xc"] - v["half_w"], v["xc"] + v["half_w"], v["y0"], 0.208),
        q_board=v["q_other"] * v["board_frac"],
        q_spread=v["q_other"] * (1 - v["board_frac"]))
    return lap, v["h_desk"]


def predict(p, dx=0.005):
    lap, h_desk = build(p, dx)
    sol = model.solve(lap, model.uniform(lap, "desk", h_desk, T_AMB), T_AMB)
    b, t, _ = sol.at(P_CHIP)
    return lap, sol, sectors(b), sectors(t)


def residuals(p):
    _, _, b, t = predict(p)
    return np.concatenate([(b - BOTTOM).ravel(), (t - TOP).ravel()])


def main():
    # The footprint snaps to grid cells, so it is searched over a small set of
    # candidates; the smooth parameters are fitted for each.
    smooth = [i for i, n in enumerate(NAMES) if n not in ("xc", "half_w", "y0")]
    lo, hi = np.array(LOW)[smooth], np.array(HIGH)[smooth]
    fit = None
    for xc in (0.115, 0.135, 0.155):
        for half_w in (0.045, 0.070):
            for y0 in (0.135, 0.160):
                def res(q, xc=xc, half_w=half_w, y0=y0):
                    full = np.array(START, float)
                    full[smooth] = q
                    full[NAMES.index("xc")], full[NAMES.index("half_w")] = xc, half_w
                    full[NAMES.index("y0")] = y0
                    res.full = full
                    return residuals(full)
                f = least_squares(res, np.array(START)[smooth], bounds=(lo, hi),
                                  x_scale=hi - lo, max_nfev=60)
                res(f.x)
                f.x = res.full.copy()
                if fit is None or f.cost < fit.cost:
                    fit = f
    lap, sol, b, t = predict(fit.x, dx=0.0025)
    # the chip-to-board resistance follows from the chip temperature target
    spreader_t = sol.base_die + P_CHIP * sol.rise_spreader   # base_die equals base spreader
    r_js = (T_DIE - spreader_t) / P_CHIP
    lap = replace(lap, r_die_spreader=float(r_js))
    params = dict(zip(NAMES, map(float, fit.x)))
    params["r_die_spreader"] = float(r_js)
    rms = float(np.sqrt(np.mean(fit.fun ** 2)))
    OUT.write_text(json.dumps({"params": params, "rms_error_k": rms,
                               "t_amb": T_AMB, "p_chip": P_CHIP, "t_die": T_DIE}, indent=2))
    np.set_printoptions(precision=1, suppress=True)
    print("fitted:", json.dumps({k: round(v, 3) for k, v in params.items()}))
    print(f"rms error {rms:.2f} K over 18 points")
    print("bottom model:\n", b, "\nbottom measured:\n", BOTTOM)
    print("top model:\n", t, "\ntop measured:\n", TOP)
    print(f"spreader {spreader_t:.1f} C, chip-to-board resistance {r_js:.2f} K/W")
    qb, qt = sol.heat_split()
    print(f"chip heat leaving by bottom {qb:.2f}, top {qt:.2f}")


def load(dx=0.0025):
    """The calibrated laptop and its desk coefficient."""
    d = json.loads(OUT.read_text())["params"]
    lap, h_desk = build([d[k] for k in NAMES], dx)
    return replace(lap, r_die_spreader=d["r_die_spreader"]), h_desk


if __name__ == "__main__":
    main()
