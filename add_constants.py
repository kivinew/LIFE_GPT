with open('config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing constants before BASE_LIFESPAN_TICKS
new_constants = '''
# Disease system
DISEASE_CHANCE = 0.001
DISEASE_DURATION = 500
DISEASE_METABOLISM_MULT = 2.0
DISEASE_TRANSMISSION_RANGE = 50.0

# Migration
MIGRATION_CHANCE = 0.001
MIGRATION_DISTANCE = 100.0

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
DIET_DEFAULT_SPEED = 2.0
DIET_DEFAULT_SENSE = 65.0

# Division
DIVIDE_ENERGY_RATIO = 0.95
DIVIDE_MIN_AGE = 1000

# Temp mutation
TEMP_MUT_DEFAULT = 0.5

# Movement
MOVEMENT_SCALE = 40.0

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
SEASON_ORDER = [\"spring\", \"summer\", \"autumn\", \"winter\"]
SEASON_LENGTH = 2000
SEASON_FACTORS = {\"spring\": 1.2, \"summer\": 1.0, \"autumn\": 0.8, \"winter\": 0.6}
SEASON_TEMPERATURES = {\"spring\": 0.4, \"summer\": 0.7, \"autumn\": 0.3, \"winter\": 0.1}

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
TIME_LAPSE_FRAMES_DIR = \"frames\"
TIME_LAPSE_MAX_FRAMES = 10000
TIME_LAPSE_DURATION_MIN = 10

# Max level
MAX_LEVEL = 10

# Corpse nutrient
CORPSE_NUTRIENT_BOOST_RADIUS = 12
CORPSE_NUTRIENT_BOOST_MULT = 2.5
CORPSE_NUTRIENT_EXTRA_ENERGY = 0.5
CORPSE_NUTRIENT_MIN_AMOUNT = 0.05

'''

content = content.replace('BASE_LIFESPAN_TICKS = 3000', new_constants + 'BASE_LIFESPAN_TICKS = 3000')

with open('config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Added missing constants')
