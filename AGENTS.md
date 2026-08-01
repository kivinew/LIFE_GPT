# AGENTS.md — LIFE_GPT Cellular Evolution Simulator

## Quick start
```bash
python main.py                      # run the sim
python setup.py build_ext --inplace  # build Cython extension (optional, ~10x speedup)
```

## Project overview

Pygame cellular evolution simulator. Cells have heritable genomes (17 traits) controlling behavior: speed, sense, mass, metabolism, mut_rate, diet, interact, divide_chance, dmg_phot/dmg_zoop/dmg_poly, lifespan_ticks, major_mut_rate, learning_rate, memory_size, herd_tendency, cautious.

- **Diet types**: PHOT=0 (photosynthesis), ZOOP=1 (predator), POLY=2 (both).
- **Continuous interaction**: float 0.01–1.0, not discrete. Thresholds in `config.py`: `COOP_INTERACT_THRESHOLD=0.34`, `AGGRO_INTERACT_THRESHOLD=0.75`.
- **Hotkeys**: Q=0.2, W=0.5, E=0.8 interaction. Rounded to 2 decimals to reduce genome fragmentation.
- **Spatial hash grid**: cell `cls` = `diet*1000 + hash(rounded genome params) % 1000`. Diet is bucketed, so different diets are ALWAYS different classes. Identical genomes share color/class. Manual edits (hotkeys 1/2/3, +/-/↑↓, Q/W/E, X) call `Cell.refresh_class()` to recompute cls + color.
- **Memory/learning**: cells track threat/coop scores per enemy/ally class via `memory.py` `CellMemory`. Adapt behavior from experience (`learning_rate`, `memory_size` genes).
- **Seasons**: 4 seasons × 2000 ticks, affect regen multiplier and temperature baseline. Temperature slider adds offset on top of season base.
- **Disease**: random infection chance, doubles metabolism, transmits at close range.
- **Migration**: rare random teleport events.

## Build pitfalls

### Cython on Windows
```bash
pip install Cython numpy
python setup.py build_ext --inplace
# Kill all python.exe processes before rebuilding .pyd (Access denied on Windows)
# May need Administrator for .pyd overwrite
```

**Critical MSVC RNG bug**: `rand()` returns 0..32767, NOT 2147483647. Always divide by `RAND_MAX`.

**Build files**: `setup.py` and `setup_sim_core.py` both build `sim_core`. The `.pyx` header references `setup_sim_core.py`.

### sim_core.pyx constants drift
**DANGER**: `sim_core.pyx` duplicates constants locally (Cython compile-time limitation). Some values diverge from `config.py`:
- `_FEED_EFFICIENCY_BASE = 17.0` vs config.py `25.0`
- `_COMBAT_DAMAGE_GAIN = 0.40` vs config.py `0.6`
- `_PHOT_FEED_EFFICIENCY = 1.0` vs config.py `1.2`

When changing balance values in `config.py`, also update `sim_core.pyx` lines 14–37.

### Module structure
No subdirectories — all source files in root. `sys.path` insertion in `main.py` is Windows-critical.

Hotkey logic lives in `hotkeys.py` (`HotkeyState`, `handle_key`, `TEMPLATES`) — `main.py` only syncs
locals after `handle_key`. Save/load JSON lives in `saveload.py` (`save_cells`, `load_saved_cells`).

### Corpses
Dead cells spawn a `Corpse` (cell.py) and release a nutrient cluster immediately. Corpse rots over
`DECOMPOSITION_TICKS=300`; POLY cells within `CORPSE_EAT_RADIUS=35` eat it (energy gain
`CORPSE_EAT_RATE=0.02`/tick), shrinking its mass until removed. `Corpse.done` triggers on age or `mass<=0`.

### Dead-cell nutrients
Death releases `mass²×ENERGY_MASS_COEFF×DECOMPOSITION_NUTRIENT_FRACTION` (0.45) as a nutrient cluster.
Clusters feed the field (`CORPSE_NUTRIENT_FIELD_RATE=0.03`/tick), fade at `CORPSE_NUTRIENT_FADE=0.99`,
and give a 2x `consume()` boost within `CORPSE_NUTRIENT_BOOST_RADIUS=8`. Drawn as circles up to
`CORPSE_NUTRIENT_DRAW_MAX=7` px. Minimap shows corpses (dark-red dots) and cluster density (via downscaled `field._fsurf`).

## Runtime gotchas

### Performance
After Cython, the sim kernel runs ~300 cells in <1ms. Rendering is the real bottleneck (~10 FPS). Don't optimize the kernel further.

### Temperature system
Temperature is driven by the slider + season base, and changes **gradually**:
`field.temperature` moves toward `clamp(season_temp + sl_temp._bias)` by `TEMP_SMOOTH_RATE=0.01`/tick.
Seasons interpolate toward the next season's base over `SEASON_LENGTH` ticks (no abrupt jumps).
Slider range is -10°C to +35°C, default 13°C. Internally 0.0–1.0 (`-10 + temp*45` maps to °C).

Temperature effects (all scale down with cold):
- Food regen: `field._get_temp_regen_factor()` (field.py).
- Movement: `move_phase` temp_speed_mult (cold slows).
- Metabolism: `metabolism_phase` multiplies cost by `TEMP_METABOLISM_MIN=0.5` at temp 0 → 1.0 at temp 1.
- Division: `can_divide` — probability factor `(temp-0.15)/0.5`, falls to 0 above `DIVIDE_MAX_TEMP`.

### Food regeneration
Slider shows an **effective** percentage (0–100%, base 30%), updated every tick as
`base% × season_mult × temp_factor` — so it visibly reacts to the temperature slider and seasons.
Dragging the slider sets the **base** % (temp/season factors scaled back out). Effective rate:
`base_regen = (regen_base/100) * REGEN_MAX_RATE(=0.1) * regen_mult_smooth`.
- `regen_base` is a local in `main.py`, separate from `sl_regen.val` (which is the display).
- `base_regen` moves toward the target by `REGEN_SMOOTH_RATE=0.03`/tick — no slider snaps.
- Season regen multiplier interpolates toward next season over `SEASON_LENGTH` (like temperature).
- Temp influence: `field._get_temp_regen_factor()` (field.py) — smooth curve: 0.3 at temp 0, peak
  1.2 at 0.6, 0.7 at temp 1.0 (discontinuity at 0.3 fixed 2026-08-01).
Final per-tick: `regen_amount = base_regen * temp_factor * dt` added to 200 random cells.

### UI layout (two-column sidebar)
```python
COL_W  = 285                     # column width
COL_LX = W - SB + 10             # left column start: 1010
COL_RX = COL_LX + COL_W + 10     # right column start: 1305
```
Left column boxes (compact slider layout, label at y-12, ticks at y+11):
- Genes: y=68, height=286 (8 sliders: speed, sense, mass, metabolism, divide_chance, diet, interact, zoophagy; 28px base / 40px labeled spacing)
- Damage: y=356, height=98 (3 sliders: dmg_phot/zoo/poly at 374/404/434)
- Environment: y=456, height=263 (6 sliders: regen=479, temp=519, diffuse=597, time=627, sfx=662, music=697)

**Slider ↔ selection binding**: speed/sense sliders are live-bound to the selected cell. Dragging
them mutates all selected cells (via `refresh_class()`); when nothing is dragged they show the
selected cell's values each frame. Diet slider keeps the old role (defaults for new cells; hotkeys
1/2/3 change selected cells). FPS is shown in the Tab stats panel (`clock.get_fps()`).

### Cell colors by diet
Color from `diet_color(diet, seed)` in cell.py — green=PHOT(120°), red=ZOOP(0°), purple=POLY(285°).
Each class (seed=cls) gets its own hue within the diet family (`_DIET_HUE_SPREAD`: ±35/±20/±30) PLUS
brightness+saturation variation, so different classes are always visually distinct (all 1000 tested
classes per diet produce unique colors) while diets stay recognizable and hue ranges never overlap.
Speciation children get diet color with random jitter. Identical genomes (same cls) share an exact
color. Diet legend sits under the population graph (legend_y=846); labels "Фототроф/Зоофаг/Полифаг" (L10N diet_0/1/2).

### Population graph (`ui.py` `PopulationGraph`)
- **Tick-based**: samples recorded every `sample_interval` sim-ticks (default 10), so the
  x-axis is sim time — independent of FPS/`time_scale`. History spans `history_length`
  ticks (default 10000 ≈ 5 seasons, `main.py` passes explicit values).
- **Season bands**: tinted background per season (`SEASON_LENGTH`=2000 ticks) with localized
  labels (`tr()`), colors in `_SEASON_COLOR`.
- Line colors use `diet_color(diet, cls)` (matches cell colors) via `cls_diet` map;
  YEL line = total.

### Sound system
10 MP3 files in `src/sounds/`: eating, divide, death, mutation, lvl_up, lvl_down, heartbeat, gurgle, gurgle2, injection.
`bg_music.mp3` is base64-encoded in `base64.txt`, extracted to disk on startup.

### Level-up mechanics
- Level-up at 60% energy (`LEVEL_UP_THRESHOLD=0.60`), drops to 20%.
- Mass: level 0=2.0, level 10=8.0 (`LEVEL_MASS_STEP=0.6`).
- Level-10 ZOOP elites divide without energy drain.

### Genome class (`genome.py`)
`Genome` uses `__slots__` (17 slots), NOT a dataclass. Values clamped in `__init__`. `clone_mutate()` does ±15% random perturbation per gene.
Default speed/sense depend on diet (`DIET_DEFAULT_SPEED/SENSE` in config.py): PHOT=min (0.5/10), POLY=mid (2.0/65), ZOOP=max (4.0/120) — applied only when speed/sense aren't passed explicitly.

### Cell class (`cell.py`)
`step()` runs 10 phases: sensory → predator behavior → reaction → pack behavior → movement → feeding → combat → metabolism → stress → energy/level/social. Imports `CellMemory` from `memory.py`.

### Dual execution path
`main.py` checks `_HAVE_SIM_CORE`: Cython path packs state into NumPy arrays → `simulate_step()`; Python path iterates `c.step()` per cell. Both import from `config.py`.

### Sound init
```python
pygame.mixer.init(44100, -16, 2, 512)
```

## Key hotkeys
| Key | Action |
|-----|--------|
| Space | Pause |
| A / S | Enter/exit add mode |
| C | Clear all cells |
| R | Reset resource field |
| Shift+Click | Place cell with current UI params (only in ADD mode; plain LMB in ADD mode also places) |
| LMB drag on empty world | Marquee box selection (Shift+box adds to selection) |
| Ctrl+Click / Shift+Click | Select cells |
| 1/2/3 | Set diet (selected) + apply class defaults (speed/sense) + sync sliders |
| Q/W/E | Set interaction mode (selected) |
| +/- | Adjust speed (selected) |
| ↑/↓ | Adjust sense (selected) |
| X | Mutate selected |
| D | Delete selected |
| Z | Zoom to selected cell (cam centers, zoom→3.0, follow ON) |
| B | Toggle follow camera on selected cell |
| Home | Recenter camera (disables follow) |
| F5 | Save to `saved_cells.json` |
| F | Load from `saved_cells.json` |
| L | Toggle language (ru/en) |
| M | Cycle music volume |
| Alt+M | Cycle SFX volume |
| Tab | Toggle top-left info/stats panel (default on) |
| Ctrl+1/2/3 | Spawn template cells |
| Wheel | Zoom in/out around cursor (0.3x–3x, anchored at viewport center) |
| MMB/RMB drag | Pan camera |

## Balance values (config.py, 2026-07-28)
```python
ENERGY_MASS_COEFF = 4.5
COMBAT_DAMAGE_GAIN = 0.6      # sim_core.pyx has 0.40 (DIVERGENT)
PREDATOR_METABOLISM_MULT = 0.75
AGGRO_INTERACT_THRESHOLD = 0.75
FEED_EFFICIENCY_BASE = 25.0    # sim_core.pyx has 17.0 (DIVERGENT)
```

## Environment requirements
- Python ≥3.14 (`.python-version` pinned)
- pygame ≥2.5.0, numpy
- Cython optional (10x speedup for sim kernel)
- `.venv/` is the project virtualenv
- No requirements.txt — uses `pyproject.toml` with minimal deps
- No test suite — visual/interactive testing only

## Localization
UI defaults to Russian (`LANG = "ru"` in config.py). Toggle with L key. Localization keys in `config.py` L10N dict. Diet slider labels: ["Ф", "З", "П"].

## Architecture docs
`CLAUDE.md` has detailed module responsibilities. `MEMORY.md` has architecture decisions. `SUGGESTION.md` for balance change specs.

---

AGENTS.md updated 2026-07-28
