#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para diagnosticar o problema do veículo QYE8359"""

from db import get_conn

def diagnosticar():
    conn = get_conn()
    cur = conn.cursor()
    
    print("=" * 80)
    print("DIAGNÓSTICO DO PROBLEMA DO VEÍCULO QYE8359")
    print("=" * 80)
    
    # 1. Verificar se o veículo existe na tabela veiculos
    print("\n1. Veículo na tabela VEICULOS:")
    cur.execute("SELECT id, placa, modelo, condutor, tipo FROM veiculos WHERE placa = 'QYE8359'")
    veiculo = cur.fetchone()
    if veiculo:
        v_id, placa, modelo, condutor, tipo = veiculo
        print(f"   ✓ ID: {v_id}")
        print(f"   ✓ Placa: {placa}")
        print(f"   ✓ Modelo: {modelo}")
        print(f"   ✓ Condutor: {condutor}")
        print(f"   ✓ Tipo: {tipo}")
    else:
        print("   ✗ Veículo NÃO encontrado")
        return
    
    # 2. Verificar se há registros de manutenção para este veículo
    print(f"\n2. Registros de MANUTENÇÃO para veículo ID {v_id}:")
    cur.execute("SELECT COUNT(*) FROM manutencao WHERE veiculo_id = ?", (v_id,))
    total_manutencao = cur.fetchone()[0]
    print(f"   Total de manutenções: {total_manutencao}")
    
    if total_manutencao > 0:
        cur.execute("SELECT id, nome_peca, data_manutencao FROM manutencao WHERE veiculo_id = ?", (v_id,))
        for row in cur.fetchall():
            print(f"     - ID: {row[0]}, Peça: {row[1]}, Data: {row[2]}")
    else:
        print("   ⚠ NENHUMA manutenção registrada para este veículo!")
    
    # 3. Verificar se há itens de checklist
    print(f"\n3. Itens de CHECKLIST para veículo ID {v_id}:")
    cur.execute("SELECT COUNT(*) FROM itens_checklist WHERE veiculo_id = ?", (v_id,))
    total_itens = cur.fetchone()[0]
    print(f"   Total de itens: {total_itens}")
    
    if total_itens > 0:
        cur.execute("SELECT id, nome_item, status FROM itens_checklist WHERE veiculo_id = ? LIMIT 5", (v_id,))
        for row in cur.fetchall():
            print(f"     - ID: {row[0]}, Item: {row[1]}, Status: {row[2]}")
    
    # 4. Comparar com outro veículo que aparece (RZL6E39)
    print("\n4. COMPARAÇÃO com RZL6E39 (que aparece na lista):")
    cur.execute("SELECT id, placa, modelo FROM veiculos WHERE placa = 'RZL6E39'")
    outro = cur.fetchone()
    if outro:
        outro_id = outro[0]
        print(f"   Veículo RZL6E39 ID: {outro_id}")
        cur.execute("SELECT COUNT(*) FROM manutencao WHERE veiculo_id = ?", (outro_id,))
        total_outro = cur.fetchone()[0]
        print(f"   Total de manutenções: {total_outro}")
        
        if total_outro > 0:
            cur.execute("SELECT id, nome_peca, data_manutencao FROM manutencao WHERE veiculo_id = ? LIMIT 3", (outro_id,))
            for row in cur.fetchall():
                print(f"     - ID: {row[0]}, Peça: {row[1]}, Data: {row[2]}")
    
    # 5. Lista todos os veículos que NÃO têm manutenção
    print("\n5. Veículos SEM manutenção registrada:")
    cur.execute("""
        SELECT v.id, v.placa, v.modelo, v.condutor
        FROM veiculos v
        LEFT JOIN manutencao m ON v.id = m.veiculo_id
        WHERE m.id IS NULL
        ORDER BY v.placa
    """)
    veiculos_sem_manutencao = cur.fetchall()
    print(f"   Total de veículos sem manutenção: {len(veiculos_sem_manutencao)}")
    for row in veiculos_sem_manutencao[:10]:
        print(f"     - {row[1]} ({row[2]}) - Condutor: {row[3]}")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("CONCLUSÃO:")
    print("O veículo QYE8359 existe na tabela VEICULOS mas NÃO tem nenhum registro")
    print("na tabela MANUTENCAO. Por isso não aparece na lista de manutenções.")
    print("=" * 80)

if __name__ == '__main__':
    diagnosticar()
