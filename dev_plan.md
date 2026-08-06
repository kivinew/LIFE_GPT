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

- `smoothscale` is called every frame (expensive) — cached when zoom unchanged
- **Per-cell surface allocation** (`draw_at()` creates a new `SRCALPHA` Surface + concentric gradient circles per cell per frame) — the single largest rendering cost at 300+ cells
- Draws individual circles for each cell (no batch rendering) — cell surface caching eliminates this
- Creates a new `pygame.Surface` for the minimap every frame it's shown — not cached between frames; batch `blit` of cached dot surfaces instead of per-pixel `set_at()`
- No FPS counter displayed to the user
- **`math.hypot` called thousands of times per tick** — replace with squared-distance comparisons where possible (eliminates sqrt)
- **Spatial grid rebuilt every tick** even when cells haven't moved — dirty flag avoids redundant rebuilds
- **Nutrient cluster surfaces recreated every frame** with sin/cos modulation — pre-render and cache
- **Population graph redrawn every frame** even when data unchanged — cache the rendered surface, only re-render on new data

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

### A.4 Optimization Plan (from update.md)

#### P0 — Critical Rendering Fixes

| # | Task | File | Effort | Expected Gain |
|---|------|------|--------|---------------|
| 1 | Cache cell surfaces per `(cls, radius)` pair; invalidate on `refresh_class()` | `cell.py` | Medium | +30–70% FPS |
| 2 | Replace `math.hypot` with squared-distance comparisons in all cell phases | `cell.py` | Low | +5–10% FPS |
| 3 | Batch minimap rendering — `blit` cached 1×1 dot surfaces instead of per-pixel `set_at()` | `main.py` | Low | +5% FPS |
| 4 | Cache population graph surface; only re-render on new data | `ui.py` | Low | +2–3% FPS |
| 5 | Return `tuple` from `get_neighbors()` to avoid list mutation overhead | `spatial.py` | Low | +2% FPS |

#### P1 — Structural Optimizations

| # | Task | File | Effort | Expected Gain |
|---|------|------|--------|---------------|
| 6 | Spatial grid dirty flag — skip rebuild when no cell moved > `CELL_SIZE/2` | `spatial.py` | Medium | +5–15% FPS |
| 7 | Pre-render nutrient cluster surfaces; cache and only recreate when amount changes >10% | `field.py` | Medium | +3–8% FPS |
| 8 | Replace biome `(x,y)` dict with 2D numpy uint8 array of biome indices | `field.py` | Medium | +3–5% FPS |
| 9 | Grid-based cell picking — use spatial grid to check only nearby cells | `main.py` | Medium | O(1) pick |

#### P2 — Cython Extension

| # | Task | File | Effort | Expected Gain |
|---|------|------|--------|---------------|
| 10 | Extend `sim_core.pyx` to cover `sensory_phase`, `combat_phase`, `social_phase` | `sim_core.pyx` | High | 2–5× on covered phases |

#### P3 — Nice-to-Have

| # | Task | File | Effort | Expected Gain |
|---|------|------|--------|---------------|
| 11 | Fixed-step simulation loop — decouple logic from rendering | `main.py` | Medium | Stable FPS under load |
| 12 | Reduce corpse/nutrient cluster lifetimes for faster FPS recovery | `config.py` | Low | Faster recovery after die-offs |
| 13 | Vectorize neighbor calculations with NumPy (Python fallback path only) | `cell.py` | High | Order-of-magnitude for sensing |

#### Implementation Priority Order
1. Squared distance comparisons (free win)
2. Cell surface caching (biggest single FPS gain)
3. Batch minimap blits (trivial)
4. Graph surface caching (trivial)
5. Return tuples from `get_neighbors` (trivial)
6. Spatial grid dirty flag (moderate, good payoff)
7. Cluster surface caching (moderate)
8. Biome array (moderate)
9. Grid-based cell picking (moderate)
10. Extend Cython coverage (highest effort, highest ceiling)

#### Testing Methodology
1. Launch with 400+ initial cells (spawn templates or cheat)
2. Observe FPS in bottom-right corner (Tab stats)
3. Clear world (`C`) and measure FPS recovery time
4. After each optimization, compare FPS at same cell count
5. Verify visual correctness: cell colors, behaviors, graph shape
6. Verify no regression in simulation logic (energy conservation, division, combat)

#### Rendering Performance Targets (updated)

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| FPS (300 cells, Cython) | ~10 | 30+ | Cell surface caching, batch minimap blits |
| FPS (300 cells, Python) | ~3 | 10+ | Move sensory_phase + combat_phase to Cython |
| Tick time (300 cells) | <1ms | <0.5ms | Already met with Cython |
| Memory usage (1000 cells) | ~50MB | ~30MB | Reduce per-cell allocations, reuse surfaces |

#### Immediate Action Items (Next Session)
1. **Fix sim_core.pyx constants drift** — update `_FEED_EFFICIENCY_BASE` from 18.0 to 22.0 (P0)
2. **Remove dead speciation code** from `cell.py` divide method (P0)
3. **Remove unused `_interact_with` alias** from `cell.py` (P0)
4. **Remove or integrate dead `adjust_biomes_for_season`** from `field.py` (P0)
5. **Remove unused import constants** from `main.py` (P0)
6. **Add FPS counter** to the stats display in `main.py` (P0)
7. **Generate requirements.txt** from pyproject.toml (P0)
8. **Implement cell surface caching** — biggest single FPS win (P1)
9. **Squared-distance comparisons** — free win across all cell phases (P1)

## A.7 Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Cython rebuild needed after config changes | Medium | High | Document the sync requirement; add a build script that auto-syncs |
| Balance changes break ecosystem equilibrium | High | Medium | Run 50k-tick regression test after each balance change |
| Rendering optimization breaks visual correctness | Medium | Low | Keep original rendering as fallback; test with both paths |
| Removing dead code breaks speciation feature | Medium | Low | The speciation code in `divide()` is already broken (references unset attributes) |
| Removing biome system breaks future features | Low | Low | Biome system is currently dead code; can be re-added from git history |

---

## A.8 Planned Mechanics: Death & Decomposition

### A.8.1 Temperature-Dependent Corpse Decomposition

**Status**: TODO
**Files**: `cell.py` (Corpse class), `field.py` (nutrient clusters), `config.py` (constants)

**Description**:
Decomposition rate of dead cells depends on ambient temperature:
- **T > 0 °C**: decomposition proceeds normally; `CORPSE_NUTRIENT_FADE` scaled by temperature factor (same formula as food regen: linear from 0 at `FREEZE` to 1.0 at `TEMP_IDEAL`).
- **T <= 0 °C**: decomposition halts completely — corpses are "frozen", their bodies preserved on the field. Nutrient clusters do not fade and do not feed the food field. Corpses remain visible until temperature rises above 0 °C, at which point decomposition resumes.
- **Visual**: frozen corpses could be drawn with a blue/white tint to indicate their frozen state.

**Implementation details**:
1. In `field.py`, `step()` already computes `temp_factor` via `_get_temp_regen_factor()`. Reuse this factor for `nutrient_fade`: when `temp_factor == 0` (below freezing), set `nutrient_fade = 1.0` (no fade).
2. Corpses (Cell instances with `alive=False`) currently remain in the `cells` list and are drawn by `draw_at()`. Add a `frozen` flag to corpses when temperature drops below `FREEZE` — frozen corpses skip decomposition logic.
3. When temperature rises above `FREEZE`, unfreeze corpses and resume normal `CORPSE_NUTRIENT_FADE` decay.
4. Optionally add a new `CORPSE_FREEZE_TINT` color constant in `config.py` for rendering frozen corpses.
