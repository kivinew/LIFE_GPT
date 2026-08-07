import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
pygame.init()
pygame.display.set_mode((800, 600))
pygame.mixer.init(44100, -16, 2, 512)
import numpy as np
from field import ResourceField
from config import *

field = ResourceField(300, 300)
cell_color = pygame.Color(255, 0, 0)
field.add_nutrient_cluster(150, 150, 5.0, cell_color=cell_color)
for _ in range(5):
    field.step(1.0, 0, decay_rate=0.001)

# Call draw to init _fsurf and apply coloring
screen = pygame.Surface((300, 300))
field.draw(screen)

# Check if red color was applied
red_pixels = []
for y in range(130, 170):
    for x in range(130, 170):
        c = screen.get_at((x, y))
        if c[0] > 50 and c[1] < 100 and c[2] < 100:
            red_pixels.append((x, y, c))

print(f'Red-ish pixels in 130-170 region: {len(red_pixels)}')
if red_pixels:
    print(f'Sample: {red_pixels[:5]}')
else:
    print('No red pixels found!')
    # Check what colors exist
    colors = set()
    for y in range(145, 156):
        for x in range(145, 156):
            c = screen.get_at((x, y))
            colors.add(c)
    print(f'Colors near center: {colors}')
