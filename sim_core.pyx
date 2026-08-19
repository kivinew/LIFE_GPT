# cython: language_level=3, boundscheck=False, wraparound=False, nonecheck=False
# sim_core.pyx - Cython-accelerated hot loops for LIFE_GPT
#
# Complements cell.py by accelerating bulk array operations.
# IMPORTANT: scalar constants are defined locally here (Cython cannot
# import Python module-level variables as compile-time cdefs).
#
# Build:  python3 setup_sim_core.py build_ext --inplace

import numpy as np
cimport numpy as np
cimport cython
from libc.stdlib cimport rand, RAND_MAX
from libc.math cimport cos as c_cos, sin as c_sin, sqrt as c_sqrt
from libc.math cimport sqrt as c_sqrt_math

# NumPy 2.x removed np.int32_t / np.int64_t aliases; map them explicitly so the
# compiled extension accepts the exact-width buffers that callers build with
# dtype=np.int32 / np.int64. Without this, `cy_sense_food` raises
# "Buffer dtype mismatch, expected 'int32_t' but got 'long'" on numpy>=2.
ctypedef np.int32_t int32_npy
ctypedef np.int64_t int64_npy

# ── Constants (duplicated from config.py for Cython compile-time) ──
# IMPORTANT: keep these in sync with config.py — edits to balance values in
# config.py are silently ignored by the compiled .pyd unless these are updated
# and sim_core is rebuilt (`python setup_sim_core.py build_ext --inplace`).
cdef int _PHOT = 0
cdef int _ZOOP = 1
cdef int _POLY = 2

cdef double _ENERGY_MASS_COEFF = 4.5          # config: ENERGY_MASS_COEFF
cdef double _LEVEL_UP_THRESHOLD = 0.60        # config: LEVEL_UP_THRESHOLD
cdef double _LEVEL_DOWN_THRESHOLD = 3.0       # config: LEVEL_DOWN_THRESHOLD
cdef int _MAX_LEVEL = 10                      # config: MAX_LEVEL
cdef double _LEVEL_MASS_BASE = 2.0            # config: LEVEL_MASS_BASE
cdef double _LEVEL_MASS_STEP = 0.6            # config: LEVEL_MASS_STEP

cdef double _BASE_METABOLISM_MULT = 1.0       # config: BASE_METABOLISM_MULT
cdef double _PREDATOR_METABOLISM_MULT = 0.55  # config: PREDATOR_METABOLISM_MULT
cdef double _SPEED_COST = 0.05                 # config: SPEED_COST
cdef double _MASS_PENALTY = 0.0028             # config: MASS_PENALTY
cdef double _FEED_EFFICIENCY_BASE = 22.0       # config: FEED_EFFICIENCY_BASE (was 18.0)
cdef double _PHOT_FEED_EFFICIENCY = 1.0        # config: PHOT_FEED_EFFICIENCY
cdef double _POLY_FEED_EFFICIENCY = 0.7        # config: POLY_FEED_EFFICIENCY
cdef double _MIN_MASS = 1.0                     # config: minimum cell mass
cdef double _MIN_MASS_EFFICIENCY = 0.55        # config: MIN_MASS_EFFICIENCY
cdef double _COMBAT_BASE_DAMAGE = 0.9          # config: COMBAT_BASE_DAMAGE
cdef double _COMBAT_DAMAGE_GAIN = 0.8          # config: COMBAT_DAMAGE_GAIN
cdef double _MASS_DMG_EFFICIENCY = 0.035        # config: MASS_DMG_EFFICIENCY
cdef double _MIN_MASS_DMG_EFF = 0.45           # config: MIN_MASS_DMG_EFF

cdef double _FEED_RADIUS = 4.0               # config: FEED_RADIUS
cdef double _FEED_RADIUS_SQ = 16.0           # config: FEED_RADIUS_SQ

cdef int _CELL_SIZE = 16
cdef int _SB = 600
cdef int _W = 1600
cdef int _H = 900

# ── Math constants (not in config.py, used only by Cython hot loops) ──
cdef double _PI2 = 6.28318530717958647692  # 2 * pi


@cython.boundscheck(False)
@cython.wraparound(False)
def apply_physics(
    np.ndarray[np.float64_t, ndim=1] xs,
    np.ndarray[np.float64_t, ndim=1] ys,
    np.ndarray[np.float64_t, ndim=1] best_dx,
    np.ndarray[np.float64_t, ndim=1] best_dy,
    np.ndarray[np.float64_t, ndim=1] speed_arr,
    double dt,
):
    """Move cells and enforce boundaries.  Pure array math — no Python objects."""
    cdef int i, n = len(xs)
    cdef double dist, nx, ny

    for i in range(n):
        dist = best_dx[i] ** 2 + best_dy[i] ** 2
        if dist > 0:
            dist = dist ** 0.5
            nx = xs[i] + (best_dx[i] / dist) * speed_arr[i] * dt
            ny = ys[i] + (best_dy[i] / dist) * speed_arr[i] * dt
        else:
            nx = xs[i]
            ny = ys[i]

        if nx < 0.0:
            nx = 0.0
        elif nx >= _W - _SB:
            nx = _W - _SB - 1.0
        if ny < 0.0:
            ny = 0.0
        elif ny >= _H:
            ny = _H - 1.0

        xs[i] = nx
        ys[i] = ny


@cython.boundscheck(False)
@cython.wraparound(False)
def apply_metabolism_and_feeding(
    np.ndarray[np.float64_t, ndim=1] xs,
    np.ndarray[np.float64_t, ndim=1] ys,
    np.ndarray[np.float64_t, ndim=1] energies,
    np.ndarray[int32_npy, ndim=1] diet_arr,
    np.ndarray[np.float64_t, ndim=1] speed_arr,
    np.ndarray[np.float64_t, ndim=1] mass_arr,
    np.ndarray[np.float64_t, ndim=1] metab_arr,
    np.ndarray[int32_npy, ndim=1] level_arr,
    np.ndarray[np.float64_t, ndim=2] field_data,
    double dt,
):
    """Metabolism + feeding + level transitions, all in tight loops."""
    cdef int i, x, y, fw, fh, n = len(xs)
    cdef double metab_mult, metab_cost, max_e, eat, mass_eff, diet_eff

    fw = field_data.shape[0]
    fh = field_data.shape[1]

    for i in range(n):
        # ── Metabolism ──
        if diet_arr[i] == _PHOT:
            metab_mult = _BASE_METABOLISM_MULT
        else:
            metab_mult = _PREDATOR_METABOLISM_MULT

        metab_cost = (metab_arr[i] + speed_arr[i] * _SPEED_COST
                      + mass_arr[i] * mass_arr[i] * _MASS_PENALTY) * metab_mult * dt
        energies[i] -= metab_cost

        # ── Feeding (PHOT / POLY from field) ──
        # Sample a small area (_FEED_RADIUS) around the cell so food is
        # actually found at 0.33% field coverage. Single-pixel eating causes
        # starvation because cells almost never land exactly on a food pixel.
        # ── Feeding (PHOT / POLY from field) ──
        if diet_arr[i] == _PHOT or diet_arr[i] == _POLY:
            x = int(xs[i])
            y = int(ys[i])
            mass_eff = 5.0 / mass_arr[i] if mass_arr[i] > 0 else _MIN_MASS_EFFICIENCY
            if mass_eff < _MIN_MASS_EFFICIENCY:
                mass_eff = _MIN_MASS_EFFICIENCY
            diet_eff = _PHOT_FEED_EFFICIENCY if diet_arr[i] == _PHOT else _POLY_FEED_EFFICIENCY
            max_eat = 3.0 * dt
            cx, cy = xs[i], ys[i]
            r = int(_FEED_RADIUS)
            x0 = x - r
            x1 = x + r + 1
            y0 = y - r
            y1 = y + r + 1
            eat = 0.0
            for px in range(x0, x1):
                if px < 0 or px >= fw:
                    continue
                for py in range(y0, y1):
                    if py < 0 or py >= fh:
                        continue
                    dx = px - cx
                    dy = py - cy
                    if dx * dx + dy * dy <= _FEED_RADIUS_SQ:
                        v = field_data[px, py]
                        if v > 0.0:
                            take = min(v, max_eat)
                            field_data[px, py] = v - take
                            eat += take
                            max_eat -= take
                            if max_eat <= 0.0:
                                break
                if max_eat <= 0.0:
                    break
            if eat > 0.0:
                energies[i] += eat * _FEED_EFFICIENCY_BASE * mass_eff * diet_eff

        # ── Energy cap ──
        max_e = mass_arr[i] * mass_arr[i] * _ENERGY_MASS_COEFF
        if energies[i] < 0.0:
            energies[i] = 0.0
        elif energies[i] > max_e:
            energies[i] = max_e

        # ── Level system ──
        # Level up: if at current level, 75% of next tier's max energy is met
        if level_arr[i] < _MAX_LEVEL:
            next_mass = mass_arr[i] * 1.15
            if next_mass > 8.0:
                next_mass = 8.0
            next_max = next_mass * next_mass * _ENERGY_MASS_COEFF
            if energies[i] >= next_max * 0.75:
                level_arr[i] += 1
                mass_arr[i] = next_mass
                new_max = mass_arr[i] * mass_arr[i] * _ENERGY_MASS_COEFF
                energies[i] = new_max * 0.70

        # Level down: if at max level, energy falls below threshold, decrease level
        if energies[i] <= _LEVEL_DOWN_THRESHOLD and level_arr[i] > 0:
            # Calculate current mass limit
            max_mass = max(_MIN_MASS, c_sqrt_math(energies[i] / _ENERGY_MASS_COEFF))
            current_mass = mass_arr[i]
            target_mass = current_mass * 0.9  # Reduce mass by 10%
            if target_mass >= _MIN_MASS and target_mass <= 8.0 and target_mass < current_mass:
                mass_arr[i] = target_mass
                new_max = mass_arr[i] * mass_arr[i] * _ENERGY_MASS_COEFF
                # Cap to current energy for smooth transition
                cap_energy = min(energies[i], new_max)
                energies[i] = cap_energy * 0.95
                level_arr[i] -= 1


def build_spatial_grid(
    np.ndarray[np.float64_t, ndim=1] xs,
    np.ndarray[np.float64_t, ndim=1] ys,
):
    """Build spatial hash grid.  Returns dict {(gx,gy): [idx,...]}."""
    cdef int i, gx, gy, n = len(xs)
    cdef dict grid = {}
    cdef list bucket

    for i in range(n):
        gx = <int>(xs[i] / _CELL_SIZE)
        gy = <int>(ys[i] / _CELL_SIZE)
        key = (gx, gy)
        if key in grid:
            bucket = grid[key]
            bucket.append(i)
        else:
            grid[key] = [i]
    return grid


@cython.boundscheck(False)
@cython.wraparound(False)
def get_neighbors(dict grid, double x, double y, int radius):
    """Return indices of cells in neighboring grid cells (Cython version).

    Mirrors spatial.py's get_neighbors() — operates on a Python dict grid
    built by build_spatial_grid(). Faster than the Python loop because
    variables are typed and grid.get() replaces 'in' + indexing.
    """
    cdef int gx = <int>(x / _CELL_SIZE)
    cdef int gy = <int>(y / _CELL_SIZE)
    cdef list result = []
    cdef int dx, dy
    cdef tuple key
    cdef list bucket

    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            key = (gx + dx, gy + dy)
            bucket = grid.get(key)
            if bucket is not None:
                result.extend(bucket)
    return tuple(result)


@cython.boundscheck(False)
@cython.wraparound(False)
def cy_sense_food(
    np.ndarray[np.float64_t, ndim=1] xs,
    np.ndarray[np.float64_t, ndim=1] ys,
    np.ndarray[int32_npy, ndim=1] diet_arr,
    np.ndarray[np.float64_t, ndim=1] sense_arr,
    np.ndarray[np.float64_t, ndim=1] best_dx,
    np.ndarray[np.float64_t, ndim=1] best_dy,
    np.ndarray[np.float64_t, ndim=2] field_data,
    int n, int fw, int fh,
):
    """Bulk food ray sampling for all cells.

    Replaces the per-cell trigonometric ray sampling in sensory_phase:
    - Sets a random initial direction for every cell.
    - For PHOT/POLY cells, samples 16 rays in the food field and picks
      the direction with the highest food score.

    Updates *best_dx* / *best_dy* in-place.  Uses C libc math
    (c_cos, c_sin, c_sqrt) and rand() for speed.
    """
    cdef int i, j, sx, sy
    cdef double ang, dist, val, score, best_score
    cdef double _bx, _by, _bn, sense
    cdef double r_max = <double>RAND_MAX

    for i in range(n):
        # Random initial direction (for all cells)
        _bx = <double>rand() / r_max * 2.0 - 1.0
        _by = <double>rand() / r_max * 2.0 - 1.0
        _bn = c_sqrt(_bx * _bx + _by * _by)
        if _bn > 0.0:
            best_dx[i] = _bx / _bn
            best_dy[i] = _by / _bn
        else:
            # Random fallback direction (NOT (0,1) downward — avoids systemic
            # downward drift when rand() yields a zero vector).
            _ang = <double>rand() / r_max * _PI2
            best_dx[i] = c_cos(_ang)
            best_dy[i] = c_sin(_ang)

        # Food ray sampling for PHOT/POLY cells only
        if diet_arr[i] == _PHOT or diet_arr[i] == _POLY:
            if sense_arr[i] < 8.0:
                sense = 8.0
            else:
                sense = sense_arr[i]
            best_score = -1.0
            for j in range(32):
                ang = <double>j / 32.0 * _PI2
                # Sample at multiple distances so food at any distance in the
                # sense range is detectable — single-distance sampling misses
                # food that's close but not at the exact ray endpoint.
                d1 = sense * 0.25
                d2 = sense * 0.5
                d3 = sense * 0.75
                sx1 = <int>(xs[i] + c_cos(ang) * d1)
                sy1 = <int>(ys[i] + c_sin(ang) * d1)
                sx2 = <int>(xs[i] + c_cos(ang) * d2)
                sy2 = <int>(ys[i] + c_sin(ang) * d2)
                sx3 = <int>(xs[i] + c_cos(ang) * d3)
                sy3 = <int>(ys[i] + c_sin(ang) * d3)
                if 0 <= sx1 < fw and 0 <= sy1 < fh:
                    val = field_data[sx1, sy1]
                    if val > 0.01:
                        score = val / (1.0 + 0.25)
                        if score > best_score:
                            best_score = score
                            best_dx[i] = c_cos(ang)
                            best_dy[i] = c_sin(ang)
                if 0 <= sx2 < fw and 0 <= sy2 < fh:
                    val = field_data[sx2, sy2]
                    if val > 0.01:
                        score = val / (1.0 + 0.5)
                        if score > best_score:
                            best_score = score
                            best_dx[i] = c_cos(ang)
                            best_dy[i] = c_sin(ang)
                if 0 <= sx3 < fw and 0 <= sy3 < fh:
                    val = field_data[sx3, sy3]
                    if val > 0.01:
                        score = val / (1.0 + 0.75)
                        if score > best_score:
                            best_score = score
                            best_dx[i] = c_cos(ang)
                            best_dy[i] = c_sin(ang)