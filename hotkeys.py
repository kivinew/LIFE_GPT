# ═══════════════════════════════════════════════════════════════════════
#  hotkeys.py — keyboard shortcuts for LIFE_GPT
#  Handlers mutate a HotkeyState object; main() re-syncs its locals from it.
# ═══════════════════════════════════════════════════════════════════════
import pygame

import config
from config import (
    W,
    H,
    MAX_CELLS,
    PHOT,
    ZOOP,
    POLY,
    tr,
    DIET_DEFAULT_SPEED,
    DIET_DEFAULT_SENSE,
    TEMP_MUT_DEFAULT,
)
from cell import Cell, play_sound
from field import ResourceField
from genome import Genome
from saveload import save_cells, load_saved_cells, SAVE_FILE


class HotkeyState:
    __slots__ = (
        "cells",
        "corpses",
        "field",
        "paused",
        "add_mode",
        "time_lapse_mode",
        "show_stats",
        "show_energy_bars",
        "show_level_bars",
        "follow_mode",
        "sel_cell",
        "running",
        "sfx_volume",
        "sfx_volume_increasing",
        "music_volume_increasing",
        "sliders",
        "sl_diet_val",
        "sl_interact",
        "sl_dmg",
        "sl_regen",
        "sl_temp",
        "sl_zoophagy",
        "sl_diffuse",
        "sl_time",
        "sl_food_lifetime",
        "sl_sfx",
        "sl_music",
        "cam_x",
        "cam_y",
        "zoom",
        "show_memory",
    )

    def __init__(self, **kwargs):
        for name in self.__slots__:
            setattr(self, name, kwargs.get(name))
        self.show_memory = kwargs.get("show_memory", False)


# ── Preset templates ──────────────────────────────────────────────────
TEMPLATES = [
    {
        "name": tr("template_balanced"),
        "genes": Genome(
            speed=1.5,
            sense=40,
            mass=4.0,
            metabolism=0.04,
            mut_rate=0.05,
            major_mut_rate=0.005,
            diet=PHOT,
            interact=0.5,
            divide_chance=0.5,
            dmg_phot=0.6,
            dmg_zoop=1.2,
            dmg_poly=1.0,
            lifespan_ticks=10000,
        ),
    },
    {
        "name": tr("template_hunter"),
        "genes": Genome(
            speed=4.0,
            sense=120,
            mass=5.0,
            metabolism=0.08,
            mut_rate=0.08,
            major_mut_rate=0.01,
            diet=ZOOP,
            interact=0.8,
            divide_chance=0.3,
            dmg_phot=0.6,
            dmg_zoop=2.0,
            dmg_poly=1.5,
            lifespan_ticks=8000,
        ),
    },
    {
        "name": tr("template_gatherer"),
        "genes": Genome(
            speed=2.0,
            sense=90,
            mass=4.5,
            metabolism=0.05,
            mut_rate=0.06,
            major_mut_rate=0.008,
            diet=POLY,
            interact=0.4,
            divide_chance=0.4,
            dmg_phot=1.0,
            dmg_zoop=1.5,
            dmg_poly=1.2,
            lifespan_ticks=9000,
        ),
    },
]


def _selected(cells):
    return [c for c in cells if c.selected]


def _set_interact(cells, value):
    for c in cells:
        if c.selected:
            c.genome.interact = round(value, 2)
            c.refresh_class()


def _set_diet(st, diet):
    # Class defaults: speed/sense follow the diet (PHOT min, POLY mid, ZOOP max)
    st.sl_diet_val = diet
    st.sliders[0].val = DIET_DEFAULT_SPEED[diet]
    st.sliders[1].val = DIET_DEFAULT_SENSE[diet]
    for c in st.cells:
        if c.selected:
            c.genome.diet = diet
            c.genome.speed = DIET_DEFAULT_SPEED[diet]
            c.genome.sense = DIET_DEFAULT_SENSE[diet]
            c.refresh_class()


def _set_speed(cells, delta):
    for c in cells:
        if c.selected:
            c.genome.speed = min(4.0, max(0.5, c.genome.speed + delta))
            c.refresh_class()


def _set_sense(cells, delta):
    for c in cells:
        if c.selected:
            c.genome.sense = min(120, max(30, c.genome.sense + delta))
            c.refresh_class()


def _apply_labels(st):
    for s in st.sliders:
        s.label = tr(s.label_key)
    st.sl_interact.label = tr("interact")
    for i, s in enumerate(st.sl_dmg):
        s.label = [tr("dmg_phot"), tr("dmg_zoo"), tr("dmg_poly")][i]
    st.sl_regen.label = tr("food_regen")
    st.sl_temp.label = tr("temp")
    st.sl_zoophagy.label = tr("zoophagy")
    st.sl_diffuse.label = tr("food_diffuse")
    st.sl_time.label = tr("time_scale")
    st.sl_food_lifetime.label = tr("food_lifetime")
    st.sl_sfx.label = tr("sfx")
    st.sl_music.label = tr("music")


def _load_last_saved(st):
    saved = load_saved_cells()
    if saved and len(st.cells) < MAX_CELLS:
        gdict = saved[-1].get("genes", saved[-1])
        gnm = Genome(
            speed=gdict.get("speed", 1.5),
            sense=gdict.get("sense", 40),
            metabolism=gdict.get("metabolism", 0.02),
            mut_rate=gdict.get("mut_rate", 0.05),
            major_mut_rate=gdict.get("major_mut_rate", 0.005),
            diet=gdict.get("diet", 0),
            interact=gdict.get("interact", 0.5),
            div=gdict.get("divide_chance", 0.5),
            mass=gdict.get("mass", 4.0),
            dmg_phot=gdict.get("dmg_phot", 0.6),
            dmg_zoop=gdict.get("dmg_zoop", 1.2),
            dmg_poly=gdict.get("dmg_poly", 1.0),
            lifespan_ticks=gdict.get("lifespan_ticks"),
        )
        st.cells.append(Cell(W // 2, H // 2, gnm))


def _save_selected(st):
    sel = _selected(st.cells)
    save_cells(sel if sel else st.cells)
    print(f"Saved {len(sel) if sel else len(st.cells)} cell(s) to {SAVE_FILE}")


def _cycle_sfx(st):
    import cell

    step = 0.10
    st.sfx_volume += step if st.sfx_volume_increasing else -step
    if st.sfx_volume >= 1.0:
        st.sfx_volume = 1.0
        st.sfx_volume_increasing = False
    elif st.sfx_volume <= 0.0:
        st.sfx_volume = 0.0
        st.sfx_volume_increasing = True
    cell._sfx_volume = st.sfx_volume
    st.sl_sfx.val = st.sfx_volume
    print(f"SFX volume: {int(st.sfx_volume * 100)}%")


def _cycle_music(st):
    step = 0.10
    v = st.sl_music.val
    if v >= 1.0:
        st.music_volume_increasing = False
    elif v <= 0.0:
        st.music_volume_increasing = True
    st.sl_music.val = max(
        0.0, min(1.0, v + (step if st.music_volume_increasing else -step))
    )
    pygame.mixer.music.set_volume(st.sl_music.val)
    print(f"Music volume: {int(st.sl_music.val * 100)}%")


def handle_key(e, st):
    k = e.key

    if k == pygame.K_SPACE:
        st.paused = not st.paused

    elif k == pygame.K_a:
        st.add_mode = True
    elif k == pygame.K_s:
        st.add_mode = False

    elif k == pygame.K_c:
        st.cells.clear()
        st.corpses.clear()
    elif k == pygame.K_r:
        st.field = ResourceField(st.field.w, st.field.h)
        st.corpses.clear()
    elif k == pygame.K_t:
        st.time_lapse_mode = not st.time_lapse_mode

    elif k == pygame.K_f:
        _load_last_saved(st)

    elif k == pygame.K_F5:
        _save_selected(st)

    elif k == pygame.K_l:
        config.LANG = "en" if config.LANG == "ru" else "ru"
        _apply_labels(st)

    elif k == pygame.K_q:
        _set_interact(st.cells, 0.2)
    elif k == pygame.K_w:
        _set_interact(st.cells, 0.5)
    elif k == pygame.K_e:
        _set_interact(st.cells, 0.8)

    elif k == pygame.K_1 and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
        _set_diet(st, PHOT)
    elif k == pygame.K_2 and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
        _set_diet(st, ZOOP)
    elif k == pygame.K_3 and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
        _set_diet(st, POLY)

    elif k == pygame.K_x:
        temp = st.field.temperature if st.field else TEMP_MUT_DEFAULT
        for c in st.cells:
            if c.selected:
                c.genome = c.genome.clone_mutate(temp)
                c.refresh_class()
                play_sound("mutation")
    elif k == pygame.K_d:
        st.cells[:] = [c for c in st.cells if not c.selected]

    elif k == pygame.K_EQUALS or k == pygame.K_KP_PLUS:
        _set_speed(st.cells, 0.1)
    elif k == pygame.K_MINUS or k == pygame.K_KP_MINUS:
        _set_speed(st.cells, -0.1)
    elif k == pygame.K_UP:
        _set_sense(st.cells, 5)
    elif k == pygame.K_DOWN:
        _set_sense(st.cells, -5)

    elif k == pygame.K_m and (getattr(e, "mod", 0) & pygame.KMOD_ALT):
        _cycle_sfx(st)
    elif k == pygame.K_m:
        _cycle_music(st)
    elif k == pygame.K_TAB:
        st.show_stats = not st.show_stats
    elif k == pygame.K_m and (getattr(e, "mod", 0) & pygame.KMOD_CTRL):
        st.show_memory = not st.show_memory

    elif k == pygame.K_z:
        if st.sel_cell is not None:
            st.cam_x = st.sel_cell.x
            st.cam_y = st.sel_cell.y
            st.zoom = 3.0
            st.follow_mode = True
    elif k == pygame.K_b:
        if st.sel_cell is not None:
            st.follow_mode = not st.follow_mode
            if st.follow_mode:
                st.cam_x = st.sel_cell.x
                st.cam_y = st.sel_cell.y
    elif k == pygame.K_f:
        st.follow_mode = False
        if st.sel_cell is not None:
            st.cam_x, st.cam_y = st.sel_cell.x, st.sel_cell.y

    elif k == pygame.K_e:
        st.show_energy_bars = not st.show_energy_bars
        print(f"Energy bars: {'ON' if st.show_energy_bars else 'OFF'}")
    elif k == pygame.K_v:
        st.show_level_bars = not st.show_level_bars
        print(f"Level bars: {'ON' if st.show_level_bars else 'OFF'}")

    elif k == pygame.K_ESCAPE:
        if _selected(st.cells):
            for c in st.cells:
                c.selected = False
            st.sel_cell = None
        else:
            st.running = False

    elif k == pygame.K_1 and (pygame.key.get_mods() & pygame.KMOD_CTRL):
        if len(st.cells) < MAX_CELLS:
            temp = st.field.temperature if st.field else TEMP_MUT_DEFAULT
            st.cells.append(Cell(W // 2, H // 2, TEMPLATES[0]["genes"].clone_mutate(temp)))
    elif k == pygame.K_2 and (pygame.key.get_mods() & pygame.KMOD_CTRL):
        if len(st.cells) < MAX_CELLS:
            temp = st.field.temperature if st.field else TEMP_MUT_DEFAULT
            g = TEMPLATES[1]["genes"].clone_mutate(temp)
            g.speed = 4.0
            st.cells.append(Cell(W // 2, H // 2, g))
    elif k == pygame.K_3 and (pygame.key.get_mods() & pygame.KMOD_CTRL):
        if len(st.cells) < MAX_CELLS:
            temp = st.field.temperature if st.field else TEMP_MUT_DEFAULT
            g = TEMPLATES[2]["genes"].clone_mutate(temp)
            g.sense = 90.0
            st.cells.append(Cell(W // 2, H // 2, g))

    elif k == pygame.K_HOME:
        st.cam_x, st.cam_y, st.zoom = 0.0, 0.0, 1.0
        st.follow_mode = False
