import re

# Read the backup file
with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py.backup', 'r', encoding='utf-8') as f:
    backup_content = f.read()

# Define the new class definitions with caching
new_slider = '''class Slider:
    def __init__(self, x, y, w, lab, mn, mx, val, labels=None, unit=None):
        self.rect = pygame.Rect(x, y, w, 20)
        self.lab, self.mn, self.mx, self.val = lab, mn, mx, val
        self.labels = labels
        self.unit = unit
        self.drag = False
        self._cached_text = None
        self._cached_text_str = None

    def draw(self, surf, font):
        if self.unit:
            text_str = f"{self.lab}: {self.val:.0f}{self.unit}"
        else:
            text_str = f"{self.lab}: {self.val:.2f}"
        if self._cached_text is None or self._cached_text_str != text_str:
            self._cached_text = font.render(text_str, True, WHITE)
            self._cached_text_str = text_str
        surf.blit(self._cached_text, (self.rect.x, self.rect.y - 12))
        pygame.draw.rect(
            surf, DARK, (self.rect.x, self.rect.y + 3, self.rect.w, 6), 0, 3
        )
        fw = int((self.val - self.mn) / (self.mx - self.mn) * self.rect.w)
        pygame.draw.rect(surf, BLUE, (self.rect.x, self.rect.y + 3, fw, 6), 0, 3)
        if self.labels and len(self.labels) > 1:
            n = len(self.labels)
            for i in range(n):
                lx = self.rect.x + int(i * self.rect.w / (n - 1))
                ly = self.rect.y + 11
                tick_col = (
                    BLUE
                    if self.val >= self.mn + i * (self.mx - self.mn) / (n - 1)
                    and self.val < self.mn + (i + 1) * (self.mx - self.mn) / (n - 1)
                    else GRAY
                )
                pygame.draw.line(surf, tick_col, (lx, ly - 1), (lx, ly + 1), 1)
                lt = font.render(self.labels[i], True, tick_col)
                surf.blit(lt, (lx - lt.get_width() // 2, ly + 3))'''

new_sliderint = '''class SliderInt:
    def __init__(self, x, y, w, lab, mn, mx, val, labels=None):
        self.rect = pygame.Rect(x, y, w, 20)
        self.lab = lab
        self.mn, self.mx = mn, mx
        self.val = int(val)
        self.labels = labels
        self.drag = False
        self._cached_text = None
        self._cached_text_str = None

    def draw(self, surf, font):
        current_label = self.labels[int(self.val)] if self.labels else str(self.val)
        text_str = f"{self.lab}: {current_label}"
        if self._cached_text is None or self._cached_text_str != text_str:
            self._cached_text = font.render(text_str, True, WHITE)
            self._cached_text_str = text_str
        surf.blit(self._cached_text, (self.rect.x, self.rect.y - 12))
        pygame.draw.rect(
            surf, DARK, (self.rect.x, self.rect.y + 3, self.rect.w, 6), 0, 3
        )
        fw = (
            int((self.val - self.mn) / (self.mx - self.mn) * self.rect.w)
            if self.mx > self.mn
            else 0
        )
        pygame.draw.rect(surf, BLUE, (self.rect.x, self.rect.y + 3, fw, 6), 0, 3)
        if self.labels and len(self.labels) > 0:
            n = len(self.labels)
            for i in range(n):
                lx = (
                    self.rect.x + int(i * self.rect.w / (n - 1))
                    if n > 1
                    else self.rect.x
                )
                ly = self.rect.y + 11
                tick_col = BLUE if i == int(self.val) else GRAY
                pygame.draw.line(surf, tick_col, (lx, ly - 1), (lx, ly + 1), 1)
                lt = font.render(self.labels[i], True, tick_col)
                surf.blit(lt, (lx - lt.get_width() // 2, ly + 3))'''

new_toggle = '''class Toggle:
    def __init__(self, x, y, w, h, labels, val=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.labels, self.val = labels, val
        self.drag = False
        self._cached_text = None
        self._cached_text_str = None

    def draw(self, surf, font):
        text_str = self.labels[self.val]
        if self._cached_text is None or self._cached_text_str != text_str:
            self._cached_text = font.render(text_str, True, WHITE)
            self._cached_text_str = text_str
        pygame.draw.rect(surf, DARK, self.rect, 0, 4)
        pygame.draw.rect(surf, BLUE, self.rect, 1, 4)
        surf.blit(
            self._cached_text,
            (
                self.rect.centerx - self._cached_text.get_width() // 2,
                self.rect.centery - self._cached_text.get_height() // 2,
            ),
        )'''

# Function to replace a class block in the content
def replace_class(content, class_name, new_class):
    # Pattern: from 'class ClassName:' to the next 'class ' or end of string
    pattern = rf'(class {class_name}:.*?)(?=\nclass |\Z)'
    return re.sub(pattern, new_class, content, flags=re.DOTALL)

# Apply replacements
content = replace_class(backup_content, 'Slider', new_slider)
content = replace_class(content, 'SliderInt', new_sliderint)
content = replace_class(content, 'Toggle', new_toggle)

# Write the new file
with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Successfully updated ui.py with caching')