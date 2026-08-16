---
name: pygame-debug
description: Diagnose why objects, resources, or effects are invisible in pygame simulations and games. Use when debugging rendering issues, missing entities, or invisible elements in pygame-based projects.
---

# Pygame Debug: Invisible Elements

Common causes and fixes for invisible or barely visible elements in pygame simulations.

## When to Use

- Objects/resources/effects are not visible on screen
- Entities exist in code but don't render
- Colors appear too dark or washed out
- Sprites/blits show but are transparent or near-black
- Simulation runs but screen appears empty

## Diagnosis Checklist

### 1. Config/Data Issues (Most Common)

Check if the data source is empty or null:

```python
# Problem: sources not defined
{ "sources": null }

# Fix: provide actual data points
{ "sources": [[200, 150, 0.9], [500, 300, 0.8]] }
```

**Verify:** Print/log the data structure before rendering:
```python
print(f"grid range: {grid.min():.3f} - {grid.max():.3f}")
print(f"nonzero cells: {(grid > 0.01).sum()} / {grid.size}")
```

### 2. Value Range → Color Mapping

Low values produce near-black colors:

```python
# Problem: values 0.0-0.25 map to very dark green
color = (30 + value * 80)  # → 30-50 out of 255

# Fix: boost the mapping or clamp minimum
color = (20 + value * 180)  # → 20-200 out of 255
```

**Rule of thumb:** If `value * multiplier < 30`, the pixel will be nearly invisible on black background.

### 3. Coordinate System Mismatch

Grid vs pixel coordinates:

```python
# Grid: (col, row) or (x, y) in tile units
# Pixels: (px, py) = (col * tile, row * tile)

# Problem: passing pixel coords to grid lookup
grid_value = grid[pixel_y][pixel_x]  # Wrong!

# Fix: convert first
grid_value = grid[y // tile][x // tile]
```

### 4. Surface/Blit Order

Later draws overwrite earlier ones:

```python
# Problem: field drawn, then black rect drawn on top
screen.fill((0, 0, 0))  # Clears everything
draw_field(screen)
screen.fill((0, 0, 0), panel_rect)  # Covers part of field!

# Fix: draw to subsurfaces or check rect bounds
```

### 5. Alpha/Transparency

`SRCALPHA` surfaces and `pygame.BLEND_*` flags:

```python
# Problem: alpha surface blitted without flag
cell_surf = pygame.Surface((w, h), pygame.SRCALPHA)
# ... draw transparent circles ...
screen.blit(cell_surf, (0, 0))  # May appear invisible

# Fix: ensure background is opaque or use BLEND
screen.blit(cell_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
```

### 6. Scale/Tiling Issues

When tiling grid cells to pixels:

```python
# Problem: tile size > grid cell → gaps or overflow
c_tiled = np.repeat(np.repeat(c, tile, axis=0), tile, axis=1)
c_tiled = c_tiled[:width, :height]  # Must trim!

# Fix: always clamp to surface dimensions
```

### 7. Render Frequency

Conditional rendering may skip draws:

```python
# Problem: field only redrawn every 4 frames
if self._bg_frame % 4 == 0:
    self._draw_field(surface)
else:
    surface.blit(self._bg, (0, 0))  # Uses cached (possibly empty) bg

# Fix: ensure first frame always draws
if self._bg is None or self._bg_frame % 4 == 0:
```

## Quick Debug Commands

```python
# Check grid statistics
print(f"grid shape: {grid.shape}")
print(f"grid dtype: {grid.dtype}")
print(f"min: {grid.min():.4f}, max: {grid.max():.4f}, mean: {grid.mean():.4f}")
print(f"above 0.01: {(grid > 0.01).sum()}")
print(f"above 0.1: {(grid > 0.1).sum()}")

# Check surface
print(f"surface size: {surface.get_size()}")
print(f"surface flags: {surface.get_flags()}")

# Dump raw pixel sample
arr = pygame.surfarray.pixels3d(surface)
print(f"pixel at (100,100): {arr[100, 100]}")
```

## Common Patterns in LIFE2-GPT

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Empty field | `sources: null` | Add source tuples to config |
| Dim food | Low values + dark color map | Increase `strength` or color multiplier |
| Food disappears | No regen without sources | Add sources, check `_regen()` |
| Cells visible, food not | Field drawn before black fill | Check draw order in renderer |
| Half screen black | Panel rect covers field | Use subsurface or adjust coords |

## Prevention

1. **Always log grid stats** on first render frame
2. **Use visible test colors** during development (bright red/green)
3. **Validate config** on load — warn if `sources` is empty
4. **Draw a bright test pixel** at known location to verify pipeline
