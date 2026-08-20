# Configuration and constants for LIFE_GPT cellular evolution simulation
# ── Screen & layout ───────────────────────────────────────────────
W, H = 1600, 900
SB = 600

# ── Fixed-step simulation ────────────────────────────────────────
FIXED_DT = 1.0 / 60.0  # Fixed timestep (1/60 s) for deterministic simulation
MAX_FRAME_SKIP = 5      # Max simulation steps per frame to prevent spiral of death

# ── Colors (R,G,B) ───────────────────────────────────────────────
BG = (15, 16, 20)
WHITE = (230, 230, 230)
GRAY = (100, 105, 120)
DARK = (25, 28, 35)
BLUE = (80, 150, 255)
YEL = (255, 220, 80)
CYAN = (100, 200, 255)
GREEN = (80, 255, 100)
RED = (220, 60, 60)
LEVEL_COLOR = (255, 200, 60)
TEAL = (150, 180, 100)

# ── Cell diet types ──────────────────────────────────────────────
PHOT = 0
ZOOP = 1
POLY = 2

# Default speed/sense per diet class (PHOT min, POLY mid, ZOOP max)
# Used by Genome when speed/sense are not specified explicitly.
DIET_DEFAULT_SPEED = {PHOT: 0.5, ZOOP: 4.0, POLY: 2.0}
DIET_DEFAULT_SENSE = {PHOT: 30.0, ZOOP: 120.0, POLY: 65.0}

# Global movement scale multiplier applied to all cell displacement.
# Speed values are ~px/sec; multiplied by FIXED_DT (1/60) per tick they yield
# <1px/tick, so cells crawl. This lifts the effective per-tick displacement to a
# visible, huntable rate while staying tunable in one place.
MOVEMENT_SCALE = 80.0  # doubled for faster visible movement  # ~PHOT 20, POLY 80, ZOOP 160 px/sec

# ── Energy coefficients ──────────────────────────────────────────
ENERGY_MASS_COEFF = 4.5  # Was 5.5 — reduced to prevent cells living too long
DRAW_ENERGY_MASS_COEFF = 4.5
STRESS_ENERGY_GAIN = 12.0
STRESS_MASS_LOSS = 0.25
STRESS_ENERGY_THRESHOLD = 5.0
STRESS_MASS_MIN = 2.0
REGEN_MAX_RATE = 0.1  # max per-tick food energy added to 200 random cells (slider 100%)
REGEN_SMOOTH_RATE = 0.03  # base_regen moves toward target by this fraction per tick

# ── Metabolism ───────────────────────────────────────────────────
BASE_METABOLISM_MULT = 1.0
PREDATOR_METABOLISM_MULT = 0.55  # Was 0.75 — reduced to help ZOOP survive longer
SPEED_COST = 0.05
MASS_PENALTY = 0.003
FEED_EFFICIENCY_BASE = 22.0   # good feed gain
PHOT_FEED_EFFICIENCY = 1.0
POLY_FEED_EFFICIENCY = 0.7
MIN_MASS_EFFICIENCY = 0.55

# ── Combat ───────────────────────────────────────────────────────
COMBAT_BASE_DAMAGE = 0.9  # Was 1.0 — reduced to prevent ZOOP from killing too fast
COMBAT_DAMAGE_GAIN = 0.8  # Was 0.6 — increased to give ZOOP better reward for hunting
MASS_DMG_EFFICIENCY = 0.035
MIN_MASS_DMG_EFF = 0.45

# ── Level system ─────────────────────────────────────────────────
LEVEL_UP_THRESHOLD = 0.85  # high — cells need nearly full energy to level up
# ── Division conditions ─────────────────────────────────────
DIVIDE_ENERGY_RATIO = 0.65
DIVIDE_MIN_AGE = 100
LEVEL_DOWN_THRESHOLD = 0.25   # Was 3.0 — lose level at 25% energy
MAX_LEVEL = 10
LEVEL_MASS_BASE = 2.0
LEVEL_MASS_STEP = 0.6

# ── Lifespan / aging ─────────────────────────────────────────────

# Disease system
DISEASE_CHANCE = 0.001
DISEASE_DURATION = 500
DISEASE_METABOLISM_MULT = 2.0
DISEASE_TRANSMISSION_RANGE = 50.0

# Migration (gradual relocation when starving — not a teleport)
MIGRATION_CHANCE = 0.0005
MIGRATION_DISTANCE = 12.0
MIGRATION_COOLDOWN = 500   # ticks between migration attempts per cell

# Temperature
TEMP_ENERGY_PENALTY = 0.02
TEMP_METABOLISM_MIN = 0.5
TEMP_FREEZE = 0.222

# Aging
AGING_METABOLISM_FACTOR = 0.5

# Major mutation
MAJOR_DIET_RATE = 0.5
MAJOR_SENSE_RATE = 0.5

# Diet defaults
DIET_DEFAULT_SPEED = {0: 0.5, 1: 4.0, 2: 2.0}
DIET_DEFAULT_SENSE = {0: 30.0, 1: 120.0, 2: 65.0}

# Division
DIVIDE_ENERGY_RATIO = 0.65
DIVIDE_MIN_AGE = 100

# Temp mutation
TEMP_MUT_DEFAULT = 0.5

# Movement
MOVEMENT_SCALE = 80.0  # doubled for faster visible movement

# Zoophagy
ZOO_PHAGY_MIN = 0.0
ZOO_PHAGY_MAX = 1.0
ZOO_PHAGY_DEFAULT = 0.5

# Decomposition
DECOMPOSITION_NUTRIENT_FRACTION = 0.45
DECOMPOSITION_TICKS = 150

# Corpse eating
CORPSE_EAT_RADIUS = 35.0
CORPSE_EAT_RATE = 0.02
CORPSE_EAT_EFFICIENCY = 0.8
CORPSE_ATTRACT_RADIUS = 80.0
CORPSE_SCAVENGE_RATE = 0.008

# Seasons
SEASON_ORDER = ["spring", "summer", "autumn", "winter"]
SEASON_LENGTH = 2000
SEASON_FACTORS = {"spring": 1.2, "summer": 1.0, "autumn": 0.8, "winter": 0.6}
SEASON_TEMPERATURES = {"spring": 0.4, "summer": 0.7, "autumn": 0.3, "winter": 0.35}

# Cell size
CELL_SIZE = 16

# Min mass
MIN_MASS = 1.0

# Food
FOOD_DECAY_RATE = 0.001
FOOD_LIFETIME_TICKS = 3000

# Temperature smooth
TEMP_SMOOTH_RATE = 0.01

# Min populations
PHOT_MIN_REQUIRED = 2
ZOOP_MIN_REQUIRED = 1
POLY_MIN_REQUIRED = 2

# Time lapse
TIME_LAPSE_DEFAULT_FPS = 30
TIME_LAPSE_FRAMES_DIR = "frames"
TIME_LAPSE_MAX_FRAMES = 10000
TIME_LAPSE_DURATION_MIN = 10

# Max level
MAX_LEVEL = 10

# Corpse nutrient
CORPSE_NUTRIENT_BOOST_RADIUS = 12
CORPSE_NUTRIENT_BOOST_MULT = 2.5
CORPSE_NUTRIENT_EXTRA_ENERGY = 0.5
CORPSE_NUTRIENT_MIN_AMOUNT = 0.05

BASE_LIFESPAN_TICKS = 3000
MAX_CELLS = 500
DECOMPOSITION_TICKS = 150  # visual decay duration of a corpse (ticks), reduced from 300
LIFESPAN_PER_MASS = 200
AGING_DAMAGE = 0.3
ZOO_INITIAL_ENERGY = 80.0  # Raised from 35.0 — ZOOP starts with enough energy to hunt before starving
PHOT_INITIAL_ENERGY = (
    70.0  # Added — PHOT starts with more energy to survive initial period
)
POLY_INITIAL_ENERGY = 60.0  # POLY starts with moderate energy

# ── Aging metabolism ─────────────────────────────────────────────
# Metabolism increases with age (0.0 = no increase, 1.0 = 2x at max lifespan)
AGING_METABOLISM_FACTOR = 0.5

# ── Major mutation AI constants ──────────────────────────────────────
MAJOR_DIET_RATE = 0.3  # 30% chance of major mutation creating new diet (reduced from 0.5)
MAJOR_SENSE_RATE = 0.5  # 50% chance of major mutation creating new sense organ

# ── Learning / Memory ────────────────────────────────────────────
AGGRO_INTERACT_THRESHOLD = 0.75  # Was 0.67 — increased to reduce aggression
COOP_INTERACT_THRESHOLD = 0.34
AGGRO_STEAL_FRACTION = 0.1
AGGRO_TRANSFER_EFF = 0.8
COOP_TRANSFER_MAX = 20.0
COOP_TRANSFER_MIN_ENERGY = 60.0
# Interaction types
INTERACT_MIN = 0.01
INTERACT_MAX = 1.0
PASS = 0

# B5: reduced from 50 to 10 so low-energy ZOOP can still transfer some energy
COOP_TRANSFER_PRESERVE = 10.0

# Spatial grid
LEARNING_RATE_BASE = 0.05  # base speed of adaptation from experience
MEMORY_MAX_EVENTS = 20  # max stored events per class
MEMORY_DECAY_TICKS = 500  # every N ticks, halve old memories
THREAT_FLEE_THRESHOLD = 0.3  # if threat_score > this, flee from class
COOP_PREFER_THRESHOLD = 0.5  # if coop_score > this, prefer cooperation

# ── Spatial grid ─────────────────────────────────────────────────
CELL_SIZE = 16  # Spatial grid cell size — reduced by 3x for finer-grained neighbor queries

# ── Seasons ──────────────────────────────────────────────────────
SEASON_ORDER = ["spring", "summer", "autumn", "winter"]
SEASON_LENGTH = 2000  # ticks per season
SEASON_TEMPERATURES = {
    "spring": 0.45,  # прохладная, потепление
    "summer": 0.85,  # жара
    "autumn": 0.55,  # похолодание
    "winter": 0.35,  # холод
}
TEMP_SEASON_OFFSET = (
    5.0  # градусы, которые добавляются к слайдеру в зависимости от сезона
)
SEASON_FACTORS = {
    "spring": {"regen_mult": 1.2, "hotspot_boost": 1.2, "divide_mult": 1.3},
    "summer": {"regen_mult": 1.0, "hotspot_boost": 1.0, "divide_mult": 1.0},
    "autumn": {"regen_mult": 0.8, "hotspot_boost": 0.8, "divide_mult": 0.8},
    "winter": {"regen_mult": 0.5, "hotspot_boost": 0.5, "divide_mult": 0.5},
}

# ── Season food colors (RGB, 0..1) for smooth interpolation ────────────────
SEASON_FOOD_COLORS = {
    "spring": (0.0, 0.8, 0.0),    # green
    "summer": (0.8, 0.9, 0.0),    # yellow-green
    "autumn": (0.9, 0.5, 0.0),    # orange
    "winter": (0.2, 0.5, 1.0),    # blue
}

# ── Food lifetime ───────────────────────────────────────────────────────────
# Food decays over time to prevent indefinite accumulation
FOOD_DECAY_RATE = 0.001    # fraction lost per tick (~50% in 693 ticks)

# ── Food generation ─────────────────────────────────────────────────────────
FOOD_REGEN_SPREAD = 1000
FOOD_CLUSTER_RADIUS = 18      # max distance from a hotspot for clustered regen
FOOD_CLUSTER_CHANCE = 0.3     # probability of regen near a hotspot vs random
FOOD_HOTSPOT_BOOST = 0.05     # extra energy added at hotspot center per regen

# ── Feeding radius ──────────────────────────────────────────────────────────
# Cells consume food within this pixel radius (not just the single pixel they
# stand on). 0.33% food coverage with 1px-eating → starvation; ~4px radius
# gives ~17% effective coverage which yields positive energy balance.
FEED_RADIUS = 4.0
FEED_RADIUS_SQ = FEED_RADIUS * FEED_RADIUS

# ── Nutrient clusters (from dead cells) ─────────────────────────────────────
CORPSE_NUTRIENT_FIELD_RATE = (
    0.06  # cluster amount fed into the field per tick
)
CORPSE_NUTRIENT_FADE = (
      0.98  # increased from 0.96 for faster cluster fade
  )
CORPSE_NUTRIENT_DRAW_MAX = 5.0  # reduced from 9.0 to skip tiny clusters
CORPSE_NUTRIENT_BOOST_RADIUS = 12  # consume-boost radius around a cluster (was 8)
CORPSE_NUTRIENT_BOOST_MULT = 2.5  # multiplier for boost consumption (was 2.0)
CORPSE_NUTRIENT_EXTRA_ENERGY = 0.5  # extra energy per boost (was 0.3)
CORPSE_NUTRIENT_MIN_AMOUNT = 0.05  # clusters below this are removed (was 0.1)

# ── Temperature ───────────────────────────────────────────────────
TEMP_MIN = 0.0  # min temperature multiplier
TEMP_MAX = 1.0  # max temperature multiplier
TEMP_DEFAULT = 0.7  # default temperature
TEMP_ENERGY_PENALTY = 0.02  # energy loss per tick for extreme temps
TEMP_SMOOTH_RATE = (
    0.01  # fraction of the gap covered per tick toward target temp (gradual change)
)
TEMP_METABOLISM_MIN = 0.5  # metabolism multiplier at temp=0.0 (cold slows metabolism)
TEMP_FREEZE = 0.222  # internal temp at 0 deg C — below this corpses are frozen (no decomposition)

# ── Temperature-dependent mutation spectrum ──────────────────────────
# Cold environments favour gross ecological shifts (diet/niche switches);
# warm environments favour fine motoric/sensory drift. The two spectra swing
# symmetrically around TEMP_MUT_NEUTRAL by ±TEMP_MUT_SWING, so the multiplier
# for each never collapses to zero (min = 1 - swing = 0.5 at the extreme).
TEMP_MUT_NEUTRAL = 0.5   # temperature where diet/other mutation chances are equal
TEMP_MUT_SWING = 0.5    # max fractional deviation of a multiplier from 1.0
TEMP_MUT_DEFAULT = 0.7   # fallback when no field temperature is available

# ── Zoophagy (predator feeding efficiency) ─────────────────────────────
ZOO_PHAGY_MIN = 0.5  # min feeding efficiency multiplier
ZOO_PHAGY_MAX = 2.0  # max feeding efficiency multiplier
ZOO_PHAGY_DEFAULT = 1.0  # default efficiency

# ── Persistence ──────────────────────────────────────────────────
SAVE_FILE = "saved_cells.json"
LOG_FILE = "logs/population.csv"

# ── Time-lapse recording ────────────────────────────────────────
TIME_LAPSE_DEFAULT_FPS = 30  # frames per second for time-lapse
TIME_LAPSE_FRAMES_DIR = "frames"  # directory to save frames
TIME_LAPSE_MAX_FRAMES = 10000  # maximum number of frames to save
TIME_LAPSE_DURATION_MIN = 10  # default duration in minutes

# ── Localization ─────────────────────────────────────────────────
LANG = "ru"

L10N = {
    "ru": {
        "diet": "Тип: {}",
        "diet_0": "Фототроф",
        "diet_1": "Зоофаг",
        "diet_2": "Полифаг",
        "diet_phot": "Фототроф",
        "diet_zoop": "Зоофаг",
        "diet_poly": "Полифаг",
        "phot": "Фототроф",
        "zoo": "Зоофаг",
        "poly": "Полифаг",
        "pass": "Пассивный",
        "aggro": "Агрессивный",
        "coop": "Кооперативный",
        "interact": "Поведение: {}",
        "energy": "Энергия",
        "level": "Уровень",
        "speed": "Скорость",
        "sense": "Дальность",
        "mass": "Масса",
        "metabolism": "Метаболизм",
        "divide_chance": "Шанс деления",
        "aggression": "Агрессия",
        "dmg_phot": "Урон Фито",
        "dmg_zoo": "Урон Зоо",
        "dmg_poly": "Урон Поли",
        "zoophagy": "Зоофагия",
        "food_regen": "Реген еды",
        "temp": "Температура",
        "food_diffuse": "Рассеивание",
        "time_scale": "Скорость времени",
        "sfx": "Звуки",
        "music": "Музыка",
        "age": "Возраст",
        "lifespan": "Время жизни",
        "food_lifetime": "Время жизни еды",
        "food_areola_lifetime": "Время жизни ареола",
        "fps": "FPS",
        "cells": "Клетки",
        "population": "Популяция",
        "corpses": "Трупы",
        "alive": "Живые",
        "dead": "Мёртвые",
        "add_mode": "Режим добавления",
        "templates": "Шаблоны",
        "genes": "Гены",
        "damage": "Урон",
        "selected": "Выбрано",
        "hint_add": "ЛКМ — выделить | Alt+ЛКМ — весь класс | Shift+ЛКМ — добавить | СКМ/ПКМ — тащить | Колесо — масштаб",
        "hotkeys": "Горячие клавиши",
        "hotkey_space": "Пауза",
        "hotkey_a": "A — добавить",
        "hotkey_s": "S — режим выбора",
        "hotkey_c": "C — очистить",
        "hotkey_r": "R — сброс поля",
        "hotkey_f": "F — загрузить",
        "hotkey_f5": "F5 — сохранить",
        "hotkey_esc": "Esc — назад / выход",
        "hotkey_1": "1/2/3 — тип (выбранным)",
        "hotkey_qwe": "Q/W/E — поведение (выбранным)",
        "hotkey_pm": "+/- — скорость",
        "hotkey_ud": "↑/↓ — дальность",
        "hotkey_x": "X — мутировать",
        "hotkey_d": "D — удалить",
        "hotkey_g": "G — полоски энергии",
        "hotkey_v": "V — полоски уровня",
        "hotkey_l": "L — язык",
        "hotkey_m": "M — громкость музыки, Alt+M — звуки",
        "hotkey_tab": "Tab — панель инфо",
        "hotkey_z": "Z — зум к клетке",
        "hotkey_b": "B — следование за клеткой",
        "follow": "Следование: {}",
        "population_graph": "Популяция по видам",
        "classes": "Классы:",
        "total": "Итого",
        "spring": "Весна",
        "summer": "Лето",
        "autumn": "Осень",
        "winter": "Зима",
        "environment": "Среда",
        "game_settings": "Настройки игры",
        "tick": "тик",
        "divisions": "делений",
        "food": "еда",
        "zoom": "Масштаб: {}",
        "rec_enter": "Центрировать [Home]",
    },
    "en": {
        "diet": "Type: {}",
        "diet_0": "Phototroph",
        "diet_1": "Zoophage",
        "diet_2": "Polyphage",
        "diet_phot": "Phototroph",
        "diet_zoop": "Zoophage",
        "diet_poly": "Polyphage",
        "phot": "Phototroph",
        "zoo": "Zoophage",
        "poly": "Polyphage",
        "pass": "Passive",
        "aggro": "Aggressive",
        "coop": "Cooperative",
        "interact": "Behavior: {}",
        "energy": "Energy",
        "level": "Level",
        "speed": "Speed",
        "sense": "Sense",
        "mass": "Mass",
        "metabolism": "Metabolism",
        "divide_chance": "Divide Chance",
        "aggression": "Aggression",
        "dmg_phot": "DMG Phot",
        "dmg_zoo": "DMG Zoo",
        "dmg_poly": "DMG Poly",
        "zoophagy": "Zoophagy",
        "food_regen": "Food Regen",
        "temp": "Temp",
        "food_diffuse": "Food Diffuse",
        "time_scale": "Time Scale",
        "sfx": "SFX",
        "music": "Music",
        "age": "Age",
        "lifespan": "Lifespan",
        "food_lifetime": "Food Lifetime",
        "food_areola_lifetime": "Food Areola Lifetime",
        "fps": "FPS",
        "cells": "Cells",
        "population": "Population",
        "corpses": "Corpses",
        "alive": "Alive",
        "dead": "Dead",
        "add_mode": "Add Mode",
        "templates": "Templates",
        "genes": "Genes",
        "damage": "Damage",
        "selected": "Selected",
        "hint_add": "LMB — select | Alt+LMB — whole class | Shift+LMB — add | MMB/RMB — drag | Scroll — zoom",
        "hotkeys": "Hotkeys",
        "hotkey_space": "Pause",
        "hotkey_a": "A — add mode",
        "hotkey_s": "S — select mode",
        "hotkey_c": "C — clear all",
        "hotkey_r": "R — reset field",
        "hotkey_f": "F — load saved",
        "hotkey_f5": "F5 — save selected",
        "hotkey_esc": "Esc — deselect / quit",
        "hotkey_1": "1/2/3 — diet type (selected)",
        "hotkey_qwe": "Q/W/E — behavior (selected)",
        "hotkey_pm": "+/- — speed",
        "hotkey_ud": "Up/Down — sense",
        "hotkey_x": "X — mutate",
        "hotkey_d": "D — delete",
        "hotkey_g": "G — energy bars",
        "hotkey_v": "V — level bars",
        "hotkey_l": "L — language",
        "hotkey_m": "M — music volume, Alt+M — SFX",
        "hotkey_tab": "Tab — info panel",
        "hotkey_z": "Z — zoom to cell",
        "hotkey_b": "B — follow cell",
        "follow": "Follow: {}",
        "population_graph": "Population by species",
        "classes": "Classes:",
        "total": "Total",
        "spring": "Spring",
        "summer": "Summer",
        "autumn": "Autumn",
        "winter": "Winter",
        "environment": "Environment",
        "game_settings": "Game Settings",
        "tick": "tick",
        "divisions": "divisions",
        "food": "food",
        "zoom": "Zoom: {}",
        "rec_enter": "Recenter [Home]",
    },
}


def tr(key: str) -> str:
    return L10N.get(LANG, L10N["en"]).get(key, key)


def tr_diet(diet_int: int) -> str:
    return L10N.get(LANG, L10N["en"]).get(f"diet_{diet_int}", str(diet_int))
