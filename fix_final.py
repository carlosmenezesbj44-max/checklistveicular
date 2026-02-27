with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Corrige linhas específicas
lines[5091] = '@app.route("/combustivel/modelo-nota")\n'
lines[5092] = '@login_required\n'
lines[5093] = 'def modelo_nota_combustivel():\n'
lines[5094] = '    """Modelo de nota fiscal padrão para abastecimento"""\n'
lines[5095] = '    return render_template("combustivel/modelo_nota.html")\n'
lines[5098] = 'if __name__ == "__main__":\n'

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('Final fix applied')
