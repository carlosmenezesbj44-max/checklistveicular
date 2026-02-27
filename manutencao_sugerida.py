"""
Funcoes para gerar e gerenciar manutencoes sugeridas automaticamente
a partir de itens com problema no checklist
"""

from db import get_conn
from datetime import datetime


def gerar_manutencao_sugerida(veiculo_id, checklist_id, itens_problema):
    """
    Cria um único registro de manutencao sugerida agrupando todos os itens com problema no checklist
    itens_problema: lista de dicts com {nome_item, comentario}
    """
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        if not itens_problema:
            return True
        
        # Agrupa todos os itens em um único registro de manutenção
        nomes_itens = [item.get('nome_item', 'Item Problema') for item in itens_problema]
        nome_peca = ', '.join(nomes_itens)  # Combina todos os nomes
        
        # Combina todos os comentários
        comentarios = [item.get('comentario', '') for item in itens_problema if item.get('comentario')]
        observacoes = ' | '.join(comentarios) if comentarios else 'Problemas detectados no checklist'
        
        # Cria um único registro com todos os itens
        cur.execute("""
            INSERT INTO manutencao 
            (veiculo_id, nome_peca, data_manutencao, quilometragem_atual, 
             status, sugestao_checklist, checklist_id, itens_problema, observacoes)
            VALUES (?, ?, datetime('now'), ?, 'pendente', 1, ?, ?, ?)
        """, (
            veiculo_id,
            nome_peca,
            0,  # quilometragem sera preenchida depois
            checklist_id,
            nome_peca,
            observacoes
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"Erro ao gerar manutencao sugerida: {e}")
        return False


def obter_manutencoes_pendentes(veiculo_id=None):
    """
    Obtém todas as manutencoes sugeridas pendentes de aprovacao e checklist com problemas
    """
    conn = get_conn()
    cur = conn.cursor()
    
    query = """
        SELECT m.id, m.veiculo_id, m.nome_peca, m.data_manutencao, m.observacoes,
               m.checklist_id, v.placa, v.modelo, v.condutor
        FROM manutencao m
        JOIN veiculos v ON m.veiculo_id = v.id
        WHERE (m.sugestao_checklist = 1 AND m.status = 'pendente') 
           OR m.status = 'em_analise'
    """
    
    params = []
    if veiculo_id:
        query += " AND m.veiculo_id = ?"
        params.append(veiculo_id)
    
    query += " ORDER BY m.data_manutencao DESC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    
    manutencoes = []
    for row in rows:
        manutencoes.append({
            'id': row[0],
            'veiculo_id': row[1],
            'nome_peca': row[2],
            'data_manutencao': row[3],
            'observacoes': row[4],
            'checklist_id': row[5],
            'placa': row[6],
            'modelo': row[7],
            'condutor': row[8]
        })
    
    conn.close()
    return manutencoes


def aprovar_manutencao(manutencao_id):
    """Aprova uma manutencao sugerida"""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE manutencao 
        SET status = 'agendada'
        WHERE id = ?
    """, (manutencao_id,))
    
    conn.commit()
    conn.close()
    return True


def rejeitar_manutencao(manutencao_id):
    """Rejeita uma manutencao sugerida"""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE manutencao 
        SET status = 'rejeitada'
        WHERE id = ?
    """, (manutencao_id,))
    
    conn.commit()
    conn.close()
    return True


def agendar_manutencao(manutencao_id, data_manutencao, mecanico=None):
    """Agenda uma manutencao sugerida"""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE manutencao 
        SET status = 'agendada', data_manutencao = ?
        WHERE id = ?
    """, (data_manutencao, manutencao_id))
    
    conn.commit()
    conn.close()
    return True
