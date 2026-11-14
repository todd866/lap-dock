"""First-order steady-state thermal model of a fanless MacBook Air on a cooling tray.

Two aluminium plates (bottom case, top case) on a 2D grid, a lumped heat spreader and a
lumped chip. Heat leaves through the outside of both plates by convection to a sink
temperature that can vary over the surface. Everything is linear, so one solve with the
chip at 1 W and one at 0 W give the temperature anywhere for any chip power.

This ranks cooling schemes and shows what the answer is sensitive to. It does not
predict absolute temperatures to better than its calibration.
"""
from dataclasses import dataclass, field, replace

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla


@dataclass(frozen=True)
class Laptop:
    """Geometry and internal thermal paths. x runs left to right as the user sees the
    open laptop, y from the front edge (0) to the hinge edge. Lengths in metres."""
    width: float = 0.3041
    depth: float = 0.215
    dx: float = 0.0025
    # conductivity x thickness of each plate, W/K
    kt_bottom: float = 160 * 0.0010
    kt_top: float = 160 * 0.0012
    # coupling between the plates
    g_edge: float = 8.0        # W/K per metre of perimeter
    h_interior: float = 3.0    # W/m2K through the air and parts between the plates
    # heat spreader footprint (x0, x1, y0, y1)
    spreader: tuple = (0.092, 0.212, 0.150, 0.205)
    r_die_spreader: float = 2.5   # K/W, chip junction to spreader
    g_spreader_top: float = 0.35  # W/K, spreader to top case through the board and screws
    h_gap: float = 22.0           # W/m2K, spreader to bottom case across the stock air gap
    # optional thermal-pad modification
    pad: tuple | None = None      # footprint (x0, x1, y0, y1) or None
    pad_k: float = 6.0            # W/mK
    pad_t: float = 0.0015         # m
    # top surface to room air (natural convection plus radiation)
    h_top: float = 9.0
    # heat from everything that is not the chip: memory, storage, power conversion,
    # radios, keyboard. q_board enters at the board with the chip; q_spread is uniform.
    q_board: float = 0.0
    q_spread: float = 0.0

    def with_pad(self, footprint=(0.122, 0.182, 0.158, 0.198)):
        return replace(self, pad=footprint)

    @property
    def shape(self):
        return (int(round(self.depth / self.dx)), int(round(self.width / self.dx)))

    def grid(self):
        ny, nx = self.shape
        x = (np.arange(nx) + 0.5) * self.dx
        y = (np.arange(ny) + 0.5) * self.dx
        return np.meshgrid(x, y)

    def mask(self, rect):
        X, Y = self.grid()
        x0, x1, y0, y1 = rect
        return (X >= x0) & (X < x1) & (Y >= y0) & (Y < y1)


@dataclass
class Cooling:
    """What the outside of the bottom case sees: a heat-transfer coefficient map and the
    temperature of whatever it is losing heat to, both on the laptop grid."""
    name: str
    h: np.ndarray
    t_sink: np.ndarray
    notes: dict = field(default_factory=dict)


@dataclass
class Solution:
    laptop: Laptop
    cooling: Cooling
    t_amb: float
    rise_bottom: np.ndarray  # K per watt of chip power
    rise_top: np.ndarray
    rise_die: float
    rise_spreader: float
    base_bottom: np.ndarray  # temperatures at zero chip power
    base_top: np.ndarray
    base_die: float

    def at(self, power):
        return (self.base_bottom + power * self.rise_bottom,
                self.base_top + power * self.rise_top,
                self.base_die + power * self.rise_die)

    def sustained_power(self, t_die_limit, t_skin_limit=None):
        """Largest chip power that keeps the chip, and optionally every point of both
        outer surfaces, at or under its limit. Returns (watts, which limit binds)."""
        p_die = (t_die_limit - self.base_die) / self.rise_die
        if t_skin_limit is None:
            return p_die, "chip"
        with np.errstate(divide="ignore", invalid="ignore"):
            pb = np.min((t_skin_limit - self.base_bottom) / self.rise_bottom)
            pt = np.min((t_skin_limit - self.base_top) / self.rise_top)
        best = min((p_die, "chip"), (pb, "bottom skin"), (pt, "top skin"))
        return best

    def heat_split(self):
        """Fraction of chip heat leaving through the bottom and the top."""
        a = self.laptop.dx ** 2
        qb = float(np.sum(self.cooling.h * a * self.rise_bottom))
        qt = float(np.sum(self.laptop.h_top * a * self.rise_top))
        return qb, qt


def _solve(laptop, cooling, t_amb, power):
    ny, nx = laptop.shape
    n = ny * nx
    a = laptop.dx ** 2
    idx = np.arange(n).reshape(ny, nx)
    B, T = 0, n               # offsets of the bottom and top plate unknowns
    S, D = 2 * n, 2 * n + 1   # spreader and chip
    rows, cols, vals = [], [], []
    diag = np.zeros(2 * n + 2)
    rhs = np.zeros(2 * n + 2)

    def link(i, j, g):
        """Conductance g between unknowns i and j (arrays or scalars)."""
        i = np.atleast_1d(i).ravel()
        j = np.atleast_1d(j).ravel()
        g = np.broadcast_to(np.atleast_1d(g).ravel(), i.shape)
        np.add.at(diag, i, g)
        np.add.at(diag, j, g)
        rows.extend([i, j])
        cols.extend([j, i])
        vals.extend([-g, -g])

    def sink(i, g, t):
        i = np.atleast_1d(i).ravel()
        g = np.broadcast_to(np.atleast_1d(g).ravel(), i.shape)
        t = np.broadcast_to(np.atleast_1d(t).ravel(), i.shape)
        np.add.at(diag, i, g)
        np.add.at(rhs, i, g * t)

    # in-plane conduction (square cells, so conductance is k*t)
    for off, kt in ((B, laptop.kt_bottom), (T, laptop.kt_top)):
        link(off + idx[:, :-1], off + idx[:, 1:], kt)
        link(off + idx[:-1, :], off + idx[1:, :], kt)

    # plate-to-plate: perimeter wall plus weak interior path
    edge = np.zeros((ny, nx), bool)
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = True
    g_pp = np.where(edge, laptop.g_edge * laptop.dx, 0.0) + laptop.h_interior * a
    link(B + idx, T + idx, g_pp)

    # outside surfaces
    sink(B + idx, cooling.h * a, cooling.t_sink)
    sink(T + idx, laptop.h_top * a, t_amb)

    # spreader to bottom case: stock air gap, or pad where fitted
    sp_mask = laptop.mask(laptop.spreader)
    u = np.where(sp_mask, laptop.h_gap, 0.0)
    if laptop.pad is not None:
        u = np.where(laptop.mask(laptop.pad), laptop.pad_k / laptop.pad_t, u)
    cells = idx[u > 0]
    link(B + cells, np.full(cells.shape, S), u[u > 0] * a)

    # spreader to top case, spread over its footprint
    cells = idx[sp_mask]
    link(T + cells, np.full(cells.shape, S), laptop.g_spreader_top / cells.size)

    # chip to spreader, and the heat source
    link(D, S, 1.0 / laptop.r_die_spreader)
    rhs[D] += power
    rhs[S] += laptop.q_board
    rhs[B:B + n] += 0.5 * laptop.q_spread / n
    rhs[T:T + n] += 0.5 * laptop.q_spread / n

    rows.append(np.arange(2 * n + 2))
    cols.append(np.arange(2 * n + 2))
    vals.append(diag)
    A = sp.csc_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                      shape=(2 * n + 2, 2 * n + 2))
    t = spla.spsolve(A, rhs)
    return t[:n].reshape(ny, nx), t[n:2 * n].reshape(ny, nx), t[S], t[D]


def solve(laptop, cooling, t_amb=25.0):
    b0, t0, s0, d0 = _solve(laptop, cooling, t_amb, 0.0)
    b1, t1, s1, d1 = _solve(laptop, cooling, t_amb, 1.0)
    return Solution(laptop, cooling, t_amb, b1 - b0, t1 - t0, d1 - d0, s1 - s0, b0, t0, d0)


def uniform(laptop, name, h, t_sink):
    ny, nx = laptop.shape
    return Cooling(name, np.full((ny, nx), float(h)), np.full((ny, nx), float(t_sink)))
