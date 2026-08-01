s=open('E\\DOWNLOADS\\CREATIVE\\PYTHON\\GitHub\\LIFE_GPT\\cell.py',encoding='utf-8').read()
s=s.replace('DIVIDE_THRESHOLD, DIVIDE_THRESHOLD', 'DIVIDE_THRESHOLD')
open('E\\DOWNLOADS\\CREATIVE\\PYTHON\\GitHub\\LIFE_GPT\\cell.py','w',encoding='utf-8').write(s)
print('import fixed')