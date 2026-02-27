#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para testar condutores no banco de dados"""

from db import get_conn

def test_condutores():
    conn = get_conn()
    cur = conn.cursor()
    
    # Contar total
    cur.execute('SELECT COUNT(*) as total FROM condutores')
    result = cur.fetchone()
    total = result['total'] if result else 0
    print(f'Total de condutores: {total}')
    
    # Listar alguns
    cur.execute('SELECT id, nome_completo, cpf FROM condutores ORDER BY nome_completo ASC LIMIT 10')
    rows = cur.fetchall()
    
    if rows:
        print('\nCondutores cadastrados:')
        for row in rows:
            nome = row['nome_completo'] if 'nome_completo' in row.keys() else row[1]
            cpf = row.get('cpf', 'sem CPF') if isinstance(row, dict) else (row[2] if len(row) > 2 else 'sem CPF')
            print(f'  - ID: {row[0]}, Nome: {nome}, CPF: {cpf}')
    else:
        print('\nNenhum condutor cadastrado!')
    
    conn.close()

if __name__ == '__main__':
    test_condutores()
