"""Fans, the air path through the tray, and the heat-transfer coefficient they produce
on the laptop's base.

The air path: in through the ribbed underside, up through the fans, against the base,
then outward through the gap between the base and the tray deck to the open edges.
"""
import math
from dataclasses import dataclass

import numpy as np

from model import Cooling

RHO = 1.16      # kg/m3 at about 30 C
NU = 1.6e-5     # m2/s
K_AIR = 0.0263  # W/mK
PR = 0.71
CP = 1007.0     # J/kgK


@dataclass(frozen=True)
class Fan:
    """An axial fan from its datasheet: free-air flow, shut-off pressure, noise."""
    name: str
    size: float        # frame size, m
    thickness: float   # m
    q_max: float       # m3/s in free air
    p_max: float       # Pa at zero flow
    noise_dba: float
    power_w: float
    price_aud: float = 0.0

    @property
    def r_tip(self):
        return 0.47 * self.size

    @property
    def r_hub(self):
        return 0.19 * self.size

    @property
    def annulus(self):
        return math.pi * (self.r_tip ** 2 - self.r_hub ** 2)

    def pressure(self, q):
        """Straight-line fan curve. Real axial curves dip in the middle; this is kind to
        the fan at mid flow and is one of the model's stated simplifications."""
        return self.p_max * max(0.0, 1.0 - q / self.q_max)


def operating_flow(fan, n_fans, a_out, a_in, k_out=1.8, k_in=1.8, speed=1.0):
    """Flow per fan (m3/s) where the fan curve meets the tray's resistance.

    a_out and a_in are the total outlet and inlet areas shared by n_fans. speed scales
    the fan (flow with speed, pressure with speed squared). Loss coefficients cover the
    turn, the contraction and the exit.
    """
    q_max = fan.q_max * speed
    p_max = fan.p_max * speed ** 2
    c = 0.5 * RHO * n_fans ** 2 * (k_out / a_out ** 2 + k_in / a_in ** 2)
    # p_max (1 - q/q_max) = c q^2
    b = p_max / q_max
    return (-b + math.sqrt(b * b + 4 * c * p_max)) / (2 * c)


def h_stagnation(v, width):
    """Under the blade annulus, where the air strikes the plate."""
    re = v * width / NU
    return 0.76 * math.sqrt(re) * PR ** 0.4 * K_AIR / width


def h_gap(v, gap, run):
    """Flow between the base and the deck, one wall heated, `run` metres downstream."""
    dh = 2 * gap
    re = np.maximum(v * dh / NU, 1.0)
    gz = re * PR * dh / (run + dh)                       # Graetz number
    lam = 5.39 + 0.0668 * gz / (1 + 0.04 * gz ** (2 / 3))  # Hausen entrance form
    turb = 0.023 * re ** 0.8 * PR ** 0.4 * (1 + (dh / (run + dh)) ** 0.7)
    nu = np.where(re > 2300, np.maximum(turb, lam), lam)
    return nu * K_AIR / dh


def impingement(laptop, name, fan, centres, zone, gap, t_amb, a_in,
                open_edges=("back", "left", "right"), speed=1.0, h_outside=4.0,
                t_outside=None, intake_preheat=0.0):
    """Cooling map for fans blowing up at the base inside a sealed zone.

    centres: fan centres (x, y) on the laptop grid. zone: (x0, x1, y0, y1) enclosed by
    the gasket; air leaves through `open_edges` of the zone, through a gap of height
    `gap`. Outside the zone the base sees h_outside to t_outside (defaults to ambient).
    intake_preheat: how much warmer than ambient the intake air is after crossing the lap.
    """
    X, Y = laptop.grid()
    x0, x1, y0, y1 = zone
    lengths = {"back": x1 - x0, "front": x1 - x0, "left": y1 - y0, "right": y1 - y0}
    a_out = gap * sum(lengths[e] for e in open_edges)
    n = len(centres)
    q = operating_flow(fan, n, a_out, a_in, speed=speed)
    v_ann = q / fan.annulus
    width = fan.r_tip - fan.r_hub
    h_ann = h_stagnation(v_ann, width)

    h = np.zeros_like(X)
    for cx, cy in centres:
        r = np.hypot(X - cx, Y - cy)
        v_r = q / (2 * math.pi * np.maximum(r, fan.r_tip) * gap)
        outer = h_gap(v_r, gap, np.maximum(r - fan.r_tip, 0.0))
        local = np.where(r < fan.r_hub, 0.35 * h_ann,
                         np.where(r <= fan.r_tip, h_ann, np.minimum(outer, h_ann)))
        h = np.maximum(h, local)

    inside = laptop.mask(zone)
    t_air = t_amb + intake_preheat
    t_out = t_amb if t_outside is None else t_outside
    h_map = np.where(inside, h, h_outside)
    sink = np.where(inside, t_air, t_out)
    notes = {
        "flow_per_fan_m3h": q * 3600, "total_flow_m3h": q * n * 3600,
        "annulus_velocity": v_ann, "h_annulus": h_ann,
        "h_zone_mean": float(h_map[inside].mean()),
        "fraction_of_free_flow": q / (fan.q_max * speed),
        "air_heat_capacity_w_per_k": q * n * RHO * CP,
        "noise_dba": fan.noise_dba + 10 * math.log10(n) + 50 * math.log10(max(speed, 1e-3)),
        "fan_power_w": fan.power_w * n * speed ** 3,
    }
    return Cooling(name, h_map, sink, notes)


def finned_plate(laptop, name, plate, h_contact, fin_area_ratio, h_fin, fin_eff, t_amb,
                 h_outside=4.0):
    """A contact plate with fins: contact conductance in series with the finned side.

    h_contact: W/m2K across the interface (thermal sheet plus whatever air is trapped).
    fin_area_ratio: finned surface per unit of plate area.
    """
    inside = laptop.mask(plate)
    u = 1.0 / (1.0 / h_contact + 1.0 / (h_fin * fin_area_ratio * fin_eff))
    ny, nx = laptop.shape
    return Cooling(name, np.where(inside, u, h_outside), np.full((ny, nx), float(t_amb)),
                   {"u_plate": u})


# --- ducted arrangements: a blower pushing air through a defined passage -------------

MU = NU * RHO


def _friction(re):
    """Darcy friction factor between parallel plates."""
    return np.where(re < 2300, 96.0 / np.maximum(re, 1.0), 0.316 * np.maximum(re, 1.0) ** -0.25)


def duct_flow(fan, n_fans, area, dh, length, a_in, k_minor=1.5, k_in=1.8, speed=1.0):
    """Total flow (m3/s) where n_fans in parallel meet a passage of flow area `area`,
    hydraulic diameter `dh` and length `length`, fed through an intake of area a_in."""
    q_max = fan.q_max * speed * n_fans
    p_max = fan.p_max * speed ** 2

    def excess(q):
        v = q / area
        re = v * dh / NU
        dp = (float(_friction(re)) * length / dh + k_minor) * 0.5 * RHO * v * v
        dp += k_in * 0.5 * RHO * (q / a_in) ** 2
        return p_max * (1 - q / q_max) - dp

    lo, hi = 0.0, q_max
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if excess(mid) > 0 else (lo, mid)
    return 0.5 * (lo + hi)


def _notes(fan, n, speed, q):
    return {
        "total_flow_m3h": q * 3600,
        "fraction_of_free_flow": q / (fan.q_max * speed * n),
        "air_heat_capacity_w_per_k": q * RHO * CP,
        "noise_dba": fan.noise_dba + 10 * math.log10(n) + 50 * math.log10(max(speed, 1e-3)),
        "fan_power_w": fan.power_w * n * speed ** 3,
    }


def channel(laptop, name, fan, n_fans, zone, gap, t_amb, a_in, speed=1.0,
            h_outside=4.0, intake_preheat=0.0):
    """Air driven front to back through the gap between the base and the deck, across
    the whole width of the zone. The air warms as it goes, so cooling fades downstream."""
    x0, x1, y0, y1 = zone
    width, length = x1 - x0, y1 - y0
    q = duct_flow(fan, n_fans, width * gap, 2 * gap, length, a_in, speed=speed)
    v = q / (width * gap)
    _, Y = laptop.grid()
    run = np.clip(Y - y0, 0.0, length)
    h_local = h_gap(v, gap, run)
    # mean h up to each point sets how much the air has already warmed
    ys = np.linspace(0, length, 200)
    hs = h_gap(v, gap, ys)
    ntu_curve = np.concatenate([[0.0], np.cumsum(0.5 * (hs[1:] + hs[:-1]) * np.diff(ys))])
    ntu_curve *= width / (q * RHO * CP)
    ntu = np.interp(run, ys, ntu_curve)
    inside = laptop.mask(zone)
    ny, nx = laptop.shape
    notes = _notes(fan, n_fans, speed, q)
    notes.update(velocity=v, h_inlet=float(hs[1]), h_outlet=float(hs[-1]))
    return Cooling(name, np.where(inside, h_local * np.exp(-ntu), h_outside),
                   np.where(inside, t_amb + intake_preheat, t_amb) * np.ones((ny, nx)), notes)


def fins(laptop, name, fan, n_fans, plate, t_amb, a_in, h_contact, fin_height=0.010,
         spacing=0.002, fin_t=0.001, k_fin=200.0, speed=1.0, h_outside=4.0,
         intake_preheat=0.0):
    """A contact plate whose fins run front to back, with a blower driving air through
    them. Contact conductance, fin convection and the air's heat capacity act in series."""
    x0, x1, y0, y1 = plate
    width, length = x1 - x0, y1 - y0
    n_ch = int(width / (spacing + fin_t))
    area = n_ch * spacing * fin_height
    dh = 2 * spacing * fin_height / (spacing + fin_height)
    q = duct_flow(fan, n_fans, area, dh, length, a_in, speed=speed)
    v = q / area
    re = v * dh / NU
    gz = re * PR * dh / length
    nu = 7.54 + 0.03 * gz / (1 + 0.016 * gz ** (2 / 3))
    h = nu * K_AIR / dh
    m = math.sqrt(2 * h / (k_fin * fin_t))
    eff = math.tanh(m * fin_height) / (m * fin_height)
    ua = h * (n_ch * 2 * fin_height * length * eff + n_ch * spacing * length)
    c_air = q * RHO * CP
    g_air = c_air * (1 - math.exp(-ua / c_air))       # W/K, referred to the inlet air
    u = 1.0 / (1.0 / h_contact + (width * length) / g_air)
    inside = laptop.mask(plate)
    ny, nx = laptop.shape
    notes = _notes(fan, n_fans, speed, q)
    notes.update(velocity=v, h_fin=h, fin_efficiency=eff, g_air_w_per_k=g_air, u_plate=u)
    return Cooling(name, np.where(inside, u, h_outside),
                   np.where(inside, t_amb + intake_preheat, t_amb) * np.ones((ny, nx)), notes)
