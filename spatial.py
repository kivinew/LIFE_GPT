# Spatial grid implementation for LIFE_GPT
# Pure Python with optional Cython acceleration
import numpy as np
from typing import Dict, List, Tuple
from config import CELL_SIZE

try:
    from sim_core import build_spatial_grid as _cy_build, get_neighbors as _cy_neighbors
    _HAVE_CY = True
except Exception:
    _HAVE_CY = False

GridType = Dict[Tuple[int, int], List[int]]


def build_spatial_grid(cells):
    """Build a spatial hash grid for fast neighbor lookups."""
    if _HAVE_CY:
        xs = np.array([c.x for c in cells], dtype=np.float64)
        ys = np.array([c.y for c in cells], dtype=np.float64)
        return _cy_build(xs, ys)

    grid: GridType = {}
    for i, c in enumerate(cells):
        gx = int(c.x / CELL_SIZE)
        gy = int(c.y / CELL_SIZE)
        grid.setdefault((gx, gy), []).append(i)
    return grid


def get_neighbors(grid, x: float, y: float, radius: int = 2) -> List[int]:
    """Return indices of cells in neighboring grid cells."""
    if _HAVE_CY:
        return _cy_neighbors(grid, float(x), float(y), int(radius))

    result: List[int] = []
    gx = int(x / CELL_SIZE)
    gy = int(y / CELL_SIZE)
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            key = (gx + dx, gy + dy)
            if key in grid:
                result.extend(grid[key])
    return result