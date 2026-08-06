# LIFE_GPT Performance Optimization Plan

## Audit Summary

Profiled the full simulation loop across all 14 cell phases, rendering, field updates, and UI. Identified the following bottleneck categories ranked by expected FPS impact.

---

## Critical Bottlenecks

### 1. Per-Cell Surface Allocation in `draw_at()` — `cell.py:1011-1025`

**Problem:** Every living cell creates a new `pygame.Surface` with `SRCALPHA` and draws concentric gradient circles via a Python `for` loop — per frame. At 300+ cells this is the dominant cost.

**Fix:** Cache a pre-rendered surface per `(cls, radius)` pair. Build once on class creation / mutation, reuse via `blit`.

```python
# cell.py — module-level cache
_CELL_SURF_CACHE: dict[tuple[int, int], pygame.Surface] = {}

def _get_cell_surface(cls: int, radius: int) -> pygame.Surface:
    key = (cls, radius)
    surf = _CELL_SURF_CACHE.get(key)
    if surf is not None:
        return surf
    size = radius * 2 + 4
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = radius + 2, radius + 2
    for ri in range(radius, 0, -1):
        t = ri / radius
        alpha = int(255 * (1.0 - t * t))
        pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), ri)
    _CELL_SURF_CACHE[key] = surf
    return surf
```

Then in `draw_at()`: `surf.blit(_get_cell_surface(cls, r), (x - cx, y - cy))`.
Invalidate cache on `refresh_class()` (color change) or mass change > 1.

**Expected gain:** +30–70 % FPS at 300+ cells.

---

### 2. Minimap `set_at()` Per Cell — `main.py:1187-1197`

**Problem:** `pygame.Surface.set_at()` is a per-pixel Python call. Called once per cell + corpse per frame. At 300 cells this is 300+ slow Python calls.

**Fix:** Batch minimap pixels into a numpy array and use `pygame.surfarray.pixels3d` or pre-render to a small Surface via `blit` of cached dot surfaces.

```python
# Pre-render a 1x1 dot surface per diet class
_MINIMAP_DOTS = {}
for diet in (PHOT, ZOOP, POLY):
    s = pygame.Surface((1, 1))
    s.fill(diet_color(diet, 10))
    _MINIMAP_DOTS[diet] = s

# In draw loop — blit instead of set_at
for c in cells:
    if 0 <= c.x < world_w and 0 <= c.y < world_h:
        px, py = int(c.x * map_scale_x), int(c.y * map_scale_y)
        screen.blit(_MINIMAP_DOTS[c.genome.diet], (px, py))
```

**Expected gain:** +5–10 % FPS (minor but eliminates a Python-hot loop).

---

### 3. Spatial Grid Rebuild Every Tick — `spatial.py:16-28`

**Problem:** `build_spatial_grid()` iterates all cells and rebuilds the dict every tick, even when cell positions barely change.

**Fix:** Only rebuild when a cell has moved more than `CELL_SIZE / 2` since last build. Track a `_grid_dirty` flag; set it on cell creation, death, or position change exceeding threshold.

```python
# spatial.py
_GRID_DIRTY = True

def mark_grid_dirty():
    global _GRID_DIRTY
    _GRID_DIRTY = True

def build_spatial_grid(cells):
    global _GRID_DIRTY
    if not _GRID_DIRTY and _LAST_GRID is not None:
        return _LAST_GRID
    # ... existing build logic ...
    _LAST_GRID = grid
    _GRID_DIRTY = False
    return grid
```

Then in `cell.py`, call `mark_grid_dirty()` in `move_phase()` only if displacement exceeds threshold.

**Expected gain:** +5–15 % FPS when many cells are stationary.

---

### 4. Nutrient Cluster Rendering — `field.py:343-365`

**Problem:** Each nutrient cluster creates a new `pygame.Surface` per frame with nested circle drawing and sin/cos modulation.

**Fix:** Pre-render cluster surfaces when created (or when amount changes significantly), cache them, and only re-create when amount changes by > 10%.

```python
# field.py — in add_nutrient_cluster / step
_cluster_surf_cache = {}

def _get_cluster_surf(cx, cy, amount):
    key = (cx, cy, int(amount * 10))  # quantize amount
    surf = _cluster_surf_cache.get(key)
    if surf is not None:
        return surf
    # ... existing rendering logic ...
    _cluster_surf_cache[key] = surf
    # Prune cache if too large
    if len(_cluster_surf_cache) > 200:
        _cluster_surf_cache.clear()
    return surf
```

**Expected gain:** +3–8 % FPS when many corpses are decomposing.

---

### 5. Neighbor List Allocation — `spatial.py:31-43`

**Problem:** `get_neighbors()` creates a new list and calls `extend()` for each neighboring cell every time it's called. Called 14+ times per cell per tick.

**Fix:** Use a pre-allocated list buffer or return a tuple. Better: in the Cython path, return indices directly into the cells list without Python list construction.

```python
# Option A: return tuple (slightly faster iteration)
def get_neighbors(grid, x, y, radius=2):
    gx, gy = int(x / CELL_SIZE), int(y / CELL_SIZE)
    result = []
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            key = (gx + dx, gy + dy)
            if key in grid:
                result.extend(grid[key])
    return tuple(result)  # avoids list mutation overhead downstream
```

**Expected gain:** +2–5 % FPS (marginal but free).

---

### 6. Cython Coverage Gap — `sim_core.pyx`

**Problem:** The Cython extension only covers `apply_physics` (movement) and `apply_metabolism_and_feeding` (metabolism + field feeding). The expensive phases — sensing, combat, social, pack behavior, disease — still run in pure Python.

**Fix:** Extend `sim_core.pyx` with Cython-accelerated versions of:
- `sensory_phase` — ray sampling is embarrassingly parallel
- `combat_phase` — neighbor iteration + damage application
- `social_phase` — interaction logic

Start with `sensory_phase` (16 rays × N cells) as it's the most uniform loop.

**Expected gain:** 2–5× speedup on the covered phases when Cython is compiled.

---

### 7. Field Biome Dict Lookups Per Cell — `field.py:119-127`

**Problem:** `get_biome()`, `get_biome_multiplier()`, `get_biome_temperature()` do dict lookups on `(x, y)` tuples per call. Called from cell phases that run N × 14 times per tick.

**Fix:** Replace the `(x, y)` dict with a 2D numpy array of biome indices. Use integer encoding (0–4) instead of string lookups.

```python
# field.py — replace dict with array
BIOME_COUNT = 5
BIOME_MAP = {"foresta": 0, "deserto": 1, "ocean": 2, "mountains": 3, "swamp": 4}
self.biome_arr = np.zeros((w, h), dtype=np.uint8)  # fill at init

def get_biome_idx(self, x, y):
    return int(self.biome_arr[x, y])
```

**Expected gain:** +3–5 % FPS (reduces Python dict overhead).

---

### 8. `_pick_cell` Linear Scan — `main.py:175-183`

**Problem:** Click picking iterates all cells with `math.hypot()` per cell. O(N) per click.

**Fix:** Use the spatial grid to only check cells in the clicked grid cell and neighbors.

```python
def _pick_cell(cells, wx, wy, zoom, grid):
    gx, gy = int(wx / CELL_SIZE), int(wy / CELL_SIZE)
    candidates = []
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            candidates.extend(grid.get((gx + dx, gy + dy), []))
    best = None
    best_d = 0
    for j in candidates:
        c = cells[j]
        d = math.hypot(c.x - wx, c.y - wy)
        hit_r = max(3, int(2 + c.genome.mass * 1.5)) * zoom + 4
        if d < hit_r and d > best_d:
            best_d = d
            best = c
    return best
```

**Expected gain:** O(1) click pick instead of O(N).

---

### 9. Population Graph Redraw Every Frame — `ui.py`

**Problem:** The graph is redrawn every frame even when data hasn't changed.

**Fix:** Cache the graph surface. Only re-render when new data points are added (every `sample_interval` ticks). Blit the cached surface each frame.

```python
# PopulationGraph — add _dirty flag and cached surface
def update(self, tick, cells):
    if tick % self.sample_interval == 0:
        self._record(tick, cells)
        self._dirty = True

def draw(self, surf, x, y, w, h):
    if self._dirty or self._cache is None:
        self._cache = self._render()
        self._dirty = False
    surf.blit(self._cache, (x, y))
```

**Expected gain:** +2–3 % FPS (graph rendering is non-trivial).

---

### 10. `math.hypot` Called Excessively — Throughout `cell.py`

**Problem:** `math.hypot(dx, dy)` is called in every sensory ray, neighbor check, combat check, social check, and movement calculation. `hypot` does `sqrt(dx*dx + dy*dy)`.

**Fix:** Use squared distances for comparisons (eliminates sqrt). Only call `hypot` when the actual distance is needed (e.g., for direction normalization).

```python
# Instead of:
d = math.hypot(c.x - cp.x, c.y - cp.y)
if d < best_d:

# Use:
dx = c.x - cp.x
dy = c.y - cp.y
d_sq = dx * dx + dy * dy
if d_sq < best_d_sq:
    best_d_sq = d_sq
    best_d = d_sq  # or sqrt only when needed
```

**Expected gain:** +5–10 % FPS (hypot is called thousands of times per tick).

---

## Quick Wins (Low Effort, High Impact)

| # | Change | File | Effort | Impact |
|---|--------|------|--------|--------|
| 1 | Cache cell surfaces | `cell.py` | Medium | +30–70% FPS |
| 2 | Squared distance comparisons | `cell.py` | Low | +5–10% FPS |
| 3 | Batch minimap blits | `main.py` | Low | +5% FPS |
| 4 | Return tuples from get_neighbors | `spatial.py` | Low | +2% FPS |
| 5 | Cache graph surface | `ui.py` | Low | +2–3% FPS |
| 6 | Spatial grid dirty flag | `spatial.py` | Medium | +5–15% FPS |
| 7 | Pre-render cluster surfaces | `field.py` | Medium | +3–8% FPS |
| 8 | Extend Cython coverage | `sim_core.pyx` | High | 2–5× on covered phases |
| 9 | Biome array instead of dict | `field.py` | Medium | +3–5% FPS |
| 10 | Grid-based cell picking | `main.py` | Medium | O(1) pick |

---

## Implementation Priority Order

1. **Squared distance comparisons** — free win, apply everywhere in `cell.py`
2. **Cell surface caching** — biggest single FPS gain
3. **Batch minimap blits** — trivial change
4. **Graph surface caching** — trivial change
5. **Return tuples from get_neighbors** — trivial change
6. **Spatial grid dirty flag** — moderate effort, good payoff
7. **Cluster surface caching** — moderate effort
8. **Biome array** — moderate effort
9. **Grid-based cell picking** — moderate effort
10. **Extend Cython coverage** — highest effort, highest ceiling

---

## Testing Methodology

1. Launch with 400+ initial cells (spawn templates or cheat)
2. Observe FPS in bottom-right corner (Tab stats)
3. Clear world (`C`) and measure FPS recovery time
4. After each optimization, compare FPS at same cell count
5. Verify visual correctness: cell colors, behaviors, graph shape
6. Verify no regression in simulation logic (energy conservation, division, combat)

---

## Notes

- The existing Cython path (`_HAVE_SIM_CORE`) already provides 10× speedup for physics + metabolism. Extending it to cover sensory/combat/social phases would yield the largest single improvement.
- The `_CELL_SURF_CACHE` invalidation strategy should tie into `refresh_class()` — when a cell's class changes (diet mutation or genome drift), its cached surface must be regenerated.
- The `DECOMPOSITION_TICKS` and `CORPSE_NUTRIENT_FADE` values in `config.py` are already tuned for reasonable corpse lifetimes; no changes needed there for performance alone.
- The population graph history was already reduced from 10,000 to 2,000 ticks (commit `a7d4a63`).
