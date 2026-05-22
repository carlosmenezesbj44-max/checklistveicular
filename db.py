import sqlite3
from config import DB_FILE

def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS veiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        condutor TEXT,
        placa TEXT,
        modelo TEXT,
        data TEXT,
        quilometragem TEXT,
        observacoes TEXT,
        foto_carro TEXT,
        tipo TEXT,
        estado_uf TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS itens_checklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER,
        nome_item TEXT,
        status TEXT,
        comentario TEXT,
        caminho_foto TEXT,
        caminho_thumb TEXT,
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS combustivel (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER,
        placa TEXT,
        tipo_veiculo TEXT,
        data_abastecimento TEXT,
        quilometragem TEXT,
        quantidade_litros TEXT,
        valor_total REAL,
        observacoes TEXT,
        created_at TEXT,
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS manutencao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER NOT NULL,
        nome_peca TEXT NOT NULL,
        data_manutencao TEXT NOT NULL,
        quilometragem_atual TEXT NOT NULL,
        vida_util_km INTEGER,
        proxima_manutencao_km INTEGER,
        valor_peca REAL,
        mao_de_obra REAL,
        observacoes TEXT,
        status TEXT DEFAULT 'pendente',
        data_conclusao TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sugestao_checklist BOOLEAN DEFAULT 0,
        checklist_id INTEGER,
        itens_problema TEXT,
        data_sugestao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS historico_manutencao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        manutencao_id INTEGER NOT NULL,
        veiculo_id INTEGER NOT NULL,
        nome_peca TEXT NOT NULL,
        valor_peca REAL,
        mao_de_obra REAL,
        data_manutencao TEXT NOT NULL,
        data_conclusao TEXT NOT NULL,
        mes_ano TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (manutencao_id) REFERENCES manutencao(id),
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        email TEXT,
        is_admin BOOLEAN DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        reset_token TEXT,
        reset_token_expiration TIMESTAMP,
        role TEXT DEFAULT 'usuario',
        profile_photo TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS condutores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_completo TEXT NOT NULL,
        cpf TEXT UNIQUE,
        rg TEXT,
        data_nascimento TEXT,
        endereco TEXT,
        telefone TEXT,
        email TEXT,
        foto_condutor TEXT,
        cnh_numero TEXT UNIQUE,
        cnh_categoria TEXT,
        cnh_data_emissao TEXT,
        cnh_data_validade TEXT,
        exame_toxicologico_data TEXT,
        exame_medico_data TEXT,
        notas TEXT,
        ativo BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS condutor_veiculo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        condutor_id INTEGER NOT NULL,
        veiculo_id INTEGER NOT NULL,
        data_inicio TEXT,
        data_fim TEXT,
        km_rodados TEXT,
        observacoes TEXT,
        FOREIGN KEY (condutor_id) REFERENCES condutores(id),
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS condutor_infracoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        condutor_id INTEGER NOT NULL,
        tipo TEXT,
        data_infracao TEXT,
        descricao TEXT,
        valor REAL,
        paga BOOLEAN DEFAULT 0,
        FOREIGN KEY (condutor_id) REFERENCES condutores(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS condutor_treinamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        condutor_id INTEGER NOT NULL,
        tipo_treinamento TEXT,
        data_realizacao TEXT,
        certificado TEXT,
        validade TEXT,
        observacoes TEXT,
        FOREIGN KEY (condutor_id) REFERENCES condutores(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notas_fiscais_veiculo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER NOT NULL,
        nome_arquivo TEXT NOT NULL,
        caminho_arquivo TEXT NOT NULL,
        data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transacoes_veiculo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        descricao TEXT,
        valor REAL NOT NULL,
        data_transacao TEXT NOT NULL,
        condutor_id INTEGER,
        nota_fiscal TEXT,
        categoria TEXT,
        observacoes TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id),
        FOREIGN KEY (condutor_id) REFERENCES condutores(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documentos_veiculo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER NOT NULL,
        tipo_documento TEXT NOT NULL,
        data_emissao TEXT,
        data_vencimento TEXT NOT NULL,
        numero_documento TEXT,
        foto_documento TEXT,
        observacoes TEXT,
        notificacao_enviada BOOLEAN DEFAULT 0,
        dias_antecedencia INTEGER DEFAULT 15,
        estado_uf TEXT,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS vencimentos_por_estado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estado_uf TEXT NOT NULL,
        tipo_documento TEXT NOT NULL,
        mes_vencimento INTEGER,
        descricao TEXT,
        observacoes TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alertas_veiculo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        veiculo_id INTEGER NOT NULL,
        tipo_alerta TEXT NOT NULL,
        titulo TEXT NOT NULL,
        descricao TEXT,
        data_alerta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        lido BOOLEAN DEFAULT 0,
        atencao_requerida BOOLEAN DEFAULT 1,
        FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
    )
    """)
    # Índices para acelerar buscas e joins
    cur.execute("CREATE INDEX IF NOT EXISTS idx_veiculos_placa ON veiculos(placa)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_veiculos_condutor ON veiculos(condutor)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_veiculos_modelo ON veiculos(modelo)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_itens_veiculo ON itens_checklist(veiculo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_itens_status ON itens_checklist(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_combustivel_veiculo ON combustivel(veiculo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_combustivel_placa ON combustivel(placa)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_manutencao_veiculo ON manutencao(veiculo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_manutencao_data ON manutencao(data_manutencao)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_manutencao_peca ON manutencao(nome_peca)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_condutores_nome ON condutores(nome_completo)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_condutores_cpf ON condutores(cpf)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_condutores_ativo ON condutores(ativo)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_condutor_veiculo_condutor ON condutor_veiculo(condutor_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_condutor_veiculo_veiculo ON condutor_veiculo(veiculo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_condutor_infracoes_condutor ON condutor_infracoes(condutor_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_condutor_treinamentos_condutor ON condutor_treinamentos(condutor_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notas_fiscais_veiculo ON notas_fiscais_veiculo(veiculo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_veiculo ON transacoes_veiculo(veiculo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_data ON transacoes_veiculo(data_transacao)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_transacoes_condutor ON transacoes_veiculo(condutor_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documentos_veiculo ON documentos_veiculo(veiculo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_documentos_vencimento ON documentos_veiculo(data_vencimento)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alertas_veiculo ON alertas_veiculo(veiculo_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alertas_lido ON alertas_veiculo(lido)")
    conn.commit()
    conn.close()

    # Adiciona colunas para controle de troca de óleo caso não existam (migrations simples)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(veiculos)")
    cols = [row[1] for row in cur.fetchall()]
    if 'oleo_data' not in cols:
        try:
            cur.execute("ALTER TABLE veiculos ADD COLUMN oleo_data TEXT")
        except Exception:
            pass
    if 'oleo_km' not in cols:
        try:
            cur.execute("ALTER TABLE veiculos ADD COLUMN oleo_km TEXT")
        except Exception:
            pass
    if 'foto_clrv' not in cols:
        try:
            cur.execute("ALTER TABLE veiculos ADD COLUMN foto_clrv TEXT")
        except Exception:
            pass
    if 'foto_cnh' not in cols:
        try:
            cur.execute("ALTER TABLE veiculos ADD COLUMN foto_cnh TEXT")
        except Exception:
            pass
    conn.commit()

    cur.execute("PRAGMA table_info(combustivel)")
    cols = [row[1] for row in cur.fetchall()]
    if 'nota_fiscal_foto' not in cols:
        try:
            cur.execute("ALTER TABLE combustivel ADD COLUMN nota_fiscal_foto TEXT")
        except Exception:
            pass
    conn.commit()
    
    cur.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cur.fetchall()]
    if 'role' not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'usuario'")
        except Exception:
            pass
    if 'profile_photo' not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN profile_photo TEXT")
        except Exception:
            pass
    if 'is_active' not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
        except Exception:
            pass
    
    cur.execute("PRAGMA table_info(manutencao)")
    cols = [row[1] for row in cur.fetchall()]
    if 'nota_fiscal_foto' not in cols:
        try:
            cur.execute("ALTER TABLE manutencao ADD COLUMN nota_fiscal_foto TEXT")
        except Exception:
            pass
    if 'status' not in cols:
        try:
            cur.execute("ALTER TABLE manutencao ADD COLUMN status TEXT DEFAULT 'pendente'")
        except Exception:
            pass
    if 'data_conclusao' not in cols:
        try:
            cur.execute("ALTER TABLE manutencao ADD COLUMN data_conclusao TEXT")
        except Exception:
            pass
    
    cur.execute("PRAGMA table_info(condutor_infracoes)")
    cols = [row[1] for row in cur.fetchall()]
    if 'responsavel_pagamento' not in cols:
        try:
            cur.execute("ALTER TABLE condutor_infracoes ADD COLUMN responsavel_pagamento TEXT DEFAULT 'condutor'")
        except Exception:
            pass
    if 'data_vencimento' not in cols:
        try:
            cur.execute("ALTER TABLE condutor_infracoes ADD COLUMN data_vencimento TEXT")
        except Exception:
            pass
    if 'pago_em' not in cols:
        try:
            cur.execute("ALTER TABLE condutor_infracoes ADD COLUMN pago_em TEXT")
        except Exception:
            pass
    if 'notificacao_enviada' not in cols:
        try:
            cur.execute("ALTER TABLE condutor_infracoes ADD COLUMN notificacao_enviada BOOLEAN DEFAULT 0")
        except Exception:
            pass
    
    # Adicionar campo telefone na tabela user
    cur.execute("PRAGMA table_info(user)")
    cols = [row[1] for row in cur.fetchall()]
    if 'telefone' not in cols:
        try:
            cur.execute("ALTER TABLE user ADD COLUMN telefone VARCHAR(20)")
            print("[OK] Campo telefone adicionado à tabela user")
        except Exception as e:
            print(f"[WARNING] Aviso ao adicionar telefone: {e}")
    
    # Adicionar campo foto_velocimetro na tabela combustivel
    cur.execute("PRAGMA table_info(combustivel)")
    cols = [row[1] for row in cur.fetchall()]
    if 'foto_velocimetro' not in cols:
        try:
            cur.execute("ALTER TABLE combustivel ADD COLUMN foto_velocimetro VARCHAR(255)")
            print("✅ Campo foto_velocimetro adicionado à tabela combustivel")
        except Exception as e:
            print(f"⚠️ Aviso ao adicionar foto_velocimetro: {e}")
    
    if 'nota_fiscal_foto' not in cols:
        try:
            cur.execute("ALTER TABLE combustivel ADD COLUMN nota_fiscal_foto VARCHAR(255)")
            print("✅ Campo nota_fiscal_foto adicionado à tabela combustivel")
        except Exception as e:
            print(f"⚠️ Aviso ao adicionar nota_fiscal_foto: {e}")
    
    if 'anomalia_detectada' not in cols:
        try:
            cur.execute("ALTER TABLE combustivel ADD COLUMN anomalia_detectada BOOLEAN DEFAULT 0")
            print("✅ Campo anomalia_detectada adicionado à tabela combustivel")
        except Exception as e:
            print(f"⚠️ Aviso ao adicionar anomalia_detectada: {e}")
    
    if 'notificacao_enviada' not in cols:
        try:
            cur.execute("ALTER TABLE combustivel ADD COLUMN notificacao_enviada BOOLEAN DEFAULT 0")
            print("✅ Campo notificacao_enviada adicionado à tabela combustivel")
        except Exception as e:
            print(f"⚠️ Aviso ao adicionar notificacao_enviada: {e}")
    
    conn.commit()
    conn.close()