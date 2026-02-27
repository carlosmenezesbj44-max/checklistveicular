with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Corrige indentação das linhas 2393-2395
for i in range(2392, min(2396, len(lines))):
    if lines[i].startswith('    """') or (lines[i].startswith('    ') and not lines[i].startswith('        ')):
        lines[i] = '        ' + lines[i][4:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Corrigido')
