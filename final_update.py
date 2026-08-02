import re

def get_class_block(content, class_name):
    # Find the start of the class
    pattern = r'class ' + class_name + r'\b.*?(?=\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(0), match.start(), match.end()
    return None, None, None

def modify_class_block(block, class_name):
    # Modify __init__: add cache attributes after self.drag = False
    # We'll split the block into lines
    lines = block.splitlines(keepends=True)
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        # Look for the line that contains 'self.drag = False' (with possible indentation)
        if line.strip() == 'self.drag = False':
            indent = len(line) - len(line.lstrip())
            # Insert after this line
            new_lines.append(' ' * indent + 'self._cached_text = None\n')
            new_lines.append(' ' * indent + 'self._cached_text_str = None\n')
        i += 1
    modified_block = ''.join(new_lines)
    
    # Now replace the draw method
    # We'll find the draw method and replace it entirely
    # We know the draw method starts with 'def draw(self, surf, font):'
    # We'll replace from that line until the next method (starting with 'def ') or end of class
    # We'll do it by reconstructing the block with a new draw method
    # Instead of doing line-by-line again, we can use regex on the modified_block
    # But let's do a simple approach: we know the exact original draw method from the backup? 
    # Instead, we'll replace the draw method with a template specific to the class.
    
    # We'll convert the block back to a string and use regex to replace the draw method
    mod_str = ''.join(new_lines)
    # Pattern for the draw method: from 'def draw(self, surf, font):' to the next line that starts with '    def ' or 'class ' or end of string
    # We'll use a non-greedy match until we see a line that starts with four spaces and 'def ' (another method) or the class ends.
    # However, note that the class might end after the draw method.
    # We'll use: r'(def draw\(self, surf, font\):.*?)(?=\n    def |\nclass |\Z)'
    # But note: the indentation of the draw method is exactly 4 spaces (one tab? but we use spaces). We'll assume 4 spaces.
    draw_pattern = r'(def draw\(self, surf, font\):.*?)(?=\n    def |\nclass |\Z)'
    # We need to replace the entire match with our new draw method
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
        new_draw = ''  # should not happen
    
    # Replace the draw method
    modified_block = re.sub(draw_pattern, new_draw, mod_str, flags=re.DOTALL)
    return modified_block

with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py.backup', 'r', encoding='utf-8') as f:
    content = f.read()

for class_name in ['Slider', 'SliderInt', 'Toggle']:
    block, start, end = get_class_block(content, class_name)
    if block is None:
        print(f"Class {class_name} not found!")
        continue
    new_block = modify_class_block(block, class_name)
    # Replace the old block with the new one
    content = content[:start] + new_block + content[end:]

with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated ui.py with caching")