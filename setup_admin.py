#!/usr/bin/env python
if __name__ == '__main__':
    import os
    import sys
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    output = []
    try:
        from db import init_db
        from models import User
        
        output.append("Inicializando banco de dados...")
        init_db()
        output.append("OK - Banco de dados inicializado")
        
        username = "carlosme"
        password = "201127121981"
        
        output.append(f"\nVerificando se usuario '{username}' ja existe...")
        existing = User.find_by_username(username)
        
        if existing:
            output.append(f"Usuario '{username}' ja existe no banco de dados")
        else:
            output.append(f"Criando super usuario '{username}'...")
            user = User.create(username, password, email=None, is_admin=True, role='admin')
            output.append(f"OK - Super usuario criado com sucesso!")
        
        output.append(f"\n=== Credenciais ===")
        output.append(f"Login: {username}")
        output.append(f"Senha: {password}")
        output.append(f"Nivel: Admin")
        
        output.append(f"\nVerificando criacao...")
        user = User.find_by_username(username)
        if user:
            output.append(f"Usuario verificado:")
            output.append(f"  ID: {user.id}")
            output.append(f"  Username: {user.username}")
            output.append(f"  is_admin: {user.is_admin}")
            output.append(f"  role: {user.role}")
            output.append(f"  email: {user.email}")
        else:
            output.append("ERRO: Usuario nao encontrado apos criacao!")
    except Exception as e:
        output.append(f"ERRO: {str(e)}")
        import traceback
        output.append(traceback.format_exc())
    
    result = "\n".join(output)
    print(result)
    with open('setup_output.txt', 'w', encoding='utf-8') as f:
        f.write(result)
