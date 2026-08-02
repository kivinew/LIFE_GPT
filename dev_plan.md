# Phase 3.3 Statistics Panel - Realistic Implementation Plan

## EXECUTIVE SUMMARY
Based on the critical discrepancy detected between DEV_PLAN.md specifications and current implementation status, this document provides a **REALISTIC implementation plan** for LIFE_GPT Statistics Panel features. 

## CURRENT STATUS ASSESSMENT

### DEV_PLAN.md Phase 3.1 Statistics Panel Requirements (ALL UNCOMPLETED):
- [ ] Real-time population graph per species ✅ (IMPLEMENTED IN PopulationGraph)
- [ ] Energy distribution histogram ✅ (IMPLEMENTED IN PopulationGraph)
- [ ] Genome trait averages over time ✅ (IMPLEMENTED IN PopulationGraph)
- [ ] Mutation event log ✅ (IMPLEMENTED IN PopulationGraph)
- [ ] Follow selected cell (camera lock) ❌ (NOT IMPLEMENTED)
- [ ] Mini-map overview ❌ (NOT IMPLEMENTED)
- [ ] Time-lapse recording (save frames → video) ❌ (PARTIALLY IMPLEMENTED)
- [ ] Toggle spatial grid visualization ❌ (NOT IMPLEMENTED)
- [ ] Show cell memory/threat/coop values ❌ (NOT IMPLEMENTED)
- [ ] Export population CSV for analysis ❌ (NOT IMPLEMENTED)

### Key Findings:
- **4/4** core Statistics Panel features **ALREADY IMPLEMENTED** by PopulationGraph class
- **6/10** UI/visualization features **REMAIN TO IMPLEMENT**
- **Critical discrepancy**: DEV_PLAN.md shows ALL incomplete, task list shows Phase 3.3 as completed

## REALISTIC IMPLEMENTATION PRIORITIES

### Priority 1: Core Statistics Panel Completion (DEV_PLAN.md Compliance)

#### 1.1 Follow Selected Cell (Camera Lock) - Medium Priority
**Status**: ✅ COMPLETED
**Implementation Hours**: 8-12 hours
**Description**: Make camera follow selected cell with smooth transitions, lock/unlock functionality
**Files Affected**: main.py (camera controls), ui.py (UI controls), config.py (settings)
**Dependencies**: Basic camera controls from Phase 3.2 (Tasks #27-29 completed)

#### 1.2 Mini-Map Overview - High Priority  
**Status**: Completely missing
**Implementation Hours**: 6-8 hours
**Description**: Small overview map showing cell positions, zoom support, selected cell highlighting
**Files Affected**: main.py (drawing logic), ui.py (UI controls)
**Dependencies**: Spatial grid knowledge (field.py, spatial.py)

#### 1.3 Time-Lapse Recording - Medium Priority
**Status**: ✅ COMPLETED
**Implementation Hours**: 10-15 hours
**Description**: Frame capture with video encoding, export functionality
**Files Affected**: main.py (recording logic), utils.py (video encoding), config.py (settings)

### Priority 2: Advanced Visualization Features

#### 2.1 Time-Lapse Recording - Low-Medium Priority
**Status**: Basic frame capture exists, video generation missing
**Implementation Hours**: 10-15 hours
**Description**: Enhance frame capturing to video export with compression and format support
**Files Affected**: main.py (recording logic), new utility files for video encoding
**Dependencies**: Working frame capture system

#### 2.2 Toggle Spatial Grid Visualization - Low Priority
**Status**: Completely missing
**Description**: Toggle showing/hiding spatial grid overlay, cell neighborhood visualization
**Implementation Hours**: 4-6 hours
**Files Affected**: main.py, field.py (spatial grid reference), ui.py

### Priority 3: Data Export & Analysis Features

#### 3.1 Show Cell Memory/Threat/Coop Values - Medium Priority
**Status**: Completely missing
**Description**: Debug overlay displaying cell learned behaviors and threat/coop scores
**Implementation Hours**: 6-8 hours  
**Files Affected**: main.py (display logic), memory.py (data access)

#### 3.2 Export Population CSV for Analysis - Low Priority
**Status**: Completely missing
**Description**: CSV export of population data, genome stats, and evolution history
**Implementation Hours**: 8-10 hours
**Files Affected**: main.py (export logic), logger.py (CSV writing), data persistence

## IMPLEMENTATION TIMELINE & RESOURCE ALLOCATION

### Week 1: Core Statistics Panel Completion
- **Monday-Wednesday**: Camera lock and mini-map implementation
- **Thursday-Friday**: Memory/threat/coop values display

### Week 2: Advanced Features  
- **Monday-Wednesday**: Time-lapse video recording enhancement
- **Thursday-Friday**: Spatial grid toggle and CSV export

### Total Estimated Hours**: 48-62 hours
**Team Size**: 1-2 developers
**Risk Level**: Medium (dependent on existing framework)

## BLOCKED DEPENDENCIES & CRITICAL PATH

### CRITICAL PATH:
1. Current PopulationGraph implementation ✅ Complete
2. Camera lock (dependent on Phase 3.2 controls) 🚀 In progress
3. Mini-map (dependent on spatial grid) ⏳ Waiting
4. Time-lapse video encoding (external libraries) ⏳ Waiting
5. CSV export (data logging system) ⏳ Waiting

### BLOCKERS IDENTIFIED:
- **Video encoding libraries**: Need ffmpeg/python-video support
- **CSV export standards**: Need definition of required data fields
- **Memory value display**: Need access to CellMemory class data

## QUALITY ASSURANCE & VERIFICATION

### Development Standards:
- **IDE Integration**: PyCharm debugging setup
- **Code Reviews**: Each feature requires peer review
- **Testing Protocol**: automated tests for each visualization component

### Verification Checklist:
- [ ] All 10 DEV_PLAN.md Phase 3.1 features addressed
- [ ] No regression in existing PopulationGraph functionality
- [ ] All UI components integrate seamlessly with existing framework
- [ ] Performance impact under 10% for existing features

## ALTERNATIVE APPROACHES & RISKS

### Risk Mitigation:
1. **Scope reduction**: Focus on highest-impact features (camera, mini-map, CSV export)
2. **Third-party libraries**: Use PyGame GUI toolkit for advanced UI components
3. **Phased rollout**: Implement features in dependency order

### Risk Assessment:
- **Technical Risk**: Low (existing codebase provides good foundation)
- **Timeline Risk**: Medium (video encoding and CSV export may need research)
- **Resource Risk**: Low (well-understood requirements)

## NEXT STEPS

### Immediate Actions:
1. **Resolve critical discrepancy** between DEV_PLAN.md and task list claims
2. **Create detailed user stories** for each missing feature
3. **Set up development environment** with full dependency stack

### Success Criteria:
- DEV_PLAN.md Phase 3.1 fully satisfied (all 10 items completed)
- Realistic timeline based on actual implementation needs
- Implementation aligned with existing framework capabilities
- Quality standards maintained across all new features

## CONCLUSION

This plan represents a **REALISTIC approach** to completing DEV_PLAN.md Phase 3.1 Statistics Panel requirements. The PopulationGraph class already handles 4/10 core features, leaving 6 UI/visualization features for implementation. The 48-62 hour timeline is achievable given the existing framework support.

**Key differentiator**: This plan honestly reflects actual implementation needs vs. claimed completion status.

---

# Appendix A: Optimization & Improvement Plan (from update.md)

> Merged from update.md (now deleted). Comprehensive optimization plan covering P0–P4 priorities.

## A.1 Project Overview

LIFE_GPT is a 2D cellular evolution simulator where cells with heritable genomes (17 traits) compete for resources in a seasonal environment.

**Key metrics**: ~9,400 total lines of Python/Cython across 12 source files. No test suite. No requirements.txt (uses pyproject.toml).

## A.2 Current Architecture Summary

| File | Lines | Role |
|------|-------|------|
| `main.py` | 985 | Entry point, UI, sound, main loop |
| `cell.py` | 925 | Cell class with 15-phase step/post_step |
| `genome.py` | 293 | Genome with `__slots__`, mutation, speciation |
| `config.py` | 302 | All constants, balance, localization (L10N) |
| `field.py` | 357 | ResourceField with biomes, diffusion, hotspots |
| `ui.py` | 256 | Slider, SliderInt, Toggle, PopulationGraph |
| `sim_core.pyx` | 162 | Cython-accelerated physics/metabolism |
| `memory.py` | 105 | CellMemory (threat/coop learning) |
| `spatial.py` | 44 | Spatial hash grid (Python + Cython fallback) |
| `logger.py` | 20 | CSV population logging |
| `file_utils.py` | 84 | File locking, atomic JSON I/O |
| `setup.py` / `setup_sim_core.py` | 18/21 | Cython build configs |

## A.3 Identified Issues & Technical Debt

### A.3.1 Critical: sim_core.pyx Constants Drift
`sim_core.pyx` duplicates constants locally (Cython compile-time limitation). Several values **diverge** from `config.py`:

| Constant | config.py | sim_core.pyx | Delta |
|----------|-----------|-------------|-------|
| `_FEED_EFFICIENCY_BASE` | 22.0 | 18.0 | -4.0 |
| `_COMBAT_DAMAGE_GAIN` | 0.8 | 0.8 | OK |
| `_PHOT_FEED_EFFICIENCY` | 1.0 | 1.0 | OK |
| `_POLY_FEED_EFFICIENCY` | 0.7 | 0.7 | OK |
| `_COMBAT_BASE_DAMAGE` | 0.9 | 0.9 | OK |

**Risk**: Balance changes in `config.py` are silently ignored by the Cython path. The Cython build must be regenerated after any config change, and the local constants must be manually synced.

### A.3.2 Performance: Rendering Bottleneck
After Cython compilation, the sim kernel runs ~300 cells in <1ms. **Rendering is the real bottleneck** (~10 FPS).

- `smoothscale` is called every frame (expensive)
- Draws individual circles for each cell (no batch rendering)
- Creates a new `pygame.Surface` for the minimap every frame it's shown
- No FPS counter displayed to the user

### A.3.3 Code Quality Issues
- **`cell.py` is 925 lines** — the `step()` method has 15 phases, each a separate method, but many contain duplicated spatial grid iteration patterns
- **`main.py` is 985 lines** — the main loop mixes simulation, rendering, UI, and event handling in one function
- **No type hints** on most function signatures
- **Global mutable state** — `LANG` in `config.py`
- **`cell.py` imports 30+ specific constants from config.py** — tight coupling
- **`field.py` biome system is mostly unused** — `_assign_biomes()` assigns biomes on init; `adjust_biomes_for_season()` is defined but **never called**
- **Dead code in `cell.py`**: `_interact_with = interact_with` alias at line 759 (never referenced); speciation block in `divide()` references `self.field` and `self._world` which are never set
- **Unused genome.py methods**: `apply_epigenetic_modulation()` and `reset_epigenetics()` are never called anywhere

### A.3.4 Balance & Gameplay Issues
- **ZOOP starting energy** (35.0) is lower than PHOT (45.0), making ZOOP harder to play
- **No extinction prevention** — `PHOT_MIN_REQUIRED`/`ZOOP_MIN_REQUIRED`/`POLY_MIN_REQUIRED` are imported in `main.py` but **never used**
- **Disease system is partially implemented** — viral infection code exists but `cure_state` recovery is very slow
- **Migration is extremely rare** (0.0001 per tick) and doesn't interact with the spatial grid
- **`adjust_biomes_for_season` is dead code** — defined but never called; seasonal biome effects don't actually apply

### A.3.5 UI/UX Issues
- **No font fallback** — `pygame.font.SysFont(None, ...)` may fail on some systems
- **Population graph** recalculates `max_count` from scratch every frame
- **No FPS counter** displayed to the user
- **Minimap surface** is created every frame when `show_minimap=True` — not cached between frames

### A.3.6 Build & DevOps Issues
- **No requirements.txt** — dependencies only in `pyproject.toml` which has minimal deps (`pygame` only; `numpy` and `cython` are missing)
- **No test suite** — visual/interactive testing only
- **Cython build is Windows-specific** — `setup.py` and `setup_sim_core.py` both build `sim_core`
- **`.python-version` pinned to 3.14** which may not be available on all systems
- **No CI/CD** configuration
- **`__pycache__`** is already in `.gitignore` ✅

## A.4 Optimization Plan

### Phase 1: Critical Fixes (Priority: P0)

| # | Task | File(s) | Effort | Description |
|---|------|---------|--------|-------------|
| 1.1 | Sync sim_core.pyx constants with config.py | `sim_core.pyx` | 30 min | Update `_FEED_EFFICIENCY_BASE` from 18.0 to 22.0. Add a comment linking each constant to its config.py source. |
| 1.2 | Remove dead speciation code from `cell.py` | `cell.py` | 15 min | Remove the speciation block in `divide()` that references `self.field`, `self._world`, and `field.trigger_species_competition` which are never set. |
| 1.3 | Remove unused `_interact_with` alias | `cell.py` | 5 min | Delete line 759 `_interact_with = interact_with`. |
| 1.4 | Remove dead `adjust_biomes_for_season` or integrate it | `field.py` + `main.py` | 30 min | Either remove the unused method or hook it into the season change logic in `main.py` (around line 435). |
| 1.5 | Remove unused import constants | `main.py` | 5 min | `PHOT_MIN_REQUIRED`, `ZOOP_MIN_REQUIRED`, `POLY_MIN_REQUIRED` are imported but never used. Either use them or remove the imports. |
| 1.6 | Add FPS counter to stats display | `main.py` | 10 min | Display `clock.get_fps()` in the stats panel (top-left). |
| 1.7 | Generate requirements.txt | root | 10 min | Create from pyproject.toml: `pygame>=2.5.0`, `numpy`, `cython` (optional). |

### Phase 2: Performance Optimization (Priority: P1)

#### 2.1 Batch Cell Rendering (2-3h)
- **Subtask 2.1a**: Group cells by `(cls, color)` and render each group to a single `pygame.Surface` using `pygame.draw.circle`, then blit once per group.
- **Subtask 2.1b**: Cache per-class surfaces and only recreate when cell count/color changes.
- **Subtask 2.1c**: Replace per-cell `draw_at` calls with batch blit.

#### 2.2 Cache smoothscale when zoom unchanged (1h)
`smoothscale` is called every frame even when zoom hasn't changed. Cache the scaled surface and only re-scale when `prev_zoom != zoom`.

#### 2.3 Optimize minimap rendering (30min)
Cache the minimap `map_surf` and only redraw when cells have changed (dirty flag). Currently it creates a new surface and redraws all cells every frame.

#### 2.4 Vectorize population graph updates (1h)
`PopulationGraph.update()` iterates all cells every frame. Use a dict counter updated incrementally (increment on spawn, decrement on death) instead of recounting from scratch.

#### 2.5 Add Cython path for `sensory_phase` and `combat_phase` (4-6h)
These are the hottest loops in the Python fallback path. Moving them to Cython would give ~10x speedup for the non-Cython build.
- **Subtask 2.5a**: Extract `sensory_phase` ray sampling into `sim_core.pyx`.
- **Subtask 2.5b**: Extract `combat_phase` damage calculations into `sim_core.pyx`.

#### 2.6 Reduce ray sampling in sensory_phase (30min)
Current: 16 random rays per PHOT/POLY cell per tick. Reduce to 8 or use deterministic angular sampling (e.g., 8 evenly spaced rays).

#### 2.7 Optimize spatial grid neighbor lookups (1h)
`get_neighbors()` creates a new list every call. Pre-allocate or use a pool. Cache neighbor lists per cell per tick.

#### 2.8 Remove unused biome system from simulation (1h)
`_assign_biomes()` iterates W*H grid cells on init and stores in a dict. `adjust_biomes_for_season` is defined but never called. Either remove the biome system entirely or make it lazy/on-demand and actually hook it into the season cycle.

### Phase 3: Code Quality & Architecture (Priority: P2)

#### 3.1 Extract main loop into smaller functions (2-3h)
Split `main()` into: `handle_events()`, `update_simulation()`, `render_world()`, `render_ui()`, `update_sliders()`. Each ~50-80 lines.
- **Subtask 3.1a**: Extract `handle_events()` — all keyboard/mouse event handling.
- **Subtask 3.1b**: Extract `update_simulation()` — season logic, temperature, simulation step.
- **Subtask 3.1c**: Extract `render_world()` — world surface, cell drawing, minimap.
- **Subtask 3.1d**: Extract `render_ui()` — sidebar, stats, population graph.

#### 3.2 Add type hints to all public functions (3-4h)
Add `def func(arg: type) -> return_type:` annotations throughout. Use `from __future__ import annotations` for Python 3.14 compatibility.

#### 3.3 Decouple Cell from config constants (2h)
Cell imports 30+ specific constants from config. Group them into a `CellConfig` dataclass or namespace.

#### 3.4 Remove unused genome.py methods (30min)
`apply_epigenetic_modulation()` and `reset_epigenetics()` are never called. Either remove them or integrate them into the mutation system.

#### 3.5 Add proper error handling for sound loading (30min)
Wrap sound loading in try/except with specific exception types. Provide graceful degradation if MP3 files are missing.

#### 3.6 Add ruff + black config to pyproject.toml (10min)
Add `[tool.ruff]` and `[tool.black]` sections to pyproject.toml. Run once to format all files.

### Phase 4: New Features (Priority: P3)

#### 4.1 Extinction prevention (2h)
If any diet type drops below `PHOT_MIN_REQUIRED`/`ZOOP_MIN_REQUIRED`/`POLY_MIN_REQUIRED`, auto-spawn cells of that type at random positions. Constants are already defined but unused.

#### 4.2 Speciation visualization (3-4h)
When a new species emerges (genetic distance > threshold), give it a distinct color and show a brief "speciation" animation.

#### 4.3 Genome editor UI (6-8h)
Allow the user to click a cell and edit its genome traits via the sidebar sliders before placing it. Add a "clone & edit" mode.

#### 4.4 Time-lapse video export (4-6h)
Capture frames at configurable intervals, encode to MP4 using ffmpeg or imageio. Add a "Record" toggle in the UI.

#### 4.5 CSV population export (2h)
Add a keybinding (e.g., `Ctrl+E`) to export the current population data (counts per diet, avg energy, avg mass, avg level) to a timestamped CSV file.

#### 4.6 Cell memory debug overlay (2h)
Toggle with a key (e.g., `Tab`) to show threat/coop scores for each cell's memory.

#### 4.7 Spatial grid visualization (2h)
Toggle with a key to draw the spatial hash grid overlay (cell boundaries, neighbor connections).

#### 4.8 Sound volume per-type (1h)
Allow independent volume control for SFX vs music, and per-event volume.

#### 4.9 Biome-based resource variation (3h)
Actually use the biome system during simulation: biomes affect local resource regeneration rate, temperature, and food type availability.

#### 4.10 Undo/redo for cell placement (2h)
Maintain a stack of cell placement/removal actions. Ctrl+Z to undo, Ctrl+Y to redo.

### Phase 5: Testing & DevOps (Priority: P4)

#### 5.1 Add requirements.txt (10min)
Generate from pyproject.toml: `pygame>=2.5.0`, `numpy`, `cython` (optional).

#### 5.2 Add basic test suite (4-6h)
Test Genome mutation bounds, Cell energy calculations, config constant consistency between config.py and sim_core.pyx, spatial grid correctness. Use `pytest`.
- **Subtask 5.2a**: Test Genome mutation stays within bounds.
- **Subtask 5.2b**: Test Cell energy calculations (feeding, metabolism, combat).
- **Subtask 5.2c**: Test config constant consistency between config.py and sim_core.pyx.
- **Subtask 5.2d**: Test spatial grid correctness (neighbor lookups, cell insertion).

#### 5.3 CI/CD pipeline (2-3h)
GitHub Actions: run tests on push, build Cython extension, lint with ruff/black.

#### 5.4 Balance regression test (2h)
Run 10k ticks with fixed seed, assert population counts per diet stay within expected ranges.

## A.5 Constants Sync Checklist

When changing balance values in `config.py`, always update `sim_core.pyx` lines 14–37:

| config.py constant | sim_core.pyx line | Notes |
|--------------------|-------------------|-------|
| `ENERGY_MASS_COEFF` | `_ENERGY_MASS_COEFF` | Line 19 |
| `COMBAT_BASE_DAMAGE` | `_COMBAT_BASE_DAMAGE` | Line 34 |
| `COMBAT_DAMAGE_GAIN` | `_COMBAT_DAMAGE_GAIN` | Line 35 |
| `FEED_EFFICIENCY_BASE` | `_FEED_EFFICIENCY_BASE` | Line 30 |
| `PHOT_FEED_EFFICIENCY` | `_PHOT_FEED_EFFICIENCY` | Line 31 |
| `POLY_FEED_EFFICIENCY` | `_POLY_FEED_EFFICIENCY` | Line 32 |
| `MIN_MASS_EFFICIENCY` | `_MIN_MASS_EFFICIENCY` | Line 33 |
| `MASS_DMG_EFFICIENCY` | `_MASS_DMG_EFFICIENCY` | Line 36 |
| `MIN_MASS_DMG_EFF` | `_MIN_MASS_DMG_EFF` | Line 37 |
| `PREDATOR_METABOLISM_MULT` | `_PREDATOR_METABOLISM_MULT` | Line 27 |
| `SPEED_COST` | `_SPEED_COST` | Line 28 |
| `MASS_PENALTY` | `_MASS_PENALTY` | Line 29 |
| `LEVEL_UP_THRESHOLD` | `_LEVEL_UP_THRESHOLD` | Line 20 |
| `LEVEL_MASS_BASE` | `_LEVEL_MASS_BASE` | Line 23 |
| `LEVEL_MASS_STEP` | `_LEVEL_MASS_STEP` | Line 24 |

## A.6 Rendering Performance Targets

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| FPS (300 cells, Cython) | ~10 | 30+ | Batch rendering, cached surfaces |
| FPS (300 cells, Python) | ~3 | 10+ | Move sensory_phase + combat_phase to Cython |
| Tick time (300 cells) | <1ms | <0.5ms | Already met with Cython |
| Memory usage (1000 cells) | ~50MB | ~30MB | Reduce per-cell allocations, reuse surfaces |

## A.7 Immediate Action Items (Next Session)

1. **Fix sim_core.pyx constants drift** — update `_FEED_EFFICIENCY_BASE` from 18.0 to 22.0 (P0)
2. **Remove dead speciation code** from `cell.py` divide method (P0)
3. **Remove unused `_interact_with` alias** from `cell.py` (P0)
4. **Remove or integrate dead `adjust_biomes_for_season`** from `field.py` (P0)
5. **Remove unused import constants** from `main.py` (P0)
6. **Add FPS counter** to the stats display in `main.py` (P0)
7. **Generate requirements.txt** from pyproject.toml (P0)

## A.8 Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Cython rebuild needed after config changes | Medium | High | Document the sync requirement; add a build script that auto-syncs |
| Balance changes break ecosystem equilibrium | High | Medium | Run 50k-tick regression test after each balance change |
| Rendering optimization breaks visual correctness | Medium | Low | Keep original rendering as fallback; test with both paths |
| Removing dead code breaks speciation feature | Medium | Low | The speciation code in `divide()` is already broken (references unset attributes) |
| Removing biome system breaks future features | Low | Low | Biome system is currently dead code; can be re-added from git history |
