import sys
content = open('cell.py', encoding='utf-8').read()
content = content.replace('return self.energy >= max_e * LEVEL_UP_THRESHOLD\n', 'return self.energy >= max_e * DIVIDE_THRESHOLD\n')
open('cell.py', 'w', encoding='utf-8').write(content)
print('Fixed can_divide threshold')