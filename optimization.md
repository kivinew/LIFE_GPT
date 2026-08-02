# Optimization Plan for LIFE_GPT

## Current State
- Reduced the history length of the population graph (`ui.PopulationGraph`) from 10,000 to 2,000 ticks (sample_interval unchanged at 10).  
  This change is already committed (`a7d4a63`) and pushed to the remote repository.

## Graph‑Specific Optimizations (already applied / can be extended)
1. **Shorter history** – fewer points to iterate and draw each frame.  
2. **Optional: update graph less frequently** – only update the graph every N ticks (e.g., `if tick % GRAPH_UPDATE_INTERVAL == 0:`).  
3. **Cache the graph surface** – render the graph to an off‑screen `Surface` when its data changes, then `blit` that surface each frame instead of redrawing lines and axes.  
4. **Toggle visibility** – allow the user to hide the graph entirely (e.g., via a hotkey) to remove its cost completely.

---

## Further Performance Improvements (ordered by expected impact)

### 1. Cache Cell Surfaces (blit instead of draw.circle)
- **Problem:** `pygame.draw.circle` is called for every living cell each frame – costly O(N) calls.
- **Solution:** Pre‑render a surface for each unique `(cell_class, radius)` pair and reuse it via `blit`.
- **Implementation Sketch:**
  ```python
  _cell_surf_cache = {}
  def get_cell_surface(cls, radius):
      key = (cls, int(radius))
      surf = _cell_surf_cache.get(key)
      if surf is None:
          surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
          color = diet_color(diet_of_cls, cls)   # obtain color
          pygame.draw.circle(surf, color, (radius, radius), radius)
          _cell_surf_cache[key] = surf
      return surf
  ```
- **Expected gain:** +30‑70 % FPS when > 300 cells, especially when many cells share the same class/size.

### 2. Dirty‑Rectangle Updates (LayeredDirty / RenderUpdates)
- **Problem:** The entire screen is cleared and redrawn each frame, even though most of the background and UI rarely changes.
- **Solution:** Use `pygame.sprite.LayeredDirty` (or `RenderUpdates`) to track which sprites changed and update only those rectangles.
- **Steps:**
  - Put all drawable entities (cells, corpses, nutrient clusters, UI elements) into dirty sprite groups.
  - Each frame call `dirty = all_sprites.draw(screen)` and then `pygame.display.update(dirty)`.
  - For static background, blit it only within the dirty rectangles.
- **Expected gain:** 2‑5× FPS increase when the frame‑to‑frame changes are localized (common in this simulator).

### 3. Fixed‑Step Simulation with Decoupled Rendering
- **Problem:** When the simulation logic becomes heavy, the main loop tries to keep up with rendering speed‑simulation to stall.
- time step, causing FPS drops and stutter.
- **Solution:** Separate logic updates from rendering using a fixed timestep (e.g., 1/60 s). Accumulate real time and perform as many logic steps as needed, rendering at the monitor’s refresh rate.
- **Pseudo‑code:**
  ```python
  FIXED_DT = 1/60.0
  accumulator = 0.0
  while running:
      frame_time = clock.tick(60) / 1000.0
      accumulator += frame_time
      while accumulator >= FIXED_DT:
          tick += 1
          if tick % GRAPH_UPDATE_INTERVAL == 0:
              pop_graph.update(tick, cells)
          for c in cells:
              if c.energy > 0:
                  c.step()
          accumulator -= FIXED_DT
      render_frame()
      pygame.display.flip()
  ```
- **Expected gain:** Stable FPS even under heavy load; simulation may run slower in‑game time but visual smoothness remains.

### 4. Reduce Lifespan of Dead‑Cell Entities
- **Problem:** Corpses and nutrient clusters persist for hundreds of ticks, adding to the draw list even after cell death.
- **Adjustments in `config.py`:**
  - Decrease `DECOMPOSITION_TICKS` (e.g., from 300 → 150) so corpses disappear faster.
  - Increase `CORPSE_NUTRIENT_FADE` (closer to 1.0) so nutrient clusters fade quicker.
  - Optionally raise the draw threshold for clusters (`CORPSE_NUTRIENT_DRAW_MAX`) to skip rendering tiny clusters.
- **Expected gain:** Fewer objects to draw after a massacre, quicker FPS recovery.

### 5. Vectorize Neighbor Calculations (NumPy) – for pure‑Python path
- **If Cython is disabled (`_HAVE_SIM_CORE == False`)**, the double loop over cells for sensing/interactions becomes a bottleneck.
- **Solution:** Convert cell positions to NumPy arrays and compute distance matrices in bulk.
- **Sketch:**
  ```python
  xs = np.array([c.x for c in cells])
  ys = np.array([c.y for c in cells])
  dx = xs[:, None] - xs[None, :]
  dy = ys[:, None] - ys[None, :]
  dist2 = dx*dx + dy*dy
  mask = dist2 < INTERACTION_RADIUS**2
  np.fill_diagonal(mask, False)
  # Use mask to sum interaction terms, apply aggression/coop, etc.
  ```
- **Expected gain:** Order‑of‑magnitude speedup for the sensing phase when running in pure Python.

### 6. Cache Static UI Elements
- **Problem:** Each frame the UI re‑renders text for slider labels, toggles, etc., even when unchanged.
- **Solution:** Render static text once to a surface and `blit` it; only re‑render when the value actually changes.
- **Expected gain:** Minor (a few milliseconds per frame) but adds up, especially on lower‑end hardware.

### 7. Profiling‑Driven Fine Tuning
- **Regularly run a profiler** (e.g., `cProfile` or `pygame`'s built‑in timing) to identify remaining hot spots.
- Typical hot spots after the above steps:
  - `cell.step()` (sensing loops)
  - Graph drawing (if not cached/surface‑blitted)
  - Collision or interaction handling
- Apply targeted optimizations (e.g., early‑exit checks, spatial grid tuning, reducing sensor rays).

---

## Prioritized Implementation Steps
1. **Cell surface caching** – biggest win for rendering many cells.
2. **Dirty‑rect update system** – reduces redundant background/UI redraws.
3. **Fixed‑step simulation loop** – stabilizes FPS under load.
4. **Adjust corpse/cluster lifetimes** – speeds up FPS recovery after die‑offs.
5. **(If needed) Vectorize sensing with NumPy** – only if you observe the Python sensing path as a bottleneck.
6. **Cache static UI & graph surface** – polish improvements.
7. **Continuous profiling** – iterate on remaining hot spots.

---

## How to Test Improvements
- Launch the simulator with a high initial cell count (e.g., via spawn templates or cheat).
- Observe FPS (shown in the Tab stats panel or via `pygame.time.Clock.get_fps()`).
- Clear the world (Hotkey `C`) and note how quickly FPS returns to baseline.
- Use the profiler snippet (insert into main loop temporarily) to verify that the targeted function’s time has dropped.
- Verify that visual correctness is preserved (cell colors, behaviors, graph shape) after each change.

---

## Closing Note
The graph optimization already yields a noticeable improvement in FPS recovery. Applying the steps above in order will transform the simulator from being render‑bound at moderate populations to staying smooth even with several hundred cells, while keeping the core evolutionary dynamics unchanged.