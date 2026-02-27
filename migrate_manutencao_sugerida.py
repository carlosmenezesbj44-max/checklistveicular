#!/usr/bin/env python3
"""
Script para adicionar colunas de manutencao sugerida
"""

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / 'data' / 'ChecklistVeicular' / 'checklist.db'

if not db_path.exists():
    print(f"Erro: Banco de dados nao encontrado em {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

try:
    # Adicionar colunas na tabela manutencao
    cur.execute("ALTER TABLE manutencao ADD COLUMN sugestao_checklist BOOLEAN DEFAULT 0")
    print("[OK] Coluna 'sugestao_checklist' adicionada")
except sqlite3.OperationalError:
    print("[SKIP] Coluna 'sugestao_checklist' ja existe")

try:
    cur.execute("ALTER TABLE manutencao ADD COLUMN checklist_id INTEGER")
    print("[OK] Coluna 'checklist_id' adicionada")
except sqlite3.OperationalError:
    print("[SKIP] Coluna 'checklist_id' ja existe")

try:
    cur.execute("ALTER TABLE manutencao ADD COLUMN itens_problema TEXT")
    print("[OK] Coluna 'itens_problema' adicionada")
except sqlite3.OperationalError:
    print("[SKIP] Coluna 'itens_problema' ja existe")

try:
    cur.execute("ALTER TABLE manutencao ADD COLUMN data_sugestao TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    print("[OK] Coluna 'data_sugestao' adicionada")
except sqlite3.OperationalError:
    print("[SKIP] Coluna 'data_sugestao' ja existe")

conn.commit()
conn.close()

print("\n[OK] Migracao concluida com sucesso!")
