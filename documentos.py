"""
Módulo para gerenciar documentos de veículos e gerar alarmes/alertas
"""

from datetime import datetime, timedelta
from db import get_conn

class Documento:
    def __init__(self, id, veiculo_id, tipo_documento, data_emissao, data_vencimento, 
                 numero_documento=None, foto_documento=None, observacoes=None, 
                 notificacao_enviada=False, dias_antecedencia=15, estado_uf=None, criado_em=None):
        self.id = id
        self.veiculo_id = veiculo_id
        self.tipo_documento = tipo_documento
        self.data_emissao = data_emissao
        self.data_vencimento = data_vencimento
        self.numero_documento = numero_documento
        self.foto_documento = foto_documento
        self.observacoes = observacoes
        self.notificacao_enviada = notificacao_enviada
        self.dias_antecedencia = dias_antecedencia
        self.estado_uf = estado_uf
        self.criado_em = criado_em

    @staticmethod
    def criar(veiculo_id, tipo_documento, data_vencimento, data_emissao=None, 
              numero_documento=None, foto_documento=None, observacoes=None, dias_antecedencia=15, estado_uf=None):
        """Cria um novo documento para um veículo"""
        conn = get_conn()
        cur = conn.cursor()
        
        # Se não informar estado, buscar do veículo
        if not estado_uf:
            cur.execute("SELECT estado_uf FROM veiculos WHERE id = ?", (veiculo_id,))
            resultado = cur.fetchone()
            if resultado and resultado[0]:
                estado_uf = resultado[0]
        
        cur.execute("""
            INSERT INTO documentos_veiculo 
            (veiculo_id, tipo_documento, data_emissao, data_vencimento, numero_documento, 
             foto_documento, observacoes, dias_antecedencia, estado_uf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (veiculo_id, tipo_documento, data_emissao, data_vencimento, numero_documento, 
              foto_documento, observacoes, dias_antecedencia, estado_uf))
        
        conn.commit()
        doc_id = cur.lastrowid
        conn.close()
        
        # Verificar se precisa gerar alerta
        verificar_e_gerar_alerta(veiculo_id, tipo_documento, data_vencimento)
        
        return doc_id

    @staticmethod
    def obter_por_veiculo(veiculo_id):
        """Obtém todos os documentos de um veículo"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, veiculo_id, tipo_documento, data_emissao, data_vencimento, 
                   numero_documento, foto_documento, observacoes, notificacao_enviada, 
                   dias_antecedencia, estado_uf, criado_em
            FROM documentos_veiculo
            WHERE veiculo_id = ?
            ORDER BY data_vencimento ASC
        """, (veiculo_id,))
        
        rows = cur.fetchall()
        documentos = []
        
        for row in rows:
            doc = Documento(
                id=row[0],
                veiculo_id=row[1],
                tipo_documento=row[2],
                data_emissao=row[3],
                data_vencimento=row[4],
                numero_documento=row[5],
                foto_documento=row[6],
                observacoes=row[7],
                notificacao_enviada=bool(row[8]),
                dias_antecedencia=row[9],
                estado_uf=row[10],
                criado_em=row[11]
            )
            documentos.append(doc)
        
        conn.close()
        return documentos

    @staticmethod
    def obter_por_id(doc_id):
        """Obtém um documento específico"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, veiculo_id, tipo_documento, data_emissao, data_vencimento, 
                   numero_documento, foto_documento, observacoes, notificacao_enviada, 
                   dias_antecedencia, estado_uf, criado_em
            FROM documentos_veiculo
            WHERE id = ?
        """, (doc_id,))
        
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Documento(
            id=row[0],
            veiculo_id=row[1],
            tipo_documento=row[2],
            data_emissao=row[3],
            data_vencimento=row[4],
            numero_documento=row[5],
            foto_documento=row[6],
            observacoes=row[7],
            notificacao_enviada=bool(row[8]),
            dias_antecedencia=row[9],
            estado_uf=row[10],
            criado_em=row[11]
        )

    @staticmethod
    def atualizar(doc_id, **kwargs):
        """Atualiza um documento"""
        conn = get_conn()
        cur = conn.cursor()
        
        # Campos que podem ser atualizados
        campos = ['tipo_documento', 'data_emissao', 'data_vencimento', 'numero_documento', 
                  'foto_documento', 'observacoes', 'notificacao_enviada', 'dias_antecedencia', 'estado_uf']
        
        updates = []
        values = []
        
        for campo in campos:
            if campo in kwargs:
                updates.append(f"{campo} = ?")
                values.append(kwargs[campo])
        
        if not updates:
            conn.close()
            return False
        
        values.append(doc_id)
        
        cur.execute(f"""
            UPDATE documentos_veiculo
            SET {', '.join(updates)}, atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def deletar(doc_id):
        """Deleta um documento"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM documentos_veiculo WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
        return True


class Alerta:
    def __init__(self, id, veiculo_id, tipo_alerta, titulo, descricao=None, 
                 data_alerta=None, lido=False, atencao_requerida=True):
        self.id = id
        self.veiculo_id = veiculo_id
        self.tipo_alerta = tipo_alerta
        self.titulo = titulo
        self.descricao = descricao
        self.data_alerta = data_alerta
        self.lido = lido
        self.atencao_requerida = atencao_requerida

    @staticmethod
    def criar(veiculo_id, tipo_alerta, titulo, descricao=None, atencao_requerida=True):
        """Cria um novo alerta"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO alertas_veiculo 
            (veiculo_id, tipo_alerta, titulo, descricao, atencao_requerida)
            VALUES (?, ?, ?, ?, ?)
        """, (veiculo_id, tipo_alerta, titulo, descricao, atencao_requerida))
        
        conn.commit()
        alerta_id = cur.lastrowid
        conn.close()
        return alerta_id

    @staticmethod
    def obter_por_veiculo(veiculo_id, apenas_nao_lidos=False):
        """Obtém alertas de um veículo"""
        conn = get_conn()
        cur = conn.cursor()
        
        if apenas_nao_lidos:
            cur.execute("""
                SELECT id, veiculo_id, tipo_alerta, titulo, descricao, 
                       data_alerta, lido, atencao_requerida
                FROM alertas_veiculo
                WHERE veiculo_id = ? AND lido = 0
                ORDER BY atencao_requerida DESC, data_alerta DESC
            """, (veiculo_id,))
        else:
            cur.execute("""
                SELECT id, veiculo_id, tipo_alerta, titulo, descricao, 
                       data_alerta, lido, atencao_requerida
                FROM alertas_veiculo
                WHERE veiculo_id = ?
                ORDER BY atencao_requerida DESC, data_alerta DESC
            """, (veiculo_id,))
        
        rows = cur.fetchall()
        alertas = []
        
        for row in rows:
            alerta = Alerta(
                id=row[0],
                veiculo_id=row[1],
                tipo_alerta=row[2],
                titulo=row[3],
                descricao=row[4],
                data_alerta=row[5],
                lido=bool(row[6]),
                atencao_requerida=bool(row[7])
            )
            alertas.append(alerta)
        
        conn.close()
        return alertas

    @staticmethod
    def marcar_como_lido(alerta_id):
        """Marca um alerta como lido"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("UPDATE alertas_veiculo SET lido = 1 WHERE id = ?", (alerta_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def deletar(alerta_id):
        """Deleta um alerta"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM alertas_veiculo WHERE id = ?", (alerta_id,))
        conn.commit()
        conn.close()
        return True


def verificar_e_gerar_alerta(veiculo_id, tipo_documento, data_vencimento):
    """
    Verifica se um documento está próximo do vencimento e gera alerta se necessário
    """
    try:
        # Converter string de data para datetime
        data_venc = datetime.strptime(data_vencimento, "%d/%m/%Y")
        data_hoje = datetime.now()
        
        # Calcular diferença de dias
        dias_para_vencer = (data_venc - data_hoje).days
        
        # Gerar alerta se está vencido ou vencendo
        if dias_para_vencer < 0:
            # Documento já venceu
            titulo = f"⚠️ {tipo_documento} VENCIDO"
            descricao = f"O documento {tipo_documento} venceu há {abs(dias_para_vencer)} dias ({data_vencimento})"
            atencao = True
        elif dias_para_vencer == 0:
            # Vence hoje
            titulo = f"🔴 {tipo_documento} VENCE HOJE"
            descricao = f"O documento {tipo_documento} vence hoje ({data_vencimento})"
            atencao = True
        elif dias_para_vencer <= 15:
            # Vence em até 15 dias
            titulo = f"🟡 {tipo_documento} VENCENDO EM {dias_para_vencer} DIAS"
            descricao = f"O documento {tipo_documento} vence em {dias_para_vencer} dias ({data_vencimento})"
            atencao = True
        else:
            # Ainda há tempo
            titulo = f"ℹ️ {tipo_documento} - Próximo vencimento"
            descricao = f"O documento {tipo_documento} vence em {dias_para_vencer} dias ({data_vencimento})"
            atencao = False
        
        # Criar alerta
        Alerta.criar(
            veiculo_id=veiculo_id,
            tipo_alerta="documento_vencimento",
            titulo=titulo,
            descricao=descricao,
            atencao_requerida=atencao
        )
        
        return True
    except Exception as e:
        print(f"Erro ao gerar alerta de documento: {e}")
        return False


def obter_alertas_vencimento_documentos():
    """
    Obtém todos os alertas de vencimento de documentos por veículo
    Retorna um dicionário com veiculo_id como chave
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # Buscar todos os documentos que estão próximos do vencimento
    cur.execute("""
        SELECT v.id, v.placa, v.modelo, dv.tipo_documento, dv.data_vencimento, 
               CAST((julianday(dv.data_vencimento, '+3 months') - julianday('now')) AS INTEGER) as dias_para_vencer
        FROM veiculos v
        JOIN documentos_veiculo dv ON v.id = dv.veiculo_id
        WHERE dv.data_vencimento IS NOT NULL
        ORDER BY v.placa, dv.data_vencimento ASC
    """)
    
    rows = cur.fetchall()
    alertas = {}
    
    for row in rows:
        veiculo_id = row[0]
        if veiculo_id not in alertas:
            alertas[veiculo_id] = {
                'placa': row[1],
                'modelo': row[2],
                'documentos': []
            }
        
        # Calcular dias para vencer (considerando formato dd/mm/yyyy)
        try:
            data_venc = datetime.strptime(row[4], "%d/%m/%Y")
            data_hoje = datetime.now()
            dias = (data_venc - data_hoje).days
            
            status = "vencido" if dias < 0 else "critico" if dias <= 15 else "aviso"
            
            alertas[veiculo_id]['documentos'].append({
                'tipo': row[3],
                'data_vencimento': row[4],
                'dias_para_vencer': dias,
                'status': status
            })
        except:
            pass
    
    conn.close()
    return alertas


# Tabela de referência: Vencimentos por Estado
VENCIMENTOS_POR_ESTADO = {
    "AC": {"IPVA": "02", "INSPECAO": "06", "REVISAO": "12"},  # Acre
    "AL": {"IPVA": "03", "INSPECAO": "06", "REVISAO": "12"},  # Alagoas
    "AP": {"IPVA": "04", "INSPECAO": "06", "REVISAO": "12"},  # Amapá
    "AM": {"IPVA": "05", "INSPECAO": "06", "REVISAO": "12"},  # Amazonas
    "BA": {"IPVA": "09", "INSPECAO": "11", "REVISAO": "12"},  # Bahia
    "CE": {"IPVA": "07", "INSPECAO": "11", "REVISAO": "12"},  # Ceará
    "DF": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},  # Distrito Federal
    "ES": {"IPVA": "11", "INSPECAO": "12", "REVISAO": "12"},  # Espírito Santo
    "GO": {"IPVA": "12", "INSPECAO": "06", "REVISAO": "12"},  # Goiás
    "MA": {"IPVA": "03", "INSPECAO": "06", "REVISAO": "12"},  # Maranhão
    "MT": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},  # Mato Grosso
    "MS": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},  # Mato Grosso do Sul
    "MG": {"IPVA": "01", "INSPECAO": "07", "REVISAO": "12"},  # Minas Gerais
    "PA": {"IPVA": "01", "INSPECAO": "06", "REVISAO": "12"},  # Pará
    "PB": {"IPVA": "10", "INSPECAO": "06", "REVISAO": "12"},  # Paraíba
    "PR": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},  # Paraná
    "PE": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},  # Pernambuco
    "PI": {"IPVA": "12", "INSPECAO": "06", "REVISAO": "12"},  # Piauí
    "RJ": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},  # Rio de Janeiro
    "RN": {"IPVA": "10", "INSPECAO": "06", "REVISAO": "12"},  # Rio Grande do Norte
    "RS": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},  # Rio Grande do Sul
    "RO": {"IPVA": "12", "INSPECAO": "06", "REVISAO": "12"},  # Rondônia
    "RR": {"IPVA": "09", "INSPECAO": "06", "REVISAO": "12"},  # Roraima
    "SC": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},  # Santa Catarina
    "SP": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},  # São Paulo
    "SE": {"IPVA": "12", "INSPECAO": "06", "REVISAO": "12"},  # Sergipe
    "TO": {"IPVA": "12", "INSPECAO": "06", "REVISAO": "12"},  # Tocantins
}

def obter_meses_vencimento_estado(estado_uf: str, tipo_documento: str) -> dict:
    """
    Obtém informações de vencimento para um documento em um estado específico
    
    Exemplo:
        >>> obter_meses_vencimento_estado("SP", "IPVA")
        {"mes": 12, "descricao": "IPVA de São Paulo vence em dezembro"}
    """
    if estado_uf not in VENCIMENTOS_POR_ESTADO:
        return {"mes": None, "descricao": "Estado não encontrado"}
    
    estado_info = VENCIMENTOS_POR_ESTADO.get(estado_uf, {})
    mes = estado_info.get(tipo_documento.upper().replace(" ", "_"))
    
    if mes:
        return {
            "mes": int(mes),
            "descricao": f"Vence em {['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'][int(mes)-1]} ({estado_uf})"
        }
    
    return {"mes": None, "descricao": f"Tipo de documento '{tipo_documento}' não configurado para {estado_uf}"}


def renovar_verificacoes_periodicas():
    """
    Função que deve ser chamada periodicamente (ex: diariamente)
    para verificar todos os documentos e atualizar alertas
    """
    conn = get_conn()
    cur = conn.cursor()
    
    # Buscar todos os documentos
    cur.execute("""
        SELECT id, veiculo_id, tipo_documento, data_vencimento
        FROM documentos_veiculo
        WHERE data_vencimento IS NOT NULL
    """)
    
    documentos = cur.fetchall()
    conn.close()
    
    for doc in documentos:
        doc_id, veiculo_id, tipo_documento, data_vencimento = doc
        verificar_e_gerar_alerta(veiculo_id, tipo_documento, data_vencimento)
