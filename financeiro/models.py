"""
Modelos de dados para o módulo financeiro
"""
from datetime import datetime
from decimal import Decimal
from db import get_conn


class Multa:
    """Modelo para registrar multas de trânsito"""
    
    def __init__(self, id=None, veiculo_id=None, numero_multa='', 
                 data_multa=None, valor=0, status='pendente', 
                 data_pagamento=None, descricao=''):
        self.id = id
        self.veiculo_id = veiculo_id
        self.numero_multa = numero_multa
        self.data_multa = data_multa
        self.valor = Decimal(str(valor)) if valor else Decimal('0')
        self.status = status  # 'pendente', 'paga'
        self.data_pagamento = data_pagamento
        self.descricao = descricao
    
    @staticmethod
    def criar(veiculo_id, numero_multa, data_multa, valor, descricao=''):
        """Cria nova multa"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO transacoes_veiculo
            (veiculo_id, tipo, descricao, valor, data_transacao, categoria)
            VALUES (?, 'multa', ?, ?, ?, 'Multa')
        """, (veiculo_id, descricao or numero_multa, valor, data_multa))
        
        conn.commit()
        multa_id = cur.lastrowid
        conn.close()
        return multa_id
    
    @staticmethod
    def marcar_paga(multa_id, data_pagamento=None):
        """Marca multa como paga"""
        if not data_pagamento:
            data_pagamento = datetime.now().strftime("%Y-%m-%d")
        
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE transacoes_veiculo 
            SET observacoes='paga em ' || ?
            WHERE id=? AND categoria='Multa'
        """, (data_pagamento, multa_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def obter_por_veiculo(veiculo_id):
        """Obtém multas de um veículo"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM transacoes_veiculo 
            WHERE veiculo_id=? AND categoria='Multa'
            ORDER BY data_transacao DESC
        """, (veiculo_id,))
        
        multas = [dict(row) for row in cur.fetchall()]
        conn.close()
        return multas
    
    @staticmethod
    def obter_pendentes():
        """Obtém todas multas pendentes"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, v.placa FROM transacoes_veiculo t
            JOIN veiculos v ON t.veiculo_id = v.id
            WHERE t.categoria='Multa' AND (t.observacoes IS NULL OR t.observacoes NOT LIKE '%paga em%')
            ORDER BY t.data_transacao DESC
        """)
        
        multas = [dict(row) for row in cur.fetchall()]
        conn.close()
        return multas


class DocumentoFinanceiro:
    """Modelo para documentos obrigatórios (IPVA, Seguro, etc)"""
    
    TIPOS = ['IPVA', 'Seguro', 'Licenciamento', 'Vistoria', 'DPVAT']
    
    def __init__(self, id=None, veiculo_id=None, tipo='', 
                 data_vencimento=None, valor=0, status='pendente',
                 data_pagamento=None):
        self.id = id
        self.veiculo_id = veiculo_id
        self.tipo = tipo
        self.data_vencimento = data_vencimento
        self.valor = Decimal(str(valor)) if valor else Decimal('0')
        self.status = status  # 'pendente', 'pago', 'vencido'
        self.data_pagamento = data_pagamento
    
    @staticmethod
    def criar(veiculo_id, tipo, data_vencimento, valor):
        """Cria novo documento financeiro"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO transacoes_veiculo
            (veiculo_id, tipo, descricao, valor, data_transacao, categoria)
            VALUES (?, 'documento', ?, ?, ?, ?)
        """, (veiculo_id, tipo, valor, data_vencimento, tipo))
        
        conn.commit()
        doc_id = cur.lastrowid
        conn.close()
        return doc_id
    
    @staticmethod
    def obter_por_veiculo(veiculo_id):
        """Obtém documentos de um veículo"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM transacoes_veiculo 
            WHERE veiculo_id=? AND tipo='documento'
            ORDER BY data_transacao ASC
        """, (veiculo_id,))
        
        docs = [dict(row) for row in cur.fetchall()]
        conn.close()
        return docs
    
    @staticmethod
    def obter_vencendo_em_dias(dias=30):
        """Obtém documentos vencendo em N dias"""
        from datetime import timedelta, date
        
        data_limite = (date.today() + timedelta(days=dias)).isoformat()
        
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, v.placa FROM transacoes_veiculo t
            JOIN veiculos v ON t.veiculo_id = v.id
            WHERE t.tipo='documento' AND t.data_transacao <= ? 
            AND t.observacoes NOT LIKE '%pago%'
            ORDER BY t.data_transacao ASC
        """, (data_limite,))
        
        docs = [dict(row) for row in cur.fetchall()]
        conn.close()
        return docs


class Transacao:
    """Modelo genérico para transações financeiras"""
    
    CATEGORIAS = ['Combustível', 'Manutenção', 'Multa', 'IPVA', 'Seguro', 
                  'Licenciamento', 'Estacionamento', 'Outros']
    
    def __init__(self, id=None, veiculo_id=None, tipo='', categoria='',
                 data=None, descricao='', valor=0, arquivos=None):
        self.id = id
        self.veiculo_id = veiculo_id
        self.tipo = tipo
        self.categoria = categoria
        self.data = data or datetime.now().strftime("%Y-%m-%d")
        self.descricao = descricao
        self.valor = Decimal(str(valor)) if valor else Decimal('0')
        self.arquivos = arquivos or []
    
    @staticmethod
    def criar(veiculo_id, tipo, categoria, data, descricao, valor):
        """Cria nova transação"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO transacoes_veiculo
            (veiculo_id, tipo, descricao, valor, data_transacao, categoria)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (veiculo_id, tipo, descricao, valor, data, categoria))
        
        conn.commit()
        transacao_id = cur.lastrowid
        conn.close()
        return transacao_id
    
    @staticmethod
    def obter_por_categoria(veiculo_id=None, categoria=None, mes=None):
        """Obtém transações filtradas"""
        conn = get_conn()
        cur = conn.cursor()
        
        query = "SELECT * FROM transacoes_veiculo WHERE 1=1"
        params = []
        
        if veiculo_id:
            query += " AND veiculo_id=?"
            params.append(veiculo_id)
        
        if categoria:
            query += " AND categoria=?"
            params.append(categoria)
        
        if mes:  # formato: 'YYYY-MM'
            query += " AND strftime('%Y-%m', data_transacao)=?"
            params.append(mes)
        
        query += " ORDER BY data_transacao DESC"
        
        cur.execute(query, params)
        transacoes = [dict(row) for row in cur.fetchall()]
        conn.close()
        return transacoes
    
    @staticmethod
    def obter_por_veiculo(veiculo_id):
        """Obtém todas as transações de um veículo"""
        return Transacao.obter_por_categoria(veiculo_id=veiculo_id)
    
    @staticmethod
    def deletar(transacao_id):
        """Deleta uma transação"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM transacoes_veiculo WHERE id=?", (transacao_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def atualizar(transacao_id, **kwargs):
        """Atualiza uma transação"""
        conn = get_conn()
        cur = conn.cursor()
        
        campos = []
        valores = []
        
        for chave, valor in kwargs.items():
            campos.append(f"{chave}=?")
            valores.append(valor)
        
        valores.append(transacao_id)
        
        query = f"UPDATE transacoes_veiculo SET {', '.join(campos)} WHERE id=?"
        cur.execute(query, valores)
        
        conn.commit()
        conn.close()
        return True
