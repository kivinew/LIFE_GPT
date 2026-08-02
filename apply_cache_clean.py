import re

def modify_class(content, class_name):
    # Find the class definition
    pattern = rf'class {class_name}:.*?(?=\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content
    class_block = match.group(0)
    start, end = match.span()
    
    # Modify __init__: add caching fields after self.drag = False
    # We'll look for the line containing 'self.drag = False' and insert after it.
    lines = class_block.splitlines(keepends=True)
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        if line.strip() == 'self.drag = False':
            indent = len(line) - len(line.lstrip())
            new_lines.append(' ' * indent + 'self._cached_text = None\n')
            new_lines.append(' ' * indent + 'self._cached_text_str = None\n')
        i += 1
    modified_block = ''.join(new_lines)
    
    # Now modify the draw method within this class block
    # We'll replace the draw method entirely with a cached version.
    # We need to know the original draw method to keep the same logic but with caching.
    # Instead of trying to be smart, we'll replace the draw method with a template
    # specific to each class.
    
    # We'll locate the draw method in the modified_block (after __init__ modifications)
    # We'll use a regex to find 'def draw(self, surf, font):' and everything until the next method or end of class.
    draw_pattern = r'(def draw\(self, surf, font\):.*?)(?=\n    def |\nclass |\Z)'
    draw_match = re.search(draw_pattern, modified_block, re.DOTALL)
    if draw_match:
        draw_method = draw_match.group(1)
        # We'll replace it with a new draw method that uses caching.
        # We need to generate the new draw method based on class_name.
        if class_name == 'Slider':
            new_draw = '''    def draw(self, surf, font):
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
            new_draw = '''    def draw(self, surf, font):
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
            new_draw = '''    def draw(self, surf, font):
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
            # Should not happen
            new_draw = draw_method
        # Replace the draw method
        modified_block = re.sub(draw_pattern, new_draw, modified_block, flags=re.DOTALL)
    else:
        # If no draw method found, leave as is (should not happen)
        pass
    
    # Replace the class block in the original content
    new_content = content[:start] + modified_block + content[end:]
    return new_content

with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py.backup', 'r', encoding='utf-8') as f:
    content = f.read()

for cls in ['Slider', 'SliderInt', 'Toggle']:
    content = modify_class(content, cls)

with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')