"""
Geração de relatórios (PDF, CSV)
"""
from datetime import datetime, date
from io import BytesIO
import csv
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from db import get_conn
from financeiro.services import CalculosFinanceiros


class RelatorioFinanceiro:
    """Classe para gerar relatórios financeiros"""
    
    @staticmethod
    def gerar_pdf_veiculo(veiculo_id, titulo="Relatório Financeiro"):
        """Gera PDF com resumo financeiro do veículo"""
        
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT placa, modelo FROM veiculos WHERE id=?", (veiculo_id,))
        veiculo_row = cur.fetchone()
        veiculo = dict(veiculo_row) if veiculo_row else {}
        conn.close()
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=20,
            alignment=1
        )
        
        elements.append(
            Paragraph(f"RELATÓRIO FINANCEIRO - {veiculo.get('placa', 'N/A')}", title_style)
        )
        elements.append(Spacer(1, 0.2 * inch))
        
        # Resumo de custos
        resumo = CalculosFinanceiros.resumo_custos_veiculo(veiculo_id)
        
        resumo_data = [
            ['Categoria', 'Total (R$)', 'Quantidade'],
            ['Combustível', f"R$ {resumo['combustivel']['total']:.2f}", 
             resumo['combustivel']['qtd']],
            ['Manutenção', f"R$ {resumo['manutencao']['total']:.2f}", 
             resumo['manutencao']['qtd']],
            ['Multas', f"R$ {resumo['multas']['total']:.2f}", 
             resumo['multas']['qtd']],
            ['Documentos', f"R$ {resumo['documentos']['total']:.2f}", 
             resumo['documentos']['qtd']],
            ['TOTAL GERAL', f"R$ {resumo['total_geral']:.2f}", '-']
        ]
        
        resumo_table = Table(resumo_data, colWidths=[2.5 * inch, 2 * inch, 1.5 * inch])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), 
             [colors.white, colors.HexColor('#f0f0f0')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#90EE90')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
        ]))
        
        elements.append(resumo_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Indicadores
        consumo_medio = CalculosFinanceiros.consumo_medio(veiculo_id)
        custo_km = CalculosFinanceiros.custo_por_km(veiculo_id)
        previsao = CalculosFinanceiros.previsao_manutencao(veiculo_id)
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2ca02c'),
            spaceAfter=10
        )
        
        elements.append(Paragraph("INDICADORES DE PERFORMANCE", heading_style))
        
        indicadores_data = [
            ['Indicador', 'Valor'],
            ['Consumo Médio', f"{consumo_medio} km/l" if consumo_medio else 'N/A'],
            ['Custo por KM', f"R$ {custo_km:.4f}"],
            ['Previsão Manutenção Mensal', f"R$ {previsao['previsao_proxima_manutencao']:.2f}"],
            ['Previsão Manutenção Anual', f"R$ {previsao['previsao_anual']:.2f}"],
            ['Confiança da Previsão', previsao['confianca'].upper()]
        ]
        
        indicadores_table = Table(indicadores_data, colWidths=[3 * inch, 3 * inch])
        indicadores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ca02c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        
        elements.append(indicadores_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Gastos mês a mês
        gastos_mes = CalculosFinanceiros.gastos_por_mes(veiculo_id, ultimos_meses=6)
        
        elements.append(Paragraph("GASTOS ÚLTIMOS 6 MESES", heading_style))
        
        gastos_data = [
            ['Mês', 'Combustível (R$)', 'Manutenção (R$)', 'Total (R$)']
        ]
        
        for g in gastos_mes:
            gastos_data.append([
                g['mes'],
                f"{g['combustivel']:.2f}",
                f"{g['manutencao']:.2f}",
                f"{g['total']:.2f}"
            ])
        
        gastos_table = Table(gastos_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        gastos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff7f0e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
             [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        
        elements.append(gastos_table)
        
        # Footer
        elements.append(Spacer(1, 0.5 * inch))
        footer = Paragraph(
            f"<i>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</i>",
            styles['Normal']
        )
        elements.append(footer)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def gerar_csv_gastos(veiculo_id=None):
        """Gera CSV com todos os gastos"""
        
        buffer = BytesIO()
        # Usar TextIOWrapper para compatibilidade com Python 3
        from io import TextIOWrapper
        text_buffer = TextIOWrapper(buffer, encoding='utf-8', newline='')
        writer = csv.writer(text_buffer)
        
        # Cabeçalho
        writer.writerow(['Data', 'Categoria', 'Descrição', 'Valor (R$)', 'Veículo'])
        
        conn = get_conn()
        cur = conn.cursor()
        
        # Combustível
        query_comb = """
            SELECT 
                c.data_abastecimento,
                'Combustível',
                'Abastecimento ' || c.quantidade_litros || 'L em ' || c.placa,
                c.valor_total,
                v.placa
            FROM combustivel c
            JOIN veiculos v ON c.veiculo_id = v.id
            WHERE 1=1
        """
        params = []
        
        if veiculo_id:
            query_comb += " AND c.veiculo_id=?"
            params.append(veiculo_id)
        
        cur.execute(query_comb, params)
        for row in cur.fetchall():
            writer.writerow([row[0], row[1], row[2], f"{row[3]:.2f}", row[4]])
        
        # Manutenção
        query_manut = """
            SELECT 
                m.data_manutencao,
                'Manutenção',
                m.nome_peca,
                (CAST(COALESCE(m.valor_peca, 0) AS REAL) + CAST(COALESCE(m.mao_de_obra, 0) AS REAL)),
                v.placa
            FROM manutencao m
            JOIN veiculos v ON m.veiculo_id = v.id
            WHERE 1=1
        """
        params = []
        
        if veiculo_id:
            query_manut += " AND m.veiculo_id=?"
            params.append(veiculo_id)
        
        cur.execute(query_manut, params)
        for row in cur.fetchall():
            writer.writerow([row[0], row[1], row[2], f"{row[3]:.2f}", row[4]])
        
        # Transações (Multas, Documentos, etc)
        query_trans = """
            SELECT 
                t.data_transacao,
                t.categoria,
                t.descricao,
                t.valor,
                v.placa
            FROM transacoes_veiculo t
            JOIN veiculos v ON t.veiculo_id = v.id
            WHERE 1=1
        """
        params = []
        
        if veiculo_id:
            query_trans += " AND t.veiculo_id=?"
            params.append(veiculo_id)
        
        cur.execute(query_trans, params)
        for row in cur.fetchall():
            writer.writerow([row[0], row[1], row[2], f"{row[3]:.2f}", row[4]])
        
        conn.close()
        
        text_buffer.flush()
        buffer.seek(0)
        return buffer
