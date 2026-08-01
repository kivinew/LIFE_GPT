# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LIFE_GPT is a 2D cellular evolution simulation inspired by Conway's Game of Life but with advanced features:
- Physics simulation (inertia, friction, metabolism)
- Genetic engineering with heredity and mutations  
- Complex ecosystem with resource competition
- Interactive UI for research and cell manipulation

The simulation includes multiple cell types:
- **PHOT** (photosynthetic): Plants, grazers - food chain base
- **ZOOP** (zoophagous): Predators, hunters - higher trophic level
- **POLY** (polyphagous): Omnivores - flexible eaters

## Running

```bash
python main.py
```

### Architecture

**Flat Structure**: All core source is in the root directory for easy navigation:

- `main.py` - Entry point, UI, sound, main simulation loop
- `cell.py` - Cell class with 14-phase step method
- `genome.py` - Genes: 11 traits with mutation system
- `config.py` - All constants, balance coefficients (single source of truth)
- `sim_core.pyx` - Cython acceleration for physics/metabolism
- `field.py` - Resource field with diffusion and seasons
- `spatial.py` - Spatial hash grid for efficient neighbor queries
- `ui.py` - Sliders, toggles, sidebar UI
- `logger.py` - CSV population logging
- `memory.py` - CellMemory with threat/coop learning
- `file_utils.py` - Thread-safe JSON read/write

### Key Features

**Cython Support**: Uses compiled `sim_core` when available for performance:
```bash
python setup.py build_ext --inplace
```

**Memory System**: Cells learn through threat/coop memory inheritance
**Sound System**: 10 sound effects with volume control
**Internationalization**: Russian/English language support
**Resource Ecosystem**: Food fields with seasonal temperature effects

## Development

### Running with Cython

1. Build extension:
   ```bash
   python setup.py build_ext --inplace
   ```
2. Requires Python ≥3.14, pygame ≥2.5.0, numpy
3. Virtual environment (`.venv/`) recommended

### Testing Protocol

1. Run 10k ticks, record population per diet
2. Check sound frequency (division, death events)
3. Verify no diet goes extinct before 50k ticks
4. Test with 100, 300, 600 max cells
5. Validate balance with current config values

### Common Issues

**Population extinction spirals** - Ensure minimum per diet type
**Performance** - Use Cython, check cell counts
**Sound loading** - Verify `src/sounds/` directory exists
**Memory leaks** - Monitor cell counts over time

### Key Constants (config.py)

- `W, H` - Window dimensions (1200×700 with sidebar)
- `MAX_CELLS = 600` - Maximum cells in simulation
- `FEED_EFFICIENCY_BASE` - Base feeding efficiency
- `PHOT_FEED_EFFICIENCY` - Photosynthetic efficiency
- `ZOO_PHAGY_DEFAULT` - Zoophagous hunting base
- `PREDATOR_METABOLISM_MULT` - Predator metabolism cost

### UI Controls

**Keyboard Hotkeys**:
- `Space` - Pause
- `A/S` - Add mode
- `C` - Clear all
- `R` - Reset field
- `F` - Spawn cell from saved state
- `F5` - Save selection
- `1/2/3` - Set cell diet
- `Q/W/E` - Set interaction level
- `+/-` - Speed adjustment
- `X` - Mutate selected
- `D` - Delete selected
- `M` - Cycle music volume
- `Alt+M` - Adjust SFX volume

**Mouse**: Click to select, Shift+Click to select species

## Development Plan Priority

### Phase 2: Core Balance (Priority: High)

1. **Population Dynamics**
   - ✅ Prevent extinction spirals (add minimum per diet)
   - ✅ Carrying capacity (resource regeneration scaling)
   - ✅ Seasonal breeding (division chance seasonal modulation)

2. **Combat & Predation**
   - ✅ Zoophage hunting AI (weakest nearby targeting)
   - ✅ Pack hunting bonus (cooperative damage multiplier)
   - ✅ Flee behavior (diet-specific escape patterns)

3. **Evolution & Mutation**
   - ✅ Major mutations (rare genome restructuring)
   - [ ] Lineage tracking (visual family trees)
   - [ ] Speciation threshold (auto-detect new species)

### Phase 3: UI & Visualization (Priority: Medium)

1. **Statistics Panel**
   - ✅ Real-time population graphs per species
   - ✅ Energy distribution histograms
   - ✅ Genome trait averages over time
   - ✅ Mutation event logging

2. **Camera & Controls**
   - ✅ Follow selected cell (camera lock)
   - ✅ Mini-map overview
   - ✅ Time-lapse recording (save frames → video)

3. **Debug Tools**
   - ✅ Toggle spatial grid visualization
   - ✅ Show cell memory/threat/coop values
   - ✅ Export population CSV for analysis

### Phase 5: Performance & Polish (Priority: Medium)

1. **Cython Optimization**
   - ✅ Move `sensory_phase` to Cython
   - ✅ Move `combat_phase` to Cython
   - ✅ SIMD vectorization for spatial queries

2. **Rendering**
   - ✅ Batch draw calls (single surface per species)
   - ✅ GPU instancing for cells
   - ✅ LOD (level of detail) for zoomed out view

3. **Save/Load**
   - ✅ Compressed save format (msgpack)
   - ✅ World state snapshots (replay system)
   - ✅ Cross-session evolution tracking

## Team Coordination

**Review Focus**: Balance changes in `config.py`, ensure smooth gameplay
**Testing**: Run 50k+ ticks after major changes
**Communication**: Use existing CLAUDE.md for notes
**Documentation**: Complete DEV_PLAN.md as work progresses

## Key Files to Edit

**Primary Development Files**:
- `config.py` - Balance adjustments
- `cell.py` - Game logic changes
- `genome.py` - Gene system modifications
- `sim_core.pyx` - Cython optimizations

**Supporting Files**:
- `main.py` - Integration testing
- `ui.py` - UI improvements
- `logger.py` - Debugging output

**Build System**:
- `setup.py` - Cython compilation
- `cython_build_and_run.py` - Local testing

## Memory and Learning

The learning system uses:
- **CellMemory** in `memory.py`: Threat assessment, cooperation learning
- **New genes**: `learning_rate`, `memory_size` inherited from parents
- **Learning indicators**: Blue dots on learned cells
- **Threat learning**: From damage, habitat recording
- **Coop learning**: From kills, social interactions

## Tips for Development

1. **Work in pairs**: Test changes with fresh simulations
2. **Version control**: Use `.git` for tracking development
3. **Documentation**: Update DEV_PLAN.md as work completes
4. **Performance monitoring**: Watch FPS and simulation stability
5. **Balance testing**: Verify all three diets (PHOT, ZOOP, POLY) can survive
6. **Sound testing**: Ensure all 10 sound effects work with volume controls

## Files to Avoid

DO NOT EDIT directly:
- Compiled `.pyc` files
- `.venv/` virtual environment
- Generated `bg_music.mp3` from base64.txt

**Dependencies**: Natural evolution may make existing code obsolete; focus on balance changes rather than wholesale rewrites.
