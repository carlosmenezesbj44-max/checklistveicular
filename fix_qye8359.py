#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para corrigir o problema do veículo QYE8359 adicionando um registro de manutenção"""

from db import get_conn
from datetime import datetime

def fix_qye8359():
    conn = get_conn()
    cur = conn.cursor()
    
    print("=" * 80)
    print("CORRIGINDO VEÍCULO QYE8359")
    print("=" * 80)
    
    # 1. Encontrar o veículo
    print("\n1. Procurando veículo QYE8359...")
    cur.execute("SELECT id, placa, quilometragem FROM veiculos WHERE placa = 'QYE8359'")
    veiculo = cur.fetchone()
    
    if not veiculo:
        print("   ✗ Veículo QYE8359 não encontrado!")
        conn.close()
        return False
    
    veiculo_id, placa, quilometragem = veiculo
    print(f"   ✓ Encontrado: ID {veiculo_id}, Placa {placa}, Quilometragem {quilometragem}")
    
    # 2. Verificar se já tem manutenção
    print(f"\n2. Verificando manutenções existentes...")
    cur.execute("SELECT COUNT(*) FROM manutencao WHERE veiculo_id = ?", (veiculo_id,))
    total = cur.fetchone()[0]
    
    if total > 0:
        print(f"   ⚠ Já existem {total} manutenção(s) para este veículo")
        cur.execute("SELECT id, nome_peca, data_manutencao FROM manutencao WHERE veiculo_id = ?", (veiculo_id,))
        for row in cur.fetchall():
            print(f"     - {row[1]} em {row[2]}")
        conn.close()
        return True
    
    # 3. Inserir registro de manutenção
    print(f"\n3. Inserindo registro de manutenção inicial...")
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    try:
        cur.execute("""
            INSERT INTO manutencao 
            (veiculo_id, nome_peca, data_manutencao, quilometragem_atual, status, observacoes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (veiculo_id, "Checklist Inicial", data_atual, quilometragem or 0, 'concluida', 'Checklist de inspeção veicular'))
        
        conn.commit()
        print("   ✓ Registro de manutenção inserido com sucesso!")
        
        # Verificar
        cur.execute("SELECT COUNT(*) FROM manutencao WHERE veiculo_id = ?", (veiculo_id,))
        novo_total = cur.fetchone()[0]
        print(f"   ✓ Total de manutenções agora: {novo_total}")
        
    except Exception as e:
        print(f"   ✗ Erro ao inserir: {e}")
        conn.close()
        return False
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✓ SUCESSO! O veículo QYE8359 agora aparecerá na lista de manutenções")
    print("=" * 80)
    return True

if __name__ == '__main__':
    fix_qye8359()
