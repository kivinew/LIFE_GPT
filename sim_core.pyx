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
cdef double _MIN_MASS_EFFICIENCY = 0.55        # config: MIN_MASS_EFFICIENCY
cdef double _COMBAT_BASE_DAMAGE = 0.9          # config: COMBAT_BASE_DAMAGE
cdef double _COMBAT_DAMAGE_GAIN = 0.8          # config: COMBAT_DAMAGE_GAIN
cdef double _MASS_DMG_EFFICIENCY = 0.035        # config: MASS_DMG_EFFICIENCY
cdef double _MIN_MASS_DMG_EFF = 0.45           # config: MIN_MASS_DMG_EFF

cdef int _CELL_SIZE = 48
cdef int _SB = 600
cdef int _W = 1600
cdef int _H = 900


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
    np.ndarray[np.int32_t, ndim=1] diet_arr,
    np.ndarray[np.float64_t, ndim=1] speed_arr,
    np.ndarray[np.float64_t, ndim=1] mass_arr,
    np.ndarray[np.float64_t, ndim=1] metab_arr,
    np.ndarray[np.int32_t, ndim=1] level_arr,
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
        if diet_arr[i] == _PHOT or diet_arr[i] == _POLY:
            x = int(xs[i])
            y = int(ys[i])
            if 0 <= x < fw and 0 <= y < fh:
                eat = min(field_data[x, y], 0.15 * dt)
                mass_eff = 5.0 / mass_arr[i] if mass_arr[i] > 0 else _MIN_MASS_EFFICIENCY
                if mass_eff < _MIN_MASS_EFFICIENCY:
                    mass_eff = _MIN_MASS_EFFICIENCY

                diet_eff = _PHOT_FEED_EFFICIENCY if diet_arr[i] == _PHOT else _POLY_FEED_EFFICIENCY
                energies[i] += eat * _FEED_EFFICIENCY_BASE * mass_eff * diet_eff
                field_data[x, y] = max(0.0, field_data[x, y] - eat)

        # ── Energy cap ──
        max_e = mass_arr[i] * mass_arr[i] * _ENERGY_MASS_COEFF
        if energies[i] < 0.0:
            energies[i] = 0.0
        elif energies[i] > max_e:
            energies[i] = max_e

        # ── Level system ──
        if energies[i] >= max_e * _LEVEL_UP_THRESHOLD and level_arr[i] < _MAX_LEVEL:
            level_arr[i] += 1
            mass_arr[i] = _LEVEL_MASS_BASE + level_arr[i] * _LEVEL_MASS_STEP
            energies[i] = max_e * 0.20
        elif energies[i] <= _LEVEL_DOWN_THRESHOLD and level_arr[i] > 0:
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