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

# Порог движения, при превышении которого сетка считается "грязной"
_DIRTY_THRESHOLD = CELL_SIZE / 2


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


class SpatialGrid:
    """Спатиальная сетка с флагом грязности (dirty flag).

    Перестраивает сетку только когда клетки изменили позицию более чем
    на CELL_SIZE/2 или изменился состав списка клеток. Экономит создание
    numpy-массивов и перехеширование на тик, когда клетки почти не движутся.
    """

    def __init__(self, cells):
        self._cells = cells
        self._grid: GridType = {}
        self._positions: List[Tuple[float, float]] = []
        self._build()

    def _build(self):
        self._positions = [(c.x, c.y) for c in self._cells]
        if _HAVE_CY:
            xs = np.array([c.x for c in self._cells], dtype=np.float64)
            ys = np.array([c.y for c in self._cells], dtype=np.float64)
            self._grid = _cy_build(xs, ys)
        else:
            self._grid = {}
            for i, c in enumerate(self._cells):
                gx = int(c.x / CELL_SIZE)
                gy = int(c.y / CELL_SIZE)
                self._grid.setdefault((gx, gy), []).append(i)

    def is_dirty(self) -> bool:
        """True, если сетка устарела (клетки сдвинулись или их стало больше/меньше)."""
        if len(self._positions) != len(self._cells):
            return True
        threshold = _DIRTY_THRESHOLD
        for i, c in enumerate(self._cells):
            px, py = self._positions[i]
            if abs(c.x - px) > threshold or abs(c.y - py) > threshold:
                return True
        return False

    def refresh(self):
        """Перестроить сетку, если она грязная. Иначе пропустить."""
        if self.is_dirty():
            self._build()

    @property
    def grid(self) -> GridType:
        return self._grid


def get_neighbors(grid, x: float, y: float, radius: int = 2) -> Tuple[int, ...]:
    """Return indices of cells in neighboring grid cells."""
    if _HAVE_CY:
        return tuple(_cy_neighbors(grid, float(x), float(y), int(radius)))

    result = []
    gx = int(x / CELL_SIZE)
    gy = int(y / CELL_SIZE)
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            key = (gx + dx, gy + dy)
            if key in grid:
                result.extend(grid[key])
    return tuple(result)


class SpatialGrid:
    """Спиральная решётка с флагом «грязности».

    Перестраивается только когда клетки сдвинулись больше чем на
    CELL_SIZE / 2 или изменился их список. В остальных случаях
    перестраивать решётку не нужно — соседи ищутся в кэшированной решётке.
    """

    def __init__(self, cells):
        self._cells = cells
        self._grid: GridType = {}
        self._positions: List[Tuple[float, float]] = []
        self._build()

    def _build(self):
        self._positions = [(c.x, c.y) for c in self._cells]
        if _HAVE_CY:
            xs = np.array([c.x for c in self._cells], dtype=np.float64)
            ys = np.array([c.y for c in self._cells], dtype=np.float64)
            self._grid = _cy_build(xs, ys)
        else:
            self._grid = {}
            for i, c in enumerate(self._cells):
                gx = int(c.x / CELL_SIZE)
                gy = int(c.y / CELL_SIZE)
                self._grid.setdefault((gx, gy), []).append(i)

    def is_dirty(self) -> bool:
        """True, если список клеток изменён или любая клетка сдвинулась больше CELL_SIZE/2."""
        if len(self._positions) != len(self._cells):
            return True
        threshold = CELL_SIZE / 2
        for i, c in enumerate(self._cells):
            px, py = self._positions[i]
            if abs(c.x - px) > threshold or abs(c.y - py) > threshold:
                return True
        return False

    def refresh(self):
        """Перестроить решётку, если клетки сдвинулись."""
        if self.is_dirty():
            self._build()

    @property
    def grid(self) -> GridType:
        return self._grid