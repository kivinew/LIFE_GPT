# ═══════════════════════════════════════════════════════════════════════
#  LIFE_GPT — Cellular Evolution Simulator
# ═══════════════════════════════════════════════════════════════════════
import sys
import os
import random
import math
import base64
import json

import pygame
import numpy as np

# Import config first (contains constants used by other modules)
from config import (
    W,
    H,
    SB,
    CELL_SIZE,
    PHOT,
    ZOOP,
    POLY,
    INTERACT_MIN,
    MAX_CELLS,
    BG,
    DARK,
    GRAY,
    WHITE,
    YEL,
    TEAL,
    BLUE,
    CYAN,
    RED,
    GREEN,
    ENERGY_MASS_COEFF,
    DRAW_ENERGY_MASS_COEFF,
    REGEN_MAX_RATE,
    REGEN_SMOOTH_RATE,
    STRESS_ENERGY_THRESHOLD,
    STRESS_MASS_MIN,
    STRESS_ENERGY_GAIN,
    STRESS_MASS_LOSS,
    BASE_METABOLISM_MULT,
    PREDATOR_METABOLISM_MULT,
    SPEED_COST,
    MASS_PENALTY,
    FEED_EFFICIENCY_BASE,
    PHOT_FEED_EFFICIENCY,
    POLY_FEED_EFFICIENCY,
    MIN_MASS_EFFICIENCY,
    COMBAT_BASE_DAMAGE,
    COMBAT_DAMAGE_GAIN,
    MASS_DMG_EFFICIENCY,
    MIN_MASS_DMG_EFF,
    LEVEL_UP_THRESHOLD,
    LEVEL_DOWN_THRESHOLD,
    MAX_LEVEL,
    LEVEL_MASS_BASE,
    LEVEL_MASS_STEP,
    AGGRO_INTERACT_THRESHOLD,
    COOP_INTERACT_THRESHOLD,
    AGGRO_STEAL_FRACTION,
    AGGRO_TRANSFER_EFF,
    COOP_TRANSFER_MAX,
    COOP_TRANSFER_MIN_ENERGY,
    COOP_TRANSFER_PRESERVE,
    BASE_LIFESPAN_TICKS,
    LIFESPAN_PER_MASS,
    AGING_DAMAGE,
    THREAT_FLEE_THRESHOLD,
    COOP_PREFER_THRESHOLD,
    LEARNING_RATE_BASE,
    ZOO_INITIAL_ENERGY,
    PHOT_INITIAL_ENERGY,
    DISEASE_CHANCE,
    DISEASE_DURATION,
    DISEASE_METABOLISM_MULT,
    DISEASE_TRANSMISSION_RANGE,
    MIGRATION_CHANCE,
    MIGRATION_DISTANCE,
    TEMP_ENERGY_PENALTY,
    AGING_METABOLISM_FACTOR,
    MAJOR_DIET_RATE,
    MAJOR_SENSE_RATE,
    DIET_DEFAULT_SPEED,
    DIET_DEFAULT_SENSE,
    ZOO_PHAGY_MIN,
    ZOO_PHAGY_MAX,
    ZOO_PHAGY_DEFAULT,
    DECOMPOSITION_NUTRIENT_FRACTION,
    DECOMPOSITION_TICKS,
    CORPSE_EAT_RADIUS,
    CORPSE_EAT_RATE,
    CORPSE_EAT_EFFICIENCY,
    SEASON_ORDER,
    SEASON_LENGTH,
    SEASON_FACTORS,
    SEASON_TEMPERATURES,
    TEMP_SMOOTH_RATE,
    tr,
    tr_diet,
)

from field import ResourceField
from cell import Cell, Corpse, diet_color, set_sounds, play_sound
from genome import Genome
from spatial import build_spatial_grid, get_neighbors
from memory import CellMemory
from logger import init_logging, log_tick, close_logging
from ui import Slider, SliderInt, PopulationGraph
from hotkeys import handle_key, HotkeyState

# Cython backend (optional)
try:
    from sim_core import apply_physics, apply_metabolism_and_feeding, simulate_step

    _HAVE_SIM_CORE = True
except ImportError:
    _HAVE_SIM_CORE = False

# Project directory for asset loading
_project_dir = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════════
#  Preset templates (moved to hotkeys.py)
# ═══════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════
#  Sidebar layout constants
# ═══════════════════════════════════════════════════════════════════════
COL_W = 285
COL_LX = W - SB + 10
COL_RX = COL_LX + COL_W + 10


# ═══════════════════════════════════════════════════════════════════════
#  Camera helpers
# ═══════════════════════════════════════════════════════════════════════
def screen_to_world(sx, sy, cam_x, cam_y, zoom):
    return (
        (sx - (W - SB) / 2) / zoom + cam_x,
        (sy - H / 2) / zoom + cam_y,
    )


# ═══════════════════════════════════════════════════════════════════════
def process_deaths(cells, field, corpses):
    alive = []
    for c in cells:
        if c.is_dead():
            field.add_nutrient_cluster(
                c.x,
                c.y,
                c.genome.mass
                * c.genome.mass
                * ENERGY_MASS_COEFF
                * DECOMPOSITION_NUTRIENT_FRACTION,
            )
            corpses.append(Corpse(c.x, c.y, c.genome.mass))
            play_sound("death")
        else:
            alive.append(c)
    if len(alive) != len(cells):
        cells[:] = alive


# ═══════════════════════════════════════════════════════════════════════
def _pick_cell(cells, wx, wy, zoom):
    """Return the topmost cell under the world point (wx, wy), or None."""
    for c in cells:
        if (
            math.hypot(c.x - wx, c.y - wy)
            < max(3, int(2 + c.genome.mass * 1.5)) * zoom + 4
        ):
            return c
    return None


def _apply_selection(cells, hit, shift, alt):
    """Apply click selection rules to a hit cell. Returns the new sel_cell.

    Alt+click selects every cell of the same class.
    Shift+click adds the cell to the current selection group.
    Plain click toggles the cell and clears the rest of the selection.
    """
    if alt:
        cls = hit.cls
        for oc in cells:
            oc.selected = oc.cls == cls
        return hit
    if shift:
        hit.selected = True
        return hit
    hit.selected = not hit.selected
    for oc in cells:
        if oc is not hit:
            oc.selected = False
    return hit if hit.selected else None


def _select_in_rect(cells, wx0, wy0, wx1, wy1, shift):
    """Marquee (box) selection in world coordinates.

    Plain box clears the previous selection; Shift+box adds to it.
    Returns the last selected cell (None if nothing selected).
    """
    wxmin, wxmax = sorted((wx0, wx1))
    wymin, wymax = sorted((wy0, wy1))
    if not shift:
        for c in cells:
            c.selected = False
    sel = None
    for c in cells:
        if wxmin <= c.x <= wxmax and wymin <= c.y <= wymax:
            c.selected = True
            sel = c
    return sel


# ── Population-graph legend / palette toggles ─────────────────────────────
LEGEND_GROUP_Y = 761
_LEGEND_GRID_Y = LEGEND_GROUP_Y + 26
LEGEND_GRID_RECT = pygame.Rect(COL_LX, _LEGEND_GRID_Y, COL_W, 22)
_LEGEND_GRID_RECT_PHOT = pygame.Rect(COL_LX, _LEGEND_GRID_Y, COL_W, 22)
_LEGEND_GRID_RECT_ZOOP = pygame.Rect(COL_LX, _LEGEND_GRID_Y + 28, COL_W, 22)
_LEGEND_GRID_RECT_POLY = pygame.Rect(COL_LX, _LEGEND_GRID_Y + 56, COL_W, 22)
_LEGEND_DOT_R = 10
_LEGEND_CLASS_R = 6


def _palette_group_dots():
    """Return [(kind, cx, cy, rect)] for the diet group dots + the Total dot."""
    xs = [COL_LX + 36, COL_LX + 118, COL_LX + 200, COL_LX + COL_W - 36]
    kinds = [PHOT, ZOOP, POLY, "total"]
    out = []
    for kind, cx in zip(kinds, xs):
        out.append(
            (
                kind,
                cx,
                LEGEND_GROUP_Y,
                pygame.Rect(
                    cx - _LEGEND_DOT_R,
                    LEGEND_GROUP_Y - _LEGEND_DOT_R,
                    _LEGEND_DOT_R * 2,
                    _LEGEND_DOT_R * 2,
                ),
            )
        )
    return out


def _palette_class_grid(pop_graph, diet_filter=None, grid_rect=None, dot_r=_LEGEND_CLASS_R, gap=8):
    """Return (entries, offset, total) for the visible scroll window of classes.

    entries = list of (cls, rect, color, visible).
    If diet_filter is given, only classes of that diet are included.
    """
    if grid_rect is None:
        grid_rect = LEGEND_GRID_RECT
    cols = max(1, (grid_rect.w - 2 * gap) // (2 * dot_r + gap))
    rows = max(1, grid_rect.h // (2 * dot_r + gap))
    all_entries = pop_graph.legend_entries()
    if diet_filter is not None:
        all_entries = [(cls, col, vis) for cls, col, vis in all_entries if pop_graph.cls_diet.get(cls) == diet_filter]
    total = len(all_entries)
    per_page = cols * rows if total else 1
    offset = max(0, min(pop_graph.legend_offset, max(0, total - per_page)))
    page = all_entries[offset : offset + per_page]
    out = []
    for i, (cls, color, visible) in enumerate(page):
        col, row = i % cols, i // cols
        cx = grid_rect.x + gap + col * (2 * dot_r + gap) + dot_r
        cy = grid_rect.y + gap + row * (2 * dot_r + gap) + dot_r
        out.append(
            (
                cls,
                pygame.Rect(cx - dot_r, cy - dot_r, 2 * dot_r, 2 * dot_r),
                color,
                visible,
            )
        )
    return out, offset, total


def _palette_click(pop_graph, pos):
    """Handle a click on the legend/palette. Returns True if consumed."""
    for kind, cx, cy, rect in _palette_group_dots():
        if rect.collidepoint(pos):
            if kind == "total":
                pop_graph.toggle_total()
            else:
                pop_graph.toggle_diet(kind)
            return True
    for grid_rect in [_LEGEND_GRID_RECT_PHOT, _LEGEND_GRID_RECT_ZOOP, _LEGEND_GRID_RECT_POLY]:
        for cls, rect, color, visible in _palette_class_grid(pop_graph, grid_rect=grid_rect)[0]:
            if rect.collidepoint(pos):
                pop_graph.toggle_cls(cls)
                return True
    return False


# ═══════════════════════════════════════════════════════════════════════
def eat_corpses(cells, corpses, dt):
    """POLY cells near a corpse consume it: corpse mass shrinks, eater gains energy."""
    if not corpses:
        return
    for cp in corpses:
        if cp.done:
            continue
        eater = None
        best_d = CORPSE_EAT_RADIUS
        for c in cells:
            if c.energy <= 0 or c.genome.diet != POLY:
                continue
            d = math.hypot(c.x - cp.x, c.y - cp.y)
            if d < best_d:
                best_d = d
                eater = c
        if eater is not None:
            gain = CORPSE_EAT_RATE * dt
            cp.mass = max(0.0, cp.mass - gain / CORPSE_EAT_EFFICIENCY)
            eater.energy = min(eater.max_energy, eater.energy + gain)


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════
def main():
    pygame.init()
    pygame.mixer.init(44100, -16, 2, 512)
    screen = pygame.display.set_mode((W, H), pygame.HWSURFACE | pygame.DOUBLEBUF)

    # ── Load sounds ───────────────────────────────────────────────────────
    _sounds = {}
    _sounds_dir = os.path.join(_project_dir, "src", "sounds")
    for name in [
        "eating",
        "divide",
        "death",
        "mutation",
        "lvl_up",
        "lvl_down",
        "heartbeat",
        "gurgle",
        "gurgle2",
        "injection",
        "mass_down",
    ]:
        path = os.path.join(_sounds_dir, f"{name}.mp3")
        if os.path.exists(path):
            _sounds[name] = pygame.mixer.Sound(path)
            print(f"Loaded sound: {name}.mp3")

    set_sounds(_sounds)

    clock = pygame.time.Clock()
    big = pygame.font.SysFont(None, 30)
    font = pygame.font.SysFont(None, 18)
    small = pygame.font.SysFont(None, 14)
    tiny = pygame.font.SysFont(None, 12)
    legend = pygame.font.SysFont(None, 20)

    field = ResourceField(W - SB, H)
    cells = [
        Cell(random.uniform(100, W - SB - 100), random.uniform(100, H - 100), Genome())
        for _ in range(40)
    ]
    corpses = []

    # ── UI widgets ─────────────────────────────────────────────────────
    sliders = [
        Slider(COL_LX, 96, COL_W, tr("speed"), 0.5, 4.0, 1.5),
        Slider(COL_LX, 124, COL_W, tr("sense"), 30, 120, 40),
        Slider(COL_LX, 152, COL_W, tr("mass"), 2, 8, 4),
        Slider(COL_LX, 180, COL_W, tr("metabolism"), 0.01, 0.15, 0.04),
        Slider(COL_LX, 208, COL_W, tr("divide_chance"), 0.1, 0.9, 0.5),
    ]
    for s, k in zip(sliders, ["speed", "sense", "mass", "metabolism", "divide_chance"]):
        s.label_key = k

    sl_diet = SliderInt(COL_LX, 248, COL_W, tr("diet"), 0, 2, 0, labels=["Ф", "З", "П"])
    sl_interact = Slider(COL_LX, 287, COL_W, tr("interact"), INTERACT_MIN, 1.0, 0.5)
    sl_zoophagy = Slider(
        COL_LX,
        327,
        COL_W,
        tr("zoophagy"),
        ZOO_PHAGY_MIN,
        ZOO_PHAGY_MAX,
        ZOO_PHAGY_DEFAULT,
        labels=["0.5", "1.0", "2.0"],
    )

    dmg_defaults = [0.6, 1.2, 1.0]
    sl_dmg = [
        Slider(
            COL_LX,
            374 + i * 30,
            COL_W,
            [tr("dmg_phot"), tr("dmg_zoo"), tr("dmg_poly")][i],
            0.1,
            3.0,
            dmg_defaults[i],
        )
        for i in range(3)
    ]

    sl_regen = Slider(
        COL_LX,
        479,
        COL_W,
        tr("food_regen"),
        0.0,
        100.0,
        30.0,
        labels=["0%", "50%", "100%"],
        unit="%",
    )
    sl_temp = Slider(
        COL_LX,
        519,
        COL_W,
        tr("temp"),
        -10.0,
        35.0,
        13.0,
        labels=["-10°C", "13°C", "35°C"],
    )
    sl_temp._bias = 0.0
    sl_diffuse = Slider(COL_LX, 597, COL_W, tr("food_diffuse"), 0.005, 0.2, 0.06)
    sl_time = Slider(COL_LX, 627, COL_W, tr("time_scale"), 0.1, 5.0, 1.0)
    sl_sfx = Slider(COL_RX, 726, COL_W, tr("sfx"), 0.0, 1.0, 0.1)
    sl_music = Slider(COL_RX, 766, COL_W, tr("music"), 0.0, 1.0, 0.8)

    # Load background music from base64.txt
    try:
        base64_path = os.path.join(_project_dir, "base64.txt")
        if os.path.exists(base64_path):
            music_data = base64.b64decode(open(base64_path, "rb").read())
            music_path = os.path.join(_sounds_dir, "bg_music.mp3")
            with open(music_path, "wb") as f:
                f.write(music_data)
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(sl_music.val)
            pygame.mixer.music.play(-1)
            print("Successfully loaded background music from base64.txt")
        else:
            raise FileNotFoundError("base64.txt not found")
    except Exception as e:
        print(f"Could not load music from base64.txt: {e}")
        heartbeat_path = os.path.join(_sounds_dir, "heartbeat.mp3")
        if os.path.exists(heartbeat_path):
            pygame.mixer.music.load(heartbeat_path)
            pygame.mixer.music.set_volume(sl_music.val)
            pygame.mixer.music.play(-1)
            print("Using heartbeat.mp3 as fallback music")
        else:
            print("No fallback music available - music will be disabled")

    # Music volume cycling state
    music_volume = 0.25
    music_volume_step = 0.25
    music_volume_increasing = False
    music_fade_timer = 0
    music_fade_duration = 300  # 5 seconds at 60 FPS
    pygame.mixer.music.set_volume(0.0)
    pygame.mixer.music.play(-1)
    sl_music.val = music_volume

    # SFX volume cycling state (like music, but for sound effects)
    sfx_volume = sl_sfx.val
    sfx_volume_step = 0.10
    sfx_volume_increasing = False
    import cell

    cell._sfx_volume = sfx_volume

    # Sound effects toggle - shared with cell.py
    cell._sounds_enabled = True
    cell._sfx_volume = sl_sfx.val

    cam_x, cam_y, zoom = (W - SB) / 2, H / 2, 1.0
    prev_zoom = 1.0

    world_w, world_h = W - SB, H
    world_surf = pygame.Surface((world_w, world_h))
    scaled_surf = None

    map_size = 225
    map_rect = pygame.Rect(COL_RX, 452, map_size, map_size)
    map_scale_x = map_size / world_w
    map_scale_y = map_size / world_h
    map_drag = False
    pan_drag = False
    marquee_active = False
    marquee_start = (0, 0)
    marquee_cur = (0, 0)
    pan_last = (0, 0)

    add_mode = False
    sel_cell = None
    paused = False
    running = True
    tick = 0
    divisions = 0
    follow_mode = False
    show_stats = True
    show_memory = False
    time_lapse_mode = False
    time_lapse_active = False
    time_lapse_timer = 0
    time_lapse_duration = 10  # seconds

    init_logging()
    # Reduced history for better performance with many cells
    pop_graph = PopulationGraph(history_length=2000, sample_interval=10)

    st = HotkeyState(
        cells=cells,
        corpses=corpses,
        field=field,
        paused=paused,
        add_mode=add_mode,
        time_lapse_mode=time_lapse_mode,
        show_stats=show_stats,
        follow_mode=follow_mode,
        sel_cell=sel_cell,
        running=running,
        sfx_volume=sfx_volume,
        sfx_volume_increasing=sfx_volume_increasing,
        music_volume_increasing=music_volume_increasing,
        sliders=sliders,
        sl_diet=sl_diet,
        sl_interact=sl_interact,
        sl_dmg=sl_dmg,
        sl_regen=sl_regen,
        sl_temp=sl_temp,
        sl_zoophagy=sl_zoophagy,
        sl_diffuse=sl_diffuse,
        sl_time=sl_time,
        sl_sfx=sl_sfx,
        sl_music=sl_music,
        cam_x=cam_x,
        cam_y=cam_y,
        zoom=zoom,
    )

    # ── Main loop ──────────────────────────────────────────────────────
    prev_diet = int(sl_diet.val)
    regen_base = sl_regen.val  # user-set base % (effective % is shown on the slider)
    while running:
        mx, my = pygame.mouse.get_pos()
        wx, wy = screen_to_world(mx, my, cam_x, cam_y, zoom)
        dt = clock.tick(60) / 16.0 * sl_time.val

        season_idx = (tick // SEASON_LENGTH) % 4
        season_name = SEASON_ORDER[season_idx]
        season_factor = SEASON_FACTORS[season_name]
        # Smooth season temperature: interpolate toward the next season
        season_progress = (tick % SEASON_LENGTH) / SEASON_LENGTH
        season_temp = SEASON_TEMPERATURES[season_name]
        season_temp += (
            SEASON_TEMPERATURES[SEASON_ORDER[(season_idx + 1) % 4]] - season_temp
        ) * season_progress

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                st.running = False

            # ── Keyboard (handled in hotkeys.py) ──────────────────────
            if e.type == pygame.KEYDOWN:
                handle_key(e, st)

            # ── Mouse wheel: palette scroll or camera zoom ──────────────────
            if e.type == pygame.MOUSEWHEEL:
                pmx, pmy = pygame.mouse.get_pos()
                over_palette = any(
                    r.collidepoint(pmx, pmy)
                    for r in [_LEGEND_GRID_RECT_PHOT, _LEGEND_GRID_RECT_ZOOP, _LEGEND_GRID_RECT_POLY]
                ) or any(
                    r.collidepoint(pmx, pmy) for *_, r in _palette_group_dots()
                )
                if over_palette:
                    total = len(pop_graph.legend_entries())
                    _, _, per_page = _palette_class_grid(pop_graph)
                    if total > per_page:
                        step = 5
                        pop_graph.legend_offset = max(
                            0,
                            min(
                                pop_graph.legend_offset - e.y * step,
                                max(0, total - per_page),
                            ),
                        )
                else:
                    old_zoom = zoom
                    new_zoom = max(0.3, min(3.0, zoom * (1.0 + e.y * 0.15)))
                    if new_zoom != old_zoom:
                        pmx, pmy = pygame.mouse.get_pos()
                        wx = (pmx - (W - SB) / 2) / old_zoom + cam_x
                        wy = (pmy - H / 2) / old_zoom + cam_y
                        zoom = new_zoom
                        cam_x = wx - (pmx - (W - SB) / 2) / zoom
                        cam_y = wy - (pmy - H / 2) / zoom
                        st.cam_x, st.cam_y, st.zoom = cam_x, cam_y, zoom

            # ── Mini-map mouse control ────────────────────────────────
            if (
                e.type == pygame.MOUSEBUTTONDOWN
                and e.button == 1
                and map_rect.collidepoint(e.pos)
            ):
                map_drag = True
                cam_x = (e.pos[0] - map_rect.x) / map_scale_x
                cam_y = (e.pos[1] - map_rect.y) / map_scale_y
                st.cam_x, st.cam_y = cam_x, cam_y
                st.follow_mode = False
                follow_mode = False
            elif e.type == pygame.MOUSEMOTION and map_drag and e.buttons[0]:
                cam_x = (e.pos[0] - map_rect.x) / map_scale_x
                cam_y = (e.pos[1] - map_rect.y) / map_scale_y
                st.cam_x, st.cam_y = cam_x, cam_y
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                map_drag = False

            # ── Camera pan (middle / right button drag) ────────────────
            if e.type == pygame.MOUSEBUTTONDOWN and e.button in (2, 3):
                pan_drag = True
                pan_last = e.pos
            elif e.type == pygame.MOUSEMOTION and pan_drag:
                cam_x -= (e.pos[0] - pan_last[0]) / zoom
                cam_y -= (e.pos[1] - pan_last[1]) / zoom
                pan_last = e.pos
                st.cam_x, st.cam_y = cam_x, cam_y
                st.follow_mode = False
                follow_mode = False
            elif e.type == pygame.MOUSEBUTTONUP and e.button in (2, 3):
                pan_drag = False

            # ── Widget events ─────────────────────────────────────────
            for s in sliders:
                s.handle(e)
            # Live-bind speed/sense sliders to selected cells (while dragging)
            if sliders[0].drag or sliders[1].drag:
                for c in cells:
                    if c.selected:
                        if sliders[0].drag:
                            c.genome.speed = sliders[0].val
                        if sliders[1].drag:
                            c.genome.sense = sliders[1].val
                        c.refresh_class()
            sl_diet.handle(e)
            if int(sl_diet.val) != prev_diet:
                prev_diet = int(sl_diet.val)
                sliders[0].val = DIET_DEFAULT_SPEED[prev_diet]
                sliders[1].val = DIET_DEFAULT_SENSE[prev_diet]
            sl_interact.handle(e)
            for s in sl_dmg:
                s.handle(e)
            sl_regen.handle(e)
            sl_temp.handle(e)
            if (
                e.type == pygame.MOUSEBUTTONDOWN
                and e.button == 1
                and sl_temp.rect.collidepoint(e.pos)
            ) or (e.type == pygame.MOUSEMOTION and sl_temp.drag):
                sl_temp._bias = max(
                    -1.0, min(1.0, (sl_temp.val + 10.0) / 45.0 - season_temp)
                )
            sl_zoophagy.handle(e)
            sl_diffuse.handle(e)
            sl_time.handle(e)
            sl_sfx.handle(e)
            sl_music.handle(e)

            # Update volumes when sliders change
            import cell

            cell._sfx_volume = sl_sfx.val
            music_volume = sl_music.val
            if music_volume >= 1.0:
                music_volume_increasing = False
            elif music_volume <= 0.0:
                music_volume_increasing = True

            # ── Mouse click / marquee selection ─────────────────────
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                alt = bool(pygame.key.get_mods() & pygame.KMOD_ALT)
                # Legend/palette clicks take priority over world clicks
                if _palette_click(pop_graph, e.pos):
                    st.sel_cell = sel_cell
                    continue
                in_world = wx < W - SB and not map_rect.collidepoint(e.pos)

                hit = _pick_cell(cells, wx, wy, zoom) if in_world else None

                if hit is not None:
                    sel_cell = _apply_selection(cells, hit, shift, alt)
                    st.sel_cell = sel_cell
                elif in_world and add_mode and len(cells) < MAX_CELLS:
                    diet = int(sl_diet.val)
                    spd = sliders[0].val
                    sns = sliders[1].val
                    mass = sliders[2].val
                    metab = sliders[3].val
                    div = sliders[4].val
                    interact = sl_interact.val
                    dmg_p = sl_dmg[0].val
                    dmg_z = sl_dmg[1].val
                    dmg_pl = sl_dmg[2].val
                    gnm = Genome(
                        speed=spd,
                        sense=sns,
                        mass=mass,
                        metabolism=metab,
                        mut_rate=0.05,
                        major_mut_rate=0.005,
                        diet=diet,
                        interact=interact,
                        divide_chance=div,
                        dmg_phot=dmg_p,
                        dmg_zoop=dmg_z,
                        dmg_poly=dmg_pl,
                    )
                    nc = Cell(wx, wy, gnm)
                    cells.append(nc)

            # ── Marquee (group) selection ────────────────────────────
            if (
                e.type == pygame.MOUSEBUTTONDOWN
                and e.button == 1
                and wx < W - SB
                and not map_rect.collidepoint(e.pos)
                and not add_mode
                and _pick_cell(cells, wx, wy, zoom) is None
            ):
                marquee_active = True
                marquee_start = e.pos
                marquee_cur = e.pos
            elif e.type == pygame.MOUSEMOTION and marquee_active and e.buttons[0]:
                marquee_cur = e.pos
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1 and marquee_active:
                marquee_active = False
                shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                x1, y1 = marquee_start
                x2, y2 = marquee_cur
                if abs(x2 - x1) >= 4 and abs(y2 - y1) >= 4:
                    wx0, wy0 = screen_to_world(x1, y1, cam_x, cam_y, zoom)
                    wx1, wy1 = screen_to_world(x2, y2, cam_x, cam_y, zoom)
                    st.sel_cell = _select_in_rect(cells, wx0, wy0, wx1, wy1, shift)

        # Re-sync hotkey-mutated state back into locals
        paused = st.paused
        add_mode = st.add_mode
        time_lapse_mode = st.time_lapse_mode
        show_stats = st.show_stats
        follow_mode = st.follow_mode
        field = st.field
        sel_cell = st.sel_cell
        running = st.running
        cam_x = st.cam_x
        cam_y = st.cam_y
        zoom = st.zoom
        sfx_volume = st.sfx_volume
        sfx_volume_increasing = st.sfx_volume_increasing
        music_volume_increasing = st.music_volume_increasing

        # Music fade-in: gradually raise volume from 0 to target over 5 seconds
        if music_fade_timer < music_fade_duration:
            music_fade_timer += 1
            fade_progress = music_fade_timer / music_fade_duration
            pygame.mixer.music.set_volume(music_volume * fade_progress)
        else:
            pygame.mixer.music.set_volume(music_volume)

        # Keep speed/sense sliders in sync with the selected cell (unless dragging)
        if sel_cell is not None and not sliders[0].drag and not sliders[1].drag:
            sliders[0].val = sel_cell.genome.speed
            sliders[1].val = sel_cell.genome.sense

        # Debug print every 100 ticks
        if not paused:
            tick += 1
            if tick % 100 == 0:
                print(f"Tick: {tick}, Cells: {len(cells)}")

            # Temperature: seasons drive it, slider bias offsets it — moves gradually
            target_temp = max(0.0, min(1.0, season_temp + sl_temp._bias))
            field.temperature += (target_temp - field.temperature) * TEMP_SMOOTH_RATE
            sl_temp.val = -10.0 + field.temperature * 45.0

            # Food regen: smooth season multiplier (interpolate toward next season)
            regen_mult_target = season_factor["regen_mult"]
            regen_mult_target += (
                SEASON_FACTORS[SEASON_ORDER[(season_idx + 1) % 4]]["regen_mult"]
                - regen_mult_target
            ) * season_progress

            # Food regen: slider is a % (0–100), moves toward target gradually.
            # The slider shows the EFFECTIVE % (base × season × temperature);
            # dragging it sets the base % (temperature/season scaled back out).
            regen_mult = regen_mult_target * field._get_temp_regen_factor()
            if sl_regen.drag and regen_mult > 0.0:
                regen_base = min(100.0, max(0.0, sl_regen.val / regen_mult))
            sl_regen.val = min(100.0, regen_base * regen_mult)
            target_regen = (regen_base / 100.0) * REGEN_MAX_RATE * regen_mult_target
            field.base_regen += (target_regen - field.base_regen) * REGEN_SMOOTH_RATE

            # Field update
            field.diff = sl_diffuse.val
            field.zoophagy_mult = sl_zoophagy.val
            field.step(dt, len(cells))

            # Simulation
            if _HAVE_SIM_CORE:
                for c in cells:
                    c.sensory_phase(field, cells, None, dt)
                n = len(cells)
                if n > 0:
                    xs = np.array([c.x for c in cells], dtype=np.float64)
                    ys = np.array([c.y for c in cells], dtype=np.float64)
                    de = np.array([c.energy for c in cells], dtype=np.float64)
                    di = np.array([c.genome.diet for c in cells], dtype=np.int32)
                    sp = np.array([c.genome.speed for c in cells], dtype=np.float64)
                    ma = np.array([c.genome.mass for c in cells], dtype=np.float64)
                    me = np.array(
                        [c.genome.metabolism for c in cells], dtype=np.float64
                    )
                    le = np.array([c.level for c in cells], dtype=np.int32)
                    ag = np.array([c.aggression for c in cells], dtype=np.float64)
                    bdx = np.array([c.best_dir[0] for c in cells], dtype=np.float64)
                    bdy = np.array([c.best_dir[1] for c in cells], dtype=np.float64)
                    rt = np.array(
                        [
                            (
                                1
                                if c.reaction_type == "flee"
                                else (2 if c.reaction_type == "attack" else 0)
                            )
                            for c in cells
                        ],
                        dtype=np.int8,
                    )
                    rtm = np.array([c.reaction_timer for c in cells], dtype=np.int32)
                    rta = np.array(
                        [
                            (
                                next(
                                    (
                                        j
                                        for j, oc in enumerate(cells)
                                        if oc is c.reaction_target
                                    ),
                                    -1,
                                )
                                if c.reaction_target
                                else -1
                            )
                            for c in cells
                        ],
                        dtype=np.int32,
                    )
                    td = np.zeros(n, dtype=np.int8)
                    fd = field.data.copy()

                    apply_physics(xs, ys, bdx, bdy, sp, dt)
                    apply_metabolism_and_feeding(xs, ys, de, di, sp, ma, me, le, fd, dt)
                    field.data[:] = fd

                    for i, c in enumerate(cells):
                        c.x = float(xs[i])
                        c.y = float(ys[i])
                        c.energy = float(de[i])
                        c.genome.mass = float(ma[i])
                        c.level = int(le[i])

                    for c in cells:
                        if c.energy > 0:
                            c.post_step(field, cells, None, td, dt, 0)
            else:
                grid = build_spatial_grid(cells)
                for c in cells:
                    if c.energy > 0:
                        c.step(field, cells, grid, dt, 0)

            # ── Corpse feeding, death & decomposition ────────────────
            eat_corpses(cells, corpses, dt)
            process_deaths(cells, field, corpses)
            for cp in corpses[:]:
                cp.update(dt)
                if cp.done:
                    corpses.remove(cp)

            # ── Camera follows the selected cell ─────────────────────
            if follow_mode and sel_cell is not None:
                if sel_cell in cells:
                    # Smooth camera following with interpolation for fluid motion
                    # Target position is the selected cell
                    target_cam_x, target_cam_y = sel_cell.x, sel_cell.y

                    # Calculate current camera position relative to world coordinates
                    # Current camera position is already in world coordinates (cam_x, cam_y)
                    # Calculate smooth interpolation factor (0.1 for smooth follow)
                    follow_speed = 0.15

                    # Interpolate camera position toward target
                    new_cam_x = cam_x + (target_cam_x - cam_x) * follow_speed
                    new_cam_y = cam_y + (target_cam_y - cam_y) * follow_speed

                    # Update camera position
                    cam_x, cam_y = new_cam_x, new_cam_y
                    st.cam_x, st.cam_y = cam_x, cam_y
                else:
                    follow_mode = False
                    st.follow_mode = False

            # ── Time-lapse recording (DEV_PLAN Phase 3.1) ─────────────────────────────────
            if time_lapse_active:
                # Capture a frame
                frame_surface = pygame.Surface((W - SB, H))
                frame_surface.fill(BG)

                # Draw the scene
                field.draw(frame_surface, season_name)
                for cp in corpses:
                    if -50 < cp.x < W - SB + 50 and -50 < cp.y < H + 50:
                        cp.draw_at(frame_surface, cp.x, cp.y)
                for c in cells:
                    if -50 < c.x < W - SB + 50 and -50 < c.y < H + 50:
                        c.draw_at(frame_surface, c.x, c.y)

                # Draw UI elements
                pygame.draw.rect(frame_surface, DARK, (W - SB, 0, SB, H))
                title_surf = big.render("LIFE_GPT", True, CYAN)
                frame_surface.blit(title_surf, (W - SB + (SB - title_surf.get_width()) // 2, 10))
                hint_surf = small.render(tr("hint_add"), True, WHITE)
                frame_surface.blit(hint_surf, (W - SB + (SB - hint_surf.get_width()) // 2, 40))

                for s in sliders:
                    s.draw(frame_surface, font)
                sl_diet.draw(frame_surface, font)
                sl_interact.draw(frame_surface, font)
                sl_zoophagy.draw(frame_surface, font)
                for s in sl_dmg:
                    s.draw(frame_surface, font)
                sl_regen.draw(frame_surface, font)
                sl_temp.draw(frame_surface, font)
                sl_diffuse.draw(frame_surface, font)
                sl_time.draw(frame_surface, font)
                sl_sfx.draw(frame_surface, font)
                sl_music.draw(frame_surface, font)

                # Save frame
                pygame.image.save(frame_surface, f"frames/frame_{frame_count:06d}.png")
                frame_count += 1

                # Auto-stop after specified duration
                time_lapse_timer += 1
                if time_lapse_timer >= time_lapse_duration * 60:  # Convert minutes to ticks
                    time_lapse_active = False
                    st.time_lapse_active = False
                    print(f"Time-lapse recording complete: {frame_count} frames saved")

        # ── Render ──────────────────────────────────────────────────────────────
        screen.fill(BG)

        # 1. Build world at native (unzoomed) resolution
        world_w, world_h = W - SB, H
        if scaled_surf is None or prev_zoom != zoom:
            scaled_surf = pygame.Surface((world_w, world_h))
        else:
            scaled_surf.fill(BG)
        world_surf = scaled_surf  # reuse

        field.draw(world_surf, season_name)
        for cp in corpses:
            if -50 < cp.x < world_w + 50 and -50 < cp.y < world_h + 50:
                cp.draw_at(world_surf, cp.x, cp.y)
        for c in cells:
            if -50 < c.x < world_w + 50 and -50 < c.y < world_h + 50:
                c.draw_at(world_surf, c.x, c.y)

        # 2. Scale to zoom
        sw = max(1, int(world_w * zoom))
        sh = max(1, int(world_h * zoom))
        scaled = pygame.transform.smoothscale(world_surf, (sw, sh))

        # 3. Center on camera
        dx = (W - SB) // 2 - int(cam_x * zoom)
        dy = H // 2 - int(cam_y * zoom)
        sx = max(0, -dx)
        sy = max(0, -dy)
        dx = max(0, dx)
        dy = max(0, dy)
        src_w = min(scaled.get_width() - sx, W - SB - dx)
        src_h = min(scaled.get_height() - sy, H - dy)
        src_w = max(0, src_w)
        src_h = max(0, src_h)
        if src_w > 0 and src_h > 0:
            screen.blit(scaled, (dx, dy), (int(sx), int(sy), int(src_w), int(src_h)))

        # ── Marquee selection rectangle ─────────────────────────────────
        if marquee_active:
            x1, y1 = marquee_start
            x2, y2 = marquee_cur
            rx, ry = min(x1, x2), min(y1, y2)
            rw, rh = abs(x2 - x1), abs(y2 - y1)
            if rw > 2 and rh > 2:
                sel_surf = pygame.Surface((rw, rh), pygame.SRCALPHA)
                sel_surf.fill((120, 180, 255, 36))
                screen.blit(sel_surf, (rx, ry))
                pygame.draw.rect(screen, (120, 180, 255), (rx, ry, rw, rh), 1)

        # ── UI: Sidebar background ────────────────────────────────────────
        pygame.draw.rect(screen, DARK, (W - SB, 0, SB, H))

        # ── UI: Sidebar header ─────────────────────────────────────────
        title_surf = big.render("LIFE_GPT", True, CYAN)
        screen.blit(title_surf, (W - SB + (SB - title_surf.get_width()) // 2, 10))
        hint_surf = small.render(tr("hint_add"), True, WHITE)
        screen.blit(hint_surf, (W - SB + (SB - hint_surf.get_width()) // 2, 40))

        # ── UI: Parameter block boxes ────────────────────────────────────
        def draw_block(y, h, title):
            pygame.draw.rect(screen, GRAY, (COL_LX - 5, y, COL_W + 10, h), 1, 4)
            t = font.render(title, True, CYAN)
            screen.blit(t, (COL_LX + COL_W // 2 - t.get_width() // 2, y + 5))

        draw_block(68, 286, tr("genes"))
        draw_block(356, 98, tr("damage"))
        draw_block(456, 185, tr("environment"))

        # ── UI: Sliders & labels ─────────────────────────────────────────
        for s in sliders:
            s.draw(screen, font)
        sl_diet.draw(screen, font)
        sl_interact.draw(screen, font)
        sl_zoophagy.draw(screen, font)
        for s in sl_dmg:
            s.draw(screen, font)
        sl_regen.draw(screen, font)
        sl_temp.draw(screen, font)
        sl_diffuse.draw(screen, font)
        sl_time.draw(screen, font)
        sl_sfx.draw(screen, font)
        sl_music.draw(screen, font)

        # ── UI: Right column — selected cell info / hotkeys ──────────────
        panel_y = 68
        pygame.draw.rect(screen, GRAY, (COL_RX - 5, panel_y, COL_W + 10, 350), 1, 4)
        if sel_cell:
            lines = [
                f"{tr('selected')}:",
                f"  {tr('energy')}: {sel_cell.energy:.1f} / {sel_cell.max_energy:.1f}",
                f"  {tr('level')}: {sel_cell.level} / {MAX_LEVEL}",
                f"  {tr('age')}: {sel_cell.age} / {sel_cell.genome.lifespan_ticks}",
                f"  {tr('speed')}: {sel_cell.genome.speed:.2f} / {sliders[0].mx:.2f}",
                f"  {tr('sense')}: {sel_cell.genome.sense:.0f} / {sliders[1].mx:.0f}",
                f"  {tr('mass')}: {sel_cell.genome.mass:.2f} / {sliders[2].mx:.2f}",
                f"  {tr('metabolism')}: {sel_cell.genome.metabolism:.3f} / {sliders[3].mx:.3f}",
                f"  {tr('diet')}: {tr_diet(sel_cell.genome.diet)}",
                f"  {tr('interact')}: {sel_cell.genome.interact:.2f} / {sl_interact.mx:.2f}",
                f"  {tr('divide_chance')}: {sel_cell.genome.divide_chance:.2f} / {sliders[4].mx:.2f}",
            ]
            for i, line in enumerate(lines):
                surf = font.render(line, True, WHITE)
                screen.blit(surf, (COL_RX + 5, panel_y + 8 + i * 18))
        else:
            t = font.render(tr("hotkeys"), True, CYAN)
            screen.blit(t, (COL_RX + COL_W // 2 - t.get_width() // 2, panel_y + 5))
            hotkey_lines = [
                tr("hotkey_space"),
                tr("hotkey_a"),
                tr("hotkey_s"),
                tr("hotkey_c"),
                tr("hotkey_r"),
                tr("hotkey_f"),
                tr("hotkey_f5"),
                tr("hotkey_esc"),
                tr("hotkey_1"),
                tr("hotkey_qwe"),
                tr("hotkey_pm"),
                tr("hotkey_ud"),
                tr("hotkey_x"),
                tr("hotkey_d"),
                tr("hotkey_m"),
                tr("hotkey_tab"),
                tr("hotkey_z"),
                tr("hotkey_b"),
                tr("hotkey_l"),
            ]
            for i, hk in enumerate(hotkey_lines):
                surf = small.render(hk, True, WHITE)
                screen.blit(surf, (COL_RX + 5, panel_y + 28 + i * 16))


        # ── UI: Stats (top-left) ─────────────────────────────────────────
        if show_stats:
            import cell
            food_pct = field.data.mean() * 100
            stats = [
                f"{tr('cells')}: {len(cells)}/{MAX_CELLS} ({tr('dead')}: {len(corpses)})",
                f"{tr('tick')}: {tick}",
                f"{tr('divisions')}: {cell.divisions}",
                f"{tr('food')}: {food_pct:.1f}%",
                f"{tr('season')}: {tr(season_name)}",
                f"{tr('temp')}: {-10.0 + field.temperature * 45.0:.1f}°C",
                f"{tr('zoom')}: {zoom:.2f}x",
                f"{tr('paused')}: {'Yes' if paused else 'No'}",
                tr("follow").format("On" if follow_mode else "Off"),
                f"{tr('timelapse')}: {'On' if time_lapse_mode else 'Off'}",
            ]
            # ── UI: Memory/Threat/Coop display (if show_memory enabled) ─────────────────────────
            if show_memory and sel_cell:
                if hasattr(sel_cell, 'memory'):
                    mem_stats = []
                    # Add general memory info
                    mem_stats.append(f"Memory classes: {len(sel_cell.memory)}")
                    # Add detailed threat/coop info for each class learned
                    if hasattr(sel_cell.memory, 'summary'):
                        summary = sel_cell.memory.summary()
                        for cls, (threat, coop, encounters) in summary.items():
                            mem_stats.append(f"  Class {cls}: Threat {threat:.2f}, Coop {coop:.2f}, Encounters {encounters}")
                    else:
                        mem_stats.append("  No summary method")
                    # Display memory info
                    for i, line in enumerate(mem_stats):
                        surf = font.render(line, True, (200, 255, 200))
                        screen.blit(surf, (10, 10 + (len(stats) + i) * 22))
                else:
                    surf = font.render("No memory for selected cell", True, (200, 200, 200))
                    screen.blit(surf, (10, 10 + len(stats) * 22))
            for i, line in enumerate(stats):
                surf = font.render(line, True, WHITE)
                screen.blit(surf, (10, 10 + i * 22))

        # ── UI: Mini-map (right column) ─────────────────────────────────
        map_surf = pygame.Surface((map_size, map_size))
        if hasattr(field, "_fsurf"):
            # Downscale the field surface to show nutrient-value density
            pygame.transform.smoothscale(field._fsurf, (map_size, map_size), map_surf)
        else:
            map_surf.fill((30, 30, 30))
        for c in cells:
            if 0 <= c.x < world_w and 0 <= c.y < world_h:
                px = int(c.x * map_scale_x)
                py = int(c.y * map_scale_y)
                if c.genome.diet == PHOT:
                    col = diet_color(PHOT, c.cls)
                elif c.genome.diet == ZOOP:
                    col = diet_color(ZOOP, c.cls)
                else:
                    col = diet_color(POLY, c.cls)
                map_surf.set_at((px, py), col)
        # Dead cells (corpses)
        for cp in corpses:
            if 0 <= cp.x < world_w and 0 <= cp.y < world_h:
                map_surf.set_at(
                    (int(cp.x * map_scale_x), int(cp.y * map_scale_y)),
                    (150, 90, 90),
                )
        # Camera rect
        cam_rect = pygame.Rect(
            int((cam_x - (W - SB) / 2 / zoom) * map_scale_x),
            int((cam_y - H / 2 / zoom) * map_scale_y),
            max(2, int((W - SB) / zoom * map_scale_x)),
            max(2, int(H / zoom * map_scale_y)),
        )
        pygame.draw.rect(map_surf, WHITE, cam_rect, 1)
        pygame.draw.rect(
            screen, GRAY, (COL_RX - 5, 430, COL_W + 10, map_size + 31), 1, 4
        )
        mt = small.render(tr("minimap"), True, CYAN)
        screen.blit(mt, (COL_RX + COL_W // 2 - mt.get_width() // 2, 435))
        screen.blit(map_surf, (map_rect.x, map_rect.y))

        # ── UI: Population graph ────────────────────────────────────────
        pygame.draw.rect(screen, GRAY, (COL_LX - 5, 651, COL_W + 10, 108), 1, 4)
        gt = font.render(tr("population_graph"), True, CYAN)
        screen.blit(gt, (COL_LX + COL_W // 2 - gt.get_width() // 2, 656))
        pop_graph.update(tick, cells)
        pop_graph.draw(screen, COL_LX, 677, COL_W, 76)

        # ── UI: Legend / palette (drawn AFTER graph so it's on top) ─────
        group_labels = {
            PHOT: tr("diet_phot"),
            ZOOP: tr("diet_zoop"),
            POLY: tr("diet_poly"),
        }
        for kind, cx, cy, rect in _palette_group_dots():
            if kind == "total":
                color = YEL
                label = tr("total")
                active = pop_graph.show_total
                if active:
                    pygame.draw.circle(screen, color, (cx, cy), _LEGEND_DOT_R)
                else:
                    pygame.draw.circle(screen, color, (cx, cy), _LEGEND_DOT_R, 1)
                    r = _LEGEND_DOT_R - 3
                    pygame.draw.line(screen, RED, (cx - r, cy - r), (cx + r, cy + r), 2)
                    pygame.draw.line(screen, RED, (cx - r, cy + r), (cx + r, cy - r), 2)
            else:
                color = diet_color(kind, 10)
                label = group_labels[kind]
                diet_hidden = not any(
                    pop_graph.cls_visible.get(c, True)
                    for c, d in pop_graph.cls_diet.items()
                    if d == kind
                )
                if diet_hidden:
                    pygame.draw.circle(screen, color, (cx, cy), _LEGEND_DOT_R, 1)
                    r = _LEGEND_DOT_R - 3
                    pygame.draw.line(screen, RED, (cx - r, cy - r), (cx + r, cy + r), 2)
                    pygame.draw.line(screen, RED, (cx - r, cy + r), (cx + r, cy - r), 2)
                else:
                    pygame.draw.circle(screen, color, (cx, cy), _LEGEND_DOT_R)
            surf = tiny.render(label, True, WHITE)
            screen.blit(surf, (cx - surf.get_width() // 2, cy + 14))
        # Scrollable per-class palette — three groups by diet
        for diet_id, grid_rect, label_key in [
            (PHOT, _LEGEND_GRID_RECT_PHOT, "diet_phot"),
            (ZOOP, _LEGEND_GRID_RECT_ZOOP, "diet_zoop"),
            (POLY, _LEGEND_GRID_RECT_POLY, "diet_poly"),
        ]:
            diet_label = tiny.render(tr(label_key), True, diet_color(diet_id, 10))
            screen.blit(diet_label, (grid_rect.x, grid_rect.y - 12))
            pal_entries, offset, total = _palette_class_grid(pop_graph, diet_filter=diet_id, grid_rect=grid_rect)
            for cls, rect, color, visible in pal_entries:
                if visible:
                    pygame.draw.circle(screen, color, rect.center, _LEGEND_CLASS_R)
                else:
                    pygame.draw.circle(screen, color, rect.center, _LEGEND_CLASS_R, 1)
                    r = _LEGEND_CLASS_R - 2
                    cx, cy = rect.center
                    pygame.draw.line(screen, RED, (cx - r, cy - r), (cx + r, cy + r), 1)
                    pygame.draw.line(screen, RED, (cx - r, cy + r), (cx + r, cy - r), 1)

        # ── SFX / Music volume indicators ───────────────────────────────
        pygame.draw.rect(screen, GRAY, (COL_RX - 5, 696, COL_W + 10, 90), 1, 4)
        gs_title = font.render(tr("game_settings"), True, CYAN)
        screen.blit(
            gs_title,
            (COL_RX + COL_W // 2 - gs_title.get_width() // 2, 701),
        )

        # ── UI: FPS (bottom-right corner) ────────────────────────────────
        fps_text = f"FPS: {clock.get_fps():.0f}"
        fps_surf = font.render(fps_text, True, WHITE)
        screen.blit(fps_surf, (W - fps_surf.get_width() - 10, H - 24))

        pygame.display.flip()
        prev_zoom = zoom


if __name__ == "__main__":
    main()
