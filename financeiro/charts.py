"""
Geração de dados para gráficos (Chart.js)
"""
from financeiro.services import CalculosFinanceiros


class ChartData:
    """Classe para preparar dados de gráficos"""
    
    @staticmethod
    def pizza_custos_por_categoria(veiculo_id):
        """Dados para gráfico pizza de custos"""
        resumo = CalculosFinanceiros.resumo_custos_veiculo(veiculo_id)
        
        labels = []
        data = []
        cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
        
        categorias = [
            ('Combustível', resumo['combustivel']['total']),
            ('Manutenção', resumo['manutencao']['total']),
            ('Multas', resumo['multas']['total']),
            ('Documentos', resumo['documentos']['total'])
        ]
        
        for i, (cat, valor) in enumerate(categorias):
            if valor > 0:
                labels.append(cat)
                data.append(valor)
        
        return {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': cores[:len(data)],
                'borderColor': '#fff',
                'borderWidth': 2
            }]
        }
    
    @staticmethod
    def linha_gastos_mensais(veiculo_id, ultimos_meses=12):
        """Dados para gráfico linha de gastos mensais"""
        gastos = CalculosFinanceiros.gastos_por_mes(veiculo_id, ultimos_meses)
        
        labels = [g['mes'] for g in gastos]
        combustivel_data = [g['combustivel'] for g in gastos]
        manutencao_data = [g['manutencao'] for g in gastos]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Combustível',
                    'data': combustivel_data,
                    'borderColor': '#FF6384',
                    'backgroundColor': 'rgba(255, 99, 132, 0.1)',
                    'tension': 0.4,
                    'fill': True
                },
                {
                    'label': 'Manutenção',
                    'data': manutencao_data,
                    'borderColor': '#36A2EB',
                    'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                    'tension': 0.4,
                    'fill': True
                }
            ]
        }
    
    @staticmethod
    def barra_comparativo_veiculos():
        """Dados para gráfico barras comparativo"""
        veiculos = CalculosFinanceiros.comparativo_veiculos()
        
        labels = [v['placa'] for v in veiculos]
        combustivel_data = [v['gasto_combustivel'] for v in veiculos]
        manutencao_data = [v['gasto_manutencao'] for v in veiculos]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Combustível',
                    'data': combustivel_data,
                    'backgroundColor': '#FF6384'
                },
                {
                    'label': 'Manutenção',
                    'data': manutencao_data,
                    'backgroundColor': '#36A2EB'
                }
            ]
        }
    
    @staticmethod
    def gauge_consumo(veiculo_id):
        """Dados para indicador de consumo"""
        desvio = CalculosFinanceiros.detectar_desvios(veiculo_id)
        
        if not desvio:
            return None
        
        return {
            'consumo_atual': desvio['consumo_atual'],
            'consumo_esperado': desvio['consumo_esperado'],
            'desvio_percentual': desvio['desvio_percentual'],
            'status': desvio['status'],
            'cor': '#FF6384' if desvio['status'] == 'alerta' else '#36A2EB'
        }
    
    @staticmethod
    def pizza_gastos_por_categoria(veiculo_id):
        """Dados para gráfico pizza de gastos por categoria"""
        categorias = CalculosFinanceiros.gastos_por_categoria(veiculo_id)
        
        labels = [c['categoria'] for c in categorias if c['total'] > 0]
        data = [c['total'] for c in categorias if c['total'] > 0]
        
        cores = [
            '#FF6384',  # Combustível
            '#36A2EB',  # Manutenção
            '#FFCE56',  # Multa
            '#4BC0C0',  # IPVA
            '#9966FF',  # Seguro
            '#FF9F40',  # Licenciamento
            '#C9CBCF',  # Estacionamento
            '#FF6B6B'   # Outros
        ]
        
        return {
            'labels': labels,
            'datasets': [{
                'data': data,
                'backgroundColor': cores[:len(data)],
                'borderColor': '#fff',
                'borderWidth': 2
            }]
        }
    
    @staticmethod
    def linha_consumo_combustivel(veiculo_id, ultimos_registros=20):
        """Dados para gráfico de evolução do consumo"""
        from db import get_conn
        
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                data_abastecimento,
                CAST(quantidade_litros AS REAL) as litros,
                CAST(quilometragem AS INTEGER) as km
            FROM combustivel
            WHERE veiculo_id=?
            ORDER BY data_abastecimento DESC
            LIMIT ?
        """, (veiculo_id, ultimos_registros))
        
        registros = list(reversed(cur.fetchall()))
        conn.close()
        
        if len(registros) < 2:
            return None
        
        labels = [r['data_abastecimento'] for r in registros]
        consumos = []
        
        for i in range(1, len(registros)):
            km_rodado = registros[i]['km'] - registros[i-1]['km']
            litros = registros[i]['litros']
            if litros > 0 and km_rodado > 0:
                consumo = km_rodado / litros
                consumos.append(consumo)
            else:
                consumos.append(0)
        
        # Adicionar None no primeiro elemento
        consumos = [None] + consumos
        
        return {
            'labels': labels,
            'datasets': [{
                'label': 'Consumo (km/l)',
                'data': consumos,
                'borderColor': '#FF6384',
                'backgroundColor': 'rgba(255, 99, 132, 0.1)',
                'tension': 0.4,
                'fill': True,
                'pointRadius': 5,
                'pointHoverRadius': 7
            }]
        }
