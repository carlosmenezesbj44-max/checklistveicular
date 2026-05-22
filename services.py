import os
import unicodedata
from datetime import datetime
from PIL import Image
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from db import get_conn
from config import ANEXOS_DIR

# Itens padrão (ajuste conforme necessário)
ITENS_CARRO = [
    "Farol Esq.", "Farol Dir.", "Pisca Esq.", "Pisca Dir.",
    "Lanterna Esq.", "Lanterna Dir.", "Luz de ré", "Luz de freio",
    "Retrovisor Esq.", "Retrovisor Dir.", "Pneus Dianteiros", "Pneus Traseiros",
    "Estepe", "Triângulo", "Macaco", "Chave de roda", "Limpador de para-brisa",
    "Vidros", "Lataria", "Interior", "Fluido de freio", "Água do Carro"
]

ITENS_MOTO = [
    "Farol", "Pisca Esq.", "Pisca Dir.", "Lanterna", "Luz de freio",
    "Retrovisor Esq.", "Retrovisor Dir.", "Pneu Dianteiro", "Pneu Traseiro",
    "Corrente", "Freio Dianteiro", "Freio Traseiro", "Manete de Câmbio", 
    "Manopla Acelerador", "Lataria", "Assento", "Fluido de freio", 
    "Sistema de Arrefecimento", "Capacete (visual)", "Espelho Retrovisor"
]

VEICULOS_CARRO = [
    "Sedan", "SUV", "Hatch", "Picape", "Minivan", "Perua", "Esportivo", 
    "Cupé", "Conversível", "Blindado", "Utilitário"
]

VEICULOS_MOTO = [
    "Street", "Esportiva", "Naked", "Cruiser", "Trail", "Scooter", 
    "Chopper", "Quadriciclo", "Triciclo", "Motocicleta"
]

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


STATUS_OK = "ok"
STATUS_ATENCAO = "atencao"
STATUS_CRITICO = "critico"
STATUS_NAO_VERIFICADO = "nao_verificado"

STATUS_META = {
    STATUS_OK: {"label": "OK", "score": 100},
    STATUS_ATENCAO: {"label": "Atenção", "score": 65},
    STATUS_CRITICO: {"label": "Crítico", "score": 25},
    STATUS_NAO_VERIFICADO: {"label": "Não verificado", "score": 45},
}

# Itens com impacto mais alto na segurança operacional.
CRITICAL_ITEM_KEYWORDS = (
    "freio",
    "pneu",
    "estepe",
    "farol",
    "lanterna",
    "pisca",
    "luz",
    "fluido",
    "oleo",
    "agua",
    "arrefecimento",
    "retrovisor",
)


def _normalize_text(text):
    base = str(text or "").strip().lower()
    normalized = unicodedata.normalize("NFKD", base)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _is_critical_item(item_name):
    normalized_name = _normalize_text(item_name)
    return any(keyword in normalized_name for keyword in CRITICAL_ITEM_KEYWORDS)


def classify_checklist_status(raw_status):
    status = _normalize_text(raw_status)
    if not status:
        return STATUS_NAO_VERIFICADO

    if status in {"ok", "normal", "conforme", "verificado"}:
        return STATUS_OK

    if status in {"danificado", "rasgo", "bolha", "nao ok", "nao-ok", "critico", "falta", "vazando", "vazamento", "nao funciona"}:
        return STATUS_CRITICO

    if status in {"desgastado", "calibrar", "baixo", "alto", "queimada", "nao tem", "regular", "ajustar"}:
        return STATUS_ATENCAO

    if any(token in status for token in ("critic", "danific", "rasg", "bolh", "falta", "vaz")):
        return STATUS_CRITICO

    if any(token in status for token in ("desgast", "calibr", "baix", "alto", "queim", "nao tem", "regular")):
        return STATUS_ATENCAO

    return STATUS_ATENCAO


def avaliar_itens_checklist(itens):
    total_weight = 0
    weighted_score = 0
    itens_ok = 0
    itens_atencao = 0
    itens_criticos = 0
    itens_nao_verificados = 0

    for item in itens or []:
        nome_item = item.get("nome_item", "")
        status_raw = item.get("status", "")
        status_tipo = classify_checklist_status(status_raw)
        status_score = STATUS_META[status_tipo]["score"]
        weight = 1.8 if _is_critical_item(nome_item) else 1.0

        total_weight += weight
        weighted_score += status_score * weight

        if status_tipo == STATUS_OK:
            itens_ok += 1
        elif status_tipo == STATUS_ATENCAO:
            itens_atencao += 1
        elif status_tipo == STATUS_CRITICO:
            itens_criticos += 1
        else:
            itens_nao_verificados += 1

    pontuacao = round(weighted_score / total_weight) if total_weight else 0

    if pontuacao >= 85:
        risco = "Baixo"
    elif pontuacao >= 70:
        risco = "Moderado"
    elif pontuacao >= 50:
        risco = "Alto"
    else:
        risco = "Crítico"

    return {
        "total_itens": len(itens or []),
        "pontuacao": pontuacao,
        "risco": risco,
        "itens_ok": itens_ok,
        "itens_atencao": itens_atencao,
        "itens_criticos": itens_criticos,
        "itens_nao_verificados": itens_nao_verificados,
    }


def _is_allowed(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXT


def _save_file_storage(file_storage, prefix="file"):
    """
    Salva arquivo em ANEXOS_DIR com nome sanitizado e timestamp.
    Retorna (filename, thumb_filename) — nomes relativos (não caminhos absolutos).
    """
    if not file_storage:
        return None, None
    filename = getattr(file_storage, "filename", None)
    if not filename:
        return None, None

    filename_secure = secure_filename(filename)
    if not _is_allowed(filename_secure):
        return None, None

    # Garantir que o diretório existe
    try:
        os.makedirs(ANEXOS_DIR, exist_ok=True)
    except Exception as e:
        print(f"Erro ao criar diretório de anexos: {e}")
        return None, None

    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    base, ext = os.path.splitext(filename_secure)
    safe_name = f"{prefix}_{ts}_{base}{ext}"
    dest_path = os.path.join(ANEXOS_DIR, safe_name)

    # salva arquivo
    try:
        file_storage.save(dest_path)
        print(f"Arquivo salvo com sucesso: {dest_path}")
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")
        return None, None

    # gera thumbnail otimizada
    thumb_name = None
    try:
        img = Image.open(dest_path)
        img.thumbnail((1200, 1200))
        thumb_base = f"thumb_{safe_name}"
        thumb_path = os.path.join(ANEXOS_DIR, thumb_base)
        img.save(thumb_path, optimize=True, quality=85)
        thumb_name = thumb_base
        print(f"Thumbnail gerado: {thumb_path}")
    except Exception as e:
        print(f"Erro ao gerar thumbnail: {e}")
        thumb_name = None

    return safe_name, thumb_name


def salvar_checklist(form, files):
    """
    Salva veículo e itens no banco. Espera campos:
      - tipo, condutor, placa, modelo, quilometragem, observacoes, foto_carro
      - status_<idx>, coment_<idx>, foto_<idx>, itemname_<idx>
    Retorna id do veículo salvo.
    """
    conn = get_conn()
    cur = conn.cursor()

    tipo = form.get("tipo") or "Carro"
    condutor = form.get("condutor")
    placa = form.get("placa")
    modelo = form.get("modelo")
    quilometragem = form.get("quilometragem")
    # campos novos para troca de óleo
    oleo_data = form.get("oleo_data")
    oleo_km = form.get("oleo_km")
    # Sanitiza oleo_km para armazenar apenas dígitos (evita letras e formatações)
    def _digits_only(v):
        try:
            s = str(v or "").strip()
            nums = ''.join(ch for ch in s if ch.isdigit())
            return nums if nums else None
        except Exception:
            return None
    oleo_km = _digits_only(oleo_km)
    observacoes = form.get("observacoes")

    # Complementos vindos do painel visual de combustível.
    combustivel_tipos = form.getlist("combustivel_tipo")
    combustivel_nivel = form.get("combustivel_nivel")
    extras_combustivel = []
    if combustivel_tipos:
        extras_combustivel.append("Combustíveis: " + ", ".join(combustivel_tipos))
    if combustivel_nivel not in (None, ""):
        try:
            nivel = int(float(str(combustivel_nivel).strip()))
            nivel = max(0, min(100, nivel))
            extras_combustivel.append(f"Tanque: {nivel}%")
        except Exception:
            pass
    if extras_combustivel:
        bloco = " | ".join(extras_combustivel)
        observacoes = f"{observacoes} | {bloco}" if observacoes else bloco

    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    foto_carro_file = files.get("foto_carro")
    foto_carro_name, foto_thumb = _save_file_storage(foto_carro_file, prefix="veic")

    cur.execute("""
        INSERT INTO veiculos (condutor, placa, modelo, data, quilometragem, observacoes, foto_carro, tipo, oleo_data, oleo_km)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (condutor, placa, modelo, data, quilometragem, observacoes, foto_carro_name, tipo, oleo_data, oleo_km))
    veic_id = cur.lastrowid

    # percorre status_* e coleta itens com problema
    itens_problema = []
    tem_problemas = False
    
    for key in list(form.keys()):
        if key.startswith("status_"):
            idx = key.split("_", 1)[1]
            status = form.get(key)
            comentario = form.get(f"coment_{idx}") or ""
            nome_item = form.get(f"itemname_{idx}") or f"Item {idx}"
            file_field = files.get(f"foto_{idx}")
            caminho_foto, caminho_thumb = _save_file_storage(file_field, prefix=f"item_{idx}")
            cur.execute("""
                INSERT INTO itens_checklist (veiculo_id, nome_item, status, comentario, caminho_foto, caminho_thumb)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (veic_id, nome_item, status, comentario, caminho_foto, caminho_thumb))
            
            # Coleta itens com problema com classificação unificada de risco
            status_tipo = classify_checklist_status(status)
            if status_tipo in (STATUS_ATENCAO, STATUS_CRITICO):
                itens_problema.append({
                    'nome_item': nome_item,
                    'comentario': comentario
                })
                tem_problemas = True

    # Criar registro automático de manutenção para o checklist salvo
    # Se houver problemas, criar com status 'em_analise', senão 'pendente'
    try:
        quilometragem = form.get("quilometragem") or 0
        status_manutencao = 'em_analise' if tem_problemas else 'pendente'
        observacoes = 'Checklist de inspeção veicular com problemas detectados' if tem_problemas else 'Checklist de inspeção veicular'
        
        cur.execute("""
            INSERT INTO manutencao 
            (veiculo_id, nome_peca, data_manutencao, quilometragem_atual, status, observacoes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (veic_id, "Checklist Inicial", data, quilometragem, status_manutencao, observacoes))
    except Exception as e:
        print(f"Aviso: Erro ao criar manutenção inicial: {e}")
    
    conn.commit()
    conn.close()
    
    # Gera manutencoes sugeridas se houver problemas
    if itens_problema:
        try:
            from manutencao_sugerida import gerar_manutencao_sugerida
            gerar_manutencao_sugerida(veic_id, veic_id, itens_problema)
        except Exception as e:
            print(f"Erro ao gerar manutenção sugerida: {e}")
    
    return veic_id


def listar_historico(placa=None, data_ini=None, data_fim=None):
    conn = get_conn()
    cur = conn.cursor()
    # Modificado para mostrar apenas veículos que têm itens de checklist
    query = """
        SELECT DISTINCT v.id, v.condutor, v.placa, v.modelo, v.data, v.quilometragem, v.tipo 
        FROM veiculos v
        INNER JOIN itens_checklist i ON v.id = i.veiculo_id
        WHERE 1=1
    """
    params = []
    if placa:
        query += " AND v.placa LIKE ?"
        params.append(f"%{placa}%")
    if data_ini:
        try:
            d = datetime.strptime(data_ini, "%d/%m/%Y").strftime("%Y-%m-%d")
            query += " AND date(substr(v.data,7,4)||'-'||substr(v.data,4,2)||'-'||substr(v.data,1,2)) >= date(?)"
            params.append(d)
        except Exception:
            pass
    if data_fim:
        try:
            d = datetime.strptime(data_fim, "%d/%m/%Y").strftime("%Y-%m-%d")
            query += " AND date(substr(v.data,7,4)||'-'||substr(v.data,4,2)||'-'||substr(v.data,1,2)) <= date(?)"
            params.append(d)
        except Exception:
            pass
    query += " ORDER BY v.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obter_registro(veiculo_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM veiculos WHERE id = ?", (veiculo_id,))
    v = cur.fetchone()
    if not v:
        conn.close()
        return None
    cur.execute("SELECT * FROM itens_checklist WHERE veiculo_id = ?", (veiculo_id,))
    itens = cur.fetchall()
    conn.close()
    reg = dict(v)
    reg["itens"] = [dict(i) for i in itens]
    # Cálculo simples para alerta de troca de óleo (6.000 km)
    def _to_int(val):
        try:
            s = str(val or "")
            nums = ''.join(ch for ch in s if ch.isdigit())
            return int(nums) if nums else None
        except Exception:
            return None

    try:
        km_atual = _to_int(reg.get('quilometragem'))
        km_oleo = _to_int(reg.get('oleo_km'))
        if km_atual is not None and km_oleo is not None:
            diff = km_atual - km_oleo
            reg['oleo_diff'] = diff
            reg['oleo_due_in'] = max(0, 6000 - diff)
            reg['oleo_alert'] = diff >= 6000
        else:
            reg['oleo_diff'] = None
            reg['oleo_due_in'] = None
            reg['oleo_alert'] = False
    except Exception:
        reg['oleo_diff'] = None
        reg['oleo_due_in'] = None
        reg['oleo_alert'] = False
    return reg


def gerar_pdf_registro(registro, caminho_saida):
    """
    Gera um PDF com:
      - Cabeçalho com dados do veículo
      - Foto principal do veículo (se existir)
      - Lista de itens com status, comentário e miniatura da foto (thumb ou foto)
      - Duas linhas de assinatura ao final: quem realizou o checklist e quem estava com o veículo
    Projetado para visualização em celular: imagens otimizadas e layout vertical.
    """
    width, height = A4
    margin = 40
    y = height - margin

    c = canvas.Canvas(caminho_saida, pagesize=A4)
    c.setTitle(f"Checklist_{registro.get('placa','sem_placa')}")

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, y, "Checklist Veicular")
    c.setFont("Helvetica", 10)
    y -= 22
    c.drawString(margin, y, f"ID: {registro.get('id')}")
    c.drawString(margin + 200, y, f"Data: {registro.get('data') or '-'}")
    y -= 16
    c.drawString(margin, y, f"Placa: {registro.get('placa') or '-'}")
    c.drawString(margin + 200, y, f"Condutor: {registro.get('condutor') or '-'}")
    y -= 16
    c.drawString(margin, y, f"Modelo: {registro.get('modelo') or '-'}")
    c.drawString(margin + 200, y, f"KM: {registro.get('quilometragem') or '-'}")
    y -= 20

    # Foto principal do veículo (se existir) - otimizada para celular (não ocupa página inteira)
    foto_carro = registro.get("foto_carro")
    if foto_carro:
        foto_path = os.path.join(ANEXOS_DIR, foto_carro)
        if os.path.exists(foto_path):
            try:
                max_width = width - 2 * margin
                max_height = 200  # mantém razoável para leitura em celular
                img = Image.open(foto_path)
                img_w, img_h = img.size
                ratio = min(max_width / img_w, max_height / img_h, 1)
                draw_w = img_w * ratio
                draw_h = img_h * ratio
                img_reader = ImageReader(foto_path)
                c.drawImage(img_reader, margin, y - draw_h, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')
                y -= (draw_h + 12)
            except Exception:
                y -= 12
        else:
            y -= 12
    else:
        y -= 6

    # Observações (se houver)
    obs = registro.get("observacoes")
    if obs:
        c.setFont("Helvetica-Oblique", 9)
        text_obj = c.beginText(margin, y)
        text_obj.textLines(f"Observações: {obs}")
        c.drawText(text_obj)
        y -= (12 * (obs.count("\n") + 1) + 6)

    # Espaço antes da lista de itens
    y -= 6
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, "Itens")
    y -= 16
    c.setFont("Helvetica", 10)

    # Layout para itens com miniaturas (pensado para celular: uma coluna)
    thumb_size = 80
    gap = 8

    for item in registro.get("itens", []):
        nome = item.get("nome_item") or "-"
        status = item.get("status") or "-"
        comentario = item.get("comentario") or ""
        thumb = item.get("caminho_thumb") or item.get("caminho_foto")

        # calcula espaço necessário
        needed_height = max(thumb_size, 36) + 12
        # reserva espaço extra para assinaturas: se faltar, cria nova página
        if y - needed_height < margin + 120:
            c.showPage()
            y = height - margin
            c.setFont("Helvetica", 10)

        # desenha miniatura (se existir)
        draw_w = draw_h = 0
        if thumb:
            thumb_path = os.path.join(ANEXOS_DIR, thumb)
            if os.path.exists(thumb_path):
                try:
                    img = Image.open(thumb_path)
                    img_w, img_h = img.size
                    ratio = min(thumb_size / img_w, thumb_size / img_h, 1)
                    draw_w = img_w * ratio
                    draw_h = img_h * ratio
                    img_reader = ImageReader(thumb_path)
                    c.drawImage(img_reader, margin, y - draw_h, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')
                except Exception:
                    draw_w = draw_h = 0

        # texto do item ao lado da miniatura
        text_x = margin + (draw_w + gap if draw_w else 0)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(text_x, y - 2, nome)
        c.setFont("Helvetica", 9)
        c.drawString(text_x, y - 16, f"Status: {status}")
        if comentario:
            # quebra simples de comentário para caber
            max_chars = 90
            lines = []
            words = comentario.split()
            line = ""
            for w in words:
                test = (line + " " + w).strip()
                if len(test) > max_chars:
                    lines.append(line)
                    line = w
                else:
                    line = test
            if line:
                lines.append(line)
            c.setFont("Helvetica-Oblique", 8)
            ly = y - 30
            for i, ln in enumerate(lines[:3]):  # limita a 3 linhas por item
                c.drawString(text_x, ly - (i * 10), ln)
            used_h = max(draw_h, 30 + (len(lines[:3]) * 10))
            y -= (used_h + 12)
        else:
            used_h = max(draw_h, 30)
            y -= (used_h + 12)

    # Antes de inserir as assinaturas, garante espaço na página atual
    signature_block_height = 80  # espaço reservado para as duas linhas de assinatura
    if y - signature_block_height < margin:
        c.showPage()
        y = height - margin
        c.setFont("Helvetica", 10)

    # Linha separadora antes das assinaturas
    y -= 10
    c.setStrokeColorRGB(0.6, 0.6, 0.6)
    c.setLineWidth(0.5)
    c.line(margin, y, width - margin, y)
    y -= 18

    # Desenha duas áreas de assinatura lado a lado
    sig_width = (width - 2 * margin - 20) / 2  # 20 px gap entre assinaturas
    left_x = margin
    right_x = margin + sig_width + 20

    line_y = y - 20  # posição da linha de assinatura

    # Linha para quem realizou o checklist
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.line(left_x, line_y, left_x + sig_width, line_y)
    c.setFont("Helvetica", 9)
    c.drawString(left_x, line_y - 14, "Assinatura (quem realizou o checklist)")

    # Linha para quem estava com o veículo
    c.line(right_x, line_y, right_x + sig_width, line_y)
    c.drawString(right_x, line_y - 14, "Assinatura (quem estava com o veículo)")

    # Espaço final
    y = line_y - 40

    c.showPage()
    c.save()


def limpar_arquivos_orfaos(dry_run=True, limit=None):
    """
    Retorna lista de arquivos órfãos. Se dry_run=False, remove os arquivos.
    limit opcional limita quantos arquivos remover/listar.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT foto_carro FROM veiculos
        UNION
        SELECT caminho_foto FROM itens_checklist
        UNION
        SELECT caminho_thumb FROM itens_checklist
    """)
    referenced = {row[0] for row in cur.fetchall() if row[0]}
    conn.close()

    all_files = sorted(os.listdir(ANEXOS_DIR))
    orphans = [f for f in all_files if f not in referenced]
    if limit:
        orphans = orphans[:limit]

    if dry_run:
        return {"orphans": orphans, "count": len(orphans)}
    removed = []
    errors = []
    for fname in orphans:
        path = os.path.join(ANEXOS_DIR, fname)
        try:
            os.remove(path)
            removed.append(fname)
        except Exception as e:
            errors.append({"file": fname, "error": str(e)})
    return {"removed": removed, "errors": errors, "removed_count": len(removed)}


# ===================== FUNÇÕES DE COMBUSTÍVEL =====================

def salvar_combustivel(form, files):
    """Salva registro de combustível no banco de dados"""
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        placa = form.get("placa", "").strip()
        tipo_veiculo = form.get("tipo_veiculo", "").strip()
        data_abastecimento = form.get("data_abastecimento", "").strip()
        quilometragem = form.get("quilometragem", "").strip()
        quantidade_litros = form.get("quantidade_litros", "").strip()
        valor_total = form.get("valor_total", "").strip()
        observacoes = form.get("observacoes", "").strip()
        
        # Validação básica
        if not placa:
            raise ValueError("Placa do veículo é obrigatória")
        if not data_abastecimento:
            raise ValueError("Data de abastecimento é obrigatória")
        if not quantidade_litros:
            raise ValueError("Quantidade de litros é obrigatória")
        if not valor_total:
            raise ValueError("Valor total é obrigatório")
        
        # Buscar veiculo_id baseado na placa
        cur.execute("SELECT id FROM veiculos WHERE placa = ?", (placa,))
        veiculo = cur.fetchone()
        veiculo_id = veiculo[0] if veiculo else None
        
        # Salvar foto se houver
        foto_nome, _ = _save_file_storage(files.get("nota_fiscal_foto"), prefix="combustivel")
        
        print(f"Salvando combustível - Placa: {placa}, Data: {data_abastecimento}, Litros: {quantidade_litros}, Valor: {valor_total}")
        
        cur.execute("""
            INSERT INTO combustivel (
                veiculo_id, placa, tipo_veiculo, data_abastecimento, 
                quilometragem, quantidade_litros, valor_total, observacoes, 
                nota_fiscal_foto, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            veiculo_id, placa, tipo_veiculo, data_abastecimento, 
            quilometragem, quantidade_litros, valor_total, observacoes, 
            foto_nome, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        combustivel_id = cur.lastrowid
        print(f"Combustível salvo com sucesso. ID: {combustivel_id}")
        return combustivel_id
        
    except ValueError as e:
        print(f"Erro de validação ao salvar combustível: {str(e)}")
        raise
    except Exception as e:
        print(f"Erro ao salvar combustível: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()


def listar_combustivel(placa=None, data_ini=None, data_fim=None, veiculo_id=None):
    """Lista registros de combustível com filtros"""
    conn = get_conn()
    cur = conn.cursor()
    
    query = "SELECT * FROM combustivel WHERE 1=1"
    params = []
    
    if placa:
        query += " AND placa LIKE ?"
        params.append(f"%{placa}%")
    if data_ini:
        query += " AND data_abastecimento >= ?"
        params.append(data_ini)
    if data_fim:
        query += " AND data_abastecimento <= ?"
        params.append(data_fim)
    if veiculo_id:
        query += " AND veiculo_id = ?"
        params.append(veiculo_id)
        
    query += " ORDER BY data_abastecimento DESC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    # Converter resultados para dict e normalizar tipos
    resultados = []
    for r in rows:
        reg = dict(r)
        # Garantir que valores numéricos são float
        if "quantidade_litros" in reg:
            try:
                val = reg["quantidade_litros"]
                if val:
                    # Limpar caracteres não numéricos exceto ponto e vírgula
                    clean_val = str(val).replace(',', '.').strip()
                    # Remover caracteres não numéricos exceto ponto
                    import re
                    clean_val = re.sub(r'[^\d.]', '', clean_val)
                    reg["quantidade_litros"] = float(clean_val) if clean_val else 0.0
                else:
                    reg["quantidade_litros"] = 0.0
            except (ValueError, TypeError):
                reg["quantidade_litros"] = 0.0

        if "valor_total" in reg:
            try:
                val = reg["valor_total"]
                if val:
                    # Limpar caracteres não numéricos exceto ponto e vírgula
                    clean_val = str(val).replace(',', '.').strip()
                    # Remover caracteres não numéricos exceto ponto
                    import re
                    clean_val = re.sub(r'[^\d.]', '', clean_val)
                    reg["valor_total"] = float(clean_val) if clean_val else 0.0
                else:
                    reg["valor_total"] = 0.0
            except (ValueError, TypeError):
                reg["valor_total"] = 0.0
        
        resultados.append(reg)
    
    return resultados


def obter_combustivel(combustivel_id):
    """Obtém um registro específico de combustível"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM combustivel WHERE id = ?", (combustivel_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def deletar_combustivel(combustivel_id):
    """Deleta um registro de combustível"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM combustivel WHERE id = ?", (combustivel_id,))
    conn.commit()
    conn.close()


def atualizar_combustivel(combustivel_id, form, files=None):
    """Atualiza um registro de combustível"""
    conn = get_conn()
    cur = conn.cursor()
    
    placa = form.get("placa")
    tipo_veiculo = form.get("tipo_veiculo")
    data_abastecimento = form.get("data_abastecimento")
    quilometragem = form.get("quilometragem")
    quantidade_litros = form.get("quantidade_litros")
    valor_total = form.get("valor_total")
    observacoes = form.get("observacoes")
    
    query = """
        UPDATE combustivel 
        SET placa = ?, tipo_veiculo = ?, data_abastecimento = ?, 
            quilometragem = ?, quantidade_litros = ?, valor_total = ?, 
            observacoes = ?
    """
    params = [placa, tipo_veiculo, data_abastecimento, quilometragem, quantidade_litros, valor_total, observacoes]
    
    # Salvar nova foto se houver
    if files and files.get("nota_fiscal_foto"):
        foto_nome, _ = _save_file_storage(files.get("nota_fiscal_foto"), prefix="combustivel")
        if foto_nome:
            query += ", nota_fiscal_foto = ?"
            params.append(foto_nome)
            
    query += " WHERE id = ?"
    params.append(combustivel_id)
    
    try:
        cur.execute(query, params)
        conn.commit()
    finally:
        conn.close()


def calcular_kmL(veiculo_id, quantidade_litros, km_percorrido):
    """Calcula km/L"""
    try:
        return km_percorrido / float(quantidade_litros) if float(quantidade_litros) > 0 else 0
    except:
        return 0


def calcular_custo_km(valor_total, km_percorrido):
    """Calcula custo por km"""
    try:
        return valor_total / float(km_percorrido) if float(km_percorrido) > 0 else 0
    except:
        return 0


def calcular_tempo_medio_manutencao(veiculo_id):
    """Calcula tempo médio entre manutenções"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(CAST((julianday(m2.data_manutencao) - julianday(m1.data_manutencao)) AS REAL))
        FROM manutencao m1
        JOIN manutencao m2 ON m1.veiculo_id = m2.veiculo_id AND julianday(m2.data_manutencao) > julianday(m1.data_manutencao)
        WHERE m1.veiculo_id = ?
        GROUP BY m1.id
    """, (veiculo_id,))
    result = cur.fetchone()
    conn.close()
    return {"tempo_km": result[0] if result and result[0] else 0}


def calcular_taxa_danificacao(veiculo_id):
    """Calcula taxa de danificação"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM itens_checklist WHERE veiculo_id = ? AND status = 'Danificado'", (veiculo_id,))
    danificados = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM itens_checklist WHERE veiculo_id = ?", (veiculo_id,))
    total = cur.fetchone()[0] or 0
    conn.close()
    taxa = (danificados / total * 100) if total > 0 else 0
    return {"taxa_danificacao": round(taxa, 2)}


def obter_todos_indicadores(veiculo_id):
    """Obtém todos os indicadores de um veículo"""
    return {
        "km_l": {"km_l": 0},
        "custo_km": {"custo_km": 0},
        "tempo_manutencao": calcular_tempo_medio_manutencao(veiculo_id),
        "taxa_danificacao": calcular_taxa_danificacao(veiculo_id),
    }


# ===================== FUNÇÕES DE CONDUTOR =====================

def salvar_condutor(nome, cpf, empresa_id):
    """Salva um novo condutor"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO condutores (nome, cpf, empresa_id)
            VALUES (?, ?, ?)
        """, (nome, cpf, empresa_id))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def listar_condutores(empresa_id=None, page=1, per_page=25):
    """Lista condutores com paginação"""
    conn = get_conn()
    cur = conn.cursor()

    # Contar total
    if empresa_id:
        cur.execute("SELECT COUNT(*) FROM condutores WHERE empresa_id = ?", (empresa_id,))
    else:
        cur.execute("SELECT COUNT(*) FROM condutores")
    total = cur.fetchone()[0]

    # Buscar com paginação
    offset = (page - 1) * per_page
    if empresa_id:
        cur.execute("SELECT * FROM condutores WHERE empresa_id = ? ORDER BY nome_completo ASC LIMIT ? OFFSET ?",
                   (empresa_id, per_page, offset))
    else:
        cur.execute("SELECT * FROM condutores ORDER BY nome_completo ASC LIMIT ? OFFSET ?",
                   (per_page, offset))

    rows = cur.fetchall()
    conn.close()

    # Calcular total de páginas
    total_pages = (total + per_page - 1) // per_page if total else 1

    return {
        'condutores': [dict(r) for r in rows],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    }


def obter_condutor(condutor_id):
    """Obtém um condutor específico"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM condutores WHERE id = ?", (condutor_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def adicionar_infracao(condutor_id, descricao, valor, data_infracao):
    """Adiciona uma infração"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO infracoes (condutor_id, descricao, valor, data_infracao)
            VALUES (?, ?, ?, ?)
        """, (condutor_id, descricao, valor, data_infracao))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def atualizar_infracao(infracao_id, descricao, valor, data_infracao):
    """Atualiza uma infração"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE infracoes
            SET descricao = ?, valor = ?, data_infracao = ?
            WHERE id = ?
        """, (descricao, valor, data_infracao, infracao_id))
        conn.commit()
    finally:
        conn.close()


def marcar_infracao_paga(infracao_id):
    """Marca uma infração como paga"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE infracoes SET pago = 1 WHERE id = ?", (infracao_id,))
        conn.commit()
    finally:
        conn.close()


def obter_infracao(infracao_id):
    """Obtém uma infração específica"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM infracoes WHERE id = ?", (infracao_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def listar_infracoes_empresa(empresa_id):
    """Lista infrações de uma empresa"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.* FROM infracoes i
        JOIN condutores c ON i.condutor_id = c.id
        WHERE c.empresa_id = ?
    """, (empresa_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def deletar_infracao(infracao_id):
    """Deleta uma infração"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM infracoes WHERE id = ?", (infracao_id,))
    conn.commit()
    conn.close()


def adicionar_treinamento(condutor_id, nome_treinamento, data_treinamento):
    """Adiciona um treinamento"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO treinamentos (condutor_id, nome_treinamento, data_treinamento)
            VALUES (?, ?, ?)
        """, (condutor_id, nome_treinamento, data_treinamento))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def desativar_condutor(condutor_id):
    """Desativa um condutor"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE condutores SET ativo = 0 WHERE id = ?", (condutor_id,))
        conn.commit()
    finally:
        conn.close()


def ativar_condutor(condutor_id):
    """Ativa um condutor"""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE condutores SET ativo = 1 WHERE id = ?", (condutor_id,))
        conn.commit()
    finally:
        conn.close()


# ===================== FUNÇÕES DE ML E ANÁLISE =====================

def prever_custo_veiculo(veiculo_id):
    """Prevê custo do veículo"""
    return {"custo_previsto": 0}


def avaliar_risco_falha_veiculo(veiculo_id):
    """Avalia risco de falha"""
    return {"risco": 0}


def treinar_modelo_ml_veiculo(veiculo_id):
    """Treina modelo ML para o veículo"""
    return {"status": "treinado"}


def obter_custo_por_rota(rota_id):
    """Obtém custo por rota"""
    return {"custo_rota": 0}


def obter_eficiencia_condutor(condutor_id):
    """Obtém eficiência do condutor"""
    return {"eficiencia": 0}


def obter_benchmarking_veiculos(empresa_id):
    """Obtém benchmarking de veículos"""
    return {"benchmark": {}}


def obter_benchmarking_condutores(empresa_id):
    """Obtém benchmarking de condutores"""
    return {"benchmark": {}}
