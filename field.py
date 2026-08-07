# ResourceField class for LIFE_GPT
# Energy field with regen, diffusion, hotspots, and nutrient clusters
import numpy as np
import pygame
import random
import math
from config import (
    W,
    H,
    CORPSE_NUTRIENT_FIELD_RATE,
    CORPSE_NUTRIENT_FADE,
    CORPSE_NUTRIENT_DRAW_MAX,
    CORPSE_NUTRIENT_BOOST_RADIUS,
    CORPSE_NUTRIENT_BOOST_MULT,
    CORPSE_NUTRIENT_EXTRA_ENERGY,
    CORPSE_NUTRIENT_MIN_AMOUNT,
    SEASON_FOOD_COLORS,
    FOOD_DECAY_RATE,
    FOOD_REGEN_SPREAD,
    FOOD_CLUSTER_RADIUS,
    FOOD_CLUSTER_CHANCE,
    FOOD_HOTSPOT_BOOST,
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

    def add_nutrient_cluster(self, x, y, amount, cell_color=None) -> None:
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h and amount > 0.01:
            # Precompute an irregular organic puddle mask for this cluster
            # so the shape stays consistent across ticks
            seed = int((x * 7 + y * 13 + amount * 1000)) % 10000
            rng = np.random.RandomState(seed)
            max_r = FOOD_CLUSTER_RADIUS
            mask_size = max_r * 2 + 1
            mx, my = np.ogrid[:mask_size, :mask_size]
            dxm = mx - max_r
            dym = my - max_r
            dist_m = np.sqrt(dxm ** 2 + dym ** 2)
            ang_m = np.arctan2(dym, dxm)
            # Organic puddle boundary: radial sine modulation + smooth noise jitter
            # Irrational frequencies break rotational symmetry; noise adds organic texture
            # Generate smooth noise field via bilinear interpolation of coarse grid
            coarse_size = max(4, max_r // 4)
            coarse_noise = rng.rand(coarse_size, coarse_size)
            yy, xx = np.mgrid[:mask_size, :mask_size]
            cx = xx * (coarse_size - 1) / (mask_size - 1)
            cy = yy * (coarse_size - 1) / (mask_size - 1)
            ixc = np.clip(cx.astype(int), 0, coarse_size - 2)
            iyc = np.clip(cy.astype(int), 0, coarse_size - 2)
            fxc = cx - ixc
            fyc = cy - iyc
            noise = (
                coarse_noise[iyc, ixc] * (1 - fxc) * (1 - fyc)
                + coarse_noise[iyc, ixc + 1] * fxc * (1 - fyc)
                + coarse_noise[iyc + 1, ixc] * (1 - fxc) * fyc
                + coarse_noise[iyc + 1, ixc + 1] * fxc * fyc
            )
            # Multi-frequency sine modulation + noise jitter
            rad_mod = (
                1.0
                + 0.30 * np.sin(seed * 0.017 + ang_m * 1.3)
                + 0.25 * np.cos(seed * 0.023 + ang_m * 2.7)
                + 0.20 * np.sin(seed * 0.031 + ang_m * 4.1)
                + 0.15 * np.cos(seed * 0.037 + ang_m * 5.9)
            )
            # Modulate amplitude by noise for organic irregularity
            rad_mod = rad_mod * (0.6 + 0.4 * noise)
            max_diag = max_r * np.sqrt(2)
            boundary_r = np.clip(rad_mod * max_r, max_r * 0.15, max_diag)
            # Binary organic mask
            puddle_mask = (dist_m <= boundary_r).astype(np.float32)
            # Organic falloff: radial with noise modulation (breaks perfect radial symmetry)
            base_falloff = np.clip(1.0 - dist_m / np.maximum(boundary_r, 1), 0, 1)
            falloff = base_falloff * (0.5 + 0.5 * noise)
            self.nutrient_clusters.append([x, y, amount, puddle_mask, falloff, max_r, cell_color])

    # ── Temperature effects on regeneration ──
    def _get_temp_regen_factor(self) -> float:
        """Temperature multiplier for food regeneration.
        Smoothly proportional to temperature: 0 at temp=0, 1 at temp=1.
        Below 0°C (temp < 0.222) no regeneration."""
        FREEZE = 0.222  # 0°C in internal units
        if self.temperature < FREEZE:
            return 0.0
        return self.temperature

    def step(self, dt: float, current_cell_count: int, decay_rate: float = None, nutrient_fade: float = None) -> None:
        w, h = self.w, self.h
        d = self.data

        # --- Temperature-modified regen ---
        temp_factor = self._get_temp_regen_factor()
        effective_regen = self.base_regen * temp_factor

        # --- Food decay (natural lifetime) ---
        # All food decays so it doesn't accumulate indefinitely.
        if decay_rate is None:
            decay_rate = FOOD_DECAY_RATE
        d *= (1.0 - decay_rate * dt)

        # --- Carrying capacity scaling ---
        if hasattr(self, "max_cells_for_carrying"):
            density_ratio = min(1.0, current_cell_count / self.max_cells_for_carrying)
            # At max density, regeneration is reduced to 20% to prevent resource depletion
            carrying_factor = 0.2 + 0.8 * (1.0 - density_ratio)
        else:
            carrying_factor = 1.0

        effective_regen *= carrying_factor

        # --- Regen: boost FOOD_REGEN_SPREAD cells (vectorized) ---
        # 30% of regen happens near nutrient clusters (hotspots),
        # 70% is spread randomly across the field.
        xs = np.random.randint(0, w, size=FOOD_REGEN_SPREAD)
        ys = np.random.randint(0, h, size=FOOD_REGEN_SPREAD)
        regen_amount = effective_regen * dt
        # Nutrient-cluster hotspots: regen in irregular organic puddle shape
        for cluster in self.nutrient_clusters:
            cx, cy, cl_amount = cluster[0], cluster[1], cluster[2]
            if cl_amount > CORPSE_NUTRIENT_MIN_AMOUNT and 0 <= cx < w and 0 <= cy < h:
                # Use precomputed organic mask from add_nutrient_cluster
                puddle_mask = cluster[3]
                falloff = cluster[4]
                max_r = cluster[5]
                weighted = puddle_mask * falloff
                dw = weighted * regen_amount * CORPSE_NUTRIENT_FIELD_RATE * 3.0
                # Apply only to masked pixels using direct indexing (no bounding box bleed)
                my_y, mx_x = np.where(puddle_mask)
                gy = np.clip(cx - max_r + mx_x, 0, w - 1)
                gx = np.clip(cy - max_r + my_y, 0, h - 1)
                d[gy, gx] = np.minimum(1.0, d[gy, gx] + dw[my_y, mx_x])
        # Random regen across the field
        d[xs, ys] = np.minimum(1.0, d[xs, ys] + regen_amount)

        # --- Diffusion: spread energy between random neighbours (vectorized) ---
        xs = np.random.randint(0, w - 1, size=200)
        ys = np.random.randint(0, h, size=200)
        y2s = np.random.randint(0, h, size=200)
        diffs = (d[xs, ys] - d[xs + 1, y2s]) * self.diff * dt
        d[xs, ys] -= diffs
        d[xs + 1, y2s] += diffs

        # --- Nutrient clusters (from dead cells) ---
        if nutrient_fade is None:
            nutrient_fade = CORPSE_NUTRIENT_FADE
        new_clusters = []
        for cluster in self.nutrient_clusters:
            cx, cy, amount = cluster[0], cluster[1], cluster[2]
            if amount > 0.1:
                if 0 <= cx < w and 0 <= cy < h:
                    d[cx, cy] = min(
                        1.0, d[cx, cy] + amount * CORPSE_NUTRIENT_FIELD_RATE * 1.0
                    )
                amount *= nutrient_fade
                # Preserve precomputed mask/falloff/max_r
                new_clusters.append([cx, cy, amount] + list(cluster[3:]))
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
            if (hs[0] - x) ** 2 + (hs[1] - y) ** 2 <= 9:  # 3px radius (squared)
                multiplier = 2.0
                break

        # Nutrient-cluster boost
        for i, cluster in enumerate(self.nutrient_clusters):
            cx, cy, cl_amount = cluster[0], cluster[1], cluster[2]
            if cl_amount > CORPSE_NUTRIENT_MIN_AMOUNT:
                dist_sq = (cx - x) ** 2 + (cy - y) ** 2
                if dist_sq <= CORPSE_NUTRIENT_BOOST_RADIUS ** 2:
                    multiplier = CORPSE_NUTRIENT_BOOST_MULT
                    consumed = min(cl_amount, amt * 0.5)
                    self.nutrient_clusters[i][2] -= consumed
                    t += consumed * CORPSE_NUTRIENT_EXTRA_ENERGY
                    break

        return t * multiplier

    def draw(self, surf, season="spring", season_progress=0.0, next_season="spring"):
        w, h = self.w, self.h
        d = self.data

        if not hasattr(self, "_fsurf") or self._fsurf.get_size() != (w, h):
            self._fsurf = pygame.Surface((w, h))

        buf = pygame.surfarray.pixels3d(self._fsurf)
        g = (np.clip(d, 0.0, 1.0) * 255).astype(np.uint8)

        # Smoothly interpolate food color between current and next season
        cur_col = SEASON_FOOD_COLORS.get(season, (0.0, 0.8, 0.0))
        nxt_col = SEASON_FOOD_COLORS.get(next_season, (0.0, 0.8, 0.0))
        sp = max(0.0, min(1.0, season_progress))
        rc = cur_col[0] * (1 - sp) + nxt_col[0] * sp
        gc = cur_col[1] * (1 - sp) + nxt_col[1] * sp
        bc = cur_col[2] * (1 - sp) + nxt_col[2] * sp
        buf[:, :, 0] = (g * rc).astype(np.uint8)
        buf[:, :, 1] = (g * gc).astype(np.uint8)
        buf[:, :, 2] = (g * bc).astype(np.uint8)

        del buf  # unlock _fsurf before creating PixelArray

        # Highlight nutrient clusters — organic shape, colored by dead cell
        for cluster in self.nutrient_clusters:
            cx, cy, amount, cluster_mask, falloff, cluster_max_r = cluster[0], cluster[1], cluster[2], cluster[3], cluster[4], cluster[5]
            cell_color = cluster[6] if len(cluster) > 6 else None
            if amount > CORPSE_NUTRIENT_MIN_AMOUNT and cell_color is not None:
                # Recolor food pixels within the organic mask to the dead cell's color
                my_y, mx_x = np.where(cluster_mask)
                gy = np.clip(cx - cluster_max_r + mx_x, 0, w - 1)
                gx = np.clip(cy - cluster_max_r + my_y, 0, h - 1)
                intensities = d[gy, gx]
                active = intensities > 0.01
                if np.any(active):
                    cr = cell_color[0]
                    cg = cell_color[1]
                    cb = cell_color[2]
                    g_ = (intensities[active] * 255).astype(np.uint8)
                    pa = pygame.PixelArray(self._fsurf)
                    for i in range(len(gy[active])):
                        gx_i = int(gx[active][i])
                        gy_i = int(gy[active][i])
                        g_val = int(g_[i])
                        pa[gy_i, gx_i] = (
                            g_val * cr // 255,
                            g_val * cg // 255,
                            g_val * cb // 255,
                        )
                    del pa

        # Highlight hotspots
        for hx, hy, hv in self.hotspots:
            if 0 <= hx < w and 0 <= hy < h and d[hx, hy] > 0:
                b = int(hv * 255)
                self._fsurf.set_at((hx, hy), (b // 2, b, 0))

        surf.blit(self._fsurf, (0, 0))
