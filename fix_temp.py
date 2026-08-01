#!/usr/bin/env python3
# Fix temperature formula to give slider meaningful influence
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'field.temperature = max(0.0, min(1.0, season_temp + slider_offset * 0.1))',
    'field.temperature = max(0.0, min(1.0, season_temp * 0.3 + slider_offset * 0.7))'
)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed temperature slider influence")