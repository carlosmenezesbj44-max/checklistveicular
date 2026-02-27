"""
Sistema de alertas financeiros
"""
from datetime import datetime, timedelta, date
from db import get_conn
from financeiro.services import CalculosFinanceiros
from financeiro.models import Multa, DocumentoFinanceiro, Transacao


class AlertasFinanceiros:
    """Classe para gerenciar alertas financeiros"""
    
    @staticmethod
    def verificar_todos_alertas():
        """Verifica todos os alertas do sistema"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM veiculos")
        veiculos = [row[0] for row in cur.fetchall()]
        
        conn.close()
        
        alertas = []
        
        for veiculo_id in veiculos:
            alertas.extend(AlertasFinanceiros.verificar_alertas_veiculo(veiculo_id))
        
        return alertas
    
    @staticmethod
    def verificar_alertas_veiculo(veiculo_id):
        """Verifica alertas para um veículo específico"""
        alertas = []
        
        # 1. Alerta de consumo acima da média
        desvio = CalculosFinanceiros.detectar_desvios(veiculo_id)
        if desvio and desvio['status'] == 'alerta':
            desvio_str = "abaixo" if desvio['desvio_percentual'] < 0 else "acima"
            alertas.append({
                'tipo': 'consumo_desvio',
                'veiculo_id': veiculo_id,
                'titulo': f"⚠️ Consumo {desvio_str} da média",
                'mensagem': f"Consumo atual: {desvio['consumo_atual']} km/l (Esperado: {desvio['consumo_esperado']} km/l)",
                'severidade': 'aviso',
                'icone': '⚠️'
            })
        
        # 2. Alerta de multas pendentes
        multas_pendentes = [m for m in Multa.obter_por_veiculo(veiculo_id) 
                           if not m['observacoes'] or 'paga' not in m['observacoes']]
        if multas_pendentes:
            total_multas = sum(float(m['valor'] or 0) for m in multas_pendentes)
            alertas.append({
                'tipo': 'multa_pendente',
                'veiculo_id': veiculo_id,
                'titulo': f"🚨 {len(multas_pendentes)} Multa(s) Pendente(s)",
                'mensagem': f"Total a pagar: R$ {total_multas:.2f}",
                'severidade': 'crítico',
                'icone': '🚨'
            })
        
        # 3. Alerta de documentos vencendo
        docs_vencendo = DocumentoFinanceiro.obter_vencendo_em_dias(dias=30)
        docs_veiculo = [d for d in docs_vencendo if d['veiculo_id'] == veiculo_id]
        if docs_veiculo:
            alertas.append({
                'tipo': 'documento_vencendo',
                'veiculo_id': veiculo_id,
                'titulo': f"📄 {len(docs_veiculo)} Documento(s) Vencendo",
                'mensagem': f"Primeiros vencimentos: {docs_veiculo[0]['data_transacao']}",
                'severidade': 'aviso',
                'icone': '📄'
            })
        
        # 4. Alerta de gasto excedente do mês
        this_month = datetime.now().strftime("%Y-%m")
        gastos_mes = CalculosFinanceiros.gastos_por_mes(veiculo_id, ultimos_meses=1)
        if gastos_mes and len(gastos_mes) > 0:
            gasto_atual = gastos_mes[-1]['total']
            
            # Comparar com média dos 3 meses anteriores
            gastos_3meses = CalculosFinanceiros.gastos_por_mes(veiculo_id, ultimos_meses=4)
            if len(gastos_3meses) > 1:
                gastos_anteriores = gastos_3meses[:-1]
                media_anterior = sum(g['total'] for g in gastos_anteriores) / len(gastos_anteriores)
                
                if gasto_atual > media_anterior * 1.3:  # 30% acima da média
                    percentual = ((gasto_atual - media_anterior) / media_anterior) * 100
                    alertas.append({
                        'tipo': 'gasto_excedente',
                        'veiculo_id': veiculo_id,
                        'titulo': "💰 Gasto do Mês Acima da Média",
                        'mensagem': f"Gasto: R$ {gasto_atual:.2f} ({percentual:.1f}% acima da média)",
                        'severidade': 'aviso',
                        'icone': '💰'
                    })
        
        # 5. Alerta de manutenção pendente
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM manutencao
            WHERE veiculo_id=? AND status='pendente'
        """, (veiculo_id,))
        
        manutencoes_pendentes = cur.fetchone()[0]
        conn.close()
        
        if manutencoes_pendentes > 0:
            alertas.append({
                'tipo': 'manutencao_pendente',
                'veiculo_id': veiculo_id,
                'titulo': f"🔧 {manutencoes_pendentes} Manutenção(ções) Pendente(s)",
                'mensagem': f"Verifique as manutenções agendadas",
                'severidade': 'aviso',
                'icone': '🔧'
            })
        
        return alertas
    
    @staticmethod
    def salvar_alerta(veiculo_id, tipo, titulo, mensagem, severidade='aviso'):
        """Salva alerta no banco de dados"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO alertas_veiculo
            (veiculo_id, tipo_alerta, titulo, descricao)
            VALUES (?, ?, ?, ?)
        """, (veiculo_id, tipo, titulo, mensagem))
        
        conn.commit()
        alerta_id = cur.lastrowid
        conn.close()
        
        return alerta_id
    
    @staticmethod
    def obter_alertas_nao_lidos(veiculo_id=None):
        """Obtém alertas não lidos"""
        conn = get_conn()
        cur = conn.cursor()
        
        query = "SELECT * FROM alertas_veiculo WHERE lido=0"
        params = []
        
        if veiculo_id:
            query += " AND veiculo_id=?"
            params.append(veiculo_id)
        
        query += " ORDER BY data_alerta DESC"
        
        cur.execute(query, params)
        alertas = [dict(row) for row in cur.fetchall()]
        
        conn.close()
        return alertas
    
    @staticmethod
    def marcar_alerta_como_lido(alerta_id):
        """Marca alerta como lido"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE alertas_veiculo SET lido=1 WHERE id=?
        """, (alerta_id,))
        
        conn.commit()
        conn.close()
