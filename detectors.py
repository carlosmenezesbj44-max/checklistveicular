"""
Detector de anomalias em registros de combustível
Valida consumo, quilometragem e valor para identificar problemas
"""

from db import get_conn
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AnomaliaDetector:
    """Detecta anomalias em registros de combustível e manutenção"""
    
    # Limites de tolerância
    DESVIO_CONSUMO_LIMITE = 10  # % de desvio permitido
    DESVIO_VALOR_LIMITE = 30    # % de diferença no preço
    
    @staticmethod
    def calcular_desvio_consumo(veiculo_id: int) -> dict:
        """
        Calcula se há desvio no consumo comparado com histórico
        
        Args:
            veiculo_id: ID do veículo
        
        Returns:
            Dict com informações do desvio detectado
        """
        try:
            conn = get_conn()
            cur = conn.cursor()
            
            # Buscar últimos 10 abastecimentos
            cur.execute("""
                SELECT quantidade_litros, quilometragem, data_abastecimento
                FROM combustivel 
                WHERE veiculo_id = ? 
                ORDER BY data_abastecimento DESC 
                LIMIT 10
            """, (veiculo_id,))
            
            registros = cur.fetchall()
            conn.close()
            
            if len(registros) < 2:
                return {
                    'tem_desvio': False,
                    'motivo': 'Poucos dados para comparação',
                    'quantidade_registros': len(registros)
                }
            
            # Calcular consumo para cada abastecimento
            consumos = []
            for i in range(len(registros) - 1):
                km_atual = registros[i][1]
                km_anterior = registros[i+1][1]
                litros = registros[i][0]
                
                km_rodado = km_atual - km_anterior
                
                if km_rodado > 0 and litros > 0:
                    consumo = km_rodado / litros
                    consumos.append({
                        'consumo': consumo,
                        'km_rodado': km_rodado,
                        'litros': litros,
                        'data': registros[i][2]
                    })
            
            if len(consumos) < 1:
                return {
                    'tem_desvio': False,
                    'motivo': 'Dados inválidos para cálculo'
                }
            
            # Calcular média (excluindo o último registro)
            consumos_anteriores = [c['consumo'] for c in consumos[1:]] if len(consumos) > 1 else [consumos[0]['consumo']]
            media = sum(consumos_anteriores) / len(consumos_anteriores) if consumos_anteriores else consumos[0]['consumo']
            
            consumo_atual = consumos[0]['consumo']
            desvio_pct = ((consumo_atual - media) / media * 100) if media > 0 else 0
            
            tem_desvio = abs(desvio_pct) > AnomaliaDetector.DESVIO_CONSUMO_LIMITE
            
            return {
                'tem_desvio': tem_desvio,
                'consumo_esperado': round(media, 2),
                'consumo_atual': round(consumo_atual, 2),
                'desvio_pct': round(desvio_pct, 2),
                'motivo': 'Consumo acima do padrão' if desvio_pct > AnomaliaDetector.DESVIO_CONSUMO_LIMITE else 'Consumo abaixo do padrão' if desvio_pct < -AnomaliaDetector.DESVIO_CONSUMO_LIMITE else 'Normal'
            }
        
        except Exception as e:
            logger.error(f"Erro ao calcular desvio de consumo: {e}")
            return {
                'tem_desvio': False,
                'motivo': f'Erro na análise: {str(e)}'
            }
    
    @staticmethod
    def verificar_quilometragem(veiculo_id: int, km_novo: int) -> dict:
        """
        Verifica se quilometragem evoluiu corretamente
        
        Args:
            veiculo_id: ID do veículo
            km_novo: Quilometragem do novo registro
        
        Returns:
            Dict com informações sobre a quilometragem
        """
        try:
            conn = get_conn()
            cur = conn.cursor()
            
            # Buscar último registro
            cur.execute("""
                SELECT quilometragem, data_abastecimento
                FROM combustivel 
                WHERE veiculo_id = ? 
                ORDER BY data_abastecimento DESC 
                LIMIT 1
            """, (veiculo_id,))
            
            resultado = cur.fetchone()
            conn.close()
            
            if not resultado:
                return {
                    'suspeita': False,
                    'motivo': 'Primeiro registro do veículo'
                }
            
            km_anterior = resultado[0]
            
            if km_novo < km_anterior:
                return {
                    'suspeita': True,
                    'km_anterior': int(km_anterior),
                    'km_atual': int(km_novo),
                    'diferenca': int(km_anterior - km_novo),
                    'motivo': 'Quilometragem diminuiu (possível fraude ou erro)'
                }
            
            if km_novo == km_anterior:
                return {
                    'suspeita': True,
                    'km_anterior': int(km_anterior),
                    'km_atual': int(km_novo),
                    'diferenca': 0,
                    'motivo': 'Quilometragem não evoluiu'
                }
            
            return {
                'suspeita': False,
                'km_anterior': int(km_anterior),
                'km_atual': int(km_novo),
                'evolucao': int(km_novo - km_anterior),
                'motivo': 'OK'
            }
        
        except Exception as e:
            logger.error(f"Erro ao verificar quilometragem: {e}")
            return {
                'suspeita': False,
                'motivo': f'Erro na análise: {str(e)}'
            }
    
    @staticmethod
    def verificar_valor(veiculo_id: int, valor_novo: float, litros: float) -> dict:
        """
        Verifica se valor está dentro do padrão histórico
        
        Args:
            veiculo_id: ID do veículo
            valor_novo: Valor pago neste abastecimento
            litros: Quantidade de litros
        
        Returns:
            Dict com análise de preço
        """
        try:
            conn = get_conn()
            cur = conn.cursor()
            
            # Buscar últimos 10 abastecimentos
            cur.execute("""
                SELECT valor_total, quantidade_litros 
                FROM combustivel 
                WHERE veiculo_id = ? 
                ORDER BY data_abastecimento DESC 
                LIMIT 10
            """, (veiculo_id,))
            
            registros = cur.fetchall()
            conn.close()
            
            if not registros:
                return {
                    'alerta': False,
                    'motivo': 'Sem histórico para comparação'
                }
            
            # Calcular preço médio por litro (últimos registros)
            precos = []
            for r in registros:
                if r[1] > 0:
                    precos.append(r[0] / r[1])
            
            if not precos:
                return {
                    'alerta': False,
                    'motivo': 'Dados inválidos'
                }
            
            preco_medio = sum(precos) / len(precos)
            preco_novo = valor_novo / litros if litros > 0 else 0
            
            diferenca_pct = ((preco_novo - preco_medio) / preco_medio * 100) if preco_medio > 0 else 0
            
            alerta = diferenca_pct > AnomaliaDetector.DESVIO_VALOR_LIMITE
            
            return {
                'alerta': alerta,
                'preco_medio': round(preco_medio, 2),
                'preco_novo': round(preco_novo, 2),
                'diferenca_pct': round(diferenca_pct, 2),
                'valor_medio': round(preco_medio * litros, 2),
                'valor_pago': round(valor_novo, 2),
                'motivo': f'Valor {diferenca_pct:.1f}% acima da média' if alerta else 'Preço normal',
                'tipo': 'PRECO_ALTO' if diferenca_pct > AnomaliaDetector.DESVIO_VALOR_LIMITE else 'NORMAL'
            }
        
        except Exception as e:
            logger.error(f"Erro ao verificar valor: {e}")
            return {
                'alerta': False,
                'motivo': f'Erro na análise: {str(e)}'
            }
    
    @staticmethod
    def validar_registro_completo(veiculo_id: int, dados: dict) -> dict:
        """
        Valida um registro completo de combustível
        
        Args:
            veiculo_id: ID do veículo
            dados: Dicionário com dados do abastecimento
        
        Returns:
            Dict com resultado da validação completa
        """
        anomalias = []
        alertas = []
        
        # Extrair dados
        km = int(dados.get('quilometragem', 0))
        litros = float(dados.get('quantidade_litros', 0))
        valor = float(dados.get('valor_total', 0))
        
        # Validação 1: Quilometragem
        quil = AnomaliaDetector.verificar_quilometragem(veiculo_id, km)
        if quil.get('suspeita'):
            anomalias.append({
                'tipo': 'QUILOMETRAGEM',
                'severidade': 'CRITICA',
                'mensagem': quil['motivo'],
                'dados': quil
            })
        
        # Validação 2: Consumo
        desvio = AnomaliaDetector.calcular_desvio_consumo(veiculo_id)
        if desvio.get('tem_desvio'):
            alertas.append({
                'tipo': 'CONSUMO',
                'severidade': 'MEDIA',
                'mensagem': desvio['motivo'],
                'dados': desvio
            })
        
        # Validação 3: Valor
        valor_analise = AnomaliaDetector.verificar_valor(veiculo_id, valor, litros)
        if valor_analise.get('alerta'):
            alertas.append({
                'tipo': 'VALOR',
                'severidade': 'MEDIA',
                'mensagem': valor_analise['motivo'],
                'dados': valor_analise
            })
        
        return {
            'valido': len(anomalias) == 0,
            'anomalias': anomalias,
            'alertas': alertas,
            'total_anomalias': len(anomalias),
            'total_alertas': len(alertas),
            'status': 'CRITICA' if anomalias else ('ALERTA' if alertas else 'OK')
        }
