if __name__ == '__main__':
    import sqlite3
    import os
    import sys
    from werkzeug.security import generate_password_hash
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ChecklistVeicular', 'checklist.db')
    
    username = 'carlosme'
    password = '201127121981'
    email = None
    is_admin = 1
    role = 'admin'
    
    password_hash = generate_password_hash(password)
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing = cur.fetchone()
        
        if existing:
            result = f"Usuario {username} ja existe!"
        else:
            cur.execute("""
                INSERT INTO users (username, password_hash, email, is_admin, role, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, password_hash, email, is_admin, role, None))
            conn.commit()
            result = f"SUCESSO! Super usuario criado:\nLogin: {username}\nSenha: {password}\nNivel: Admin"
        
        conn.close()
        print(result)
        with open('admin_created.log', 'w') as f:
            f.write(result)
    except Exception as e:
        error_msg = f"ERRO: {e}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        with open('admin_created.log', 'w') as f:
            f.write(error_msg + "\n" + traceback.format_exc())
