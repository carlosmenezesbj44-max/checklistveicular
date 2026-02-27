with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove espaços antes de decoradores nas linhas problemáticas
for i in range(2380, min(2400, len(lines))):
    if lines[i].startswith('     @app.route') or \
       lines[i].startswith('     @login_required') or \
       lines[i].startswith('     def modelo_nota') or \
       lines[i].startswith('     def listar_condutores'):
        lines[i] = lines[i][5:]  # Remove 5 espaços

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Final fix applied')
