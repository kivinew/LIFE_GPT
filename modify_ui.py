import re

with open('ui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add caching fields to Slider __init__
# Find the line after self.drag = False in Slider.__init__
# We'll use regex to insert after that line within the __init__ method.
def insert_after_init(cls_name, field_lines):
    pattern = rf'(class {cls_name}:[\s\S]*?def __init__\(self[^)]*\):[\s\S]*?self\.drag = False)'
    # We need to capture the indentation of that line to match.
    # Instead, we'll do a simpler approach: replace the whole __init__ block with added lines.
    # But to avoid breaking, we'll just add after the first occurrence of 'self.drag = False' in the class.
    # Since the file is small, we can do:
    lines = content.splitlines(keepends=True)
    in_class = False
    in_init = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'class {cls_name}:'):
            in_class = True
            continue
        if in_class and line.strip().startswith('def __init__'):
            in_init = True
            continue
        if in_init and line.strip() == 'self.drag = False':
            indent = len(line) - len(line.lstrip())
            # Insert after this line
            for field in reversed(field_lines):
                lines.insert(i+1, ' ' * indent + field + '\n')
            break
        # Reset if we leave the class or init
        if in_class and line.strip().startswith('def ') and '__init__' not in line:
            in_init = False
        if in_class and line.strip().startswith('class ') and not line.strip().startswith(f'class {cls_name}:'):
            in_class = False
    return ''.join(lines)

# Add to Slider
content = insert_after_init('Slider', ['self._cached_text = None', 'self._cached_text_str = None'])
# Add to SliderInt
content = insert_after_init('SliderInt', ['self._cached_text = None', 'self._cached_text_str = None'])
# Add to Toggle
content = insert_after_init('Toggle', ['self._cached_text = None', 'self._cached_text_str = None'])

# 2. Replace draw methods with cached version
# We'll do each class separately using regex substitution with a helper.

def replace_draw(cls_name, new_draw_body):
    # We'll replace the entire draw method from 'def draw(self, surf, font):' to the line before next method or class.
    # Use regex with DOTALL to capture until next 'def ' or 'class ' at same indent level.
    # Since we know the exact indentation (4 spaces), we can do:
    pattern = rf'(    def draw\(self, surf, font\):[\s\S]*?)(?=\n    def |\nclass |\Z)'
    # We need to use a function to replace with new_draw_body keeping the same indentation.
    def repl(match):
        return '    def draw(self, surf, font):\n' + new_draw_body
    return re.sub(pattern, repl, content, flags=re.MULTILINE)

# Slider draw new body (with caching)
slider_body = '''        if self.unit:
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
content = replace_draw('Slider', slider_body)

# SliderInt draw new body
sliderint_body = '''        current_label = self.labels[int(self.val)] if self.labels else str(self.val)
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
content = replace_draw('SliderInt', sliderint_body)

# Toggle draw new body
toggle_body = '''        text_str = self.labels[self.val]
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
content = replace_draw('Toggle', toggle_body)

with open('ui.py', 'w', encoding='utf-8') as f:
    f.write(content)
