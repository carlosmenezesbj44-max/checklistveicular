if __name__ == '__main__':
    import sqlite3
    import os
    
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'ChecklistVeicular', 'checklist.db')
    
    output = []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM users WHERE username = 'carlosme'")
        user = cur.fetchone()
        
        if user:
            output.append("Usuario encontrado!")
            for key in user.keys():
                output.append(f"  {key}: {user[key]}")
        else:
            output.append("Usuario NAO encontrado no banco de dados")
        
        output.append("\nTodos os usuarios:")
        cur.execute("SELECT id, username, email, is_admin, role FROM users")
        for row in cur.fetchall():
            output.append(f"  ID={row[0]}, Username={row[1]}, Email={row[2]}, Admin={row[3]}, Role={row[4]}")
        
        conn.close()
    except Exception as e:
        output.append(f"ERRO: {e}")
        import traceback
        output.append(traceback.format_exc())
    
    result = "\n".join(output)
    print(result)
    with open('check_user.log', 'w') as f:
        f.write(result)
