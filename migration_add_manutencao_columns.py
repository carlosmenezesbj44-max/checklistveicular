"""
Script para adicionar as colunas faltantes à tabela manutencao
"""

from db import get_conn

def migrate():
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Verificar se as colunas já existem
        cur.execute("PRAGMA table_info(manutencao)")
        columns = [row[1] for row in cur.fetchall()]
        
        # Adicionar as colunas se não existirem
        if 'sugestao_checklist' not in columns:
            cur.execute("ALTER TABLE manutencao ADD COLUMN sugestao_checklist BOOLEAN DEFAULT 0")
            print("✓ Coluna 'sugestao_checklist' adicionada")
        
        if 'checklist_id' not in columns:
            cur.execute("ALTER TABLE manutencao ADD COLUMN checklist_id INTEGER")
            print("✓ Coluna 'checklist_id' adicionada")
        
        if 'itens_problema' not in columns:
            cur.execute("ALTER TABLE manutencao ADD COLUMN itens_problema TEXT")
            print("✓ Coluna 'itens_problema' adicionada")
        
        if 'data_sugestao' not in columns:
            cur.execute("ALTER TABLE manutencao ADD COLUMN data_sugestao TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✓ Coluna 'data_sugestao' adicionada")
        
        conn.commit()
        print("\n✓ Migração concluída com sucesso!")
    except Exception as e:
        print(f"✗ Erro durante migração: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
