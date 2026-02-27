with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontra as linhas com espaços antes de @app.route
for i in range(2380, min(2400, len(lines))):
    if lines[i].startswith('     @app.route'):
        lines[i] = lines[i][5:]  # Remove 5 espaços
    elif lines[i].startswith('     @login_required'):
        lines[i] = lines[i][5:]
    elif lines[i].startswith('     def '):
        lines[i] = lines[i][5:]

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Decorators corrigidos')
