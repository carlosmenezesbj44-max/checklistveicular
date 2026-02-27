with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove espaços da indentação das rotas
content = content.replace('     @app.route("/combustivel/modelo-nota")', '@app.route("/combustivel/modelo-nota")')
content = content.replace('     @login_required\n     def modelo_nota_combustivel():', '@login_required\ndef modelo_nota_combustivel():')
content = content.replace('     @app.route("/condutores", methods=["GET"])', '@app.route("/condutores", methods=["GET"])')
content = content.replace('     @login_required\n     def listar_condutores_rota():', '@login_required\ndef listar_condutores_rota():')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Rotas corrigidas')
