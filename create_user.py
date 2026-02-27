#!/usr/bin/env python
if __name__ == '__main__':
    import os
    import sys
    import traceback

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.stdout.flush()

    try:
        from models import User
        from db import init_db
        
        init_db()
        
        username = "carlosme"
        password = "201127121981"

        existing_user = User.find_by_username(username)
        if existing_user:
            msg = f"Usuario '{username}' ja existe."
        else:
            user = User.create(username, password, email=None, is_admin=True, role='admin')
            msg = f"SUCESSO: Super usuario criado!\nLogin: {username}\nSenha: {password}\nNivel: Admin"
        
        print(msg)
        sys.stdout.flush()
            
    except Exception as e:
        msg = f"ERRO: {str(e)}\n{traceback.format_exc()}"
        print(msg, file=sys.stderr)
        sys.stderr.flush()
