with open('config.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Increase winter temperature above freeze point (0.222)
# Winter 0.1 -> 0.35 (above freeze, but still cold)
content = content.replace(
    'SEASON_TEMPERATURES = {\"spring\": 0.4, \"summer\": 0.7, \"autumn\": 0.3, \"winter\": 0.1}',
    'SEASON_TEMPERATURES = {\"spring\": 0.4, \"summer\": 0.7, \"autumn\": 0.3, \"winter\": 0.35}'
)

# Also fix the duplicate
content = content.replace(
    'SEASON_TEMPERATURES = {\n    \"spring\": 0.4,\n    \"summer\": 0.7,\n    \"autumn\": 0.3,\n    \"winter\": 0.1\n}',
    'SEASON_TEMPERATURES = {\n    \"spring\": 0.4,\n    \"summer\": 0.7,\n    \"autumn\": 0.3,\n    \"winter\": 0.35\n}'
)

# Fix 2: Lower division requirements
# DIVIDE_ENERGY_RATIO: 0.95 -> 0.70 (70% of max energy)
content = content.replace('DIVIDE_ENERGY_RATIO = 0.95', 'DIVIDE_ENERGY_RATIO = 0.70')

# DIVIDE_MIN_AGE: 1000 -> 200 (faster first division)
content = content.replace('DIVIDE_MIN_AGE = 1000', 'DIVIDE_MIN_AGE = 200')

# Fix 3: Increase initial energy for better survival
# ZOO_INITIAL_ENERGY: 50 -> 80
content = content.replace('ZOO_INITIAL_ENERGY = 50.0', 'ZOO_INITIAL_ENERGY = 80.0')
# PHOT_INITIAL_ENERGY: 45 -> 70
content = content.replace('PHOT_INITIAL_ENERGY = (\n    45.0', 'PHOT_INITIAL_ENERGY = (\n    70.0')

with open('config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Config fixes applied')
