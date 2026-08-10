# LIFE_GPT Agent Coordination Protocol

Two agents — **Controller** and **Executor** — work on LIFE_GPT simultaneously without race conditions. This document defines the protocol.

---

## Roles

### Controller
- **Creates** tasks in `.task_queue/` by priority
- **Reviews** completed work (reads `.agent_logs/<task>.log` + inspects diffs)
- **Approves** merges to codebase
- **Never** writes to source files in `src/`, `*.py`, `*.pyx`, `*.json`
- **Only** writes to `.task_queue/`, `.agent_logs/`, and `*.review` files

### Executor
- **Claims** the highest-priority pending task atomically
- **Writes** a log entry to `.agent_logs/<task>.log` after each significant step
- **Edits** source files (`cell.py`, `field.py`, `main.py`, `ui.py`, `sim_core.pyx`, `config.py`)
- **Never** edits `.task_queue/` files directly (must use `agent_coordinator.py`)
- Marks task `done` when finished, then claims the next

---

## Task Lifecycle

```
 Controller creates  →  .task_queue/P1.json (status: pending)
       ↓
 Executor: agent_coordinator.py next   →  atomically claims, status: claimed
       ↓
 Executor: works on source, logs to .agent_logs/P1.log
       ↓
 Executor: agent_coordinator.py done P1  →  status: done
       ↓
 Controller: agent_coordinator.py review P1  →  inspects logs + diff
       ↓
 Controller: approves merge / requests changes
```

### Atomic claim guarantee
The claim operation uses `agent_coordinator.py` which acquires the `queue` lock (`.locks/queue.lock` via `os.mkdir` atomicity) before scanning for the next pending task. Two executors racing for the same task will serialize — only one wins.

---

## File Access Rules (Prevents Race Conditions)

| Resource | Controller | Executor |
|---|---|---|
| `.task_queue/*.json` | ✅ write (add/re-prioritize) | read-only |
| `.agent_logs/*.log` | ✅ read (review) | ✅ write (append) |
| `cell.py`, `field.py`, `main.py`, `ui.py`, `sim_core.pyx`, `config.py` | ❌ read-only* | ✅ edit |
| `requirements.txt`, `pyproject.toml` | ❌ read-only | ✅ create/edit |
| `git` (commit/push) | ✅ commit after review | ❌ never commit |
| Source code review comments | ✅ write to `.reviews/` | ✅ read |

\* Controller reads source to assign tasks but never modifies them.

### When both need the same file
If Controller needs to write `dev_plan.md` while Executor is editing it:
```bash
python agent_coordinator.py lock dev_plan
# ... edit ...
python agent_coordinator.py unlock dev_plan
```
Executor will wait for the lock to release before claiming its next task.

---

## Current Task Queue

Run `python agent_coordinator.py list` to see live status.

| ID  | Priority | Title |
|-----|----------|-------|
| P0  | P0 | Remove dead speciation code from cell.py divide() |
| P1  | P0 | Remove unused _interact_with alias from cell.py |
| P2  | P0 | Remove or integrate dead adjust_biomes_for_season from field.py |
| P3  | P0 | Remove unused import constants from main.py |
| P4  | P0 | Add FPS counter to stats display in main.py |
| P5  | P0 | Generate requirements.txt from pyproject.toml |
| P1-1| P1 | Implement cell surface caching (biggest FPS win) |
| P1-2| P1 | Replace math.hypot with squared-distance comparisons |
| P1-3| P1 | Cache population graph surface; re-render only on new data |
| P1-4| P1 | Spatial grid dirty flag — skip rebuild when cells haven't moved |
| P1-5| P1 | Batch minimap rendering — cached 1x1 dot surfaces |

---

## Commands Reference

```bash
# List all tasks
python agent_coordinator.py list

# Claim the next highest-priority task (Executor)
python agent_coordinator.py next

# Claim a specific task by ID
python agent_coordinator.py claim P0

# Mark a task done with optional notes
python agent_coordinator.py done P0 "Removed 12 lines of dead speciation code"

# Write a progress log entry (Executor, during work)
python agent_coordinator.py log P0 "Started: found dead code at line ~1100"

# Review a completed task (Controller)
python agent_coordinator.py review P0

# Add a new task (Controller)
python agent_coordinator.py add "Task title" "P1" "details"
```

---

## Protocol Log

### [2026-08-09] Infrastructure Setup
- Created `.task_queue/`, `.locks/`, `.agent_logs/` directories
- Created `agent_coordinator.py` with atomic task claim/done/lock/unlock
- Populated queue with 11 tasks (6 P0, 5 P1) from `dev_plan.md` Immediate Action Items
- `sim_core.pyx` constants already synced (`_FEED_EFFICIENCY_BASE = 22.0` matches `config.py`)
- Updated `.gitignore` to exclude `.locks/` and `.agent_logs/`

### [2026-08-09] Role Prompts
- Created `CONTROLLER_PROMPT.md` — full instructions for the Controller agent
- Created `EXECUTOR_PROMPT.md` — full instructions for the Executor agent
- Both include core loop, permission matrix, testing protocol, and conflict resolution

### [2026-08-09] P2 Decision: Remove dead `adjust_biomes_for_season()` from field.py

**Decision**: Removed `ResourceField.adjust_biomes_for_season(self, season)` (was field.py:144, 59 lines).

**Rationale**:
1. **Never called** — grep across all `.py` files returned zero call sites before removal.
2. **Misleading docstring** — claims "called from cell.py when seasons change", which was false.
3. **Architectural inconsistency** — directly mutates `self.data[pos[0], pos[1]]` with hardcoded additive values (+0.02, -0.01), bypassing the existing seasonal system which uses `SEASON_FACTORS["regen_mult"]` (smooth global multiplier) + `field.temperature` via `_get_temp_regen_factor()`.
4. **Biome system survives** — `self.biomes` is still used by `_assign_biomes()`, `get_biome()`, and `analyze_biome_distribution()`. The biome assignment and lookup remain functional.
5. **Recoverable** — the method is preserved in git history (was last present before commit `5a87b76`) if integration is desired later.

**Integration alternative (rejected)**: Would have required adding season-transition detection to main.py's main loop (comparing `season_idx` across ticks) and wiring `field.adjust_biomes_for_season(season_name)` at the boundary. The additive data mutation is not compatible with the existing regen-decay-diffusion cycle, risking visual artifacts (food "pops") and gameplay imbalance. If biome-specific seasonal effects are wanted later, they should be implemented as biome-indexed regen multipliers applied through `step()`'s `effective_regen` path.
