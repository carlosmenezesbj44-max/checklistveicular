with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontra e remove as linhas com a indentação errada
new_lines = []
skip = False
i = 0
while i < len(lines):
    if '     @app.route("/combustivel/modelo-nota")' in lines[i]:
        skip = True
        i += 1
        # Pula até @app.route("/condutores"
        while i < len(lines) and '@app.route("/condutores"' not in lines[i]:
            i += 1
        continue
    new_lines.append(lines[i])
    i += 1

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Removido')
