with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Linhas 2386-2387 precisam de indentação
for i in [2385, 2386]:
    if i < len(lines):
        if lines[i].startswith('    """') or lines[i].startswith('    return'):
            lines[i] = '    ' + lines[i]

# Linhas 2393-2395 precisam de indentação
for i in [2392, 2393, 2394]:
    if i < len(lines):
        if lines[i].startswith('    """') or lines[i].startswith('    condutores') or lines[i].startswith('    return'):
            lines[i] = '    ' + lines[i]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Indentation fixed')
