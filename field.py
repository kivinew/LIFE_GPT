# ResourceField class for LIFE_GPT
# Energy field with regen, diffusion, hotspots, and nutrient clusters
import numpy as np
import pygame
import random
from config import (
    W,
    H,
    CORPSE_NUTRIENT_FIELD_RATE,
    CORPSE_NUTRIENT_FADE,
    CORPSE_NUTRIENT_DRAW_MAX,
    CORPSE_NUTRIENT_BOOST_RADIUS,
)


class ResourceField:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.regen: float = 0.06
        self.base_regen: float = 0.06
        self.diff: float = 0.06
        self.temperature: float = 0.7  # Global temperature (0.0-1.0)
        self.zoophagy_mult: float = 1.0  # Predator feeding efficiency multiplier

        # Initialize biomes
        self.biomes = {}
        self.biome_registry = self._init_biome_registry()
        self.current_biome_index = 0

        # 2D field of energy values [0.0 .. 1.0]
        self.data = np.zeros((w, h), dtype=np.float64)

        # Hotspots and nutrient clusters
        self.hotspots = []
        self.nutrient_clusters = []

        # Scatter initial energy seeds — dense enough for cells to find food
        for _ in range(3000):
            self.data[np.random.randint(0, w), np.random.randint(0, h)] = (
                np.random.uniform(0.4, 1.0)
            )

        # Assign biomes to grid cells
        self._assign_biomes()

    def _init_biome_registry(self):
        """Initialize biome definitions with unique characteristics."""
        return {
            "foresta": {  # Forest biome
                "name": "Forest",
                "regen_mult": 1.5,
                "hotspot_boost": 1.5,
                "temperature_range": (0.4, 0.6),
                "resource_scatter": (3000, 0.4, 1.0),  # base, min, max
                "description": "High resource density, cooler temperatures",
            },
            "deserto": {  # Desert biome
                "name": "Desert",
                "regen_mult": 0.4,
                "hotspot_boost": 0.5,
                "temperature_range": (0.8, 0.95),
                "resource_scatter": (1500, 0.2, 0.8),
                "description": "Low resources, high temperatures",
            },
            "ocean": {  # Ocean biome
                "name": "Ocean",
                "regen_mult": 1.2,
                "hotspot_boost": 1.0,
                "temperature_range": (0.1, 0.4),
                "resource_scatter": (2500, 0.3, 0.9),
                "description": "Stable temperature, moderate resources",
            },
            "mountains": {  # Mountain biome
                "name": "Mountains",
                "regen_mult": 0.6,
                "hotspot_boost": 1.0,
                "temperature_range": (0.2, 0.5),
                "resource_scatter": (2000, 0.3, 0.8),
                "description": "Patchy resources, variable temperatures",
            },
            "swamp": {  # Swamp biome
                "name": "Swamp",
                "regen_mult": 1.8,
                "hotspot_boost": 2.0,
                "temperature_range": (0.5, 0.8),
                "resource_scatter": (3500, 0.3, 1.0),
                "description": "High resources, excellent hotspots",
            },
        }

    def _assign_biomes(self):
        """Assign biome types to all grid cells based on biome probabilities."""
        biomes = self.biomes
        biome_names = list(self.biome_registry.keys())
        biome_weights = [
            0.25,
            0.15,
            0.20,
            0.15,
            0.25,
        ]  # forest, desert, ocean, mountains, swamp

        for x in range(self.w):
            for y in range(self.h):
                # Choose biome based on weighted random
                biome_type = random.choices(biome_names, weights=biome_weights)[0]
                biomes[(x, y)] = biome_type

    def get_biome(self, x, y):
        """Get biome type at coordinates."""
        return self.biomes.get((x, y), "foresta")  # Default to forest

    def get_biome_multiplier(self, x, y, multiplier_type="regen_mult"):
        """Get biome-specific multiplier for a given cell."""
        biome_name = self.get_biome(x, y)
        biome_data = self.biome_registry.get(biome_name, self.biome_registry["foresta"])
        return biome_data.get(multiplier_type, 1.0)

    def get_biome_temperature(self, x, y):
        """Get biome-specific base temperature for a cell."""
        biome_name = self.get_biome(x, y)
        biome_data = self.biome_registry.get(biome_name, self.biome_registry["foresta"])
        temp_range = biome_data.get("temperature_range", (0.5, 0.5))
        return random.uniform(temp_range[0], temp_range[1])

    def analyze_biome_distribution(self):
        """Analyze and return statistics about biome distribution."""
        distribution = {}
        for biome_name in self.biome_registry.keys():
            count = sum(1 for b in self.biomes.values() if b == biome_name)
            distribution[biome_name] = count
        return distribution

    def adjust_biomes_for_season(self, season):
        """Adjust biome characteristics based on current season.

        This method is called from cell.py when seasons change, allowing biomes
        to adapt their characteristics to seasonal changes.
        """
        if season == "spring":
            # Spring: Increased resources, moderate temperature
            for pos, biome_name in self.biomes.items():
                if biome_name == "foresta":
                    # Forest benefits from spring growth
                    self.data[pos[0], pos[1]] = min(
                        1.0, self.data[pos[0], pos[1]] + 0.02
                    )
                elif biome_name == "swamp":
                    # Swamp shows strong spring growth
                    self.data[pos[0], pos[1]] = min(
                        1.0, self.data[pos[0], pos[1]] + 0.03
                    )

        elif season == "summer":
            # Summer: Heat stress, potential resource depletion
            for pos, biome_name in self.biomes.items():
                if biome_name == "deserto":
                    # Desert suffers from summer heat
                    self.data[pos[0], pos[1]] = max(
                        0.0, self.data[pos[0], pos[1]] - 0.01
                    )
                elif biome_name == "ocean":
                    # Ocean remains stable
                    pass

        elif season == "autumn":
            # Autumn: Resource cycling, preparation for winter
            for pos, biome_name in self.biomes.items():
                if biome_name == "mountains":
                    # Mountains show autumn resource decline
                    self.data[pos[0], pos[1]] = max(
                        0.0, self.data[pos[0], pos[1]] - 0.01
                    )
                elif biome_name == "foresta":
                    # Forest shows autumn resource dynamics
                    self.data[pos[0], pos[1]] = min(
                        1.0, self.data[pos[0], pos[1]] + 0.015
                    )

        elif season == "winter":
            # Winter: Cold stress, reduced regeneration
            for pos, biome_name in self.biomes.items():
                if biome_name == "ocean":
                    # Ocean maintains resources well in winter
                    self.data[pos[0], pos[1]] = min(
                        1.0, self.data[pos[0], pos[1]] + 0.01
                    )
                elif biome_name == "swamp":
                    # Swamp faces winter challenges
                    self.data[pos[0], pos[1]] = max(
                        0.0, self.data[pos[0], pos[1]] - 0.01
                    )

    def add_nutrient_cluster(self, x, y, amount) -> None:
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.nutrient_clusters.append([x, y, amount])

    # ── Temperature effects on regeneration ──
    def _get_temp_regen_factor(self) -> float:
        """Temperature multiplier for food regeneration.
        Optimal at ~0.6 (temperate), decreases at extremes."""
        temp = self.temperature
        if temp < 0.3:
            # Cold: slow regen, smooth up to the temperate branch (0.6 at 0.3)
            return 0.3 + temp  # 0.3 at 0.0, 0.6 at 0.3
        elif temp > 0.8:
            # Hot: slow regen (desertification)
            return 1.2 - temp * 0.5  # 0.8 at 0.8, 0.7 at 1.0
        else:
            # Temperate: optimal regen
            # Peak at 0.6 with smooth interpolation
            return 0.8 + 0.4 * (
                1.0 - abs(temp - 0.6) / 0.2
            )  # 1.2 at 0.6, 0.8 at 0.3/0.8

    def step(self, dt: float, current_cell_count: int) -> None:
        w, h = self.w, self.h
        d = self.data

        # --- Temperature-modified regen ---
        temp_factor = self._get_temp_regen_factor()
        effective_regen = self.base_regen * temp_factor

        # --- Carrying capacity scaling ---
        if hasattr(self, "max_cells_for_carrying"):
            density_ratio = min(1.0, current_cell_count / self.max_cells_for_carrying)
            # At max density, regeneration is reduced to 20% to prevent resource depletion
            carrying_factor = 0.2 + 0.8 * (1.0 - density_ratio)
        else:
            carrying_factor = 1.0

        effective_regen *= carrying_factor

        # --- Regen: randomly boost 200 cells (vectorized) ---
        xs = np.random.randint(0, w, size=200)
        ys = np.random.randint(0, h, size=200)
        regen_amount = effective_regen * dt
        d[xs, ys] = np.minimum(1.0, d[xs, ys] + regen_amount)

        # --- Diffusion: spread energy between random neighbours (vectorized) ---
        xs = np.random.randint(0, w - 1, size=200)
        ys = np.random.randint(0, h, size=200)
        y2s = np.random.randint(0, h, size=200)
        diffs = (d[xs, ys] - d[xs + 1, y2s]) * self.diff * dt
        d[xs, ys] -= diffs
        d[xs + 1, y2s] += diffs

        # --- Nutrient clusters (from dead cells) ---
        new_clusters = []  # <-- initialised OUTSIDE the regen/diff loops
        for cx, cy, amount in self.nutrient_clusters:
            if amount > 0.1:
                if 0 <= cx < w and 0 <= cy < h:
                    d[cx, cy] = min(
                        1.0, d[cx, cy] + amount * CORPSE_NUTRIENT_FIELD_RATE
                    )
                amount *= CORPSE_NUTRIENT_FADE  # fade out
                new_clusters.append([cx, cy, amount])
        self.nutrient_clusters = new_clusters

    def consume(self, x, y, amt):
        """Remove up to `amt` energy from (x, y). Returns energy actually taken."""
        x, y = int(x), int(y)
        if not (0 <= x < self.w and 0 <= y < self.h):
            return 0.0

        t = min(self.data[x, y], amt)
        self.data[x, y] -= t

        multiplier = 1.0

        # Hotspot boost
        for hs in self.hotspots:
            if abs(hs[0] - x) + abs(hs[1] - y) <= 3:
                multiplier = 2.0
                break

        # Nutrient-cluster boost
        for i, (cx, cy, cl_amount) in enumerate(self.nutrient_clusters):
            if (
                cl_amount > 0.1
                and abs(cx - x) + abs(cy - y) <= CORPSE_NUTRIENT_BOOST_RADIUS
            ):
                multiplier = 2.0
                consumed = min(cl_amount, amt * 0.5)
                self.nutrient_clusters[i][2] -= consumed
                t += consumed * 0.3
                break

        return t * multiplier

    # ── Speciation biological consequences ──
    def trigger_species_competition(self, parent_cls, child_cls):
        """
        Trigger competitive dynamics between parent and child species.

        Introduces resource competition when a new species emerges from division.
        """
        # Find all cells of the parent species
        parent_cells = [
            c
            for c in getattr(self, "_cells", [])
            if hasattr(c, "cls") and c.cls == parent_cls
        ]

        if len(parent_cells) > 1 and len(parent_cells) >= 3:  # At least 3 parent cells
            # Increased competition dynamics
            for cell in parent_cells:
                if cell.energy > 0:
                    # Cells compete for limited resources
                    cell.compete_for_resources = True
                    # Resource allocation penalty
                    cell.energy *= 0.95
                    cell.energy = max(0.0, cell.energy)

    def schedule_species_migration(self, child_cls):
        """
        Schedule migratory patterns for newly speciated species.

        New species migrate to find less competitive environments.
        """
        # Calculate desired migration destination based on field characteristics
        potential_positions = []

        for x in range(0, self.w, 20):  # Check every 20 cells
            for y in range(0, self.h, 20):
                biome = self.get_biome(x, y)
                # Prefer biomes with moderate resource levels
                food_level = self.data[x, y]

                if 0.4 <= food_level <= 0.7:  # Moderate food areas
                    potential_positions.append((x, y, biome, food_level))

        if potential_positions:
            # Sort by food quality and biome diversity preference
            potential_positions.sort(
                key=lambda pos: (
                    abs(pos[3] - 0.55),
                    len(
                        [b for b in [p[2] for p in potential_positions] if b == pos[2]]
                    ),
                )
            )

            best_pos = potential_positions[0]
            # Create migration event for new species
            self.pending_migrations = getattr(self, "pending_migrations", {})
            self.pending_migrations[child_cls] = {
                "target_x": best_pos[0],
                "target_y": best_pos[1],
                "biome": best_pos[2],
                "food_level": best_pos[3],
            }

    def record_speciation_event(self, parent_cls, child_cls, child_diet):
        """
        Record speciation events for evolutionary tracking and feedback.

        Creates historical record of new species emergence for analysis.
        """
        self.speciation_history = getattr(self, "speciation_history", [])

        event = {
            "timestamp": len(self.speciation_history),
            "parent_species": parent_cls,
            "child_species": child_cls,
            "child_diet": child_diet,
            "parent_biome": self.get_biome(0, 0),  # Simplified - use cell position
            "resource_competition": True,
        }

        self.speciation_history.append(event)

        # Maintain event history limit (keep last 1000 events)
        if len(self.speciation_history) > 1000:
            self.speciation_history = self.speciation_history[-1000:]

    def draw(self, surf):
        w, h = self.w, self.h
        d = self.data

        if not hasattr(self, "_fsurf") or self._fsurf.get_size() != (w, h):
            self._fsurf = pygame.Surface((w, h))

        buf = pygame.surfarray.pixels3d(self._fsurf)
        g = (np.clip(d, 0.0, 1.0) * 255).astype(np.uint8)
        buf[:, :, 0] = 0
        buf[:, :, 1] = g
        buf[:, :, 2] = 0

        # Highlight hotspots
        for hx, hy, hv in self.hotspots:
            if 0 <= hx < w and 0 <= hy < h and d[hx, hy] > 0:
                b = int(hv * 255)
                buf[hx, hy] = (b // 2, b, 0)

        # Highlight nutrient clusters
        for cx, cy, amount in self.nutrient_clusters:
            if 0 <= cx < w and 0 <= cy < h and amount > 0.1:
                it = int(min(255, amount * 30))
                r = min(int(CORPSE_NUTRIENT_DRAW_MAX), int(amount * 0.4))
                pygame.draw.circle(self._fsurf, (it, it // 2, 0), (cx, cy), max(1, r))

        del buf
        surf.blit(self._fsurf, (0, 0))
