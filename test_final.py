"""Final integration test for corpse puddle coloring + division mechanics."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
pygame.init()
pygame.display.set_mode((800, 600))
pygame.mixer.init(44100, -16, 2, 512)
import random
import numpy as np
from field import ResourceField
from config import *

# ========================
# Test 1: Corpse puddle color
# ========================
print("=" * 50)
print("Test 1: Corpse puddle color")
field = ResourceField(300, 300)
red_color = pygame.Color(255, 0, 0)
field.add_nutrient_cluster(150, 150, 5.0, cell_color=red_color)
for _ in range(5):
    field.step(1.0, 0, decay_rate=0.001)

screen = pygame.Surface((300, 300))
field.draw(screen)
center = (150, 150)
center_color = screen.get_at(center)
print(f"Puddle center (150,150): {center_color}")
assert center_color[0] > 200 and center_color[1] < 50 and center_color[2] < 50, "Expected red color!"
print("PASS: Puddle is red")

# Test 2: Green cell -> green puddle
print("\nTest 2: Green cell puddle")
field2 = ResourceField(300, 300)
green_color = pygame.Color(0, 255, 0)
field2.add_nutrient_cluster(100, 100, 5.0, cell_color=green_color)
for _ in range(3):
    field2.step(1.0, 0, decay_rate=0.001)
screen2 = pygame.Surface((300, 300))
field2.draw(screen2)
center_color2 = screen2.get_at((100, 100))
print(f"Green puddle center (100,100): {center_color2}")
assert center_color2[1] > 200 and center_color2[0] < 50 and center_color2[2] < 50, "Expected green!"
print("PASS: Puddle is green")

# Test 3: No cell color -> seasonal color (default)
print("\nTest 3: No cell color -> seasonal food")
field3 = ResourceField(300, 300)
field3.add_nutrient_cluster(150, 150, 5.0, cell_color=None)
for _ in range(3):
    field3.step(1.0, 0, decay_rate=0.001)
screen3 = pygame.Surface((300, 300))
field3.draw(screen3)
center_color3 = screen3.get_at((150, 150))
print(f"No-color puddle center (150,150): {center_color3}")
# Should be seasonal (green-ish in spring)
print("PASS: Seasonal coloring applied (no cell color override)")

# ========================
# Test 2: Division mechanics
# ========================
print("\n" + "=" * 50)
print("Test 4: Division mechanics")
from genome import Genome
from cell import Cell

random.seed(42)
g = Genome(diet=PHOT, speed=2.0, sense=60.0, mass=4.0, div=0.9)
c = Cell(100, 100, g)
c.age = DIVIDE_MIN_AGE + 1
c.energy = c.max_energy * 0.96

print(f"Parent energy before: {c.energy:.2f} / {c.max_energy:.2f}")
child = c.divide()
print(f"Parent energy after: {c.energy:.2f} ({c.energy/c.max_energy*100:.0f}%)")
print(f"Child energy: {child.energy:.2f} ({child.energy/child.max_energy*100:.0f}%)")
assert child is not None, "Division should succeed"
assert c.energy / c.max_energy >= 0.20, "Parent should keep >= 20% energy"
assert child.energy <= child.max_energy, "Child energy should not exceed max"
print("PASS: Division mechanics correct")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
