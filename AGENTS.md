# AGENTS.md — LIFE_GPT Cellular Evolution Simulator

Pygame cellular evolution sim. See `CLAUDE.md` for additional project context.

## Quick start
```bash
python main.py                      # run the sim
python setup.py build_ext --inplace  # Cython extension (optional, ~10x kernel speedup)
python build_exe.py                 # build standalone .exe (requires PyInstaller)
```

## Module layout
All source is flat in the repo root. No subdirectories.
- `main.py` — entry point, UI, sound, sim loop, seasonal temperature/food-regen interpolation
- `cell.py` — `Cell` (14-phase step), `Corpse`, diet color, sound playback
- `genome.py` — `Genome` (`__slots__`), `clone_mutate(temperature=...)`
- `config.py` — all balance constants, L10N, season/food color tables
- `field.py` — `ResourceField`: food grid, diffusion, decay, seasonal color draw
- `memory.py` — `CellMemory`: per-class threat/coop learning
- `spatial.py` — spatial hash grid for neighbor queries
- `ui.py` — `Slider`, `PopulationGraph` (pop-by-species visualization)
- `hotkeys.py` — `HotkeyState`, `handle_key`, `TEMPLATES`
- `sim_core.pyx` — optional Cython hot-loop acceleration
- `saveload.py` — JSON save/load
- `logger.py` — CSV population logging

## Cython caveats (Windows)
- Kill all `python.exe` processes before rebuilding — Windows locks `.pyd` files.
- May need Administrator to overwrite the `.pyd`.
- `rand()` returns 0..32767 (NOT 2147483647) — always divide by `RAND_MAX`.
- `sim_core.pyx` duplicates config constants as `cdef` — rebuild the `.pyd` after editing either `config.py` or `sim_core.pyx` for changes to take effect.

## Cell lifecycle (`cell.py`)
`step()` runs 14 phases per tick: sensory → reaction → pack → movement → feeding → combat → metabolism → stress → level → social → aging → disease → migration → temperature.

`Cell.divide_phase(cells, grid, field.temperature)` → `divide(temperature)` → `Genome.clone_mutate(temperature)`.

## Mutation system (`genome.py`)
`clone_mutate(temperature=TEMP_MUT_DEFAULT)` drives all genetic drift. Temperature biases the spectrum:
- **Cold** (T < 0.5): favors **diet/niche** mutations (ecological shifts).
- **Hot** (T > 0.5): favors **motoric/sensory** drift.
- Multiplier range: `[1 - TEMP_MUT_SWING, 1 + TEMP_MUT_SWING]` = `[0.5, 1.5]`, never zero.

Major mutation (~`major_mut_rate`): single coherent leap — either a **diet switch** or a **sense-organ jump**, never both. Diet switch resets speed/sense to `DIET_DEFAULT_SPEED/SENSE` for the new niche.

Diet transitions are asymmetrically weighted (circular niche cycle PHOT→POLY→ZOOP→PHOT):
- Forward (PHOT→POLY, POLY→ZOOP, ZOOP→POLY): weight **0.3**
- Reverse: weight **0.1**

Minor path: ±15% jitter on all numeric genes via `drift()`.

## Food system (`field.py`, `config.py`)
- **Decay**: field decays at `FOOD_DECAY_RATE` (0.001/tick, ~50% per 693 ticks).
- **Lifetime**: `FOOD_LIFETIME_TICKS=3000` — after this, food retains ~5% of value.
- **Seasonal color**: `SEASON_FOOD_COLORS` (RGB 0..1) interpolated between current and next season via `field.draw(season=, season_progress=, next_season=)`.
- **Temperature factor**: `_get_temp_regen_factor()` returns 0 below freeze (0.222), otherwise linear with temperature.

## Temperature system
- Driven by season base + slider bias, smoothed by `TEMP_SMOOTH_RATE=0.01`/tick.
- Affects: food regen, movement speed, metabolism, energy penalty at extremes.
- Slider range: -10°C to +35°C (internal 0.0–1.0).

## Key balance values (config.py)
```python
ENERGY_MASS_COEFF = 4.5
COMBAT_DAMAGE_GAIN = 0.8
PREDATOR_METABOLISM_MULT = 0.55
FEED_EFFICIENCY_BASE = 22.0
PHOT_FEED_EFFICIENCY = 1.0
POLY_FEED_EFFICIENCY = 0.7
LEVEL_UP_THRESHOLD = 0.60
DIVIDE_ENERGY_RATIO = 0.95
DIVIDE_MIN_AGE = 1000
MAX_LEVEL = 10
MAX_CELLS = 500
```

## Hotkeys
| Key | Action |
|-----|--------|
| Space | Pause |
| A / S | Add / select mode |
| C | Clear all cells |
| R | Reset resource field |
| F5 / F | Save / load cells |
| 1/2/3 | Set diet (selected), apply defaults, sync sliders |
| Ctrl+1/2/3 | Spawn template cell |
| Q/W/E | Set interaction (0.2/0.5/0.8) |
| +/- | Adjust speed |
| ↑/↓ | Adjust sense |
| X | Mutate selected |
| D | Delete selected |
| E | Toggle energy bars |
| V | Toggle level bars |
| Z | Zoom to selected cell |
| B | Toggle follow camera |
| Home | Recenter camera |
| L | Toggle language (ru/en) |
| M / Alt+M | Cycle music / SFX volume |
| Tab | Toggle info panel |

## Sound system
- 10 MP3 SFX in `src/sounds/`: eating, divide, death, mutation, lvl_up, lvl_down, heartbeat, gurgle, gurgle2, injection, mass_down.
- Background music: tries `base64.txt` → existing `bg_music.mp3` → `heartbeat.mp3` fallback.
- `pygame.mixer.init(44100, -16, 2, 512)`

## Speciation system
- `cls = diet * 1000 + hash(rounded genome params) % 1000` — diet always separates classes.
- `refresh_class()` recomputes cls + color. Called on all manual mutations and divisions.
- Identical genomes share color/class; different diets are always different classes.

## Environment requirements
- Python ≥3.14 (`.python-version` pinned to 3.14)
- pygame ≥2.5.0, numpy
- `.venv/` is the project virtualenv
- No test suite — visual/interactive testing only
- `sys.path` insertion in `main.py` ensures imports work from bundled exe

## UI layout (two-column sidebar)
- Left column (Genes/Damage/Environment), Right column (Selected cell info/Memory/Minimap/Game Settings)
- Population graph with diet-group toggles and per-class palette (click to toggle, wheel to scroll)
- Smooth seasonal color interpolation for food field
