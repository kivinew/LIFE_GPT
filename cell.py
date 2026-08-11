# Cell class for LIFE_GPT
# Core organism — unified step() + learning/memory system
import math
import random
import pygame
import numpy as np
from typing import Optional, List, Dict

divisions = 0
_show_energy_bars = True
_show_level_bars = True

from config import (
    PHOT,
    ZOOP,
    POLY,
    PASS,
    INTERACT_MIN,
    W,
    H,
    SB,
    CELL_SIZE,
    ENERGY_MASS_COEFF,
    DRAW_ENERGY_MASS_COEFF,
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
    YEL,
    WHITE,
    CYAN,
    RED,
    TEAL,
    LEVEL_COLOR,
    DECOMPOSITION_TICKS,
    DISEASE_CHANCE,
    DISEASE_DURATION,
    DISEASE_METABOLISM_MULT,
    DISEASE_TRANSMISSION_RANGE,
    MIGRATION_CHANCE,
    MIGRATION_DISTANCE,
    TEMP_ENERGY_PENALTY,
    TEMP_METABOLISM_MIN,
    TEMP_FREEZE,
    AGING_METABOLISM_FACTOR,
    MAJOR_DIET_RATE,
    MAJOR_SENSE_RATE,
    DIVIDE_ENERGY_RATIO,
    DIVIDE_MIN_AGE,
    TEMP_MUT_DEFAULT,
    MOVEMENT_SCALE,
)
from spatial import get_neighbors
from memory import CellMemory

# Detect Cython sim_core availability (shared with main.py)
try:
    from sim_core import apply_physics, apply_metabolism_and_feeding
    _HAVE_SIM_CORE = True
except ImportError:
    _HAVE_SIM_CORE = False

# Diet → hue (green=phot, red=zoop, purple=poly). Each class gets its own
# combination of hue within the diet family + brightness/saturation, so
# cells of different classes are visually distinct while the diet stays
# recognizable. Hue ranges never overlap between diets.
_DIET_HUE = {PHOT: 120, ZOOP: 0, POLY: 285}
_DIET_HUE_SPREAD = {PHOT: 35, ZOOP: 20, POLY: 30}


def diet_color(diet: int, seed: int = 0) -> pygame.Color:
    base = _DIET_HUE.get(diet, 200)
    spread = _DIET_HUE_SPREAD.get(diet, 25)
    h = (base + (seed % (2 * spread + 1)) - spread) % 360
    s = 60 + (seed // 17) % 31
    v = 70 + (seed // 3) % 31
    c = pygame.Color(0)
    c.hsva = (h, s, v, 100)
    return c


# Global sound dictionary (set by main.py)
_sounds = {}
_sounds_enabled = True
_sfx_volume = 1.0  # Can be controlled via cell._sfx_volume from main.py


def set_sounds(sounds_dict):
    """Set the global sound dictionary from main.py."""
    global _sounds
    _sounds = sounds_dict


def play_sound(name: str):
    """Play a sound if available and sound effects are enabled."""
    global _sfx_volume
    if not _sounds_enabled:
        return
    if name not in _sounds:
        return
    try:
        _sounds[name].set_volume(_sfx_volume)
        # Play eating sound with 200ms duration for audibility
        if name == "eating":
            _sounds[name].play(maxtime=200)
        elif name == "divide":
            _sounds[name].play(maxtime=150)
        elif name == "death":
            _sounds[name].play(maxtime=200)
        else:
            _sounds[name].play()
    except Exception:
        pass


# Cache for cell body gradient surfaces, keyed by (cls, radius, energy_band, selected).
# Avoids per-frame Surface allocation + r circle draws per cell — the biggest rendering cost.
_cell_surface_cache: dict = {}
_ENERGY_BANDS = 5  # Quantize energy_ratio into bands to bound cache size


def _get_cached_cell_surface(cls, radius, col, energy_ratio, selected):
    """Return a cached gradient surface for a cell body, creating it if needed.

    Surfaces are immutable after creation, so they can be safely shared/blitted
    by many cells.  The cache is keyed by (cls, radius, energy_band, selected)
    so that color changes from refresh_class() naturally produce new entries.
    An entire-cache flush prevents unbounded growth across long simulations.
    """
    band = min(_ENERGY_BANDS - 1, int(energy_ratio * _ENERGY_BANDS))
    cache_key = (cls, radius, band, selected)
    ss = _cell_surface_cache.get(cache_key)
    if ss is not None:
        return ss
    if len(_cell_surface_cache) > 2000:
        _cell_surface_cache.clear()
    er = (band + 0.5) / _ENERGY_BANDS
    bright = tuple(int(c * (0.4 + 0.6 * er)) for c in col)
    dark = tuple(int(c * 0.2) for c in col)
    ss = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
    cx, cy = radius + 2, radius + 2
    for ri in range(radius, 0, -1):
        t = ri / radius
        alpha = int(255 * (1.0 - t * t))
        c = tuple(int(d + (b - d) * (1.0 - t)) for d, b in zip(dark, bright))
        pygame.draw.circle(ss, (*c, alpha), (cx, cy), ri)
    _cell_surface_cache[cache_key] = ss
    return ss


class Cell:
    """A single living cell with behaviour shaped by learned experience."""

    def __init__(self, x, y, g=None):
        self.x, self.y = x, y
        self.genome = g
        if self.genome is None:
            from genome import Genome

            self.genome = Genome()

        self.energy = (
            ZOO_INITIAL_ENERGY
            if self.genome.diet == ZOOP
            else (PHOT_INITIAL_ENERGY if self.genome.diet == PHOT else 40.0)
        )
        self.selected = False
        self._heartbeat_timer = 0
        self.level = 0
        self.age = 0

        self.refresh_class()

        self._dir = (0.0, 0.0)
        self.best_dir = (0.0, 1.0)
        self.look_dir = (0.0, 1.0)
        self.reaction_target = None
        self.reaction_type = None
        self.reaction_timer = 0
        self.chase_timer = 0
        self.aggression = 0.0
        self.sick = False
        self.sick_timer = 0

        # Viral infection support
        self.infected = False
        self.infection_timer = 0
        self.virus_type = 0
        self.virus_contagious = 0.0
        self.cure_state = 0.0

        # Learning speed (cached from genome)
        self._lr = LEARNING_RATE_BASE * (1.0 + self.genome.mut_rate)
        mem_size = max(5, min(50, int(self.genome.memory_size)))
        self.memory = CellMemory(max_slots=mem_size)

    def refresh_class(self):
        """Recompute class + color from the current genome.
        Diet is put in its own bucket (diet*1000) so cells of different diets
        always end up in different classes."""
        h = hash(
            (
                round(self.genome.speed, 1),
                round(self.genome.sense, 1),
                round(self.genome.mass, 1),
                round(self.genome.metabolism, 1),
                round(self.genome.interact, 2),
            )
        )
        self.cls = self.genome.diet * 1000 + (h % 1000)
        self.color = diet_color(self.genome.diet, self.cls)

    @property
    def max_energy(self):
        return self.genome.mass * self.genome.mass * ENERGY_MASS_COEFF

    # ── Phase 1: sensory ──
    def sensory_phase(self, field, cells, grid, dt, skip_food_ray=False):
        sense = max(8.0, self.genome.sense)
        d = self.genome.diet

        if not skip_food_ray:
            best_score = -1.0
            _bx, _by = random.uniform(-1, 1), random.uniform(-1, 1)
            _bn = math.hypot(_bx, _by)
            self.best_dir = (_bx / _bn, _by / _bn) if _bn > 0 else (0.0, 1.0)

            # Cache field dimensions and data for faster access
            fd = field.data
            fw, fh = W - SB, H

            if d in (PHOT, POLY):
                # Vectorized ray sampling - fewer iterations, more efficient
                for _ in range(16):  # Reduced from 24
                    ang = random.random() * math.tau
                    dist = random.random() * sense
                    sx = int(self.x + math.cos(ang) * dist)
                    sy = int(self.y + math.sin(ang) * dist)
                    if 0 <= sx < fw and 0 <= sy < fh:
                        val = fd[sx][sy]
                        score = val / (1.0 + dist / sense)
                        if score > best_score:
                            best_score = score
                            self.best_dir = (math.cos(ang), math.sin(ang))

        if d == PHOT and random.random() < 0.35:
            for j in get_neighbors(grid, self.x, self.y, radius=2):
                other = cells[j]
                if (
                    other is not self
                    and other.energy > 0
                    and other.cls != self.cls
                    and other.genome.diet != ZOOP
                ):
                    dx, dy = other.x - self.x, other.y - self.y
                    dist_sq = dx * dx + dy * dy
                    if 0 < dist_sq <= min(sense, 50.0) ** 2:
                        angle = math.atan2(-dy, -dx) + random.uniform(-0.5, 0.5)
                        self.best_dir = (math.cos(angle), math.sin(angle))
                        break

        if d in (ZOOP, POLY):
            weakest_energy = float("inf")
            weakest_prey = None
            best_prey_score = -1.0
            best_prey = None

            for j in get_neighbors(grid, self.x, self.y, radius=2):
                other = cells[j]
                if other is not self and other.energy > 0 and other.cls != self.cls:
                    dx, dy = other.x - self.x, other.y - self.y
                    dist_sq = dx * dx + dy * dy
                    if 0 < dist_sq <= sense * sense:
                        memory_bias = 1.0 - self.memory.coop(other.cls) * 0.3
                        effective_e = other.energy * memory_bias
                        if d == ZOOP:
                            if effective_e < weakest_energy:
                                weakest_energy = effective_e
                                weakest_prey = other
                        else:
                            val = min(1.0, other.energy / 100.0)
                            score = (
                                val / (1.0 + math.sqrt(dist_sq) / sense) * memory_bias
                            )
                            if score > best_prey_score:
                                best_prey_score = score
                                best_prey = other

            target = weakest_prey if d == ZOOP else best_prey
            if target:
                dx = target.x - self.x
                dy = target.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    self.best_dir = (dx / dist, dy / dist)

        if d == ZOOP and self.energy < 12.0:
            if random.random() < self.genome.cautious:
                self.best_dir = (random.uniform(-1, 1), random.uniform(-1, 1))
                norm = math.hypot(self.best_dir[0], self.best_dir[1])
                if norm > 0:
                    self.best_dir = (self.best_dir[0] / norm, self.best_dir[1] / norm)

    # ── Phase 2: reaction ──
    def reaction_phase(self):
        if self.reaction_timer > 0 and self.reaction_target:
            rt = self.reaction_target
            if rt.energy > 0:
                dx = rt.x - self.x
                dy = rt.y - self.y
                dist_sq = dx * dx + dy * dy
                if 0 < dist_sq <= (max(8.0, self.genome.sense)) ** 2:
                    if self.reaction_type == "flee":
                        angle = math.atan2(-dy, -dx) + random.uniform(-0.3, 0.3)
                        self.best_dir = (math.cos(angle), math.sin(angle))
                    elif self.reaction_type == "attack":
                        dist = math.sqrt(dist_sq)
                        self.best_dir = (dx / dist, dy / dist)
                    self.reaction_timer -= 1
                else:
                    self.reaction_target = None
                    self.reaction_type = None
                    self.reaction_timer = 0
            else:
                self.reaction_target = None
                self.reaction_type = None
                self.reaction_timer = 0
        else:
            if self.reaction_type == "attack" and self.chase_timer > 0:
                self.chase_timer -= 1
                rt = self.reaction_target
                if rt and self.energy < rt.energy:
                    self.reaction_target = None
                    self.reaction_type = None
                elif rt:
                    dx = rt.x - self.x
                    dy = rt.y - self.y
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        self.best_dir = (dx / dist, dy / dist)
            else:
                self.reaction_target = None
                self.reaction_type = None

    # ── Phase 3: pack behavior ──
    def pack_phase(self, cells, grid):
        sense = max(8.0, self.genome.sense)
        sense_sq = sense * sense
        ally_energy = 0.0
        enemy_energy = 0.0
        has_ally = has_enemy = False
        my_cls = self.cls
        my_x, my_y = self.x, self.y

        for j in get_neighbors(grid, my_x, my_y, radius=2):
            other = cells[j]
            if other is not self and other.energy > 0:
                dx = other.x - my_x
                dy = other.y - my_y
                dist_sq = dx * dx + dy * dy
                if 0 < dist_sq <= sense_sq:
                    if other.cls == my_cls:
                        ally_energy += other.energy
                        has_ally = True
                    else:
                        mem_threat = self.memory.threat(other.cls)
                        enemy_energy += other.energy * (1.0 + mem_threat * 0.5)
                        has_enemy = True

        pack_decision = None
        if has_ally and has_enemy:
            pack_decision = "flee" if (ally_energy - enemy_energy) < 0 else "attack"

        if pack_decision and not (self.reaction_timer > 0 and self.reaction_target):
            nearest_enemy = None
            nearest_dist_sq = float("inf")
            for j in get_neighbors(grid, my_x, my_y, radius=2):
                other = cells[j]
                if other is not self and other.energy > 0 and other.cls != my_cls:
                    dx = other.x - my_x
                    dy = other.y - my_y
                    dist_sq = dx * dx + dy * dy
                    if 0 < dist_sq <= sense_sq and dist_sq < nearest_dist_sq:
                        nearest_dist_sq = dist_sq
                        nearest_enemy = other
            if nearest_enemy:
                dx = nearest_enemy.x - my_x
                dy = nearest_enemy.y - my_y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist > 0:
                    if pack_decision == "flee":
                        angle = math.atan2(-dy, -dx) + random.uniform(-0.4, 0.4)
                        self.best_dir = (math.cos(angle), math.sin(angle))
                    else:
                        self.best_dir = (dx / dist, dy / dist)

        # Herd tendency — follow same-class cells
        if self.genome.herd_tendency > 0.3 and has_ally:
            ally_positions = []
            for j in get_neighbors(grid, my_x, my_y, radius=2):
                other = cells[j]
                if other is not self and other.energy > 0 and other.cls == my_cls:
                    dx = other.x - my_x
                    dy = other.y - my_y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq <= sense_sq:
                        ally_positions.append((other.x, other.y))
            if ally_positions:
                avg_x = sum(p[0] for p in ally_positions) / len(ally_positions)
                avg_y = sum(p[1] for p in ally_positions) / len(ally_positions)
                dx, dy = avg_x - self.x, avg_y - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    herd_dir = (dx / dist, dy / dist)
                    h = self.genome.herd_tendency
                    self.best_dir = (
                        self.best_dir[0] * (1 - h) + herd_dir[0] * h,
                        self.best_dir[1] * (1 - h) + herd_dir[1] * h,
                    )

        return pack_decision

    # ── Phase 4: movement ──
    def move_phase(self, dt, temperature=0.7):
        inertia = 0.88
        cur_dir = self._dir
        if cur_dir == (0.0, 0.0):
            cur_dir = self.best_dir
        blended = (
            cur_dir[0] * inertia + self.best_dir[0] * (1 - inertia),
            cur_dir[1] * inertia + self.best_dir[1] * (1 - inertia),
        )
        self._dir = blended

        # Temperature speed modifier: cold slows, heat slightly speeds then slows at extreme
        if temperature < 0.3:
            temp_speed_mult = 0.4 + temperature * 0.6  # 0.4 at 0.0, 0.58 at 0.3
        elif temperature > 0.8:
            temp_speed_mult = 1.2 - temperature * 0.3  # 0.96 at 0.8, 0.7 at 1.0
        else:
            temp_speed_mult = 1.0  # Optimal range

        effective_speed = self.genome.speed * temp_speed_mult * MOVEMENT_SCALE
        new_x = self.x + blended[0] * effective_speed * dt
        new_y = self.y + blended[1] * effective_speed * dt
        # Wall bounce: reflect direction at boundaries instead of sticking
        # (prevents cells piling at edges and looking "stuck downward").
        if new_x <= 0.0:
            new_x = 0.0
            self._dir = (-self._dir[0], self._dir[1])
            self.best_dir = (-self.best_dir[0], self.best_dir[1])
        elif new_x >= float(W - SB - 1):
            new_x = float(W - SB - 1)
            self._dir = (-self._dir[0], self._dir[1])
            self.best_dir = (-self.best_dir[0], self.best_dir[1])
        if new_y <= 0.0:
            new_y = 0.0
            self._dir = (self._dir[0], -self._dir[1])
            self.best_dir = (self.best_dir[0], -self.best_dir[1])
        elif new_y >= float(H - 1):
            new_y = float(H - 1)
            self._dir = (self._dir[0], -self._dir[1])
            self.best_dir = (self.best_dir[0], -self.best_dir[1])
        self.x = new_x
        self.y = new_y

    # ── Phase 5: feeding ──
    def feed_phase(self, field, cells, grid, dt):
        d = self.genome.diet
        if d in (PHOT, POLY):
            eat = field.consume(int(self.x), int(self.y), 0.15 * dt)
            if eat > 0 and self.selected:
                play_sound("eating")
            mass_eff = max(MIN_MASS_EFFICIENCY, 5.0 / self.genome.mass)
            diet_eff = PHOT_FEED_EFFICIENCY if d == PHOT else POLY_FEED_EFFICIENCY
            self.energy += eat * FEED_EFFICIENCY_BASE * mass_eff * diet_eff
        elif d == ZOOP or d == POLY:
            # Zoophagy: gain energy from consuming phototrophs
            sense = max(8.0, self.genome.sense)
            zoophagy_mult = field.zoophagy_mult if field else 1.0
            for j in get_neighbors(grid, self.x, self.y, radius=1):
                other = cells[j]
                if (
                    other is not self
                    and other.energy > 0
                    and other.genome.diet == PHOT
                    and other.cls != self.cls
                ):
                    dx = other.x - self.x
                    dy = other.y - self.y
                    if dx * dx + dy * dy <= sense * sense:
                        # Gain energy from prey (parasitic feeding)
                        feed_gain = min(2.0, other.energy * 0.08 * zoophagy_mult)
                        self.energy += feed_gain * COMBAT_DAMAGE_GAIN
                        break

    # ── Phase 6: combat ──
    def combat_phase(self, cells, grid, pack_decision, dt, field=None, attackers=None):
        if pack_decision == "flee":
            return

        sense = max(8.0, self.genome.sense)
        sense_sq = sense * sense
        my_diet = self.genome.diet
        zoophagy = field.zoophagy_mult if field else 1.0
        my_energy = self.energy
        my_mass = self.genome.mass
        my_cls = self.cls

        # Calculate pack hunting bonus if this is a ZOOP attacking
        pack_boost = 1.0
        if my_diet == ZOOP and pack_decision == "attack":
            pack_size = 1  # Start with self
            for j in get_neighbors(grid, self.x, self.y, radius=1):
                other = cells[j]
                if (
                    other is not self
                    and other.energy > 0
                    and other.genome.diet == ZOOP
                    and other.genome.interact >= COOP_INTERACT_THRESHOLD
                    and other.cls != my_cls
                ):
                    dx = other.x - self.x
                    dy = other.y - self.y
                    if dx * dx + dy * dy <= sense_sq:
                        pack_size += 1

            # Apply pack hunting bonus based on pack size
            # Pack boost scales: 1.0 (solo), 1.3 (pair), 1.6 (tri), 2.0 (4+)
            if pack_size == 1:
                pack_boost = 1.0
            elif pack_size == 2:
                pack_boost = 1.3
            elif pack_size == 3:
                pack_boost = 1.6
            else:
                pack_boost = 2.0

        combat_pack_boost = 1.5 if pack_decision == "attack" else 1.0

        for j in get_neighbors(grid, self.x, self.y, radius=1):
            other = cells[j]
            if other is not self and other.energy > 0 and other.cls != my_cls:
                # PHOT cells do not attack ZOOP cells
                if my_diet == PHOT and other.genome.diet == ZOOP:
                    continue
                dx = other.x - self.x
                dy = other.y - self.y
                dist_sq = dx * dx + dy * dy
                atk_range = my_mass + other.genome.mass + (7 if my_diet == ZOOP else 3)
                if 0 < dist_sq <= sense_sq and dist_sq < atk_range * atk_range:
                    # Compare energy: only attack if target is weaker or equal
                    # If target is stronger, trigger flee reaction instead
                    if other.energy > my_energy:
                        # Target is stronger - flee (but don't override an existing attack on a weaker target)
                        if (
                            self.reaction_type != "flee"
                            and self.reaction_target != other
                            and self.reaction_type != "attack"
                        ):
                            self.reaction_target = other
                            self.reaction_type = "flee"
                            self.reaction_timer = 120
                        continue
                    if my_diet == PHOT:
                        dmg_mult = self.genome.dmg_phot
                    elif my_diet == ZOOP:
                        dmg_mult = self.genome.dmg_zoop
                    else:
                        dmg_mult = self.genome.dmg_poly
                    amount = min(
                        other.energy,
                        COMBAT_BASE_DAMAGE * dt * combat_pack_boost * dmg_mult,
                    )
                    other.take_damage(amount, self)

                    enemy_cls = other.cls
                    if amount > 0:
                        if enemy_cls in self.memory._slots:
                            self.memory._slots[enemy_cls].threat = max(
                                0.0,
                                self.memory._slots[enemy_cls].threat - self._lr * 0.05,
                            )
                    if other.energy <= 0:
                        self.memory.record_cooperation(enemy_cls, magnitude=0.5)

                    if my_diet in (ZOOP, POLY):
                        mass_eff = max(
                            MIN_MASS_DMG_EFF,
                            1.0 - (my_mass - 4.0) * MASS_DMG_EFFICIENCY,
                        )
                        if my_diet == ZOOP:
                            de = PHOT_FEED_EFFICIENCY * zoophagy
                        else:
                            de = POLY_FEED_EFFICIENCY
                        self.energy += amount * COMBAT_DAMAGE_GAIN * mass_eff * de
                    else:
                        self.aggression += amount * 0.5

    # ── Phase 7: metabolism ──
    def metabolism_phase(self, dt, temperature=0.7):
        d = self.genome.diet
        metab_mult = BASE_METABOLISM_MULT if d == PHOT else PREDATOR_METABOLISM_MULT
        if self.sick:
            metab_mult *= DISEASE_METABOLISM_MULT

        # Temperature: cold slows metabolism
        temp_factor = TEMP_METABOLISM_MIN + (1.0 - TEMP_METABOLISM_MIN) * max(
            0.0, min(1.0, temperature)
        )
        metab_mult *= temp_factor

        # Aging metabolism: increases as cell gets older
        if self.genome.lifespan_ticks > 0:
            age_ratio = self.age / self.genome.lifespan_ticks
            aging_mult = 1.0 + age_ratio * AGING_METABOLISM_FACTOR
            metab_mult *= aging_mult

        self.energy -= (
            (
                self.genome.metabolism
                + self.genome.speed * SPEED_COST
                + self.genome.mass * self.genome.mass * MASS_PENALTY
            )
            * metab_mult
            * dt
        )

    # ── Phase 8: stress ──
    def stress_phase(self):
        if (
            self.genome.diet == PHOT
            and self.energy < STRESS_ENERGY_THRESHOLD
            and self.genome.mass > STRESS_MASS_MIN
            and self.reaction_type is None
        ):
            self.energy += STRESS_ENERGY_GAIN
            self.genome.mass = max(STRESS_MASS_MIN, self.genome.mass - STRESS_MASS_LOSS)
            play_sound("mass_down")

    def _heartbeat_tick(self):
        """Play heartbeat sound for selected cells with low energy."""
        if not self.selected or self.energy <= 0:
            return
        if self.energy < self.max_energy * 0.30:
            self._heartbeat_timer += 1
            if self._heartbeat_timer >= 60:
                self._heartbeat_timer = 0
                play_sound("heartbeat")
        else:
            self._heartbeat_timer = 0

    # ── Phase 9: level ──
    def level_phase(self):
        max_e = self.genome.mass * self.genome.mass * ENERGY_MASS_COEFF
        old_level = self.level
        if self.level < MAX_LEVEL:
            # Grow mass — never shrink
            next_mass = min(8.0, self.genome.mass * 1.15)
            next_max = next_mass * next_mass * ENERGY_MASS_COEFF
            threshold = next_max * 0.75
            if self.energy >= threshold:
                self.level += 1
                self.genome.mass = next_mass
                new_max = self.genome.mass * self.genome.mass * ENERGY_MASS_COEFF
                self.energy = new_max * 0.70
        elif self.energy <= LEVEL_DOWN_THRESHOLD and self.level > 0:
            self.level -= 1

        # Clamp energy after level changes
        self.energy = max(0.0, min(max_e, self.energy))

        # Play level up/down sounds
        if self.level > old_level:
            play_sound("lvl_up")
        elif self.level < old_level:
            play_sound("lvl_down")

    # ── Phase 10: social + memory ──
    def social_phase(self, cells, grid):
        if self.genome.interact < INTERACT_MIN:
            return
        sense = max(8.0, self.genome.sense)
        d = self.genome.diet

        for j in get_neighbors(grid, self.x, self.y, radius=1):
            other = cells[j]
            if other is not self and other.energy > 0 and other.cls != self.cls:
                dx, dy = self.x - other.x, self.y - other.y
                dist_sq = dx * dx + dy * dy
                mass_threshold = self.genome.mass + other.genome.mass + 4.0
                if dist_sq < mass_threshold * mass_threshold:
                    enemy_cls = other.cls
                    known_threat = self.memory.threat(enemy_cls)
                    known_coop = self.memory.coop(enemy_cls)

                    if known_threat > THREAT_FLEE_THRESHOLD:
                        angle = math.atan2(-dy, -dx) + random.uniform(-0.5, 0.5)
                        self.best_dir = (math.cos(angle), math.sin(angle))
                        self.memory._slots[enemy_cls].threat = min(
                            1.0, self.memory._slots[enemy_cls].threat + 0.05
                        )
                        return

                    if (
                        d == ZOOP
                        and self.energy < 15.0
                        and known_coop > COOP_PREFER_THRESHOLD
                    ):
                        if random.random() < 0.4:
                            transfer = min(
                                COOP_TRANSFER_MAX, self.energy - COOP_TRANSFER_PRESERVE
                            )
                            if transfer > 0:
                                other.energy += transfer * 0.5
                                self.energy -= transfer * 0.5
                                self.memory.record_cooperation(enemy_cls, magnitude=0.5)
                                play_sound("injection")  # Sound for energy injection
                                return

                    self.interact_with(other)

                    if self.energy > 30.0:
                        self.memory.record_cooperation(enemy_cls, magnitude=0.1)
                    elif self.energy < 15.0:
                        self.memory.record_threat(enemy_cls, magnitude=0.2)
                    break

    # ── Phase 11: aging ──
    def aging_phase(self, dt):
        if self.genome.lifespan_ticks > 0 and self.age > self.genome.lifespan_ticks:
            overage = self.age - self.genome.lifespan_ticks
            aging_loss = AGING_DAMAGE * (1.0 + overage / 100.0)
            self.energy -= aging_loss * dt

    # ── Phase 12: disease ──
    def disease_phase(self, cells, grid, dt):
        if self.sick:
            self.sick_timer -= 1
            if self.sick_timer <= 0:
                if self.sick:  # Still sick before timer ended
                    self.sick = False
                    play_sound("gurgle2")  # Recovery sound
            else:
                self.energy -= 0.1 * dt  # energy loss from disease
        elif random.random() < DISEASE_CHANCE:
            # Check for nearby sick cells
            for j in get_neighbors(grid, self.x, self.y, radius=1):
                other = cells[j]
                if other is not self and other.sick:
                    dx = other.x - self.x
                    dy = other.y - self.y
                    if dx * dx + dy * dy < DISEASE_TRANSMISSION_RANGE ** 2:
                        self.sick = True
                        self.sick_timer = DISEASE_DURATION
                        play_sound("gurgle")  # Disease onset sound
                        break

        # Viral infection phase
        if self.infected:
            self.infection_timer -= 1

            # Calculate infection severity and effects
            severity = self.virus_type / 10.0  # Higher virus type = more severe
            disease_mult = DISEASE_METABOLISM_MULT

            # Cure mechanism - random recovery based on environmental factors
            if self.cure_state < 0.2 and random.random() < 0.01:
                # Weak cure effect - slow recovery
                self.cure_state += random.uniform(0.05, 0.1)

            # Virus activation if becomes strong enough
            if self.virus_type > 7 and random.random() < 0.001:
                self.cure_state += 0.1

            # Virus leaves body when cure > 70%
            if self.cure_state > 0.7:
                self.cure_state = 0.0
                self.infected = False
                self.infection_timer = 0
                self.virus_type = 0
                play_sound("gurgle2")  # Recovery sound
                return

            # Effects of viral infection: accelerated metabolism, reduced lifespan
            # This helps virus spread but harms the host
            self.energy -= (
                0.15 * dt * severity * disease_mult
            )  # Higher energy loss when sick
            self.genome.lifespan_ticks = int(
                self.genome.lifespan_ticks * 0.85
            )  # Speed up aging

            # Virus can spread to nearby healthy cells
            if random.random() < 0.1 * severity:
                for j in get_neighbors(grid, self.x, self.y, radius=1):
                    other = cells[j]
                    if (
                        other is not self
                        and other.energy > 0
                        and not other.infected
                        and other.genome.diet == self.genome.diet
                    ):  # Infect same diet type
                        dx = other.x - self.x
                        dy = other.y - self.y
                        spread_radius = 5.0 + self.virus_type * 2
                        if dx * dx + dy * dy <= spread_radius * spread_radius:  # Larger radius for more dangerous viruses
                            other.infected = True
                            other.infection_timer = DISEASE_DURATION * random.uniform(
                                0.5, 2.0
                            )
                            other.virus_type = self.virus_type
                            other.cure_state = 0.0
                            play_sound("gurgle")  # Disease onset sound
                            break

        elif random.random() < 0.01:  # 1% chance per tick to get infected with virus
            # Chance to get viral infection from nearby infected cells (simplified)
            for j in get_neighbors(grid, self.x, self.y, radius=1):
                other = cells[j]
                if other is not self and other.infected and other.virus_type > 0:
                    dx = other.x - self.x
                    dy = other.y - self.y
                    if dx * dx + dy * dy < 25.0:  # Close transmission
                        self.infected = True
                        self.infection_timer = DISEASE_DURATION * random.uniform(
                            0.5, 2.0
                        )
                        self.virus_type = other.virus_type
                        self.cure_state = 0.0
                        play_sound("gurgle")  # Disease onset sound
                        break

    # ── Phase 13: migration ──
    def migration_phase(self):
        if random.random() < MIGRATION_CHANCE:
            if self.energy < self.max_energy * 0.3:  # only hungry cells migrate
                angle = random.random() * math.tau
                dist = random.random() * MIGRATION_DISTANCE
                new_x = self.x + math.cos(angle) * dist
                new_y = self.y + math.sin(angle) * dist
                # Stay within bounds
                self.x = max(0, min(W - SB - 1, new_x))
                self.y = max(0, min(H - 1, new_y))

    # ── Phase 14: temperature ──
    def temperature_phase(self, field, dt):
        temp = field.temperature
        if temp < 0.3 or temp > 0.9:
            penalty = abs(temp - 0.6) * TEMP_ENERGY_PENALTY
            self.energy -= penalty * dt

    def memory_decay_tick(self, every_n=500):
        self.memory.tick(every_n)

    # ── Visual look direction with smooth inertia ──
    def update_look_dir(self, dt):
        """Smoothly rotate look_dir toward movement direction with inertia."""
        target = self._dir
        tlen = math.hypot(target[0], target[1])
        if tlen < 0.01:
            target = self.best_dir
            tlen = math.hypot(target[0], target[1])
            if tlen < 0.01:
                return
        tx, ty = target[0] / tlen, target[1] / tlen

        lx, ly = self.look_dir
        llen = math.hypot(lx, ly)
        if llen < 0.01:
            self.look_dir = (tx, ty)
            return
        lx, ly = lx / llen, ly / llen

        # Exponential smoothing: rate 0.25 means ~15% of remaining angle per tick
        smooth_rate = 0.25
        t = 1.0 - math.exp(-smooth_rate * max(dt, 0.001))
        nx = lx + (tx - lx) * t
        ny = ly + (ty - ly) * t
        nlen = math.hypot(nx, ny)
        if nlen > 0.001:
            self.look_dir = (nx / nlen, ny / nlen)

    # ── Unified step (pure Python) ──
    def step(self, field, cells, grid, dt, tick):
        if self.energy <= 0:
            return
        self.age += 1
        if tick % 500 == 0:
            self.memory_decay_tick()
        self.sensory_phase(field, cells, grid, dt)
        self.reaction_phase()
        pack_decision = self.pack_phase(cells, grid)
        self.move_phase(dt, field.temperature)
        self.feed_phase(field, cells, grid, dt)
        self.combat_phase(cells, grid, pack_decision, dt, field)
        self.metabolism_phase(dt, field.temperature)
        self.stress_phase()
        self._heartbeat_tick()
        self.level_phase()
        self.divide_phase(cells, grid, field.temperature)
        self.social_phase(cells, grid)
        self.aging_phase(dt)
        self.disease_phase(cells, grid, dt)
        self.migration_phase()
        self.temperature_phase(field, dt)
        self.update_look_dir(dt)

    def post_step(self, field, cells, grid, pd, dt, tick):
        if self.energy <= 0:
            return
        self.age += 1
        if tick % 500 == 0:
            self.memory_decay_tick()
        pack_decision = self.pack_phase(cells, grid)
        self.combat_phase(cells, grid, pack_decision, dt, field)
        # feed_phase/metabolism_phase are handled by apply_metabolism_and_feeding in Cython mode
        if not _HAVE_SIM_CORE:
            self.feed_phase(field, cells, grid, dt)
            self.metabolism_phase(dt, field.temperature)
        self.stress_phase()
        self._heartbeat_tick()
        self.level_phase()
        self.divide_phase(cells, grid, field.temperature)
        self.social_phase(cells, grid)
        self.aging_phase(dt)
        self.disease_phase(cells, grid, dt)
        self.migration_phase()
        self.temperature_phase(field, dt)
        self.update_look_dir(dt)

    # ── Standard methods ──
    def interact_with(self, other):
        if self.genome.interact < INTERACT_MIN or other.energy <= 0:
            return
        if other.energy > self.energy * 1.5:
            return
        if self.genome.interact >= AGGRO_INTERACT_THRESHOLD:
            if random.random() < 0.5:
                steal = min(
                    other.energy,
                    (
                        self.energy * AGGRO_STEAL_FRACTION
                        if other.energy > self.energy * AGGRO_STEAL_FRACTION
                        else other.energy
                    ),
                )
                if steal > 0:
                    other.energy -= steal
                    self.energy += steal * AGGRO_TRANSFER_EFF
        elif self.genome.interact >= COOP_INTERACT_THRESHOLD:
            if random.random() < 0.3 and self.energy > COOP_TRANSFER_MIN_ENERGY:
                transfer = min(COOP_TRANSFER_MAX, self.energy - COOP_TRANSFER_PRESERVE)
                if transfer > 0:
                    other.energy += transfer
                    self.energy -= transfer

    def take_damage(self, amount, attacker=None):
        self.energy -= amount
        if attacker and attacker.cls != self.cls:
            self.memory.record_threat(attacker.cls, magnitude=0.5)
        if attacker:
            # Compare energy instead of level: flee if attacker has more energy
            if attacker.energy > self.energy:
                self.reaction_target = attacker
                self.reaction_type = "flee"
                self.reaction_timer = 120
            else:
                self.reaction_target = attacker
                self.reaction_type = "attack"
                self.reaction_timer = 180
                self.chase_timer = 180

    def can_divide(self):
        """Check if cell can divide based on energy and age."""
        if self.energy < self.max_energy * DIVIDE_ENERGY_RATIO:
            return False
        if self.age < DIVIDE_MIN_AGE:
            return False
        return True

    def divide(self, temperature=TEMP_MUT_DEFAULT):
        """Divide the cell if conditions are met. Returns child Cell or None."""
        if not self.can_divide():
            return None

        zoo_elite = (
            self.genome.diet == ZOOP
            and self.level >= MAX_LEVEL
            and random.random() < 0.03
        )
        # Energy split: parent keeps enough to survive; child gets the rest.
        # Higher-level cells pass proportionally more energy to offspring.
        parent_keep_ratio = 0.20 + (self.level / MAX_LEVEL) * 0.10  # 20%-30%
        parent_e = self.max_energy * parent_keep_ratio
        available = self.energy - parent_e
        child_e = available if zoo_elite else available

        # Child needs at least 15% of max to survive
        if child_e < self.max_energy * 0.15 and not zoo_elite:
            return None

        child_genome = self.genome.clone_mutate(temperature)
        # Small chance of additional mutation during division
        if random.random() < 0.05:
            child_genome = child_genome.clone_mutate(temperature)
        child = Cell(
            self.x + random.uniform(-8, 8),
            self.y + random.uniform(-8, 8),
            child_genome,
        )
        # Child inherits its own cls/color from refresh_class() in __init__,
        # computed from the mutated genome. This enables natural speciation:
        # when enough genome drift occurs, refresh_class() yields a new cls,
        # giving the offspring a distinct appearance class.
        child.age = 0
        child.level = random.randint(0, self.level)
        child.genome.mass = LEVEL_MASS_BASE + child.level * LEVEL_MASS_STEP
        child._lr = self._lr
        child.memory = self.memory.clone()  # Deep copy to avoid shared memory

        if zoo_elite:
            child.energy = self.max_energy * 0.30
            self.energy = parent_e
        else:
            # Clamp child energy so it never exceeds the child's own capacity
            child.energy = min(child_e, child.max_energy)
            self.energy = parent_e

        # Removed mass-based abort chance
        if self.energy <= LEVEL_DOWN_THRESHOLD and self.level > 0:
            self.level -= 1
        play_sound("divide")
        global divisions
        divisions += 1
        return child

    def divide_phase(self, cells, grid, temperature=TEMP_MUT_DEFAULT):
        """Attempt to divide if all conditions are met.

        Uses genome.divide_chance as a per-tick probability gate.
        High-level cells divide less frequently but pass more energy
        to offspring, creating a natural selection pressure for
        longer-lived, more investment-heavy lineages.
        """
        if self.energy <= 0:
            return
        if not self.can_divide():
            return
        # divide_chance: probability per tick when conditions are met.
        # Scaled by level — higher-level cells divide less often.
        level_penalty = 1.0 - (self.level / MAX_LEVEL) * 0.7  # 30% less chance at max level
        if random.random() > self.genome.divide_chance * level_penalty:
            return

        child = self.divide(temperature)
        if child is not None and cells is not None:
            cells.append(child)

    def is_dead(self):
        # Dies from energy depletion or old age (lifespan * 1.5 with low energy)
        return self.energy <= 0.0 or (
            self.age > self.genome.lifespan_ticks * 1.5
            and self.energy < self.max_energy * 0.15
        )

    # ── Drawing ──
    def draw(self, surf, ox=0.0, oy=0.0):
        self.draw_at(surf, self.x + ox, self.y + oy)

    def draw_at(self, surf, dx, dy):
        x, y = int(dx), int(dy)
        r = max(3, int(2 + self.genome.mass * 1.5))
        col = YEL if self.selected else self.color[:3]
        energy_ratio = max(0.0, min(1.0, self.energy / self.max_energy))
        ss = _get_cached_cell_surface(self.cls, r, col, energy_ratio, self.selected)
        cx, cy = r + 2, r + 2
        surf.blit(ss, (x - cx, y - cy))
        if self.selected:
            sr = int(self.genome.sense)
            ss = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
            pygame.draw.circle(ss, (100, 100, 255, 40), (sr, sr), sr)
            surf.blit(ss, (x - sr, y - sr))
            pygame.draw.circle(surf, WHITE, (x, y), r + 2, 2)

        lx, ly = self.look_dir
        blen = math.hypot(lx, ly)
        if blen < 0.01:
            lx, ly = 0.0, 1.0
        else:
            lx, ly = lx / blen, ly / blen
        sx_a = x + int(lx * (r + 2))
        sy_a = y + int(ly * (r + 2))
        alen = 8
        ex = int(x + lx * (r + 2 + alen))
        ey = int(y + ly * (r + 2 + alen))
        lw = 2
        ang = math.atan2(ly, lx)
        ah = 8
        ww = 2
        a_col = CYAN
        pygame.draw.line(surf, a_col, (sx_a, sy_a), (ex, ey), lw)
        pygame.draw.line(
            surf,
            a_col,
            (ex, ey),
            (int(ex - ah * math.cos(ang - 0.4)), int(ey - ah * math.sin(ang - 0.4))),
            ww,
        )
        pygame.draw.line(
            surf,
            a_col,
            (ex, ey),
            (int(ex - ah * math.cos(ang + 0.4)), int(ey - ah * math.sin(ang + 0.4))),
            ww,
        )

        bw2 = r * 2
        max_e = self.genome.mass * self.genome.mass * DRAW_ENERGY_MASS_COEFF
        lw = bw2 * 2
        # Energy bar (topmost)
        if _show_energy_bars:
            pygame.draw.rect(surf, (30, 30, 30), (x - bw2, y - r - 12, lw, 3), 0, 2)
            if max_e > 0:
                pw = int((self.energy / max_e) * lw)
                cl = int(255 * max(0.0, min(1.0, self.energy / max_e)))
                ec = (max(0, min(255, 255 - cl)), min(255, cl), 0)
                pygame.draw.rect(surf, ec, (x - bw2, y - r - 12, pw, 3), 0, 2)
        # Level indicator (thin bar below energy bar)
        if _show_level_bars:
            pygame.draw.rect(surf, (40, 40, 45), (x - bw2, y - r - 9, lw, 2), 0, 1)
            lvl_w = int((self.level / MAX_LEVEL) * lw)
            if lvl_w > 0:
                pygame.draw.rect(surf, LEVEL_COLOR, (x - bw2, y - r - 9, lvl_w, 2), 0, 1)

        # Diet type indicator next to the energy bar
        diet_col = (
            TEAL
            if self.genome.diet == PHOT
            else (RED if self.genome.diet == ZOOP else YEL)
        )
        pygame.draw.circle(surf, diet_col, (x + bw2 + 4, y - r - 4), 2)

        if self.selected and len(self.memory) > 0:
            dot_r = max(2, r // 3)
            pygame.draw.circle(surf, CYAN, (x + r + 4, y - r), dot_r)

        # Disease indicator
        if self.sick:
            pygame.draw.circle(surf, RED, (x + r + 2, y - r - 2), 2)


# ── Corpse ────────────────────────────────────────────────────────────
class Corpse:
    """A dead cell body. Releases nutrients into the field while it rots
    away; visually shrinks and disappears after DECOMPOSITION_TICKS."""

    __slots__ = ("x", "y", "mass", "age", "dur", "frozen")

    def __init__(self, x, y, mass, dur=DECOMPOSITION_TICKS):
        self.x = float(x)
        self.y = float(y)
        self.mass = mass
        self.age = 0.0
        self.dur = dur
        self.frozen = False  # True when below freeze temp, decomposition paused

    def update(self, dt, temperature=TEMP_MUT_DEFAULT):
        if temperature < TEMP_FREEZE:
            self.frozen = True
        else:
            self.frozen = False
            self.age += dt

    @property
    def done(self):
        return self.age >= self.dur or self.mass <= 0.0

    def draw_at(self, surf, dx, dy):
        frac = 1.0 - min(1.0, self.age / self.dur)
        r = max(2, int((2 + self.mass * 1.5) * (0.35 + 0.65 * frac)))
        x, y = int(dx), int(dy)
        if self.frozen:
            # Замороженные трупы: синий оттенок (не разлагаются)
            pygame.draw.circle(surf, (45, 55, 85), (x, y), r)
            pygame.draw.circle(surf, (80, 95, 130), (x, y), r, 1)
        else:
            pygame.draw.circle(surf, (55, 55, 62), (x, y), r)
            pygame.draw.circle(surf, (95, 97, 105), (x, y), r, 1)


# ── Vectorized neighbor calculation (NumPy fallback) ────────────────────────
def vectorized_sensory_phase(cells, grid, field, dt, skip_food_ray=False):
    """Batch-process sensory_phase for all cells using NumPy.

    Replaces the per-cell Python loop with vectorized array operations
    for neighbor-based sensory logic (PHOT flee, ZOOP/POLY prey hunting).
    Food ray sampling is also batched when skip_food_ray=False.
    """
    n = len(cells)
    if n == 0:
        return

    xs = np.array([c.x for c in cells], dtype=np.float64)
    ys = np.array([c.y for c in cells], dtype=np.float64)
    diets = np.array([c.genome.diet for c in cells], dtype=np.int32)
    senses = np.array([max(8.0, c.genome.sense) for c in cells], dtype=np.float64)
    energies = np.array([c.energy for c in cells], dtype=np.float64)
    cls_ids = np.array([c.cls for c in cells], dtype=np.int64)
    bdx = np.array([c.best_dir[0] for c in cells], dtype=np.float64)
    bdy = np.array([c.best_dir[1] for c in cells], dtype=np.float64)
    cautious = np.array([c.genome.cautious for c in cells], dtype=np.float64)

    field_w = W - SB

    # Food ray sampling (batched per cell, vectorized distance scoring)
    if not skip_food_ray:
        for i in range(n):
            d = diets[i]
            if d in (PHOT, POLY):
                sense = senses[i]
                cx, cy = xs[i], ys[i]
                best_score = -1.0
                best_ang_x, best_ang_y = bdx[i], bdy[i]
                for _ray in range(16):
                    ang = random.random() * math.tau
                    dist = random.random() * sense
                    sx = int(cx + math.cos(ang) * dist)
                    sy = int(cy + math.sin(ang) * dist)
                    if 0 <= sx < field_w and 0 <= sy < H:
                        val = field.data[sx][sy]
                        score = val / (1.0 + dist / sense)
                        if score > best_score:
                            best_score = score
                            best_ang_x = math.cos(ang)
                            best_ang_y = math.sin(ang)
                if best_score < 0.0:
                    # No food sampled (all empty/uniform): pick a random direction,
                    # not (0,1) downward, to avoid systemic downward drift.
                    _a = random.random() * math.tau
                    best_ang_x, best_ang_y = math.cos(_a), math.sin(_a)
                bdx[i] = best_ang_x
                bdy[i] = best_ang_y

    # Neighbor-based sensory logic (PHOT flee, ZOOP/POLY prey hunt)
    for i in range(n):
        d = diets[i]
        cx, cy = xs[i], ys[i]
        sense = senses[i]
        sense_sq = sense * sense

        neighbors = get_neighbors(grid, cx, cy, radius=2)
        neighbors = [j for j in neighbors if j != i]
        if len(neighbors) == 0:
            continue

        # Vectorized distance calc to all neighbors
        nx = np.array([xs[j] for j in neighbors], dtype=np.float64)
        ny = np.array([ys[j] for j in neighbors], dtype=np.float64)
        dx_arr = nx - cx
        dy_arr = ny - cy
        dist_sq = dx_arr * dx_arr + dy_arr * dy_arr

        # PHOT: flee from non-same-class non-ZOOP cells
        if d == PHOT and random.random() < 0.35:
            threat_mask = np.zeros(len(neighbors), dtype=bool)
            for k, j in enumerate(neighbors):
                if (energies[j] > 0 and cls_ids[j] != cls_ids[i] and diets[j] != ZOOP
                        and dist_sq[k] > 0 and dist_sq[k] <= min(sense, 50.0) ** 2):
                    threat_mask[k] = True
            threat_idx = np.where(threat_mask)[0]
            if len(threat_idx) > 0:
                k = threat_idx[0]
                angle = math.atan2(-dy_arr[k], -dx_arr[k]) + random.uniform(-0.5, 0.5)
                bdx[i] = math.cos(angle)
                bdy[i] = math.sin(angle)

        # ZOOP/POLY: hunt prey
        if d in (ZOOP, POLY):
            prey_mask = np.zeros(len(neighbors), dtype=bool)
            prey_scores = np.full(len(neighbors), -1.0)
            for k, j in enumerate(neighbors):
                if energies[j] > 0 and cls_ids[j] != cls_ids[i]:
                    if dist_sq[k] > 0 and dist_sq[k] <= sense_sq:
                        prey_mask[k] = True
                        if d == ZOOP:
                            mem_bias = 1.0 - cells[j].memory.coop(cls_ids[i]) * 0.3 if hasattr(cells[j], 'memory') else 1.0
                            prey_scores[k] = energies[j] * mem_bias
                        else:
                            val = min(1.0, energies[j] / 100.0)
                            prey_scores[k] = val / (1.0 + math.sqrt(dist_sq[k]) / sense)
            prey_idx = np.where(prey_mask)[0]
            if len(prey_idx) > 0:
                if d == ZOOP:
                    k = prey_idx[np.argmin(prey_scores[prey_idx])]
                else:
                    k = prey_idx[np.argmax(prey_scores[prey_idx])]
                dist = math.sqrt(dist_sq[k])
                if dist > 0:
                    bdx[i] = dx_arr[k] / dist
                    bdy[i] = dy_arr[k] / dist

        # ZOOP cautious flee when low energy
        if d == ZOOP and energies[i] < 12.0:
            if random.random() < cautious[i]:
                rand_x = random.uniform(-1, 1)
                rand_y = random.uniform(-1, 1)
                norm = math.hypot(rand_x, rand_y)
                if norm > 0:
                    bdx[i] = rand_x / norm
                    bdy[i] = rand_y / norm

    # Write back best_dir
    for i, c in enumerate(cells):
        c.best_dir = (float(bdx[i]), float(bdy[i]))
