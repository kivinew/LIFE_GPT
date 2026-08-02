import sys

def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # We'll process line by line, keeping track of when we are inside a specific class and method.
    # We'll have flags: in_class (which class), in_init, in_draw.
    # When we are in the __init__ of a target class and we see the line with 'self.drag = False',
    # we insert the cache lines after it.
    # When we are in the draw method of a target class, we replace the entire method body with our cached version.

    # Target classes
    target_classes = {'Slider', 'SliderInt', 'Toggle'}
    # We'll store the new lines
    new_lines = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        # Detect class start
        if stripped.startswith('class ') and ':' in line:
            # Extract class name
            class_name = line.split()[1].split(':')[0]
            if class_name in target_classes:
                # We are in a target class
                # We'll process until the end of the class (next class or end of file)
                # For simplicity, we'll collect the entire class block and then process it.
                # But let's do a simpler approach: we'll just look for __init__ and draw within the class.
                # We'll keep the lines as is and modify when we see the specific patterns.
                pass
        # For now, we'll just do simple string replacement for the specific patterns we know.
        i += 1

    # Instead of complex state machine, let's do specific replacements for each class using the known structure.
    # We'll join the lines and use regex for each class's __init__ and draw.
    text = ''.join(lines)

    # Helper to replace after a pattern in a class
    def replace_after(text, class_name, after_pattern, insert_lines):
        # Find the class block
        pattern = rf'(class {class_name}:.*?)(?=\nclass |\Z)'
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            return text
        block = match.group(1)
        start, end = match.span()
        # In the block, find the after_pattern and insert after it
        # We'll insert after the line that contains after_pattern (assuming it's on its own line)
        lines_block = block.splitlines(keepends=True)
        new_block_lines = []
        for bl in lines_block:
            new_block_lines.append(bl)
            if bl.strip() == after_pattern.strip():
                # Insert the indent of bl
                indent = len(bl) - len(bl.lstrip())
                for il in insert_lines:
                    new_block_lines.append(' ' * indent + il + '\n')
        new_block = ''.join(new_block_lines)
        return text[:start] + new_block + text[end:]

    # For each class, add cache attributes after 'self.drag = False' in __init__
    for cls in target_classes:
        text = replace_after(text, cls, 'self.drag = False', [
            'self._cached_text = None',
            'self._cached_text_str = None'
        ])

    # Now replace the draw method for each class with the cached version
    # We'll replace the entire draw method body from 'def draw(self, surf, font):' to the end of the method.
    # We'll assume the method ends when we see a line that starts with the same indentation as 'def ' but not part of the method.
    # We'll do a regex that matches from 'def draw(self, surf, font):' up to the next line that starts with '    def ' or 'class ' or end of string, but we need to keep the indentation.
    # Let's do per class.

    # Define the new draw method for each class (including the def line)
    new_draws = {
        'Slider': '''    def draw(self, surf, font):
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
                surf.blit(lt, (lx - lt.get_width() // 2, ly + 3))''',
        'SliderInt': '''    def draw(self, surf, font):
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
                surf.blit(lt, (lx - lt.get_width() // 2, ly + 3))''',
        'Toggle': '''    def draw(self, surf, font):
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
    }

    for cls, new_draw in new_draws.items():
        # Replace the draw method for class cls
        # We'll find the pattern: '    def draw(self, surf, font):' followed by the method body until the next method or class.
        # We'll use regex with DOTALL to capture until we see a line that starts with four spaces and 'def ' (another method) or the class ends.
        # But note: the class might have no other methods after draw (like Toggle only has draw and __init__). We'll stop at next class or end of string.
        pattern = rf'(class {cls}:.*?\n    def draw\(self, surf, font\):.*?)(?=\n    def |\nclass |\Z)'
        # We need to replace the entire match with the class prefix up to the def line, then the new draw.
        # Let's do: capture the class prefix up to the def line, then replace the rest.
        # We'll do two-step: first find the class block, then within that replace the draw method.
        def replace_draw_in_class(text):
            pattern = rf'(class {cls}:.*?\n    def draw\(self, surf, font\):.*?)(?=\n    def |\nclass |\Z)'
            match = re.search(pattern, text, re.DOTALL)
            if not match:
                return text
            # We want to keep everything up to and including the def line, then replace the rest of the method.
            # Actually, we can replace the entire match with: the class prefix up to the def line + new_draw + the rest after the method.
            # But we don't have the rest after the method easily. Instead, we can split the match into: head (up to the end of the def line) and tail (the method body).
            # Let's do: match the whole class block, then within it replace the draw method.
            # We'll do a separate function for clarity.
            return text  # placeholder, we'll do below

        # Instead, let's do a simpler approach: we already have the class blocks modified for the __init__.
        # Let's just replace the draw method by searching for the def line and then replacing until the next method or class.
        # We'll do it by iterating lines again but only for the specific class.
        # Given time, let's do a simpler but risky approach: replace the draw method using a regex that matches from the def line to the next line that starts with the same indentation as the def line but is not part of the method (i.e., a new method or class).
        # We'll assume the method body is indented by 4 spaces more than the def line.
        # We'll do: find the def line, then capture until we see a line that starts with the same indentation as the def line and is not empty? Actually, the method ends when we see a line that has less indentation than the method body.
        # We'll implement a simple state machine for each class.

        # Given the complexity and time, let's just do a string replace for the entire class block with a version that includes our modifications.
        # We have the original class block from the backup. We can generate the new class block by taking the original block and:
        #   - insert the cache attributes after 'self.drag = False' in __init__
        #   - replace the draw method body with our new_draw (but keep the def line)
        # We'll do this for each class using the original backup lines.

    # Let's instead start from the backup and build the new file by processing each class block individually.
    # We'll read the backup again and process.

with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py.backup', 'r', encoding='utf-8') as f:
    backup_lines = f.readlines()

# We'll process the backup lines and produce new lines.
new_lines = []
i = 0
n = len(backup_lines)
while i < n:
    line = backup_lines[i]
    stripped = line.strip()
    # Check if this line starts a class we care about
    if stripped.startswith('class ') and ':' in line:
        class_name = line.split()[1].split(':')[0]
        if class_name in target_classes:
            # We are at the start of a target class.
            # We'll copy the class line.
            new_lines.append(line)
            i += 1
            # Now process the rest of the class until we hit another class or end of file.
            # We'll look for __init__ and draw.
            in_init = False
            in_draw = False
            while i < n:
                lin = backup_lines[i]
                stripped_lin = lin.strip()
                # If we see another class, break
                if stripped_lin.startswith('class ') and ':' in lin:
                    break
                # If we see a def, we need to know which method
                if stripped_lin.startswith('def '):
                    if '__init__' in lin:
                        in_init = True
                        in_draw = False
                    elif 'draw' in lin:
                        in_init = False
                        in_draw = True
                    else:
                        in_init = False
                        in_draw = False
                # If we are in __init__ and we see the line with 'self.drag = False', we will add the cache lines after it.
                if in_init and lin.strip() == 'self.drag = False':
                    new_lines.append(lin)
                    i += 1
                    # Add the cache lines with the same indentation
                    indent = len(lin) - len(lin.lstrip())
                    new_lines.append(' ' * indent + 'self._cached_text = None\n')
                    new_lines.append(' ' * indent + 'self._cached_text_str = None\n')
                    continue
                # If we are in draw, we want to skip the entire method body and replace it with our new version.
                if in_draw and stripped_lin.startswith('def draw'):
                    # We have the def line, we want to keep it and then replace the body.
                    new_lines.append(lin)  # the def line
                    i += 1
                    # Now skip the existing method body until we reach a line that is not indented more than the def line (or empty line with same indent?).
                    # The def line indentation is the class indent (usually 0) plus 4 spaces? Actually, inside class, def is indented by 4 spaces.
                    # We'll skip lines that have more indentation than the def line.
                    def_indent = len(lin) - len(lin.lstrip())
                    while i < n:
                        lin2 = backup_lines[i]
                        stripped_lin2 = lin2.strip()
                        # If we encounter a line that is not indented more than def_indent, we break (unless it's empty? but we treat empty as break)
                        if len(lin2) - len(lin2.lstrip()) <= def_indent and stripped_lin2 != '':
                            break
                        i += 1
                    # Now we are at the line that starts the next method or class or end of class.
                    # We need to insert our new draw method body.
                    # The indentation for the method body should be def_indent + 4.
                    body_indent = ' ' * (def_indent + 4)
                    # Now add the lines of the new draw method body (without the def line)
                    if class_name == 'Slider':
                        body = '''if self.unit:
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
                        body = '''current_label = self.labels[int(self.val)] if self.labels else str(self.val)
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
                        body = '''text_str = self.labels[self.val]
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
                        body = ''
                    # Split body into lines and add indentation
                    for bline in body.splitlines():
                        if bline.strip() == '':
                            new_lines.append('\n')
                        else:
                            new_lines.append(body_indent + bline + '\n')
                    # Now we do not increment i because we already consumed the lines until the next method/class.
                    # We'll continue the loop without incrementing i again.
                    continue
                # If not in draw or not the special case, just copy the line.
                new_lines.append(lin)
                i += 1
            # After processing the class, we continue (the outer loop will increment i again? Actually we already incremented i inside.
            # We'll continue without incrementing i again.
            continue
        else:
            # Not a target class start, just copy the line.
            new_lines.append(line)
            i += 1

# Write the new file
with open('/mnt/e/DOWNLOADS/CREATIVE/PYTHON/GitHub/LIFE_GPT/ui.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('File updated with caching')