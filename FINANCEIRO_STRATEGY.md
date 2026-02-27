# Estratégia: Aba Financeira Completa

## Visão Geral
Implementar módulo financeiro completo com 5 seções: Resumo de Custos, Abastecimento, Manutenções, Multas/Documentos e Relatórios.

---

## 1. Arquitetura do Banco de Dados

### Modelo de Dados

```sql
-- Tabelas existentes: combustivel, manutencao

-- Tabela de multas (nova)
CREATE TABLE IF NOT EXISTS multas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id INTEGER NOT NULL,
    numero_multa VARCHAR(20),
    data_multa DATE,
    valor DECIMAL(10, 2),
    status VARCHAR(20), -- 'pendente', 'paga'
    data_pagamento DATE,
    descricao TEXT,
    FOREIGN KEY(veiculo_id) REFERENCES veiculos(id)
);

-- Tabela de documentos (nova)
CREATE TABLE IF NOT EXISTS documentos_financeiros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id INTEGER NOT NULL,
    tipo VARCHAR(50), -- 'IPVA', 'Seguro', 'Licenciamento', etc
    data_vencimento DATE,
    valor DECIMAL(10, 2),
    status VARCHAR(20), -- 'pago', 'pendente', 'vencido'
    data_pagamento DATE,
    renovacao_automatica BOOLEAN,
    FOREIGN KEY(veiculo_id) REFERENCES veiculos(id)
);

-- Tabela de categorias de gastos (nova)
CREATE TABLE IF NOT EXISTS categorias_gasto (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100),
    descricao TEXT,
    cor HEX_COLOR
);

-- Tabela de gastos gerais (nova)
CREATE TABLE IF NOT EXISTS gastos_gerais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL,
    data DATE,
    descricao TEXT,
    valor DECIMAL(10, 2),
    arquivo_comprovante VARCHAR(255),
    FOREIGN KEY(veiculo_id) REFERENCES veiculos(id),
    FOREIGN KEY(categoria_id) REFERENCES categorias_gasto(id)
);

-- Tabela de alertas financeiros (nova)
CREATE TABLE IF NOT EXISTS alertas_financeiros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veiculo_id INTEGER NOT NULL,
    tipo VARCHAR(50), -- 'consumo_acima', 'vencimento', 'multa_pendente'
    mensagem TEXT,
    data_criacao DATETIME,
    lido BOOLEAN DEFAULT 0,
    FOREIGN KEY(veiculo_id) REFERENCES veiculos(id)
);
```

---

## 2. Estrutura de Pastas

```
checklist-carros/
├── financeiro/
│   ├── __init__.py
│   ├── models.py (Classes de dados)
│   ├── services.py (Lógica de cálculos)
│   ├── reports.py (Geração de relatórios)
│   ├── charts.py (Dados para gráficos)
│   └── alerts.py (Sistema de alertas)
├── static/
│   ├── js/
│   │   └── financeiro.js (Charts.js)
│   └── css/
│       └── financeiro.css
├── templates/
│   ├── financeiro/
│   │   ├── index.html (Dashboard principal)
│   │   ├── resumo.html (Resumo custos)
│   │   ├── abastecimento.html (Controle combustível)
│   │   ├── manutencoes.html (Gestão manutenção)
│   │   ├── multas.html (Multas e documentos)
│   │   └── relatorios.html (Relatórios)
└── app.py (adicionar rotas)
```

---

## 3. Models - Classe de Dados Financeiros (`financeiro/models.py`)

```python
from datetime import datetime
from decimal import Decimal
from db import get_conn

class CategoriasGasto:
    COMBUSTIVEL = 'Combustível'
    MANUTENCAO = 'Manutenção'
    MULTA = 'Multa'
    SEGURO = 'Seguro'
    IPVA = 'IPVA'
    LICENCIAMENTO = 'Licenciamento'
    ESTACIONAMENTO = 'Estacionamento'
    OUTROS = 'Outros'

class Multa:
    def __init__(self, id=None, veiculo_id=None, numero_multa='', 
                 data_multa=None, valor=0, status='pendente', 
                 data_pagamento=None, descricao=''):
        self.id = id
        self.veiculo_id = veiculo_id
        self.numero_multa = numero_multa
        self.data_multa = data_multa
        self.valor = Decimal(str(valor))
        self.status = status
        self.data_pagamento = data_pagamento
        self.descricao = descricao
    
    @staticmethod
    def criar(veiculo_id, numero_multa, data_multa, valor, descricao=''):
        """Cria nova multa"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO multas 
            (veiculo_id, numero_multa, data_multa, valor, status, descricao)
            VALUES (?, ?, ?, ?, 'pendente', ?)
        """, (veiculo_id, numero_multa, data_multa, valor, descricao))
        
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
            UPDATE multas 
            SET status='paga', data_pagamento=?
            WHERE id=?
        """, (data_pagamento, multa_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def obter_por_veiculo(veiculo_id):
        """Obtém multas de um veículo"""
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM multas WHERE veiculo_id=?
            ORDER BY data_multa DESC
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
            SELECT m.*, v.placa FROM multas m
            JOIN veiculos v ON m.veiculo_id = v.id
            WHERE m.status='pendente'
            ORDER BY m.data_multa DESC
        """)
        
        multas = [dict(row) for row in cur.fetchall()]
        conn.close()
        return multas

class DocumentoFinanceiro:
    TIPOS = ['IPVA', 'Seguro', 'Licenciamento', 'Vistoria']
    
    def __init__(self, id=None, veiculo_id=None, tipo='', 
                 data_vencimento=None, valor=0, status='pendente'):
        self.id = id
        self.veiculo_id = veiculo_id
        self.tipo = tipo
        self.data_vencimento = data_vencimento
        self.valor = Decimal(str(valor))
        self.status = status
    
    @staticmethod
    def criar(veiculo_id, tipo, data_vencimento, valor):
        """Cria novo documento"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO documentos_financeiros
            (veiculo_id, tipo, data_vencimento, valor, status)
            VALUES (?, ?, ?, ?, 'pendente')
        """, (veiculo_id, tipo, data_vencimento, valor))
        
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
            SELECT * FROM documentos_financeiros 
            WHERE veiculo_id=?
            ORDER BY data_vencimento ASC
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
            SELECT d.*, v.placa FROM documentos_financeiros d
            JOIN veiculos v ON d.veiculo_id = v.id
            WHERE d.data_vencimento <= ? 
            AND d.status IN ('pendente', 'vencido')
            ORDER BY d.data_vencimento ASC
        """, (data_limite,))
        
        docs = [dict(row) for row in cur.fetchall()]
        conn.close()
        return docs

class GastoGeral:
    def __init__(self, id=None, veiculo_id=None, categoria=None, 
                 data=None, descricao='', valor=0):
        self.id = id
        self.veiculo_id = veiculo_id
        self.categoria = categoria
        self.data = data or datetime.now().strftime("%Y-%m-%d")
        self.descricao = descricao
        self.valor = Decimal(str(valor))
    
    @staticmethod
    def criar(veiculo_id, categoria, data, descricao, valor):
        """Cria novo gasto"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO gastos_gerais
            (veiculo_id, categoria, data, descricao, valor)
            VALUES (?, ?, ?, ?, ?)
        """, (veiculo_id, categoria, data, descricao, valor))
        
        conn.commit()
        gasto_id = cur.lastrowid
        conn.close()
        return gasto_id
    
    @staticmethod
    def obter_por_categoria(veiculo_id=None, categoria=None, mes=None):
        """Obtém gastos filtrados"""
        conn = get_conn()
        cur = conn.cursor()
        
        query = "SELECT * FROM gastos_gerais WHERE 1=1"
        params = []
        
        if veiculo_id:
            query += " AND veiculo_id=?"
            params.append(veiculo_id)
        
        if categoria:
            query += " AND categoria=?"
            params.append(categoria)
        
        if mes:  # formato: 'YYYY-MM'
            query += " AND strftime('%Y-%m', data)=?"
            params.append(mes)
        
        query += " ORDER BY data DESC"
        
        cur.execute(query, params)
        gastos = [dict(row) for row in cur.fetchall()]
        conn.close()
        return gastos
```

---

## 4. Serviços de Cálculo (`financeiro/services.py`)

```python
from datetime import datetime, timedelta, date
from decimal import Decimal
from db import get_conn
from financeiro.models import Multa, DocumentoFinanceiro

class CalculosFinanceiros:
    
    @staticmethod
    def resumo_custos_veiculo(veiculo_id, mes=None):
        """Retorna resumo completo de custos de um veículo"""
        conn = get_conn()
        cur = conn.cursor()
        
        query_base = """
            SELECT 
                'Combustível' as categoria,
                SUM(CAST(valor_total AS REAL)) as total,
                COUNT(*) as qtd
            FROM combustivel
            WHERE veiculo_id=?
        """
        params = [veiculo_id]
        
        if mes:  # formato: 'YYYY-MM'
            query_base += " AND strftime('%Y-%m', data_abastecimento)=?"
            params.append(mes)
        
        cur.execute(query_base, params)
        combustivel = dict(cur.fetchone() or {})
        
        # Manutenção
        query_manut = """
            SELECT 
                'Manutenção' as categoria,
                SUM(CAST(valor_peca AS REAL) + CAST(mao_de_obra AS REAL)) as total,
                COUNT(*) as qtd
            FROM manutencao
            WHERE veiculo_id=?
        """
        
        cur.execute(query_manut, params[:1])
        manutencao = dict(cur.fetchone() or {})
        
        # Multas
        multas = Multa.obter_por_veiculo(veiculo_id)
        multa_total = sum(float(m['valor']) for m in multas if m['status'] == 'paga')
        
        # Documentos
        docs = DocumentoFinanceiro.obter_por_veiculo(veiculo_id)
        doc_total = sum(float(d['valor']) for d in docs if d['status'] == 'pago')
        
        conn.close()
        
        return {
            'combustivel': {
                'total': float(combustivel.get('total') or 0),
                'qtd': combustivel.get('qtd') or 0
            },
            'manutencao': {
                'total': float(manutencao.get('total') or 0),
                'qtd': manutencao.get('qtd') or 0
            },
            'multas': {
                'total': multa_total,
                'qtd': len([m for m in multas if m['status'] == 'paga'])
            },
            'documentos': {
                'total': doc_total,
                'qtd': len([d for d in docs if d['status'] == 'pago'])
            },
            'total_geral': (
                float(combustivel.get('total') or 0) +
                float(manutencao.get('total') or 0) +
                multa_total +
                doc_total
            )
        }
    
    @staticmethod
    def custo_por_km(veiculo_id):
        """Calcula custo médio por quilômetro"""
        conn = get_conn()
        cur = conn.cursor()
        
        # Obter quilometragem total
        cur.execute("""
            SELECT MAX(quilometragem) as km_max
            FROM veiculos WHERE id=?
        """, (veiculo_id,))
        
        km_total = cur.fetchone()[0] or 0
        
        if km_total == 0:
            conn.close()
            return 0
        
        # Obter custos totais
        resumo = CalculosFinanceiros.resumo_custos_veiculo(veiculo_id)
        custo_total = resumo['total_geral']
        
        conn.close()
        return round(custo_total / km_total, 2)
    
    @staticmethod
    def consumo_medio(veiculo_id, ultimos_registros=10):
        """Calcula consumo médio (km/litro)"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                quilometragem,
                quantidade_litros,
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
            
            if litros > 0:
                consumo = km_rodado / litros
                consumos.append(consumo)
        
        return round(sum(consumos) / len(consumos), 2) if consumos else None
    
    @staticmethod
    def consumo_esperado(veiculo_id):
        """Retorna consumo esperado (média histórica)"""
        return CalculosFinanceiros.consumo_medio(veiculo_id, ultimos_registros=50)
    
    @staticmethod
    def detectar_desvios(veiculo_id):
        """Detecta desvios anormais de consumo"""
        consumo_atual = CalculosFinanceiros.consumo_medio(veiculo_id, 5)
        consumo_esperado = CalculosFinanceiros.consumo_esperado(veiculo_id)
        
        if not consumo_atual or not consumo_esperado:
            return None
        
        desvio_percentual = ((consumo_atual - consumo_esperado) / consumo_esperado) * 100
        
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
                COUNT(DISTINCT c.id) as abastecimentos,
                SUM(CAST(c.valor_total AS REAL)) as gasto_combustivel,
                COUNT(DISTINCT m.id) as manutencoes,
                SUM(CAST(m.valor_peca AS REAL) + CAST(m.mao_de_obra AS REAL)) as gasto_manutencao
            FROM veiculos v
            LEFT JOIN combustivel c ON v.id = c.veiculo_id
            LEFT JOIN manutencao m ON v.id = m.veiculo_id
            WHERE 1=1
        """
        params = []
        
        if user_id:
            query += " AND v.user_id=?"
            params.append(user_id)
        
        query += """
            GROUP BY v.id, v.placa, v.modelo
            ORDER BY (CAST(gasto_combustivel AS REAL) + CAST(gasto_manutencao AS REAL)) DESC
        """
        
        cur.execute(query, params)
        veiculos = []
        
        for row in cur.fetchall():
            combustivel = float(row['gasto_combustivel'] or 0)
            manutencao = float(row['gasto_manutencao'] or 0)
            
            veiculos.append({
                'id': row['id'],
                'placa': row['placa'],
                'modelo': row['modelo'],
                'abastecimentos': row['abastecimentos'],
                'gasto_combustivel': combustivel,
                'manutencoes': row['manutencoes'],
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
                AVG(CAST(valor_peca AS REAL) + CAST(mao_de_obra AS REAL)) as media_mensal,
                COUNT(*) as qtd_manutencoes
            FROM manutencao
            WHERE veiculo_id=? AND data_manutencao >= ?
        """, (veiculo_id, seis_meses_atras))
        
        resultado = cur.fetchone()
        media_mensal = resultado[0] or 0
        
        conn.close()
        
        return {
            'previsao_proxima_manutencao': round(media_mensal, 2),
            'previsao_anual': round(media_mensal * 12, 2),
            'confianca': 'alta' if resultado[1] > 5 else 'baixa'
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
            
            query = """
                SELECT 
                    SUM(CAST(valor_total AS REAL)) as combustivel,
                    0 as manutencao
                FROM combustivel
                WHERE data_abastecimento BETWEEN ? AND ?
            """
            params = [data_inicio.isoformat(), data_fim.isoformat()]
            
            if veiculo_id:
                query += " AND veiculo_id=?"
                params.insert(1, veiculo_id)
            
            cur.execute(query, params)
            comb = cur.fetchone()[0] or 0
            
            query_manut = """
                SELECT SUM(CAST(valor_peca AS REAL) + CAST(mao_de_obra AS REAL))
                FROM manutencao
                WHERE data_manutencao BETWEEN ? AND ?
            """
            params_manut = [data_inicio.isoformat(), data_fim.isoformat()]
            
            if veiculo_id:
                query_manut += " AND veiculo_id=?"
                params_manut.insert(1, veiculo_id)
            
            cur.execute(query_manut, params_manut)
            manut = cur.fetchone()[0] or 0
            
            meses.append({
                'mes': mes,
                'combustivel': float(comb),
                'manutencao': float(manut),
                'total': float(comb) + float(manut)
            })
        
        conn.close()
        return meses
```

---

## 5. Dados para Gráficos (`financeiro/charts.py`)

```python
import json
from datetime import datetime, date
from financeiro.services import CalculosFinanceiros

class ChartData:
    
    @staticmethod
    def pizza_custos_por_categoria(veiculo_id):
        """Dados para gráfico pizza de custos"""
        resumo = CalculosFinanceiros.resumo_custos_veiculo(veiculo_id)
        
        labels = []
        data = []
        cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
        
        for i, (cat, valor_dict) in enumerate(resumo.items()):
            if cat != 'total_geral' and valor_dict['total'] > 0:
                labels.append(cat.upper())
                data.append(valor_dict['total'])
        
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
                    'tension': 0.4
                },
                {
                    'label': 'Manutenção',
                    'data': manutencao_data,
                    'borderColor': '#36A2EB',
                    'backgroundColor': 'rgba(54, 162, 235, 0.1)',
                    'tension': 0.4
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
        """Dados para gráfico medidor de consumo"""
        desvio = CalculosFinanceiros.detectar_desvios(veiculo_id)
        
        if not desvio:
            return None
        
        return {
            'consumo_atual': desvio['consumo_atual'],
            'consumo_esperado': desvio['consumo_esperado'],
            'desvio_percentual': desvio['desvio_percentual'],
            'status': desvio['status']
        }
```

---

## 6. Relatórios (`financeiro/reports.py`)

```python
from datetime import datetime, date, timedelta
from io import BytesIO
import csv
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from financeiro.services import CalculosFinanceiros

class RelatorioFinanceiro:
    
    @staticmethod
    def gerar_pdf_veiculo(veiculo_id, titulo="Relatório Financeiro"):
        """Gera PDF com resumo financeiro do veículo"""
        
        from db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT placa, modelo FROM veiculos WHERE id=?", (veiculo_id,))
        veiculo = dict(cur.fetchone())
        conn.close()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=20
        )
        
        elements.append(
            Paragraph(f"RELATÓRIO FINANCEIRO - {veiculo['placa']}", title_style)
        )
        elements.append(Spacer(1, 0.3))
        
        # Resumo de custos
        resumo = CalculosFinanceiros.resumo_custos_veiculo(veiculo_id)
        
        resumo_data = [
            ['Categoria', 'Total', 'Quantidade'],
            ['Combustível', f"R$ {resumo['combustivel']['total']:.2f}", 
             resumo['combustivel']['qtd']],
            ['Manutenção', f"R$ {resumo['manutencao']['total']:.2f}", 
             resumo['manutencao']['qtd']],
            ['Multas', f"R$ {resumo['multas']['total']:.2f}", 
             resumo['multas']['qtd']],
            ['Documentos', f"R$ {resumo['documentos']['total']:.2f}", 
             resumo['documentos']['qtd']],
            ['TOTAL', f"R$ {resumo['total_geral']:.2f}", '-']
        ]
        
        resumo_table = Table(resumo_data, colWidths=[200, 150, 150])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        
        elements.append(resumo_table)
        elements.append(Spacer(1, 0.5))
        
        # Indicadores
        consumo_medio = CalculosFinanceiros.consumo_medio(veiculo_id)
        custo_km = CalculosFinanceiros.custo_por_km(veiculo_id)
        previsao = CalculosFinanceiros.previsao_manutencao(veiculo_id)
        
        indicadores_data = [
            ['Indicador', 'Valor'],
            ['Consumo Médio', f"{consumo_medio} km/l" if consumo_medio else 'N/A'],
            ['Custo por KM', f"R$ {custo_km:.4f}"],
            ['Previsão Manutenção Anual', f"R$ {previsao['previsao_anual']:.2f}"]
        ]
        
        indicadores_table = Table(indicadores_data, colWidths=[250, 200])
        indicadores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ca02c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        elements.append(indicadores_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def gerar_csv_gastos(veiculo_id=None):
        """Gera CSV com todos os gastos"""
        
        buffer = BytesIO()
        writer = csv.writer(buffer)
        
        # Cabeçalho
        writer.writerow(['Data', 'Categoria', 'Descrição', 'Valor', 'Veículo'])
        
        # Combustível
        from db import get_conn
        conn = get_conn()
        cur = conn.cursor()
        
        query = """
            SELECT 
                data_abastecimento,
                'Combustível',
                'Abastecimento ' || quantidade_litros || 'L',
                valor_total,
                placa
            FROM combustivel c
            JOIN veiculos v ON c.veiculo_id = v.id
            WHERE 1=1
        """
        params = []
        
        if veiculo_id:
            query += " AND c.veiculo_id=?"
            params.append(veiculo_id)
        
        query += " UNION ALL SELECT "
        query += """
            data_manutencao,
            'Manutenção',
            nome_peca,
            valor_peca + mao_de_obra,
            placa
            FROM manutencao m
            JOIN veiculos v ON m.veiculo_id = v.id
            WHERE 1=1
        """
        
        if veiculo_id:
            query += " AND m.veiculo_id=?"
            params.append(veiculo_id)
        
        query += " ORDER BY data DESC"
        
        cur.execute(query, params)
        
        for row in cur.fetchall():
            writer.writerow(row)
        
        conn.close()
        
        buffer.seek(0)
        return buffer
```

---

## 7. Alertas (`financeiro/alerts.py`)

```python
from datetime import datetime, timedelta, date
from db import get_conn
from financeiro.services import CalculosFinanceiros
from financeiro.models import Multa, DocumentoFinanceiro

class AlertasFinanceiros:
    
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
            alertas.append({
                'tipo': 'consumo_acima',
                'veiculo_id': veiculo_id,
                'mensagem': f"Consumo acima da média: {desvio['desvio_percentual']:.1f}%",
                'severidade': 'aviso'
            })
        
        # 2. Alerta de multas pendentes
        multas_pendentes = [m for m in Multa.obter_por_veiculo(veiculo_id) 
                           if m['status'] == 'pendente']
        if multas_pendentes:
            alertas.append({
                'tipo': 'multa_pendente',
                'veiculo_id': veiculo_id,
                'mensagem': f"{len(multas_pendentes)} multa(s) pendente(s) - Total: R$ {sum(float(m['valor']) for m in multas_pendentes):.2f}",
                'severidade': 'crítico'
            })
        
        # 3. Alerta de documentos vencendo
        docs_vencendo = DocumentoFinanceiro.obter_vencendo_em_dias(dias=30)
        docs_veiculo = [d for d in docs_vencendo if d['veiculo_id'] == veiculo_id]
        if docs_veiculo:
            alertas.append({
                'tipo': 'documento_vencendo',
                'veiculo_id': veiculo_id,
                'mensagem': f"{len(docs_veiculo)} documento(s) vencendo",
                'severidade': 'aviso'
            })
        
        # 4. Alerta de gasto excedente do mês
        this_month = datetime.now().strftime("%Y-%m")
        gastos_mes = CalculosFinanceiros.gastos_por_mes(veiculo_id, ultimos_meses=1)
        if gastos_mes:
            gasto_total = gastos_mes[-1]['total']
            # Comparar com média dos 3 meses anteriores
            gastos_3meses = CalculosFinanceiros.gastos_por_mes(veiculo_id, ultimos_meses=4)
            media = sum(g['total'] for g in gastos_3meses[:-1]) / 3
            
            if gasto_total > media * 1.3:
                alertas.append({
                    'tipo': 'gasto_excedente',
                    'veiculo_id': veiculo_id,
                    'mensagem': f"Gasto do mês 30% acima da média",
                    'severidade': 'aviso'
                })
        
        return alertas
    
    @staticmethod
    def salvar_alerta(veiculo_id, tipo, mensagem):
        """Salva alerta no banco de dados"""
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO alertas_financeiros
            (veiculo_id, tipo, mensagem, data_criacao, lido)
            VALUES (?, ?, ?, ?, 0)
        """, (veiculo_id, tipo, mensagem, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
```

---

## 8. Rotas (`app.py` - adicionar)

```python
from flask import render_template, jsonify, request, send_file
from financeiro.services import CalculosFinanceiros
from financeiro.charts import ChartData
from financeiro.reports import RelatorioFinanceiro
from financeiro.alerts import AlertasFinanceiros
from financeiro.models import Multa, DocumentoFinanceiro

# DASHBOARD FINANCEIRO
@app.route('/financeiro')
@login_required
def financeiro_dashboard():
    """Dashboard principal financeiro"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT id, placa FROM veiculos")
    veiculos = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    # Selecionar primeiro veículo por padrão
    veiculo_selecionado = veiculos[0]['id'] if veiculos else None
    
    if veiculo_selecionado:
        resumo = CalculosFinanceiros.resumo_custos_veiculo(veiculo_selecionado)
        consumo = CalculosFinanceiros.consumo_medio(veiculo_selecionado)
        custo_km = CalculosFinanceiros.custo_por_km(veiculo_selecionado)
    else:
        resumo = None
        consumo = None
        custo_km = None
    
    alertas = AlertasFinanceiros.verificar_todos_alertas()
    
    return render_template('financeiro/index.html',
                         veiculos=veiculos,
                         veiculo_selecionado=veiculo_selecionado,
                         resumo=resumo,
                         consumo_medio=consumo,
                         custo_km=custo_km,
                         alertas=alertas)

# API: Dados de gráficos
@app.route('/api/financeiro/grafico-pizza/<int:veiculo_id>')
@login_required
def api_grafico_pizza(veiculo_id):
    """Retorna dados para gráfico pizza"""
    data = ChartData.pizza_custos_por_categoria(veiculo_id)
    return jsonify(data)

@app.route('/api/financeiro/grafico-linha/<int:veiculo_id>')
@login_required
def api_grafico_linha(veiculo_id):
    """Retorna dados para gráfico linha"""
    data = ChartData.linha_gastos_mensais(veiculo_id)
    return jsonify(data)

@app.route('/api/financeiro/grafico-barras')
@login_required
def api_grafico_barras():
    """Retorna dados para gráfico barras comparativo"""
    data = ChartData.barra_comparativo_veiculos()
    return jsonify(data)

@app.route('/api/financeiro/consumo/<int:veiculo_id>')
@login_required
def api_consumo(veiculo_id):
    """Retorna análise de consumo"""
    desvio = CalculosFinanceiros.detectar_desvios(veiculo_id)
    return jsonify(desvio)

# MULTAS
@app.route('/financeiro/multas')
@login_required
def financeiro_multas():
    """Página de gestão de multas"""
    
    multas_pendentes = Multa.obter_pendentes()
    
    return render_template('financeiro/multas.html',
                         multas=multas_pendentes)

@app.route('/api/financeiro/multa', methods=['POST'])
@login_required
def api_criar_multa():
    """Cria nova multa"""
    
    data = request.get_json()
    
    multa_id = Multa.criar(
        veiculo_id=data['veiculo_id'],
        numero_multa=data.get('numero_multa'),
        data_multa=data['data_multa'],
        valor=data['valor'],
        descricao=data.get('descricao')
    )
    
    return jsonify({'success': True, 'multa_id': multa_id})

@app.route('/api/financeiro/multa/<int:multa_id>/pagar', methods=['POST'])
@login_required
def api_pagar_multa(multa_id):
    """Marca multa como paga"""
    
    data = request.get_json()
    Multa.marcar_paga(multa_id, data.get('data_pagamento'))
    
    return jsonify({'success': True})

# DOCUMENTOS
@app.route('/financeiro/documentos')
@login_required
def financeiro_documentos():
    """Página de gestão de documentos"""
    
    docs_vencendo = DocumentoFinanceiro.obter_vencendo_em_dias(dias=90)
    
    return render_template('financeiro/documentos.html',
                         documentos=docs_vencendo)

@app.route('/api/financeiro/documento', methods=['POST'])
@login_required
def api_criar_documento():
    """Cria novo documento financeiro"""
    
    data = request.get_json()
    
    doc_id = DocumentoFinanceiro.criar(
        veiculo_id=data['veiculo_id'],
        tipo=data['tipo'],
        data_vencimento=data['data_vencimento'],
        valor=data['valor']
    )
    
    return jsonify({'success': True, 'documento_id': doc_id})

# RELATÓRIOS
@app.route('/financeiro/relatorios')
@login_required
def financeiro_relatorios():
    """Página de relatórios"""
    return render_template('financeiro/relatorios.html')

@app.route('/api/financeiro/relatorio-pdf/<int:veiculo_id>')
@login_required
def api_relatorio_pdf(veiculo_id):
    """Gera PDF do relatório"""
    
    pdf_buffer = RelatorioFinanceiro.gerar_pdf_veiculo(veiculo_id)
    
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'relatorio_veiculo_{veiculo_id}.pdf'
    )

@app.route('/api/financeiro/relatorio-csv/<int:veiculo_id>')
@login_required
def api_relatorio_csv(veiculo_id):
    """Gera CSV dos gastos"""
    
    csv_buffer = RelatorioFinanceiro.gerar_csv_gastos(veiculo_id)
    
    return send_file(
        csv_buffer,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'gastos_veiculo_{veiculo_id}.csv'
    )
```

---

## 9. Templates HTML

### `templates/financeiro/index.html`

```html
{% extends "base.html" %}

{% block content %}
<div class="container-fluid mt-4">
    <h1>💰 Aba Financeira</h1>
    
    <!-- Alertas -->
    {% if alertas %}
    <div class="alert-container">
        {% for alerta in alertas %}
        <div class="alert alert-{{ alerta.severidade }} alert-dismissible fade show">
            <strong>{{ alerta.tipo|upper }}:</strong> {{ alerta.mensagem }}
            <button type="button" class="close">&times;</button>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <!-- Seletor de veículo -->
    <div class="form-group mb-4">
        <label>Selecione um veículo:</label>
        <select id="veiculo-select" class="form-control" onchange="carregarDados()">
            <option value="">-- Todos --</option>
            {% for v in veiculos %}
            <option value="{{ v.id }}" {% if v.id == veiculo_selecionado %}selected{% endif %}>
                {{ v.placa }}
            </option>
            {% endfor %}
        </select>
    </div>
    
    <!-- Cards de Resumo -->
    {% if resumo %}
    <div class="row">
        <div class="col-md-3">
            <div class="card bg-danger text-white">
                <div class="card-body">
                    <h5>Combustível</h5>
                    <h3>R$ {{ "%.2f"|format(resumo.combustivel.total) }}</h3>
                    <small>{{ resumo.combustivel.qtd }} abastecimentos</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-info text-white">
                <div class="card-body">
                    <h5>Manutenção</h5>
                    <h3>R$ {{ "%.2f"|format(resumo.manutencao.total) }}</h3>
                    <small>{{ resumo.manutencao.qtd }} registros</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-warning text-white">
                <div class="card-body">
                    <h5>Multas</h5>
                    <h3>R$ {{ "%.2f"|format(resumo.multas.total) }}</h3>
                    <small>{{ resumo.multas.qtd }} pagas</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <h5>TOTAL</h5>
                    <h3>R$ {{ "%.2f"|format(resumo.total_geral) }}</h3>
                    <small>Custo/KM: R$ {{ "%.4f"|format(custo_km) }}</small>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
    
    <!-- Abas de conteúdo -->
    <ul class="nav nav-tabs mt-4">
        <li class="nav-item">
            <a class="nav-link active" href="#resumo">Resumo</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/financeiro/abastecimento">Abastecimento</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/financeiro/manutencoes">Manutenções</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/financeiro/multas">Multas</a>
        </li>
        <li class="nav-item">
            <a class="nav-link" href="/financeiro/relatorios">Relatórios</a>
        </li>
    </ul>
    
    <!-- Gráficos -->
    <div class="row mt-4">
        <div class="col-md-6">
            <div class="card">
                <div class="card-body">
                    <h5>Distribuição de Custos</h5>
                    <canvas id="chart-pizza"></canvas>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card">
                <div class="card-body">
                    <h5>Consumo de Combustível</h5>
                    {% if consumo_medio %}
                    <p class="text-center">
                        <strong>{{ consumo_medio }} km/l</strong>
                    </p>
                    {% endif %}
                    <canvas id="chart-consumo"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <div class="row mt-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-body">
                    <h5>Gastos Mês a Mês</h5>
                    <canvas id="chart-linha"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="{{ url_for('static', filename='js/financeiro.js') }}"></script>

<script>
function carregarDados() {
    const veiculo_id = document.getElementById('veiculo-select').value;
    if (veiculo_id) {
        window.location.href = `/financeiro?veiculo=${veiculo_id}`;
    }
}
</script>
{% endblock %}
```

### `static/js/financeiro.js`

```javascript
// Gráfico Pizza - Distribuição de Custos
const veiculoId = new URLSearchParams(window.location.search).get('veiculo') || 
                  document.getElementById('veiculo-select').value;

if (veiculoId) {
    fetch(`/api/financeiro/grafico-pizza/${veiculoId}`)
        .then(r => r.json())
        .then(data => {
            const ctx = document.getElementById('chart-pizza').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: data,
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        });
    
    // Gráfico Linha - Gastos Mensais
    fetch(`/api/financeiro/grafico-linha/${veiculoId}`)
        .then(r => r.json())
        .then(data => {
            const ctx = document.getElementById('chart-linha').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: data,
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        });
    
    // Análise de Consumo
    fetch(`/api/financeiro/consumo/${veiculoId}`)
        .then(r => r.json())
        .then(data => {
            if (data && data.desvio_percentual) {
                const canvas = document.getElementById('chart-consumo');
                const valor = Math.min(100, Math.abs(data.desvio_percentual) + 50);
                
                // Gauge chart (circular)
                const ctx = canvas.getContext('2d');
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        datasets: [{
                            data: [valor, 100 - valor],
                            backgroundColor: [
                                data.status === 'alerta' ? '#FF6384' : '#36A2EB',
                                '#ddd'
                            ]
                        }]
                    },
                    options: {
                        responsive: true
                    }
                });
            }
        });
}
```

---

## 10. Requisitos (`requirements.txt` - adicionar)

```
reportlab>=3.6.0
openpyxl>=3.7.0
```

---

## 11. Fluxo Completo

```
┌─────────────────────────────────────┐
│  ABA FINANCEIRA (Dashboard)         │
├─────────────────────────────────────┤
│                                     │
│ ├─ Resumo Custos                    │
│ │  ├─ Card: Combustível             │
│ │  ├─ Card: Manutenção              │
│ │  ├─ Card: Multas                  │
│ │  └─ Card: Total                   │
│ │                                   │
│ ├─ Gráficos                         │
│ │  ├─ Pizza: Distribuição           │
│ │  ├─ Linha: Mês a Mês              │
│ │  └─ Barras: Comparativo           │
│ │                                   │
│ ├─ Abastecimento                    │
│ │  ├─ Tabela Registros              │
│ │  ├─ Consumo Médio                 │
│ │  └─ Alertas Desvio                │
│ │                                   │
│ ├─ Manutenções                      │
│ │  ├─ Histórico Gastos              │
│ │  ├─ Previsão Futura               │
│ │  └─ Comparativo Veículos          │
│ │                                   │
│ ├─ Multas & Documentos              │
│ │  ├─ Multas Pendentes              │
│ │  ├─ Documentos Vencendo           │
│ │  └─ Alertas                       │
│ │                                   │
│ └─ Relatórios                       │
│    ├─ PDF Completo                  │
│    └─ CSV Exportação                │
│                                     │
└─────────────────────────────────────┘
```

---

## 12. Próximos Passos

- [ ] Criar tabelas SQL
- [ ] Implementar `financeiro/models.py`
- [ ] Implementar `financeiro/services.py`
- [ ] Implementar `financeiro/charts.py`
- [ ] Implementar `financeiro/reports.py`
- [ ] Implementar `financeiro/alerts.py`
- [ ] Adicionar rotas em `app.py`
- [ ] Criar templates HTML
- [ ] Implementar gráficos Chart.js
- [ ] Testar cálculos e relatórios
- [ ] Integrar com notificações WhatsApp
- [ ] Adicionar agendamento de relatórios

---

## 13. Indicadores Principais

| Indicador | Fórmula | Uso |
|-----------|---------|-----|
| **Custo/KM** | Gasto Total / KM Rodado | Comparar veículos |
| **Consumo Médio** | KM Rodado / Litros | Detectar desvios |
| **Custo por Litro** | Gasto Combustível / Litros | Análise de preços |
| **Taxa Danificação** | Itens Danificados / Total | Qualidade |
| **Previsão Manutenção** | Média Histórica (6 meses) | Orçamento |

