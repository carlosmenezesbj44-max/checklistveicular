"""
Serviços de cálculo e análise financeira
"""
from datetime import datetime, timedelta, date
from decimal import Decimal
from db import get_conn
from financeiro.models import Multa, DocumentoFinanceiro, Transacao


class CalculosFinanceiros:
    """Classe com métodos estáticos para cálculos financeiros"""
    
    @staticmethod
    def resumo_custos_veiculo(veiculo_id, mes=None):
        """Retorna resumo completo de custos de um veículo"""
        conn = get_conn()
        cur = conn.cursor()
        
        # Combustível
        query_comb = """
            SELECT 
                COUNT(*) as qtd,
                SUM(CAST(valor_total AS REAL)) as total
            FROM combustivel
            WHERE veiculo_id=?
        """
        params = [veiculo_id]
        
        if mes:
            query_comb += " AND strftime('%Y-%m', data_abastecimento)=?"
            params.append(mes)
        
        cur.execute(query_comb, params)
        comb_row = cur.fetchone()
        combustivel = {
            'qtd': comb_row[0] or 0,
            'total': float(comb_row[1] or 0)
        }
        
        # Manutenção
        query_manut = """
            SELECT 
                COUNT(*) as qtd,
                SUM(CAST(COALESCE(valor_peca, 0) AS REAL) + CAST(COALESCE(mao_de_obra, 0) AS REAL)) as total
            FROM manutencao
            WHERE veiculo_id=?
        """
        
        cur.execute(query_manut, [veiculo_id])
        manut_row = cur.fetchone()
        manutencao = {
            'qtd': manut_row[0] or 0,
            'total': float(manut_row[1] or 0)
        }
        
        # Multas (transações com tipo='multa')
        cur.execute("""
            SELECT 
                COUNT(*) as qtd,
                SUM(CAST(valor AS REAL)) as total
            FROM transacoes_veiculo
            WHERE veiculo_id=? AND categoria='Multa'
        """, [veiculo_id])
        
        multa_row = cur.fetchone()
        multas = {
            'qtd': multa_row[0] or 0,
            'total': float(multa_row[1] or 0)
        }
        
        # Documentos (IPVA, Seguro, etc)
        cur.execute("""
            SELECT 
                COUNT(*) as qtd,
                SUM(CAST(valor AS REAL)) as total
            FROM transacoes_veiculo
            WHERE veiculo_id=? AND tipo='documento'
        """, [veiculo_id])
        
        doc_row = cur.fetchone()
        documentos = {
            'qtd': doc_row[0] or 0,
            'total': float(doc_row[1] or 0)
        }
        
        conn.close()
        
        total_geral = (combustivel['total'] + manutencao['total'] + 
                      multas['total'] + documentos['total'])
        
        return {
            'combustivel': combustivel,
            'manutencao': manutencao,
            'multas': multas,
            'documentos': documentos,
            'total_geral': total_geral
        }
    
    @staticmethod
    def custo_por_km(veiculo_id):
        """Calcula custo médio por quilômetro"""
        conn = get_conn()
        cur = conn.cursor()
        
        # Obter quilometragem total
        cur.execute("""
            SELECT MAX(CAST(quilometragem AS INTEGER)) as km_max
            FROM veiculos WHERE id=?
        """, (veiculo_id,))
        
        km_result = cur.fetchone()
        km_total = int(km_result[0]) if km_result and km_result[0] else 0
        
        if km_total == 0:
            conn.close()
            return 0
        
        # Obter custos totais
        resumo = CalculosFinanceiros.resumo_custos_veiculo(veiculo_id)
        custo_total = resumo['total_geral']
        
        conn.close()
        return round(custo_total / km_total, 4) if km_total > 0 else 0
    
    @staticmethod
    def consumo_medio(veiculo_id, ultimos_registros=10):
        """Calcula consumo médio (km/litro)"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                CAST(quilometragem AS INTEGER) as quilometragem,
                CAST(quantidade_litros AS REAL) as quantidade_litros,
                data_abastecimento
            FROM combustivel
            WHERE veiculo_id=?
            ORDER BY data_abastecimento DESC
            LIMIT ?
        """, (veiculo_id, ultimos_registros))
        
        registros = cur.fetchall()
        conn.close()
        
        if len(registros) < 2:
            return None
        
        consumos = []
        registros_ordenados = list(reversed(registros))
        
        for i in range(1, len(registros_ordenados)):
            km_rodado = registros_ordenados[i][0] - registros_ordenados[i-1][0]
            litros = registros_ordenados[i][1]
            
            if litros > 0 and km_rodado > 0:
                consumo = km_rodado / litros
                consumos.append(consumo)
        
        return round(sum(consumos) / len(consumos), 2) if consumos else None
    
    @staticmethod
    def consumo_esperado(veiculo_id):
        """Retorna consumo esperado (média histórica de 50 registros)"""
        return CalculosFinanceiros.consumo_medio(veiculo_id, ultimos_registros=50)
    
    @staticmethod
    def detectar_desvios(veiculo_id):
        """Detecta desvios anormais de consumo"""
        consumo_atual = CalculosFinanceiros.consumo_medio(veiculo_id, 5)
        consumo_esperado = CalculosFinanceiros.consumo_esperado(veiculo_id)
        
        if not consumo_atual or not consumo_esperado:
            return None
        
        desvio_percentual = ((consumo_esperado - consumo_atual) / consumo_esperado) * 100
        
        return {
            'consumo_atual': consumo_atual,
            'consumo_esperado': consumo_esperado,
            'desvio_percentual': round(desvio_percentual, 2),
            'status': 'alerta' if abs(desvio_percentual) > 10 else 'normal'
        }
    
    @staticmethod
    def comparativo_veiculos(user_id=None):
        """Compara custos entre veículos"""
        conn = get_conn()
        cur = conn.cursor()
        
        query = """
            SELECT 
                v.id,
                v.placa,
                v.modelo,
                COUNT(DISTINCT c.id) as qtd_abastecimentos,
                SUM(CAST(c.valor_total AS REAL)) as gasto_combustivel,
                COUNT(DISTINCT m.id) as qtd_manutencoes,
                SUM(CAST(COALESCE(m.valor_peca, 0) AS REAL) + CAST(COALESCE(m.mao_de_obra, 0) AS REAL)) as gasto_manutencao
            FROM veiculos v
            LEFT JOIN combustivel c ON v.id = c.veiculo_id
            LEFT JOIN manutencao m ON v.id = m.veiculo_id
            GROUP BY v.id, v.placa, v.modelo
            ORDER BY (SUM(CAST(c.valor_total AS REAL)) + SUM(CAST(COALESCE(m.valor_peca, 0) AS REAL) + CAST(COALESCE(m.mao_de_obra, 0) AS REAL))) DESC
        """
        
        cur.execute(query)
        veiculos = []
        
        for row in cur.fetchall():
            combustivel = float(row['gasto_combustivel'] or 0)
            manutencao = float(row['gasto_manutencao'] or 0)
            
            veiculos.append({
                'id': row['id'],
                'placa': row['placa'],
                'modelo': row['modelo'],
                'abastecimentos': row['qtd_abastecimentos'],
                'gasto_combustivel': combustivel,
                'manutencoes': row['qtd_manutencoes'],
                'gasto_manutencao': manutencao,
                'gasto_total': combustivel + manutencao
            })
        
        conn.close()
        return veiculos
    
    @staticmethod
    def previsao_manutencao(veiculo_id):
        """Prevê custos futuros de manutenção"""
        conn = get_conn()
        cur = conn.cursor()
        
        # Obter histórico de manutenção (últimos 6 meses)
        seis_meses_atras = (date.today() - timedelta(days=180)).isoformat()
        
        cur.execute("""
            SELECT 
                AVG(CAST(COALESCE(valor_peca, 0) AS REAL) + CAST(COALESCE(mao_de_obra, 0) AS REAL)) as media,
                COUNT(*) as qtd_manutencoes
            FROM manutencao
            WHERE veiculo_id=? AND data_manutencao >= ?
        """, (veiculo_id, seis_meses_atras))
        
        resultado = cur.fetchone()
        media_mensal = float(resultado[0] or 0)
        qtd = resultado[1] or 0
        
        conn.close()
        
        return {
            'previsao_proxima_manutencao': round(media_mensal, 2),
            'previsao_anual': round(media_mensal * 12, 2),
            'confianca': 'alta' if qtd > 5 else 'baixa',
            'qtd_registros': qtd
        }
    
    @staticmethod
    def gastos_por_mes(veiculo_id=None, ultimos_meses=12):
        """Retorna gastos mês a mês"""
        conn = get_conn()
        cur = conn.cursor()
        
        meses = []
        
        for i in range(ultimos_meses, 0, -1):
            data_inicio = date.today() - timedelta(days=30*i)
            data_fim = date.today() - timedelta(days=30*(i-1))
            mes = data_inicio.strftime("%Y-%m")
            
            # Combustível
            query = """
                SELECT SUM(CAST(valor_total AS REAL)) as total
                FROM combustivel
                WHERE data_abastecimento BETWEEN ? AND ?
            """
            params = [data_inicio.isoformat(), data_fim.isoformat()]
            
            if veiculo_id:
                query += " AND veiculo_id=?"
                params.insert(1, veiculo_id)
            
            cur.execute(query, params)
            comb = float(cur.fetchone()[0] or 0)
            
            # Manutenção
            query_manut = """
                SELECT SUM(CAST(COALESCE(valor_peca, 0) AS REAL) + CAST(COALESCE(mao_de_obra, 0) AS REAL)) as total
                FROM manutencao
                WHERE data_manutencao BETWEEN ? AND ?
            """
            params_manut = [data_inicio.isoformat(), data_fim.isoformat()]
            
            if veiculo_id:
                query_manut += " AND veiculo_id=?"
                params_manut.insert(1, veiculo_id)
            
            cur.execute(query_manut, params_manut)
            manut = float(cur.fetchone()[0] or 0)
            
            meses.append({
                'mes': mes,
                'combustivel': comb,
                'manutencao': manut,
                'total': comb + manut
            })
        
        conn.close()
        return meses
    
    @staticmethod
    def gastos_por_categoria(veiculo_id=None, mes=None):
        """Retorna gastos por categoria"""
        conn = get_conn()
        cur = conn.cursor()
        
        query = """
            SELECT categoria, SUM(CAST(valor AS REAL)) as total, COUNT(*) as qtd
            FROM transacoes_veiculo
            WHERE 1=1
        """
        params = []
        
        if veiculo_id:
            query += " AND veiculo_id=?"
            params.append(veiculo_id)
        
        if mes:
            query += " AND strftime('%Y-%m', data_transacao)=?"
            params.append(mes)
        
        query += " GROUP BY categoria ORDER BY total DESC"
        
        cur.execute(query, params)
        
        categorias = []
        for row in cur.fetchall():
            categorias.append({
                'categoria': row['categoria'],
                'total': float(row['total'] or 0),
                'qtd': row['qtd']
            })
        
        conn.close()
        return categorias
