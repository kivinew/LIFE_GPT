#!/usr/bin/env python3
# Make legend font bigger and add music control
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Increase legend font size
content = content.replace(
    'legend = pygame.font.SysFont(None, 16)  # Larger font for legend',
    'legend = pygame.font.SysFont(None, 20)  # Even larger font for legend'
)

# 2. Add music slider (assuming pygame.mixer is already initialized)
# Find the UI widgets section (around line 185-210)
ui_widgets_start = content.find('sl_time    = Slider(COL_LX, 611, COL_W, tr("time_scale"), 0.1, 5.0, 1.0)')
if ui_widgets_start == -1:
    print("Could not find UI widgets section")
else:
    # Add music slider after time_scale slider
    music_slider = '''    sl_music = Slider(COL_LX, 641, COL_W, tr("music"), 0.0, 1.0, 0.8)
'''
    
    # Replace the time_scale line and add music slider
    old_section = '''    sl_time    = Slider(COL_LX, 611, COL_W, tr("time_scale"), 0.1, 5.0, 1.0)'''
    new_section = '''    sl_time    = Slider(COL_LX, 611, COL_W, tr("time_scale"), 0.1, 5.0, 1.0)
    sl_music  = Slider(COL_LX, 641, COL_W, tr("music"), 0.0, 1.0, 0.8)'''
    
    content = content.replace(old_section, new_section)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Made legend font bigger and added music slider")