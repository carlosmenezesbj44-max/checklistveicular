#!/usr/bin/env python3
"""
Script para criar a tabela de permissões
"""

import sqlite3
from pathlib import Path

# Encontrar o banco de dados
db_path = Path(__file__).parent / 'data' / 'ChecklistVeicular' / 'checklist.db'

if not db_path.exists():
    print(f"Erro: Banco de dados não encontrado em {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

# Criar tabela de permissões
cur.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_key TEXT UNIQUE NOT NULL,
        feature_name TEXT NOT NULL,
        description TEXT,
        icon TEXT,
        category TEXT,
        admin_enabled BOOLEAN DEFAULT 1,
        user_enabled BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Inserir permissões padrão
features = [
    # Dashboard
    ('dashboard_view', 'Visualizar Dashboard', 'Acessar a página principal com estatísticas', 'bi-graph-up', 'Dashboard', 1, 1),

    # Checklist
    ('checklist_criar', 'Criar Checklist', 'Criar novos checklists de veículos', 'bi-plus-circle', 'Checklist', 1, 1),
    ('checklist_editar', 'Editar Checklist', 'Editar checklists existentes', 'bi-pencil', 'Checklist', 1, 1),
    ('checklist_deletar', 'Deletar Checklist', 'Deletar checklists (apenas itens, mantém veículo)', 'bi-trash', 'Checklist', 1, 0),
    ('checklist_ver_historico', 'Ver Histórico', 'Visualizar histórico completo de checklists', 'bi-clock-history', 'Checklist', 1, 1),

    # Manutenção
    ('manutencao_criar', 'Criar Manutenção', 'Registrar novas manutenções', 'bi-tools', 'Manutenção', 1, 1),
    ('manutencao_editar', 'Editar Manutenção', 'Editar registros de manutenção existentes', 'bi-pencil', 'Manutenção', 1, 1),
    ('manutencao_deletar', 'Deletar Manutenção', 'Deletar registros de manutenção', 'bi-trash', 'Manutenção', 1, 0),
    ('manutencao_dashboard', 'Dashboard Manutenção', 'Acessar dashboard e estatísticas de manutenção', 'bi-graph-up', 'Manutenção', 1, 1),
    ('manutencao_concluir', 'Concluir Manutenção', 'Marcar manutenções como concluídas', 'bi-check-circle', 'Manutenção', 1, 1),

    # Financeiro
    ('financeiro_view', 'Visualizar Financeiro', 'Acessar módulo financeiro e relatórios pessoais', 'bi-cash', 'Financeiro', 1, 1),
    ('financeiro_editar', 'Editar Financeiro', 'Editar dados financeiros e transações', 'bi-pencil', 'Financeiro', 1, 0),
    ('financeiro_relatorios', 'Relatórios Financeiros', 'Gerar relatórios financeiros em PDF/CSV', 'bi-file-earmark', 'Financeiro', 1, 1),

    # Combustível
    ('combustivel_adicionar', 'Registrar Abastecimento', 'Registrar novos abastecimentos', 'bi-fuel-pump', 'Combustível', 1, 1),
    ('combustivel_editar', 'Editar Abastecimento', 'Editar registros de abastecimento', 'bi-pencil', 'Combustível', 1, 1),
    ('combustivel_deletar', 'Deletar Abastecimento', 'Deletar registros de abastecimento', 'bi-trash', 'Combustível', 1, 0),
    ('combustivel_relatorio', 'Relatório Combustível', 'Visualizar relatórios de consumo e custos', 'bi-file-earmark', 'Combustível', 1, 1),

    # Documentos
    ('documentos_upload', 'Upload de Documentos', 'Fazer upload de documentos de veículos', 'bi-cloud-upload', 'Documentos', 1, 1),
    ('documentos_download', 'Download de Documentos', 'Baixar documentos anexados', 'bi-download', 'Documentos', 1, 1),
    ('documentos_deletar', 'Deletar Documentos', 'Deletar documentos (admin apenas)', 'bi-trash', 'Documentos', 1, 0),
    ('documentos_alarmes', 'Ver Alarmes', 'Visualizar notificações de documentos vencidos', 'bi-bell', 'Documentos', 1, 1),

    # Condutores
    ('condutores_criar', 'Cadastrar Condutor', 'Cadastrar novos condutores', 'bi-person-plus', 'Condutores', 1, 1),
    ('condutores_editar', 'Editar Condutor', 'Editar dados de condutores', 'bi-pencil', 'Condutores', 1, 1),
    ('condutores_deletar', 'Deletar Condutor', 'Desativar condutores', 'bi-person-dash', 'Condutores', 1, 0),
    ('condutores_infracoes', 'Gerenciar Infrações', 'Registrar e gerenciar infrações de trânsito', 'bi-exclamation-triangle', 'Condutores', 1, 1),

    # Veículos
    ('veiculos_cadastrar', 'Cadastrar Veículo', 'Cadastrar novos veículos no sistema', 'bi-car-front', 'Veículos', 1, 1),
    ('veiculos_editar', 'Editar Veículo', 'Editar dados de veículos existentes', 'bi-pencil', 'Veículos', 1, 1),
    ('veiculos_deletar', 'Deletar Veículo', 'Remover veículos do sistema', 'bi-trash', 'Veículos', 1, 0),
    ('veiculos_excluir_placa', 'Excluir por Placa', 'Excluir veículo e vínculos pela placa', 'bi-trash', 'Veículos', 1, 0),

    # Usuários (Admin apenas)
    ('usuarios_criar', 'Criar Usuário', 'Criar novos usuários do sistema', 'bi-person-plus', 'Administração', 1, 0),
    ('usuarios_editar', 'Editar Usuário', 'Editar dados de usuários', 'bi-pencil', 'Administração', 1, 0),
    ('usuarios_deletar', 'Deletar Usuário', 'Remover usuários do sistema', 'bi-trash', 'Administração', 1, 0),
    ('usuarios_gerenciar', 'Gerenciar Usuários', 'Administração completa de usuários', 'bi-people-gear', 'Administração', 1, 0),

    # Configurações
    ('configuracoes_twilio', 'Configurar WhatsApp', 'Configurar integração com Twilio WhatsApp', 'bi-whatsapp', 'Configurações', 1, 0),
    ('configuracoes_email', 'Configurar Email', 'Configurar servidor de email', 'bi-envelope', 'Configurações', 1, 0),
    ('configuracoes_sistema', 'Configurar Sistema', 'Configurações gerais do sistema', 'bi-gear', 'Configurações', 1, 0),
    ('permissoes_gerenciar', 'Gerenciar Permissões', 'Administrar permissões de usuários', 'bi-shield-check', 'Configurações', 1, 0),

    # Backup e Restauração
    ('backup_criar', 'Fazer Backup', 'Criar backup completo dos dados', 'bi-download', 'Sistema', 1, 0),
    ('backup_restaurar', 'Restaurar Backup', 'Restaurar dados de backup', 'bi-upload', 'Sistema', 1, 0),
    ('sistema_limpar_orfaos', 'Limpar Órfãos', 'Remover registros órfãos do sistema', 'bi-broom', 'Sistema', 1, 0),

    # Relatórios Avançados
    ('relatorios_view', 'Visualizar Relatórios', 'Acessar relatórios avançados do sistema', 'bi-file-earmark', 'Relatórios', 1, 1),
    ('relatorios_exportar', 'Exportar Relatórios', 'Exportar relatórios em PDF/Excel', 'bi-download', 'Relatórios', 1, 1),
    ('relatorios_personalizados', 'Relatórios Personalizados', 'Criar relatórios personalizados', 'bi-graph-up', 'Relatórios', 1, 0),

    # Inteligência Artificial
    ('inteligencia_view', 'Visualizar Analytics', 'Acessar dados de inteligência e previsões', 'bi-robot', 'Inteligência', 1, 1),
    ('inteligencia_ml', 'Usar Machine Learning', 'Executar modelos de ML para previsões', 'bi-cpu', 'Inteligência', 1, 0),
]

for feature in features:
    try:
        cur.execute("""
            INSERT OR IGNORE INTO permissions 
            (feature_key, feature_name, description, icon, category, admin_enabled, user_enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, feature)
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()

print("[OK] Tabela de permissoes criada com sucesso!")
print(f"Localizacao: {db_path}")
print(f"{len(features)} permissoes padrao inseridas")
