import random

from config import (
    ENERGY_MASS_COEFF,
    MAJOR_DIET_RATE,
    MAJOR_SENSE_RATE,
    DIET_DEFAULT_SPEED,
    DIET_DEFAULT_SENSE,
    PHOT,
    ZOOP,
    POLY,
    TEMP_MUT_NEUTRAL,
    TEMP_MUT_SWING,
    TEMP_MUT_DEFAULT,
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
        self.sense = max(30.0, min(120.0, float(se)))
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

    def clone_mutate(self, temperature=TEMP_MUT_DEFAULT) -> "Genome":
        has_major = random.random() < self.major_mut_rate

        # Temperature biases the mutational spectrum:
        #   cold  -> ecological (diet/niche) novelty
        #   warm  -> motoric/sensory fine-tuning
        # Each multiplier stays in [1 - swing, 1 + swing] (never zero), so
        # mutation never freezes out at either extreme.
        t = max(0.0, min(1.0, temperature))
        norm = max(-1.0, min(1.0, 2.0 * (t - TEMP_MUT_NEUTRAL)))  # [-1,1], 0 at neutral
        diet_mult = 1.0 - TEMP_MUT_SWING * norm  # cold up, warm down
        other_mult = 1.0 + TEMP_MUT_SWING * norm  # warm up, cold down

        # Effective per-gene rates: non-diet genes follow `other_mult`,
        # diet-switch drift follows `diet_mult`.
        mut_other = self.mut_rate * other_mult
        mut_diet = self.mut_rate * diet_mult

        def drift(v, mn, mx, rate=mut_other):
            """Minor per-gene mutation: ±15% jitter on the per-gene roll.
            Drives the continuous drift that produces speciation via the
            hash in refresh_class()."""
            if random.random() < rate:
                v *= random.uniform(0.85, 1.15)
            return max(mn, min(mx, v))

        # A diet switch is a niche shift (PHOT<->ZOOP<POLY): the sensory/motor
        # baseline reshapes to viable defaults for that role.
        alt_diets = (PHOT, ZOOP, POLY)

        def reset_to_diet(diet):
            return DIET_DEFAULT_SPEED[diet], DIET_DEFAULT_SENSE[diet]

        child_diet = self.diet
        child_speed = drift(self.speed, 0.5, 4.0)
        child_sense = drift(self.sense, 30.0, 120.0)

        if has_major:
            # A major mutation is a single coherent evolutionary leap — either
            # an ecological shift (diet) or a sensory re-org, never both.
            diet_change = random.random() < MAJOR_DIET_RATE * diet_mult
            sense_change = random.random() < MAJOR_SENSE_RATE * other_mult
            if diet_change and sense_change:
                if random.random() < 0.5:
                    diet_change = False
                else:
                    sense_change = False

            if diet_change:
                child_diet = random.choice([d for d in alt_diets if d != self.diet])
                child_speed, child_sense = reset_to_diet(child_diet)
            elif sense_change:
                # Evolve / lose a sense organ: a big jump on the perception axis.
                child_sense = min(120.0, child_sense * random.uniform(1.5, 2.0))
        else:
            # Minor path: rare diet drift. A niche tweak still reshapes the
            # speed/sense baseline (no half-viable hybrid phenotypes).
            if random.random() < mut_diet * 0.5:
                alt = [d for d in alt_diets if d != self.diet]
                if alt:
                    child_diet = random.choice(alt)
                    child_speed, child_sense = reset_to_diet(child_diet)

        child_lifespan = int(self.lifespan_ticks * random.uniform(0.80, 1.20))

        return Genome(
            speed=child_speed,
            sense=child_sense,
            metabolism=drift(self.metabolism, 0.005, 0.15),
            mut_rate=drift(self.mut_rate, 0.005, 0.3),
            major_mut_rate=drift(self.major_mut_rate, 0.0, 0.1),
            diet=child_diet,
            interact=drift(self.interact, 0.01, 1.0),
            divide_chance=drift(self.divide_chance, 0.05, 0.95),
            mass=drift(self.mass, 1.5, 8.0),
            dmg_phot=drift(self.dmg_phot, 0.05, 3.0),
            dmg_zoop=drift(self.dmg_zoop, 0.05, 3.0),
            dmg_poly=drift(self.dmg_poly, 0.05, 3.0),
            lifespan_ticks=child_lifespan,
            learning_rate=drift(self.learning_rate, 0.001, 0.2),
            memory_size=max(5, min(50, int(self.memory_size * random.uniform(0.8, 1.2)))),
            herd_tendency=drift(self.herd_tendency, 0.0, 1.0),
            cautious=drift(self.cautious, 0.0, 1.0),
            epigenetics=drift(self.epigenetics, 0.0, 1.0),
        )

