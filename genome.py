import random
from typing import Tuple, List

from config import (
    ENERGY_MASS_COEFF,
    MAJOR_DIET_RATE,
    MAJOR_SENSE_RATE,
    DIET_DEFAULT_SPEED,
    DIET_DEFAULT_SENSE,
)


class Genome:
    """
    Genetic blueprint for a cell, controlling physical and behavioral traits.
    Includes learning_rate — how fast the cell adapts behavior from experience.
    """

    __slots__ = (
        "speed",
        "sense",
        "mass",
        "metabolism",
        "mut_rate",
        "diet",
        "interact",
        "divide_chance",
        "dmg_phot",
        "dmg_zoop",
        "dmg_poly",
        "lifespan_ticks",
        "major_mut_rate",
        "learning_rate",
        "memory_size",
        "herd_tendency",
        "cautious",
        "epigenetics",  # epigenetic trait for temporary expression changes
    )

    def __init__(
        self,
        s=None,
        se=None,
        m=0.02,
        mr=0.08,
        diet=0,
        interact=0.5,
        div=0.5,
        mass=4.0,
        dmg_phot=0.6,
        dmg_zoop=1.2,
        dmg_poly=1.0,
        lifespan_ticks=None,
        major_mut_rate=0.1,
        learning_rate=0.05,
        memory_size=20,
        herd_tendency=0.2,
        cautious=0.3,
        epigenetics=0.3,
        # keyword aliases
        speed=None,
        sense=None,
        metabolism=None,
        mut_rate=None,
        divide_chance=None,
    ):
        if speed is not None:
            s = speed
        if sense is not None:
            se = sense
        if metabolism is not None:
            m = metabolism
        if mut_rate is not None:
            mr = mut_rate
        if divide_chance is not None:
            div = divide_chance

        if s is None:
            s = DIET_DEFAULT_SPEED[diet if diet in (0, 1, 2) else 0]
        if se is None:
            se = DIET_DEFAULT_SENSE[diet if diet in (0, 1, 2) else 0]

        self.speed = max(0.5, min(4.0, float(s)))
        self.sense = max(10.0, min(120.0, float(se)))
        self.mass = max(2.0, min(8.0, float(mass)))
        self.metabolism = max(0.01, min(0.15, float(m)))
        self.mut_rate = max(0.01, min(0.3, float(mr)))
        self.diet = diet if diet in (0, 1, 2) else 0
        self.interact = max(0.01, min(1.0, float(interact)))
        self.divide_chance = max(0.1, min(0.9, float(div)))
        self.dmg_phot = max(0.1, min(3.0, float(dmg_phot)))
        self.dmg_zoop = max(0.1, min(3.0, float(dmg_zoop)))
        self.dmg_poly = max(0.1, min(3.0, float(dmg_poly)))

        if lifespan_ticks is None:
            base = 3000 + self.mass * 200
            self.lifespan_ticks = int(base * random.uniform(0.85, 1.15))
        else:
            self.lifespan_ticks = max(500, int(lifespan_ticks))

        self.major_mut_rate = max(0.0, min(0.1, float(major_mut_rate or 0.1)))

        # Learning parameters — how fast cell adapts from experience
        self.learning_rate = max(0.001, min(0.2, float(learning_rate)))
        # Max number of memorised events
        self.memory_size = max(5, min(50, int(memory_size)))
        # Herd tendency — tendency to follow same-class cells
        self.herd_tendency = max(0.0, min(1.0, float(herd_tendency)))
        # Cautious — probability to flee when low energy
        self.cautious = max(0.0, min(1.0, float(cautious)))

        # Epigenetics — heritable trait expression level (0.0-1.0)
        self.epigenetics = max(0.0, min(1.0, float(epigenetics)))

    @property
    def max_energy(self) -> float:
        return self.mass * self.mass * ENERGY_MASS_COEFF

    def clone_mutate(self) -> "Genome":
        has_major = random.random() < self.major_mut_rate

        def mut(v: float, mn: float, mx: float) -> float:
            if random.random() < self.mut_rate:
                if has_major:
                    v *= random.uniform(0.5, 1.5)
                else:
                    v *= random.uniform(0.85, 1.15)
            return max(mn, min(mx, v))

        # Major mutations: ~10% chance to create new diet or sense organ
        child_diet = self.diet
        child_sense = self.sense
        if has_major:
            # Major mutations can create new diets or sense organs (but not both)
            # Each has ~50% chance - use both constants for independent decisions
            diet_change = random.random() < MAJOR_DIET_RATE
            sense_change = random.random() < MAJOR_SENSE_RATE

            # Ensure we don't change both diet and sense (excluded combinations)
            if diet_change and sense_change:
                # Randomly choose one to avoid changing both
                if random.random() < 0.5:
                    diet_change = False
                else:
                    sense_change = False

            if diet_change:
                child_diet = random.choice([0, 1, 2])
                # Sense reset to base when diet changes
                child_sense = 10.0
            elif sense_change:
                # Sense progression: 0 (none) -> 1 -> 2 (full)
                current_level = (
                    child_sense / 120.0
                )  # 0.0 = 10, 0.083 = 10~20, 1.0 = 120
                if current_level < 0.5:  # If sense level 0 or basic (0-60)
                    child_sense = random.choice(
                        [10.0, 60.0]
                    )  # Jump to 0 (disabled) or 1 (basic)
                elif current_level < 1.0:  # If sense level intermediate (60-120)
                    child_sense = 120.0  # Jump to full (2)
                else:
                    child_sense = current_level  # Keep same if already at max
        else:
            # Minor mutations: random diet change with smaller probability
            if random.random() < self.mut_rate * 0.5:
                child_diet = random.choice([0, 1, 2])

        child_lifespan = int(self.lifespan_ticks * random.uniform(0.80, 1.20))

        return Genome(
            speed=mut(self.speed, 0.5, 4.0),
            sense=mut(self.sense, 10.0, 120.0),
            metabolism=mut(self.metabolism, 0.005, 0.15),
            mut_rate=mut(self.mut_rate, 0.005, 0.3),
            major_mut_rate=mut(self.major_mut_rate, 0.0, 0.1),
            diet=child_diet,
            interact=mut(self.interact, 0.01, 1.0),
            divide_chance=mut(self.divide_chance, 0.05, 0.95),
            mass=mut(self.mass, 1.5, 8.0),
            dmg_phot=mut(self.dmg_phot, 0.05, 3.0),
            dmg_zoop=mut(self.dmg_zoop, 0.05, 3.0),
            dmg_poly=mut(self.dmg_poly, 0.05, 3.0),
            lifespan_ticks=child_lifespan,
            learning_rate=mut(self.learning_rate, 0.001, 0.2),
            memory_size=int(self.memory_size * random.uniform(0.8, 1.2)),
            herd_tendency=mut(self.herd_tendency, 0.0, 1.0),
            cautious=mut(self.cautious, 0.0, 1.0),
            epigenetics=mut(self.epigenetics, 0.0, 1.0),
        )

    def trait_tuple(self) -> Tuple[float, ...]:
        return (
            round(self.speed, 1),
            round(self.sense, 1),
            round(self.mass, 1),
            round(self.metabolism, 2),
            round(self.interact, 2),
            round(self.herd_tendency, 2),
            round(self.cautious, 2),
            round(self.epigenetics, 3),
        )

    def apply_epigenetic_modulation(self, environment_factor: float = 1.0) -> "Genome":
        """
        Apply epigenetic modulation - temporary gene expression changes.
        The epigenetics trait (0.0-1.0) represents the level of heritable expression
        changes that modify phenotype without changing DNA sequence.

        Args:
            environment_factor: Multiplier from environmental conditions (0.5-2.0)

        Returns:
            New Genome instance with modulated traits based on epigenetics
        """
        # Epigenetic influence scales traits based on environment
        # Higher epigenetics = more pronounced environmental response
        modulation = 1.0 + (self.epigenetics * (environment_factor - 1.0) * 0.5)

        return Genome(
            speed=mut(self.speed * modulation, 0.5, 4.0),
            sense=mut(self.sense * modulation, 10.0, 120.0),
            metabolism=mut(self.metabolism * modulation, 0.005, 0.15),
            mut_rate=mut(self.mut_rate, 0.005, 0.3),
            major_mut_rate=mut(self.major_mut_rate, 0.0, 0.1),
            diet=self.diet,  # Diet remains fixed, epigenetics affects expression
            interact=mut(self.interact * modulation, 0.01, 1.0),
            divide_chance=mut(self.divide_chance, 0.05, 0.95),
            mass=mut(self.mass, 1.5, 8.0),
            dmg_phot=mut(self.dmg_phot, 0.05, 3.0),
            dmg_zoop=mut(self.dmg_zoop, 0.05, 3.0),
            dmg_poly=mut(self.dmg_poly, 0.05, 3.0),
            lifespan_ticks=self.lifespan_ticks,
            learning_rate=mut(self.learning_rate, 0.001, 0.2),
            memory_size=int(self.memory_size * random.uniform(0.8, 1.2)),
            herd_tendency=mut(self.herd_tendency, 0.0, 1.0),
            cautious=mut(self.cautious, 0.0, 1.0),
            epigenetics=mut(self.epigenetics * 0.95, 0.0, 1.0),  # Decay over time
        )

    def reset_epigenetics(self) -> "Genome":
        """Reset epigenetics to baseline (0.0) without passing through environment."""
        # Create new genome with baseline epigenetics
        return Genome(
            speed=self.speed,
            sense=self.sense,
            metabolism=self.metabolism,
            mut_rate=self.mut_rate,
            major_mut_rate=self.major_mut_rate,
            diet=self.diet,
            interact=self.interact,
            divide_chance=self.divide_chance,
            mass=self.mass,
            dmg_phot=self.dmg_phot,
            dmg_zoop=self.dmg_zoop,
            dmg_poly=self.dmg_poly,
            lifespan_ticks=self.lifespan_ticks,
            learning_rate=self.learning_rate,
            memory_size=self.memory_size,
            herd_tendency=self.herd_tendency,
            cautious=self.cautious,
            epigenetics=0.0,  # Reset to baseline
        )

    def genetic_distance(self, other_genome) -> float:
        """Calculate genetic distance between this and another genome.

        Returns a value 0.0-1.0 where 0.0 = identical, 1.0 = completely different.
        Based on trait differences normalized by each trait's possible range.
        """
        total_distance = 0.0
        # Traits with their max/min ranges for normalization
        trait_ranges = {
            "speed": (0.5, 4.0),
            "sense": (10.0, 120.0),
            "mass": (2.0, 8.0),
            "metabolism": (0.01, 0.15),
            "mut_rate": (0.01, 0.3),
            "divide_chance": (0.1, 0.9),
            "dmg_phot": (0.1, 3.0),
            "dmg_zoop": (0.1, 3.0),
            "dmg_poly": (0.1, 3.0),
            "learning_rate": (0.001, 0.2),
            "memory_size": (5, 50),
            "herd_tendency": (0.0, 1.0),
            "cautious": (0.0, 1.0),
            "epigenetics": (0.0, 1.0),
        }

        # Skip diet - major mutations can create new diets but they're considered separate species
        # Skip lifespan which is derived from mass

        for trait, (min_val, max_val) in trait_ranges.items():
            trait_distance = 0.0
            if hasattr(self, trait) and hasattr(other_genome, trait):
                val1 = getattr(self, trait)
                val2 = getattr(other_genome, trait)
                if val1 is not None and val2 is not None:
                    # Normalize difference by range size
                    range_size = max_val - min_val if max_val != min_val else 1.0
                    trait_distance = abs(val1 - val2) / range_size
                    total_distance += trait_distance

        # Normalize to 0-1 scale
        return min(total_distance / len(trait_ranges), 1.0)

    def species_signature(self) -> tuple:
        """Create a species signature based on key traits.

        Used for initial species classification - focuses on diet, sense, and major traits
        rather than all individual genes.
        """
        return (
            self.diet,
            self.sense,
            self.mass,
            self.metabolism,
            self.learning_rate,
            self.memory_size,
            self.herd_tendency,
            self.cautious,
            round(self.epigenetics, 3),
        )

    def is_new_species(self, other_genome, distance_threshold=0.85) -> bool:
        """Determine if another genome represents a new species.

        Uses genetic distance to compare to SPECIES_SIMILARITY_THRESHOLD from config.
        Returns True if the genomes are different enough to be considered separate species.
        """
        from config import SPECIES_SIMILARITY_THRESHOLD

        distance = self.genetic_distance(other_genome)
        return distance >= SPECIES_SIMILARITY_THRESHOLD

    def distance_to(self, other_genome) -> float:
        """Helper method for easy access to genetic distance."""
        return self.genetic_distance(other_genome)
