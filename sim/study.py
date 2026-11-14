"""Compare cooling arrangements for the Lap Dock on the calibrated model.

Writes a results table (Markdown) and temperature maps (PNG) into docs/.
Run after calibrate.py.
"""
import pathlib
from dataclasses import replace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

import airflow  # noqa: E402
import calibrate  # noqa: E402
import model  # noqa: E402

DOCS = pathlib.Path(__file__).resolve().parent.parent / "docs"
T_DIE = 100.0
T_SKIN = 48.0     # IEC 62368-1 limit for surfaces touched for more than a minute
T_THIGH = 34.0

MMH2O = 9.81
# Manufacturer figures. Noise for the Arctic fans is converted from 0.3 sone (estimate);
# the NF-A9x14 noise figure and the non-P14 prices are from memory, not checked today.
FANS = {
    "92": airflow.Fan("Noctua NF-A9x14 (92 mm)", 0.092, 0.014, 50.5 / 3600, 1.64 * MMH2O, 19.9, 1.32, 35),
    "120": airflow.Fan("Arctic P12 Slim (120 mm)", 0.120, 0.015, 71.5 / 3600, 1.45 * MMH2O, 22.0, 1.44, 12),
    "140": airflow.Fan("Arctic P14 Slim (140 mm)", 0.140, 0.016, 88.35 / 3600, 1.55 * MMH2O, 22.0, 2.3, 12),
}
# Centrifugal blowers, typical datasheet figures (Mechatronics B5015, Same Sky CBM-7530B,
# Sofasco sDB9733). Power for the 7530 and all blower prices are estimates.
INH2O = 249.0
CFM = 1.699 / 3600
FANS.update({
    "5015": airflow.Fan("5015 blower", 0.051, 0.015, 4 * CFM, 14.3 * MMH2O, 40.0, 2.4, 8),
    "7530": airflow.Fan("7530 blower", 0.075, 0.030, 10 * CFM, 0.35 * INH2O, 36.0, 2.5, 15),
    "9733": airflow.Fan("9733 blower", 0.097, 0.033, 19.7 * CFM, 133.0, 45.0, 4.8, 20),
})
A_IN_BENCH = 0.0030   # m2 of rib-channel opening with nothing blocking it
A_IN_LAP = 0.0012     # the same with thighs and clothing closing most of the channels


def on_lap(lap, t_amb):
    """Bare laptop across two thighs: skin contact under each thigh, still air between."""
    X, _ = lap.grid()
    thigh = ((X > 0.03) & (X < 0.13)) | ((X > 0.17) & (X < 0.27))
    return model.Cooling("bare on the lap", np.where(thigh, 9.0, 3.0),
                         np.where(thigh, T_THIGH, t_amb))


def klim(lap, t_amb):
    """One 200 mm, 750 rpm fan under the middle of the laptop, intake partly blocked by
    the lap: about 1 m/s onto the base inside the fan circle, a drift of air outside."""
    X, Y = lap.grid()
    disc = np.hypot(X - lap.width / 2, Y - 0.105) < 0.10
    ny, nx = lap.shape
    return model.Cooling("Klim (200 mm fan)", np.where(disc, 14.0, 7.0),
                         np.full((ny, nx), t_amb + 1.0), {"noise_dba": 23.0})


def tray(lap, t_amb, key, centres, zone, gap, speed=1.0, a_in=A_IN_LAP, label=None):
    fan = FANS[key]
    name = label or f"{len(centres)} x {int(fan.size * 1000)} mm, {gap * 1000:.0f} mm gap"
    if speed != 1.0:
        name += f", {speed:.0%} speed"
    return airflow.impingement(lap, name, fan, centres, zone, gap, t_amb, a_in,
                               speed=speed, intake_preheat=1.0)


def layouts(lap):
    """(fan key, centres, sealed zone) for each arrangement. y = 0 is the front edge."""
    w, d = lap.width, lap.depth
    hot_x = 0.5 * (lap.spreader[0] + lap.spreader[1])
    return {
        "3 x 92 across the back": ("92", [(0.056, 0.165), (0.152, 0.165), (0.248, 0.165)],
                                   (0.0, w, 0.115, d)),
        "2 x 120 across the back": ("120", [(0.082, 0.150), (0.222, 0.150)], (0.0, w, 0.085, d)),
        "2 x 140 across the back": ("140", [(0.076, 0.140), (0.228, 0.140)], (0.0, w, 0.065, d)),
        "1 x 140 under the hot spot": ("140", [(hot_x, 0.145)], (0.0, w, 0.070, d)),
        "1 x 120 under the hot spot": ("120", [(hot_x, 0.150)], (0.0, w, 0.085, d)),
    }


def ducted(lap, t_amb):
    """Blower-driven arrangements: air through the gap along the bare base, or through
    the fins of a contact plate. Both draw their air across the lap first."""
    w, d = lap.width, lap.depth
    sx0, sx1, sy0, _ = lap.spreader
    zone = (0.0, w, 0.135, d)
    plate = (max(sx0 - 0.01, 0.0), min(sx1 + 0.01, w), 0.135, d - 0.005)
    out = []
    for key, n, speed in (("5015", 2, 1.0), ("5015", 3, 0.7), ("7530", 1, 1.0),
                          ("7530", 1, 0.7), ("9733", 1, 0.6)):
        tag = f"{n} x {key} blower" + ("" if speed == 1.0 else f" at {speed:.0%}")
        out.append((f"Bare base, 4 mm channel, {tag}",
                    airflow.channel(lap, "", FANS[key], n, zone, 0.004, t_amb, A_IN_LAP,
                                    speed=speed, intake_preheat=1.0)))
        out.append((f"Finned plate, poor contact, {tag}",
                    airflow.fins(lap, "", FANS[key], n, plate, t_amb, A_IN_LAP, 170.0,
                                 speed=speed, intake_preheat=1.0)))
    out.append(("Finned plate, fair contact, 1 x 7530 blower at 70%",
                airflow.fins(lap, "", FANS["7530"], 1, plate, t_amb, A_IN_LAP, 500.0,
                             speed=0.7, intake_preheat=1.0)))
    ny, nx = lap.shape
    out.append(("Ceiling: hot zone of the base held at air temperature",
                model.Cooling("", np.where(lap.mask(zone), 5000.0, 4.0),
                              np.full((ny, nx), float(t_amb)))))
    return out


def evaluate(lap, cooling, t_amb):
    """Sustained chip power at the chip's temperature limit, and how hot the two outer
    surfaces are at that power."""
    sol = model.solve(lap, cooling, t_amb)
    p_die, _ = sol.sustained_power(T_DIE)
    b, t, _ = sol.at(p_die)
    return {"sol": sol, "p_die": p_die, "bottom_max": float(b.max()), "top_max": float(t.max())}


def row(name, r, base, cooling):
    n = cooling.notes
    noise = f"{n['noise_dba']:.0f}" if "noise_dba" in n else "-"
    flow = f"{n['total_flow_m3h']:.0f}" if "total_flow_m3h" in n else "-"
    return (f"| {name} | {r['p_die']:.1f} | {r['p_die'] / base['p_die'] - 1:+.0%} | "
            f"{r['bottom_max']:.0f} | {r['top_max']:.0f} | {flow} | {noise} |")


HEAD = ("| Arrangement | Sustained chip power (W) | vs bare lap | Hottest base (C) "
        "| Hottest keyboard deck (C) | Air (m3/h) | Noise (dBA) |\n|---|---|---|---|---|---|---|")


def table(lap, t_amb, title):
    out = [f"### {title}", "", HEAD]
    base_c = on_lap(lap, t_amb)
    base = evaluate(lap, base_c, t_amb)
    cases = [(base_c.name, base_c), ("Klim (200 mm fan)", klim(lap, t_amb))]
    for name, (key, centres, zone) in layouts(lap).items():
        cases.append((name + ", 5 mm gap", tray(lap, t_amb, key, centres, zone, 0.005)))
    cases += ducted(lap, t_amb)
    results = {}
    for name, c in cases:
        r = base if c is base_c else evaluate(lap, c, t_amb)
        results[name] = (r, c)
        out.append(row(name, r, base, c))
    return "\n".join(out), results, base


def sweep_gap_speed(lap, t_amb, name, key, centres, zone, base):
    out = [f"### {name}: gap height, fan speed and a blocked intake", "", HEAD]
    for gap in (0.003, 0.005, 0.008):
        for speed in (1.0, 0.6):
            c = tray(lap, t_amb, key, centres, zone, gap, speed)
            out.append(row(c.name, evaluate(lap, c, t_amb), base, c))
    c = tray(lap, t_amb, key, centres, zone, 0.005, 1.0, a_in=A_IN_BENCH,
             label="5 mm gap, intake unobstructed (on a bench)")
    out.append(row(c.name, evaluate(lap, c, t_amb), base, c))
    return "\n".join(out)


def sweep_position(lap, t_amb, key, zone, base):
    """One fan moved across the back, to show how much position matters."""
    out = ["### One 140 mm fan moved left to right along the back", "",
           "| Fan centre from the left edge (mm) | Chip W (chip limit only) | vs bare lap |",
           "|---|---|---|"]
    for x in (0.076, 0.110, 0.140, 0.170, 0.200, 0.228):
        c = tray(lap, t_amb, key, [(x, 0.145)], zone, 0.005)
        r = evaluate(lap, c, t_amb)
        out.append(f"| {x * 1000:.0f} | {r['p_die']:.1f} | {r['p_die'] / base['p_die'] - 1:+.0%} |")
    return "\n".join(out)


def finned(lap, t_amb, base):
    out = ["### Finned contact plate under the hot zone, by quality of contact", "", HEAD]
    sx0, sx1, sy0, sy1 = lap.spreader
    plate = (sx0 - 0.01, sx1 + 0.01, sy0 - 0.01, lap.depth)
    for label, hc in (("poor contact (0.15 mm of trapped air)", 170.0),
                      ("fair contact", 500.0), ("ideal contact", 3000.0)):
        c = airflow.finned_plate(lap, f"Finned plate, {label}", plate, hc, 6.0, 40.0, 0.8, t_amb + 1.0)
        out.append(row(c.name, evaluate(lap, c, t_amb), base, c))
    return "\n".join(out)


def maps(cases, t_amb, path):
    fig, axes = plt.subplots(2, len(cases), figsize=(4.2 * len(cases), 6.2), constrained_layout=True)
    for i, (name, r, c) in enumerate(cases):
        lap = r["sol"].laptop
        ext = [0, lap.width * 1000, 0, lap.depth * 1000]
        b, _, _ = r["sol"].at(r["p_die"])
        im0 = axes[0, i].imshow(c.h, origin="lower", extent=ext, cmap="viridis", vmin=0, vmax=80)
        axes[0, i].set_title(name, fontsize=9)
        im1 = axes[1, i].imshow(b, origin="lower", extent=ext, cmap="inferno", vmin=t_amb, vmax=70)
        axes[1, i].set_title(f"{r['p_die']:.1f} W in the chip", fontsize=9)
        for ax in axes[:, i]:
            ax.set_xticks([]); ax.set_yticks([])
    axes[0, 0].set_ylabel("cooling on the base\n(hinge edge at top)")
    axes[1, 0].set_ylabel("base temperature")
    fig.colorbar(im0, ax=axes[0, :], shrink=0.8, label="W/m2K")
    fig.colorbar(im1, ax=axes[1, :], shrink=0.8, label="C")
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main():
    stock, _ = calibrate.load()
    sx0, sx1, _, _ = stock.spreader
    padded = replace(stock, pad=(sx0 + 0.02, sx1 - 0.02, 0.160, 0.202), pad_k=12.8)
    parts = []
    (DOCS / "img").mkdir(exist_ok=True)
    for t_amb in (25.0, 35.0):
        parts.append(f"## Air temperature {t_amb:.0f} C")
        for lap, label in ((stock, "Stock Air"), (padded, "Air with the thermal pad fitted")):
            text, results, base = table(lap, t_amb, label)
            parts.append(text)
            if t_amb == 25.0 and lap is padded:
                lay = layouts(lap)
                axial = max((n for n in results if n.endswith("5 mm gap")),
                            key=lambda n: results[n][0]["p_die"])
                key, centres, zone = lay[axial.replace(", 5 mm gap", "")]
                parts.append(sweep_gap_speed(lap, t_amb, axial.replace(", 5 mm gap", ""),
                                             key, centres, zone, base))
                best = max((n for n in results if "blower" in n and "poor" in n),
                           key=lambda n: results[n][0]["p_die"])
                picks = [base.get("name", "bare on the lap"), "Klim (200 mm fan)", best]
                cases = [("Bare on the lap", base, on_lap(lap, t_amb))]
                cases += [(n, results[n][0], results[n][1]) for n in picks[1:]]
                maps(cases, t_amb, DOCS / "img" / "cooling-maps.png")
    (DOCS / "cooling-study-tables.md").write_text("\n\n".join(parts) + "\n")
    print("\n\n".join(parts))


if __name__ == "__main__":
    main()
