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
- `main.py` — entry point, UI, sound, sim loop, seasonal temperature/food-regen interpolation, time-lapse recording
- `cell.py` — `Cell` (14-phase step), `Corpse`, diet color, sound playback, viral infection, herd behavior, epigenetics
- `genome.py` — `Genome` (`__slots__`), `clone_mutate(temperature=...)`, learning parameters, epigenetics
- `config.py` — all balance constants, L10N, season/food color tables, biome system
- `field.py` — `ResourceField`: food grid, diffusion, decay, seasonal color draw, biomes, nutrient clusters
- `memory.py` — `CellMemory`: per-class threat/coop learning
- `spatial.py` — spatial hash grid for neighbor queries (Cython-optional)
- `ui.py` — `Slider`, `PopulationGraph` (pop-by-species visualization)
- `hotkeys.py` — `HotkeyState`, `handle_key`, `TEMPLATES`
- `sim_core.pyx` — optional Cython hot-loop acceleration
- `saveload.py` — JSON save/load
- `logger.py` — CSV population logging
- `file_utils.py` — file locking utilities
- `build_exe.py` — PyInstaller build script
- `cython_build_and_run.py` — helper to build and run with Cython

## Cython caveats (Windows)
- Kill all `python.exe` processes before rebuilding — Windows locks `.pyd` files.
- May need Administrator to overwrite the `.pyd`.
- `rand()` returns 0..32767 (NOT 2147483647) — always divide by `RAND_MAX`.
- `sim_core.pyx` duplicates config constants as `cdef` — rebuild the `.pyd` after editing either `config.py` or `sim_core.pyx` for changes to take effect.
- Build with: `python setup_sim_core.py build_ext --inplace`

## Cell lifecycle (`cell.py`)
`step()` runs 14 phases per tick: sensory → reaction → pack → movement → feeding → combat → metabolism → stress → level → social → aging → disease → migration → temperature.

`Cell.divide_phase(cells, grid, field.temperature)` → `divide(temperature)` → `Genome.clone_mutate(temperature)`.

**New features in cell.py:**
- **Viral infection system**: `infected`, `infection_timer`, `virus_type`, `virus_contagious`, `cure_state` fields
- **Herd tendency**: cells with `herd_tendency > 0.3` follow same-class neighbors
- **Cautious behavior**: ZOOP cells with low energy may flee randomly based on `cautious` gene
- **Epigenetics**: heritable trait expression level (0.0–1.0) passed to offspring
- **Corpse class**: decomposes over `DECOMPOSITION_TICKS`, leaves nutrient clusters

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

**New genome fields:**
- `learning_rate` (0.001–0.2): how fast cell adapts from experience
- `memory_size` (5–50): max memorised events
- `herd_tendency` (0.0–1.0): tendency to follow same-class cells
- `cautious` (0.0–1.0): probability to flee when low energy
- `epigenetics` (0.0–1.0): heritable trait expression level

## Food system (`field.py`, `config.py`)
- **Decay**: field decays at `FOOD_DECAY_RATE` (0.001/tick, ~50% per 693 ticks).
- **Lifetime**: `FOOD_LIFETIME_TICKS=3000` — after this, food retains ~5% of value.
- **Seasonal color**: `SEASON_FOOD_COLORS` (RGB 0..1) interpolated between current and next season via `field.draw(season=, season_progress=, next_season=)`.
- **Temperature factor**: `_get_temp_regen_factor()` returns 0 below freeze (0.222), otherwise linear with temperature.
- **Carrying capacity**: regen scales down at high cell density (20% at max density).

**New biome system:**
- 5 biomes: `foresta` (forest), `deserto` (desert), `ocean`, `mountains`, `swamp`
- Each biome has unique: regen multiplier, hotspot boost, temperature range, resource scatter
- Biomes adjust per season (spring/summer/autumn/winter effects)
- `ResourceField.analyze_biome_distribution()` for stats

**Nutrient clusters (from dead cells):**
- Organic puddle-shaped masks with multi-frequency sine + noise
- Feed field via `CORPSE_NUTRIENT_FIELD_RATE`
- Boost consumption within `CORPSE_NUTRIENT_BOOST_RADIUS`
- Fade at `CORPSE_NUTRIENT_FADE` per tick

## Temperature system
- Driven by season base + slider bias, smoothed by `TEMP_SMOOTH_RATE=0.01`/tick.
- Affects: food regen, movement speed, metabolism, energy penalty at extremes.
- Slider range: -10°C to +35°C (internal 0.0–1.0).
- Movement speed: cold slows (0.4× at 0°C), heat speeds then slows at extreme (1.2× at 0.8, 0.7× at 1.0)

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
BASE_LIFESPAN_TICKS = 3000
LIFESPAN_PER_MASS = 200
AGING_METABOLISM_FACTOR = 0.5
FOOD_DECAY_RATE = 0.001
TEMP_SMOOTH_RATE = 0.01
TEMP_ENERGY_PENALTY = 0.02
MAJOR_DIET_RATE = 0.5
MAJOR_SENSE_RATE = 0.5
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
| G | Toggle energy bars |
| V | Toggle level bars |
| Z | Zoom to selected cell |
| B | Toggle follow camera |
| F | Recenter camera (was Home) |
| Home | Recenter camera + reset zoom |
| L | Toggle language (ru/en) |
| M / Alt+M | Cycle music / SFX volume |
| Tab | Toggle info panel |
| T | Toggle time-lapse mode |
| H | Toggle minimap |
| Ctrl+M | Toggle memory panel |
| Esc | Deselect / quit |

## Sound system
- 10 MP3 SFX in `src/sounds/`: eating, divide, death, mutation, lvl_up, lvl_down, heartbeat, gurgle, gurgle2, injection, mass_down.
- Background music: tries `base64.txt` → existing `bg_music.mp3` → `heartbeat.mp3` fallback.
- `pygame.mixer.init(44100, -16, 2, 512)`
- Music fade-in over 5 seconds on start
- SFX volume cycling (M) and music volume cycling (Alt+M) with ping-pong 0→1→0

## Speciation system
- `cls = diet * 1000 + hash(rounded genome params) % 1000` — diet always separates classes.
- `refresh_class()` recomputes cls + color. Called on all manual mutations and divisions.
- Identical genomes share color/class; different diets are always different classes.

## Population graph (`ui.py`)
- `PopulationGraph(history_length=2000, sample_interval=10)` — reduced from 10000 for FPS recovery
- Season bands as tinted background with labels
- Per-class lines colored by diet color
- Total population line (YEL)
- Legend: diet group toggles (PHOT/ZOOP/POLY/Total) + per-class palette with scroll

## Time-lapse recording
- Toggle with **T** key
- Captures frames at `TIME_LAPSE_DEFAULT_FPS=30`
- Saves to `TIME_LAPSE_FRAMES_DIR="frames"`
- Max `TIME_LAPSE_MAX_FRAMES=10000`
- Default duration `TIME_LAPSE_DURATION_MIN=10` minutes

## Disease system
- `DISEASE_CHANCE=0.001` per tick to get infected
- `DISEASE_DURATION=500` ticks of sickness
- `DISEASE_METABOLISM_MULT=2.0` when sick
- `DISEASE_TRANSMISSION_RANGE=50.0` distance

## Minimum populations (extinction prevention)
- `PHOT_MIN_REQUIRED=2`
- `ZOOP_MIN_REQUIRED=1`
- `POLY_MIN_REQUIRED=2`

## Environment requirements
- Python ≥3.14 (`.python-version` pinned to 3.14)
- pygame ≥2.5.0, numpy
- `.venv/` is the project virtualenv
- No test suite — visual/interactive testing only
- `sys.path` insertion in `main.py` ensures imports work from bundled exe
- Cython 3.2.9+ for `sim_core.pyx`

## UI layout (two-column sidebar)
- Left column (Genes/Damage/Environment), Right column (Selected cell info/Memory/Minimap/Game Settings)
- Population graph with diet-group toggles and per-class palette (click to toggle, wheel to scroll)
- Smooth seasonal color interpolation for food field
- Minimap with click-to-pan and cell dots

## File locking
- `file_utils.py` provides `lock_file()` / `unlock_file()` for cross-process CSV/JSON safety
- Uses `fcntl` on Unix, no-op on Windows

## Build / packaging
- `build_exe.py` — PyInstaller spec: bundles `src/sounds/`, `base64.txt`, hides console
- `cython_build_and_run.py` — builds sim_core and launches main.py
- `setup_sim_core.py` — standalone Cython build script