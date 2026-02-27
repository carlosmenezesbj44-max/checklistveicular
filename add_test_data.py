import os
import sys
from datetime import datetime, timedelta

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from db import get_conn
from models import Manutencao

def add_test_maintenance_data():
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM veiculos LIMIT 1")
    veiculo_id_result = cur.fetchone()
    
    if not veiculo_id_result:
        print("Nenhum veículo encontrado. Adicione um veículo primeiro.")
        sys.exit(1)
    
    veiculo_id = veiculo_id_result[0]
    
    test_data = [
        {
            'nome_peca': 'Óleo de Motor',
            'data_manutencao': (datetime.now() - timedelta(days=30)).strftime('%d/%m/%Y'),
            'quilometragem_atual': 45000,
            'valor_peca': 150.00,
            'mao_de_obra': 80.00,
            'observacoes': 'Troca de óleo e filtro - Manutenção preventiva'
        },
        {
            'nome_peca': 'Pneus',
            'data_manutencao': (datetime.now() - timedelta(days=20)).strftime('%d/%m/%Y'),
            'quilometragem_atual': 46000,
            'valor_peca': 600.00,
            'mao_de_obra': 150.00,
            'observacoes': 'Troca de 4 pneus - Desgaste excessivo'
        },
        {
            'nome_peca': 'Pastilhas de Freio',
            'data_manutencao': (datetime.now() - timedelta(days=10)).strftime('%d/%m/%Y'),
            'quilometragem_atual': 47500,
            'valor_peca': 200.00,
            'mao_de_obra': 120.00,
            'observacoes': 'Troca de pastilhas dianteiras'
        },
        {
            'nome_peca': 'Bateria',
            'data_manutencao': (datetime.now() - timedelta(days=5)).strftime('%d/%m/%Y'),
            'quilometragem_atual': 48000,
            'valor_peca': 400.00,
            'mao_de_obra': 50.00,
            'observacoes': 'Troca de bateria - Falha na partida'
        },
        {
            'nome_peca': 'Fluido de Refrigeração',
            'data_manutencao': (datetime.now() - timedelta(days=2)).strftime('%d/%m/%Y'),
            'quilometragem_atual': 48500,
            'valor_peca': 100.00,
            'mao_de_obra': 60.00,
            'observacoes': 'Reposição de fluido'
        },
        {
            'nome_peca': 'Óleo de Motor',
            'data_manutencao': datetime.now().strftime('%d/%m/%Y'),
            'quilometragem_atual': 49000,
            'valor_peca': 150.00,
            'mao_de_obra': 80.00,
            'observacoes': 'Troca de óleo e filtro - Manutenção preventiva'
        }
    ]
    
    for data in test_data:
        try:
            manu = Manutencao.create(
                veiculo_id=veiculo_id,
                nome_peca=data['nome_peca'],
                data_manutencao=data['data_manutencao'],
                quilometragem_atual=data['quilometragem_atual'],
                valor_peca=data['valor_peca'],
                mao_de_obra=data['mao_de_obra'],
                observacoes=data['observacoes']
            )
            print(f"[OK] Manutencao criada: {data['nome_peca']} - R$ {data['valor_peca'] + data['mao_de_obra']:.2f}")
        except Exception as e:
            print(f"[ERRO] Erro ao criar manutencao: {e}")
    
    conn.close()
    print("\nDados de teste adicionados com sucesso!")

if __name__ == "__main__":
    add_test_maintenance_data()
