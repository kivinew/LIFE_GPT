import re

def process_class(content, class_name):
    # Find the class block
    pattern = rf'class {class_name}:.*?(?=\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content
    class_block = match.group(0)
    start, end = match.span()
    
    # Split into lines
    lines = class_block.splitlines(keepends=True)
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        # Look for the line with 'self.drag = False' in __init__
        if line.strip() == 'self.drag = False':
            # Check if we are inside __init__ (simple heuristic: we haven't seen a def yet after class start)
            # We'll just add after this line; if it's not in __init__, it might be wrong but unlikely.
            indent = len(line) - len(line.lstrip())
            new_lines.append(' ' * indent + 'self._cached_text = None\n')
            new_lines.append(' ' * indent + 'self._cached_text_str = None\n')
        i += 1
    # Now we have the class block with added caching fields in __init__
    # Next, replace the draw method with the cached version
    class_block_new = ''.join(new_lines)
    # Now replace the draw method
    # We'll find the draw method and replace it
    draw_pattern = r'(def draw\(self, surf, font\):.*?)(?=\n    def |\nclass |\Z)'
    # We need to apply this on the class_block_new
    def replace_draw(match):
        # Draw method content
        # We'll return the new draw method based on class_name
        if class_name == 'Slider':
            return '''    def draw(self, surf, font):
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
        elif class_name == 'SliderInt':
            return '''    def draw(self, surf, font):
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
        elif class_name == 'Toggle':
            return '''    def draw(self, surf, font):
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
        else:
            return match.group(0)  # fallback
    # Apply the replacement
    class_block_new = re.sub(draw_pattern, replace_draw, class_block_new, flags=re.DOTALL)
    # Replace the original class block with the new one
    return content[:start] + class_block_new + content[end:]

with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py.backup', 'r', encoding='utf-8') as f:
    content = f.read()

for cls in ['Slider', 'SliderInt', 'Toggle']:
    content = process_class(content, cls)

with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Processed classes')