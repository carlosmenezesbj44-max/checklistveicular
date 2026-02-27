with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Encontra o if __name__ e adiciona a rota antes
marker = 'if __name__ == "__main__":'
new_route = '''@app.route("/combustivel/modelo-nota")
@login_required
def modelo_nota_combustivel():
    """Modelo de nota fiscal padrão para abastecimento"""
    return render_template("combustivel/modelo_nota.html")


'''

if marker in content:
    content = content.replace(marker, new_route + marker)
    
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Route added')
