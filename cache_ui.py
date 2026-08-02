import re

def add_cache_fields(text):
    # Add _cached_text and _cached_text_str to __init__ of Slider, SliderInt, Toggle
    # We'll find the line after 'self.drag = False' in each __init__ and insert two lines.
    # We'll do it for each class separately.
    classes = ['Slider', 'SliderInt', 'Toggle']
    for cls in classes:
        # Pattern to find the __init__ method of the class and then the line with 'self.drag = False'
        # We'll use a regex that captures the class and up to the end of __init__ (or until next method) but we'll do a simpler approach:
        # Find the class, then find __init__, then find the line with 'self.drag = False' and insert after it.
        # We'll do it by iterating lines.
        lines = text.splitlines(keepends=True)
        in_class = False
        in_init = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f'class {cls}:'):
                in_class = True
                continue
            if in_class and line.strip().startswith('def __init__'):
                in_init = True
                continue
            if in_init and line.strip() == 'self.drag = False':
                indent = len(line) - len(line.lstrip())
                # Insert after this line
                lines.insert(i+1, ' ' * indent + 'self._cached_text = None\n')
                lines.insert(i+2, ' ' * indent + 'self._cached_text_str = None\n')
                break  # assuming only one such line per __init__
            # Reset if we leave the class or init
            if in_class and line.strip().startswith('def ') and '__init__' not in line:
                in_init = False
            if in_class and line.strip().startswith('class ') and not line.strip().startswith(f'class {cls}:'):
                in_class = False
        text = ''.join(lines)
    return text

def replace_draw_methods(text):
    # We'll replace the draw method for each class with a version that caches the rendered text.
    # We'll do it by regex matching the entire draw method and replacing it.
    # We'll define new draw methods for each class.

    # Slider draw
    new_slider_draw = '''    def draw(self, surf, font):
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
                surf.blit(lt, (lx - lt.get_width() // 2, ly + 3))
'''

    # SliderInt draw
    new_sliderint_draw = '''    def draw(self, surf, font):
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
                surf.blit(lt, (lx - lt.get_width() // 2, ly + 3))
'''

    # Toggle draw
    new_toggle_draw = '''    def draw(self, surf, font):
        text_str = self.labels[self.val]
        if self._cached_text is None or self._cached_text_str != text_str:
            self._cached_text = font.render(text_str, True, WHITE)
            self._cached_text_str = text_str
        pygame.draw.rect(surf, DARK, self.rect, 0, 4)
        pygame.draw.rect(surf, BLUE, self.rect, 1, 4)
        surf.blit
                rect.width
                 .centery - text_height_half 
        ),
       .blit(self._cached_text, blit_correction_centered)
     .
    '''

    # Actually, let's write the correct Toggle draw:
    new_toggle_draw = '''    def draw(self, surf, font):
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
        )
'''

    # Now replace each draw method. We'll use regex to match from 'def draw(self, surf, font):' to the next line that starts with '    def ' or 'class ' (same indent) or end of string.
    # We'll do it for each class by specifying the class name in the pattern to avoid cross-over? Actually, the draw method is inside the class, so we can just replace the first occurrence after the class.
    # We'll do a simple approach: replace the draw method for each class by searching for the pattern within the class block? But we can do a global replace because the method signatures are unique enough.

    # We'll do three separate replacements.

    # For Slider
    pattern = r'(    def draw\(self, surf, font\):.*?)(?=\n    def |\nclass |\Z)'
    def repl(match):
        return new_slider_draw
    text = re.sub(pattern, repl, text, flags=re.DOTALL)

    # For SliderInt
    pattern = r'(    def draw\(self, surf, font\):.*?)(?=\n    def |\nclass |\Z)'
    def repl(match):
        return new_sliderint_draw
    text = re.sub(pattern, repl, text, flags=re.DOTALL)

    # For Toggle
    pattern = r'(    def draw\(self, surf, font\):.*?)(?=\n    def |\nclass |\Z)'
    def repl(match):
        return new_toggle_draw
    text = re.sub(pattern, repl, text, flags=re.DOTALL)

    return text

with open('ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = add_cache_fields(content)
content = replace_draw_methods(content)

with open('ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
