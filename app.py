import os
import math
import tempfile
import zipfile
import shutil
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    jsonify,
    send_from_directory,
    Response,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from db import init_db, get_conn
from models import User, Manutencao
from auth import auth_bp
from documentos import Documento, Alerta, obter_alertas_vencimento_documentos, obter_meses_vencimento_estado, VENCIMENTOS_POR_ESTADO
from functools import wraps
from services import (
    salvar_checklist,
    listar_historico,
    obter_registro,
    gerar_pdf_registro,
    ITENS_CARRO,
    ITENS_MOTO,
    VEICULOS_CARRO,
    VEICULOS_MOTO,
    limpar_arquivos_orfaos,
    salvar_combustivel,
    listar_combustivel,
    obter_combustivel,
    deletar_combustivel,
    atualizar_combustivel,
    calcular_kmL,
    calcular_custo_km,
    calcular_tempo_medio_manutencao,
    calcular_taxa_danificacao,
    obter_todos_indicadores,
    salvar_condutor,
    listar_condutores,
    obter_condutor,
    adicionar_infracao,
    atualizar_infracao,
    marcar_infracao_paga,
    obter_infracao,
    listar_infracoes_empresa,
    deletar_infracao,
    adicionar_treinamento,
    desativar_condutor,
    ativar_condutor,
    prever_custo_veiculo,
    avaliar_risco_falha_veiculo,
    treinar_modelo_ml_veiculo,
    obter_custo_por_rota,
    obter_eficiencia_condutor,
    obter_benchmarking_veiculos,
    obter_benchmarking_condutores,
)
from config import (
    ANEXOS_DIR,
    MAIL_SERVER,
    MAIL_PORT,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER,
    SECRET_KEY,
)

# Importações do módulo financeiro
from financeiro.services import CalculosFinanceiros
from financeiro.charts import ChartData
from financeiro.reports import RelatorioFinanceiro
from financeiro.alerts import AlertasFinanceiros
from financeiro.models import Multa, DocumentoFinanceiro, Transacao

# Importações do gerenciador de configurações
from config_manager import (
    ConfigManager,
    get_twilio_config,
    verify_twilio_connection,
)

# Inicializa DB (cria tabelas e índices)
init_db()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave")

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "warning"
login_manager.init_app(app)


# Decorators para proteção por role
def usuario_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if current_user.role not in ["usuario", "admin"]:
            flash("Acesso negado.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)

    return decorated_function


# Configuração do envio de e-mail
def send_email(subject, recipient, html_content):
    if not MAIL_SERVER or not MAIL_USERNAME or not MAIL_PASSWORD:
        print("Configuração de e-mail não encontrada. E-mail não enviado.")
        print(f"Assunto: {subject}")
        print(f"Para: {recipient}")
        print(f"Conteúdo: {html_content}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = MAIL_DEFAULT_SENDER
        msg["To"] = recipient

        part = MIMEText(html_content, "html")
        msg.attach(part)

        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# Registrar Blueprint de autenticação
app.register_blueprint(auth_bp, url_prefix="/")


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Acesso restrito a administradores", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)

    return decorated_function


def permission_required(feature_key, message="Você não tem permissão para acessar esta funcionalidade"):
    """Decorador para verificar permissões específicas"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))

            # Admin sempre tem acesso
            if current_user.is_admin:
                return f(*args, **kwargs)

            # Verificar permissão do usuário
            if not has_permission(feature_key):
                flash(message, "error")
                return redirect(url_for("dashboard"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def has_permission(feature_key):
    """Verifica se o usuário atual tem uma permissão específica baseada nos seus roles"""
    if not current_user.is_authenticated:
        return False

    # Admin sempre tem todas as permissões
    if current_user.is_admin:
        return True

    try:
        conn = get_conn()
        cur = conn.cursor()

        # Verificar se o usuário tem algum role que possui esta permissão
        cur.execute("""
            SELECT COUNT(*) FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            WHERE ur.user_id = ? AND rp.permission_key = ?
        """, (current_user.id, feature_key))

        result = cur.fetchone()
        conn.close()

        return result and result[0] > 0
    except Exception as e:
        print(f"Erro ao verificar permissão {feature_key}: {e}")
        return False


def table_exists(cur, table_name):
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cur.fetchone() is not None


def get_user_roles(user_id=None):
    """Retorna os roles de um usuário"""
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
    elif user_id is None:
        return []

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT r.id, r.name, r.display_name, r.description, r.color, r.icon
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = ?
            ORDER BY r.display_name
        """, (user_id,))

        roles = [dict(row) for row in cur.fetchall()]
        conn.close()

        return roles
    except Exception as e:
        print(f"Erro ao obter roles do usuário {user_id}: {e}")
        return []


def get_all_roles():
    """Retorna todos os roles disponíveis"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, display_name, description, color, icon, is_system_role
            FROM roles
            ORDER BY display_name
        """)

        roles = [dict(row) for row in cur.fetchall()]
        conn.close()

        return roles
    except Exception as e:
        print(f"Erro ao obter roles: {e}")
        return []


def assign_role_to_user(user_id, role_id, assigned_by=None):
    """Atribui um role a um usuário"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            INSERT OR IGNORE INTO user_roles (user_id, role_id, assigned_by)
            VALUES (?, ?, ?)
        """, (user_id, role_id, assigned_by or (current_user.id if current_user.is_authenticated else None)))

        conn.commit()
        conn.close()

        return True
    except Exception as e:
        print(f"Erro ao atribuir role {role_id} ao usuário {user_id}: {e}")
        return False


def remove_role_from_user(user_id, role_id):
    """Remove um role de um usuário"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute("""
            DELETE FROM user_roles
            WHERE user_id = ? AND role_id = ?
        """, (user_id, role_id))

        conn.commit()
        conn.close()

        return True
    except Exception as e:
        print(f"Erro ao remover role {role_id} do usuário {user_id}: {e}")
        return False


@app.context_processor
def inject_year():
    return {"current_year": datetime.now().year, "has_permission": has_permission}


@app.route("/")
def home():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_conn()
    cur = conn.cursor()

    # Total de checklists (veículos que possuem itens de checklist)
    cur.execute("""
        SELECT COUNT(DISTINCT v.id)
        FROM veiculos v
        JOIN itens_checklist i ON i.veiculo_id = v.id
    """)
    total_checklists = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM veiculos WHERE tipo='Carro'")
    total_carros = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM veiculos WHERE tipo='Moto'")
    total_motos = cur.fetchone()[0] or 0
    cur.execute(
        """
        SELECT COUNT(*) FROM itens_checklist
        WHERE status='Danificado' OR status IN ('Desgastado','Calibrar','Baixo','Alto')
    """
    )
    total_criticos = cur.fetchone()[0] or 0

    # Contabilizar apenas registros com veiculo existente
    cur.execute("SELECT COUNT(*) FROM combustivel c JOIN veiculos v ON v.id = c.veiculo_id")
    total_combustiveis = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(c.valor_total) FROM combustivel c JOIN veiculos v ON v.id = c.veiculo_id")
    total_gasto_combustivel = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM manutencao m JOIN veiculos v ON v.id = m.veiculo_id")
    total_manutencoes = cur.fetchone()[0] or 0
    cur.execute(
        "SELECT SUM(CAST(m.valor_peca AS REAL)) + SUM(CAST(m.mao_de_obra AS REAL)) FROM manutencao m JOIN veiculos v ON v.id = m.veiculo_id WHERE m.valor_peca IS NOT NULL OR m.mao_de_obra IS NOT NULL"
    )
    total_gasto_manutencao = cur.fetchone()[0] or 0

    cur.execute(
        """
        SELECT substr(data, 4, 2) || '/' || substr(data, 7, 4) as mes, COUNT(*) as qtd
        FROM veiculos
        WHERE data IS NOT NULL AND data <> ''
        GROUP BY mes
        ORDER BY substr(data, 7, 4) ASC, substr(data, 4, 2) ASC
    """
    )
    meses_rows = cur.fetchall()
    meses_labels = [r[0] for r in meses_rows]
    meses_data = [r[1] for r in meses_rows]

    cur.execute(
        """
        SELECT nome_item, COUNT(*) as qtd
        FROM itens_checklist
        WHERE status='Danificado' OR status IN ('Desgastado','Calibrar','Baixo','Alto')
        GROUP BY nome_item
        ORDER BY qtd DESC
        LIMIT 5
    """
    )
    criticos_rows = cur.fetchall()
    criticos_labels = [r[0] for r in criticos_rows]
    criticos_data = [r[1] for r in criticos_rows]

    cur.execute(
        """
        SELECT c.id, c.placa, c.tipo_veiculo, c.quantidade_litros, c.valor_total, c.data_abastecimento
        FROM combustivel c
        JOIN veiculos v ON v.id = c.veiculo_id
        ORDER BY data_abastecimento DESC
        LIMIT 5
    """
    )
    ultimos_combustiveis = [dict(r) for r in cur.fetchall()]

    cur.execute(
        """
        SELECT m.id, m.nome_peca, m.data_manutencao, m.valor_peca, m.mao_de_obra
        FROM manutencao m
        JOIN veiculos v ON v.id = m.veiculo_id
        ORDER BY data_manutencao DESC
        LIMIT 5
    """
    )
    ultimas_manutencoes = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT DISTINCT v.id, v.placa, v.condutor, v.modelo, v.tipo, v.data
        FROM veiculos v
        JOIN itens_checklist i ON i.veiculo_id = v.id
        ORDER BY v.data DESC
        LIMIT 5
    """)
    ultimos_checklists = [dict(r) for r in cur.fetchall()]

    conn.close()
    return render_template(
        "dashboard.html",
        total_checklists=total_checklists,
        total_carros=total_carros,
        total_motos=total_motos,
        total_criticos=total_criticos,
        total_combustiveis=total_combustiveis,
        total_gasto_combustivel=total_gasto_combustivel,
        total_manutencoes=total_manutencoes,
        total_gasto_manutencao=total_gasto_manutencao,
        meses_labels=meses_labels,
        meses_data=meses_data,
        criticos_labels=criticos_labels,
        criticos_data=criticos_data,
        ultimos_combustiveis=ultimos_combustiveis,
        ultimas_manutencoes=ultimas_manutencoes,
        ultimos_checklists=ultimos_checklists,
    )


@app.route("/api/analytics/checklists")
@login_required
def api_analytics_checklists():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            substr(data, 7, 4) || '-' || substr(data, 4, 2) as mes_ano,
            COUNT(*) as total_checklists,
            SUM(CASE WHEN EXISTS (
                SELECT 1 FROM itens_checklist 
                WHERE veiculo_id = veiculos.id 
                AND (status='Danificado' OR status IN ('Desgastado','Calibrar','Baixo','Alto'))
            ) THEN 1 ELSE 0 END) as com_criticos
        FROM veiculos
        WHERE data IS NOT NULL AND data <> ''
        GROUP BY mes_ano
        ORDER BY mes_ano ASC
    """
    )
    monthly_rows = cur.fetchall()

    monthly_stats = []
    for row in monthly_rows:
        total = row[1] or 0
        with_critical = row[2] or 0
        percentage = (with_critical / total * 100) if total > 0 else 0
        monthly_stats.append(
            {
                "mes_ano": row[0],
                "total": total,
                "com_criticos": with_critical,
                "percentual_criticos": round(percentage, 2),
            }
        )

    cur.execute(
        """
        SELECT 
            DATE(substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-01') as mes,
            COUNT(*) as qtd
        FROM veiculos
        WHERE data IS NOT NULL AND data <> ''
        GROUP BY DATE(substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-01')
        ORDER BY mes ASC
    """
    )
    trend_rows = cur.fetchall()
    trend_data = [{"mes": row[0], "quantidade": row[1]} for row in trend_rows]

    conn.close()

    return jsonify({"monthly_stats": monthly_stats, "trend": trend_data})


@app.route("/api/analytics/critical-items")
@login_required
def api_analytics_critical_items():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT COUNT(*) FROM itens_checklist
        WHERE status='Danificado' OR status IN ('Desgastado','Calibrar','Baixo','Alto')
    """
    )
    total_critical = cur.fetchone()[0] or 0

    cur.execute(
        """
        SELECT nome_item, COUNT(*) as qtd, 
               GROUP_CONCAT(status, ', ') as tipos
        FROM itens_checklist
        WHERE status='Danificado' OR status IN ('Desgastado','Calibrar','Baixo','Alto')
        GROUP BY nome_item
        ORDER BY qtd DESC
        LIMIT 15
    """
    )
    most_common_rows = cur.fetchall()
    most_common = [
        {"item": row[0], "ocorrencias": row[1], "tipos": row[2]}
        for row in most_common_rows
    ]

    cur.execute(
        """
        SELECT v.placa, v.modelo, COUNT(*) as qtd_criticos
        FROM itens_checklist ic
        JOIN veiculos v ON ic.veiculo_id = v.id
        WHERE ic.status='Danificado' OR ic.status IN ('Desgastado','Calibrar','Baixo','Alto')
        GROUP BY ic.veiculo_id
        ORDER BY qtd_criticos DESC
        LIMIT 10
    """
    )
    vehicles_critical_rows = cur.fetchall()
    vehicles_critical = [
        {"placa": row[0], "modelo": row[1], "quantidade": row[2]}
        for row in vehicles_critical_rows
    ]

    cur.execute(
        """
        SELECT 
            substr(v.data, 7, 4) || '-' || substr(v.data, 4, 2) as mes_ano,
            COUNT(*) as qtd_criticos
        FROM itens_checklist ic
        JOIN veiculos v ON ic.veiculo_id = v.id
        WHERE (ic.status='Danificado' OR ic.status IN ('Desgastado','Calibrar','Baixo','Alto'))
        AND v.data IS NOT NULL AND v.data <> ''
        GROUP BY mes_ano
        ORDER BY mes_ano ASC
    """
    )
    evolution_rows = cur.fetchall()
    evolution = [{"mes_ano": row[0], "quantidade": row[1]} for row in evolution_rows]

    cur.execute(
        """
        SELECT status, COUNT(*) as qtd
        FROM itens_checklist
        WHERE status='Danificado' OR status IN ('Desgastado','Calibrar','Baixo','Alto')
        GROUP BY status
        ORDER BY qtd DESC
    """
    )
    status_rows = cur.fetchall()
    status_dist = [{"status": row[0], "quantidade": row[1]} for row in status_rows]

    conn.close()

    return jsonify(
        {
            "total_criticos": total_critical,
            "itens_recorrentes": most_common,
            "veiculos_criticos": vehicles_critical,
            "evolucao_temporal": evolution,
            "distribuicao_status": status_dist,
        }
    )


@app.route("/api/critical-vehicles-details")
@login_required
def api_critical_vehicles_details():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT DISTINCT v.id, v.placa, v.modelo, v.condutor, v.tipo
        FROM itens_checklist ic
        JOIN veiculos v ON ic.veiculo_id = v.id
        WHERE ic.status='Danificado' OR ic.status IN ('Desgastado','Calibrar','Baixo','Alto')
        ORDER BY v.placa ASC
    """
    )

    veiculos_criticos = []
    for row in cur.fetchall():
        veiculo_id, placa, modelo, condutor, tipo = row

        cur.execute(
            """
            SELECT nome_item, status, COUNT(*) as qtd
            FROM itens_checklist
            WHERE veiculo_id = ? AND (status='Danificado' OR status IN ('Desgastado','Calibrar','Baixo','Alto'))
            GROUP BY nome_item, status
            ORDER BY nome_item ASC
        """,
            (veiculo_id,),
        )

        pecas_criticas = [
            {"nome": r[0], "status": r[1], "quantidade": r[2]} for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT COALESCE(SUM(CAST(valor_peca AS REAL)), 0) + COALESCE(SUM(CAST(mao_de_obra AS REAL)), 0)
            FROM manutencao
            WHERE veiculo_id = ?
        """,
            (veiculo_id,),
        )

        custo_total_manutencao = cur.fetchone()[0] or 0

        veiculos_criticos.append(
            {
                "id": veiculo_id,
                "placa": placa,
                "modelo": modelo,
                "condutor": condutor,
                "tipo": tipo,
                "pecas_criticas": pecas_criticas,
                "custo_total_manutencao": round(custo_total_manutencao, 2),
            }
        )

    conn.close()

    return jsonify({"veiculos_criticos": veiculos_criticos})


@app.route("/index")
@login_required
def index():
    pneus = [i for i in ITENS_CARRO if "Pneu" in i or "Pneus" in i or "Estepe" in i]
    fluidos = [i for i in ITENS_CARRO if "Fluido" in i or "Óleo" in i]
    return render_template(
        "index.html",
        itens_carro=ITENS_CARRO,
        itens_moto=ITENS_MOTO,
        veiculos_carro=VEICULOS_CARRO,
        veiculos_moto=VEICULOS_MOTO,
        pneus=pneus,
        fluidos=fluidos,
    )


@app.route("/salvar", methods=["POST"])
def salvar():
    try:
        veic_id = salvar_checklist(request.form, request.files)
        flash(f"Checklist salvo com sucesso! ID: {veic_id}", "success")
        return redirect(url_for("detalhes", veiculo_id=veic_id))
    except Exception as e:
        flash(f"Erro ao salvar checklist: {e}", "error")
        return redirect(url_for("index"))


@app.route("/historico", methods=["GET", "POST"])
@login_required
def historico():
    resultados = []
    try:
        if request.method == "POST":
            placa = request.form.get("placa")
            data_ini = request.form.get("data_ini")
            data_fim = request.form.get("data_fim")
            resultados = listar_historico(placa, data_ini, data_fim)
        else:
            resultados = listar_historico(None, None, None)
    except Exception as e:
        flash(f"Erro ao buscar histórico: {e}", "error")
    return render_template("historico.html", resultados=resultados)


@app.route("/veiculos-cadastrados")
@login_required
def veiculos_cadastrados():
    try:
        placa = (request.args.get("placa") or "").strip()
        modelo = (request.args.get("modelo") or "").strip()
        tipo = (request.args.get("tipo") or "").strip()
        condutor = (request.args.get("condutor") or "").strip()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM veiculos ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        resultados = [dict(r) for r in rows]
        def _match(val, q):
            return q.lower() in str(val or "").lower()
        if placa:
            resultados = [r for r in resultados if _match(r.get("placa"), placa)]
        if modelo:
            resultados = [r for r in resultados if _match(r.get("modelo"), modelo)]
        if tipo and tipo in ("Carro", "Moto"):
            resultados = [r for r in resultados if r.get("tipo") == tipo]
        if condutor:
            resultados = [r for r in resultados if _match(r.get("condutor"), condutor)]
        return render_template("veiculos_cadastrados.html", resultados=resultados)
    except Exception as e:
        flash(f"Erro ao buscar veículos: {e}", "error")
        return render_template("veiculos_cadastrados.html", resultados=[])


@app.route("/detalhes/<int:veiculo_id>")
@login_required
def detalhes(veiculo_id):
    reg = obter_registro(veiculo_id)
    if not reg:
        flash("Registro não encontrado.", "error")
        return redirect(url_for("historico"))

    indicadores = obter_todos_indicadores(veiculo_id)

    return render_template("detalhes.html", reg=reg, indicadores=indicadores)


@app.route("/checklist/editar/<int:veiculo_id>", methods=["GET", "POST"])
@login_required
def editar_checklist(veiculo_id):
    """Edita um checklist existente"""
    try:
        reg = obter_registro(veiculo_id)
        if not reg:
            flash("Checklist não encontrado.", "error")
            return redirect(url_for("historico"))
        
        if request.method == "POST":
            # Atualizar dados do veículo
            conn = get_conn()
            cur = conn.cursor()
            
            # Obter tipo do formulário (apenas admin pode mudar)
            novo_tipo = request.form.get('tipo')
            tipo_final = novo_tipo if current_user.is_admin else reg.get('tipo')
            
            # Atualizar informações básicas do veículo
            cur.execute("""
                UPDATE veiculos 
                SET placa=?, modelo=?, condutor=?, tipo=?, quilometragem=?, 
                    observacoes=?, oleo_data=?, oleo_km=?
                WHERE id=?
            """, (
                request.form.get('placa'),
                request.form.get('modelo') or reg.get('modelo'),
                request.form.get('condutor'),
                tipo_final,
                request.form.get('quilometragem'),
                request.form.get('observacoes'),
                request.form.get('oleo_data'),
                request.form.get('oleo_km'),
                veiculo_id
            ))
            
            # Atualizar itens do checklist
            itens = request.form.getlist('itens[]')
            comentarios = request.form.getlist('comentarios[]')
            
            # Limpar itens antigos
            cur.execute("DELETE FROM itens_checklist WHERE veiculo_id = ?", (veiculo_id,))
            
            # Adicionar itens atualizados
            for i, item in enumerate(itens):
                if item:
                    comentario = comentarios[i] if i < len(comentarios) else ""
                    cur.execute("""
                        INSERT INTO itens_checklist (veiculo_id, nome_item, status, comentario)
                        VALUES (?, ?, ?, ?)
                    """, (veiculo_id, item, "OK", comentario))
            
            conn.commit()
            conn.close()
            
            flash("Checklist atualizado com sucesso!", "success")
            return redirect(url_for("detalhes", veiculo_id=veiculo_id))
        
        # GET - Preparar dados para edição
        tipo_veiculo = reg.get('tipo', 'Carro')
        
        # Definir itens baseado no tipo do veículo
        itens_base = ITENS_CARRO if tipo_veiculo == 'Carro' else ITENS_MOTO
        
        # Filtrar pneus e fluidos do tipo específico
        pneus = [i for i in itens_base if "Pneu" in i or "Pneus" in i or "Estepe" in i]
        fluidos = [i for i in itens_base if "Fluido" in i or "Óleo" in i or "Água" in i]
        
        # Obter itens do checklist atual
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT nome_item, comentario FROM itens_checklist WHERE veiculo_id = ? ORDER BY id", (veiculo_id,))
        itens_atuais = cur.fetchall()
        conn.close()
        
        itens_dict = {item[0]: item[1] for item in itens_atuais}
        itens_disponibles = itens_base
        
        return render_template(
            "editar_checklist.html",
            reg=reg,
            itens_disponibles=itens_disponibles,
            itens_atuais=itens_dict,
            pneus=pneus,
            fluidos=fluidos,
            tipo_veiculo=tipo_veiculo,
            is_admin=current_user.is_admin
        )
        
    except Exception as e:
        flash(f"Erro ao editar checklist: {str(e)}", "error")
        return redirect(url_for("historico"))


@app.route("/checklist/deletar/<int:veiculo_id>", methods=["POST"])
@login_required
def deletar_checklist(veiculo_id):
    """Remove definitivamente o veículo e os itens do checklist associados"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Obter informações do veículo para confirmar
        cur.execute("SELECT placa FROM veiculos WHERE id = ?", (veiculo_id,))
        veiculo = cur.fetchone()
        
        if not veiculo:
            flash("Veículo não encontrado.", "error")
            return redirect(url_for("historico"))
        
        placa = veiculo[0]
        
        # Deletar dados relacionados (sem ON DELETE CASCADE no SQLite)
        if table_exists(cur, "itens_checklist"):
            cur.execute("DELETE FROM itens_checklist WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "combustivel"):
            cur.execute("DELETE FROM combustivel WHERE veiculo_id = ? OR placa = ?", (veiculo_id, placa))
        if table_exists(cur, "manutencao"):
            cur.execute("DELETE FROM manutencao WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "transacoes_veiculo"):
            cur.execute("DELETE FROM transacoes_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "historico_manutencao"):
            cur.execute("DELETE FROM historico_manutencao WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "notas_fiscais_veiculo"):
            cur.execute("DELETE FROM notas_fiscais_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "documentos_veiculo"):
            cur.execute("DELETE FROM documentos_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "alertas_veiculo"):
            cur.execute("DELETE FROM alertas_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "condutor_veiculo"):
            cur.execute("DELETE FROM condutor_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        # Por fim, deletar o veículo
        cur.execute("DELETE FROM veiculos WHERE id = ?", (veiculo_id,))
        
        conn.commit()
        conn.close()
        
        # Limpar arquivos órfãos
        try:
            limpar_arquivos_orfaos()
        except:
            pass
        
        flash(f"Veículo {placa} e checklist removidos com sucesso!", "success")
        return redirect(url_for("historico"))
        
    except Exception as e:
        flash(f"Erro ao deletar checklist: {str(e)}", "error")
        return redirect(url_for("historico"))


@app.route("/checklist/limpar/<int:veiculo_id>", methods=["POST"])
@login_required
def limpar_checklist(veiculo_id):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT placa FROM veiculos WHERE id = ?", (veiculo_id,))
        veiculo = cur.fetchone()
        if not veiculo:
            flash("Veículo não encontrado.", "error")
            return redirect(url_for("historico"))
        placa = veiculo[0]
        cur.execute("DELETE FROM itens_checklist WHERE veiculo_id = ?", (veiculo_id,))
        conn.commit()
        conn.close()
        try:
            limpar_arquivos_orfaos()
        except:
            pass
        flash(f"Checklist do veículo {placa} limpo com sucesso!", "success")
        return redirect(url_for("historico"))
    except Exception as e:
        flash(f"Erro ao limpar checklist: {str(e)}", "error")
        return redirect(url_for("historico"))


@app.route("/admin/veiculo/excluir-placa", methods=["POST"])
@permission_required("veiculos_excluir_placa", "Você não tem permissão para excluir veículo por placa")
def excluir_por_placa():
    """Exclui completamente um veículo e todos os vínculos a partir da placa"""
    try:
        placa = (request.form.get("placa") or "").strip().upper()
        if not placa:
            flash("Informe a placa para excluir.", "error")
            return redirect(url_for("dashboard"))
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM veiculos WHERE placa = ?", (placa,))
        row = cur.fetchone()
        if not row:
            conn.close()
            flash(f"Placa {placa} não encontrada.", "warning")
            return redirect(url_for("dashboard"))
        veiculo_id = row[0]
        if table_exists(cur, "combustivel"):
            cur.execute("DELETE FROM combustivel WHERE veiculo_id = ? OR placa = ?", (veiculo_id, placa))
        if table_exists(cur, "itens_checklist"):
            cur.execute("DELETE FROM itens_checklist WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "manutencao"):
            cur.execute("DELETE FROM manutencao WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "transacoes_veiculo"):
            cur.execute("DELETE FROM transacoes_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "historico_manutencao"):
            cur.execute("DELETE FROM historico_manutencao WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "notas_fiscais_veiculo"):
            cur.execute("DELETE FROM notas_fiscais_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "documentos_veiculo"):
            cur.execute("DELETE FROM documentos_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "alertas_veiculo"):
            cur.execute("DELETE FROM alertas_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        if table_exists(cur, "condutor_veiculo"):
            cur.execute("DELETE FROM condutor_veiculo WHERE veiculo_id = ?", (veiculo_id,))
        cur.execute("DELETE FROM veiculos WHERE id = ?", (veiculo_id,))
        conn.commit()
        conn.close()
        try:
            limpar_arquivos_orfaos()
        except:
            pass
        flash(f"Veículo {placa} e todos os registros associados foram removidos.", "success")
        return redirect(url_for("dashboard"))
    except Exception as e:
        flash(f"Erro ao excluir por placa: {str(e)}", "error")
        return redirect(url_for("dashboard"))

@app.route("/performance")
@login_required
def performance():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, placa, modelo, condutor, tipo
        FROM veiculos
        ORDER BY placa ASC
    """
    )

    veiculos_raw = cur.fetchall()
    conn.close()

    veiculos = []
    for row in veiculos_raw:
        veiculo_id, placa, modelo, condutor, tipo = row
        indicadores = obter_todos_indicadores(veiculo_id)

        if any(
            [
                indicadores["km_l"].get("km_l"),
                indicadores["custo_km"].get("custo_km"),
                indicadores["tempo_manutencao"].get("tempo_km"),
                indicadores["taxa_danificacao"].get("taxa_danificacao"),
            ]
        ):
            veiculos.append(
                {
                    "id": veiculo_id,
                    "placa": placa,
                    "modelo": modelo,
                    "condutor": condutor,
                    "tipo": tipo,
                    "indicadores": indicadores,
                }
            )

    return render_template("performance.html", veiculos=veiculos)


@app.route("/pdf/<int:veiculo_id>")
@login_required
def pdf(veiculo_id):
    reg = obter_registro(veiculo_id)
    if not reg:
        flash("Registro não encontrado.", "error")
        return redirect(url_for("historico"))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
    gerar_pdf_registro(reg, tmp.name)
    filename = f"checklist_{reg.get('placa','sem_placa')}_{(reg.get('data') or '').replace('/','-')}.pdf"
    return send_file(tmp.name, as_attachment=True, download_name=filename)


@app.route("/uploads/<path:filename>")
def uploads(filename):
    file_path = os.path.join(ANEXOS_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(ANEXOS_DIR, filename, as_attachment=False)
    else:
        return send_file("static/images/placeholder.svg", mimetype="image/svg+xml")


@app.route("/api/veiculos/listar")
@login_required
def api_veiculos_listar():
    """Endpoint para listar todos os veículos do checklist"""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, placa, modelo, tipo, condutor
        FROM veiculos
        ORDER BY placa ASC
    """
    )

    veiculos = []
    for row in cur.fetchall():
        veiculos.append(
            {
                "id": row[0],
                "placa": row[1],
                "modelo": row[2],
                "tipo": row[3],
                "condutor": row[4] or "Não definido",
            }
        )

    conn.close()
    return jsonify({"veiculos": veiculos})


# API com busca e paginação e contagem otimizada para críticos
@app.route("/api/veiculos")
@login_required
def api_veiculos():
    tipo = request.args.get("tipo")
    criticos = request.args.get("criticos")
    q = (request.args.get("q") or "").strip()
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    try:
        per_page = max(5, min(100, int(request.args.get("per_page", 10))))
    except ValueError:
        per_page = 10

    conn = get_conn()
    cur = conn.cursor()

    where_clauses = []
    params = []

    if tipo:
        where_clauses.append("v.tipo = ?")
        params.append(tipo)

    if q:
        where_clauses.append("(v.placa LIKE ? OR v.condutor LIKE ? OR v.modelo LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # Conta total
    if criticos == "1":
        crit_query = f"""
            SELECT COUNT(DISTINCT v.id) FROM veiculos v
            {where_sql and 'WHERE ' + ' AND '.join(where_clauses) or ''}
            AND EXISTS (
                SELECT 1 FROM itens_checklist it
                WHERE it.veiculo_id = v.id
                AND (it.status = 'Danificado' OR it.status IN ('Desgastado','Calibrar','Baixo','Alto'))
            )
        """
        # Ajuste: se where_sql vazio, crit_query terá 'AND EXISTS' sem WHERE; corrigimos montando condicionalmente
        if where_clauses:
            crit_query = f"""
                SELECT COUNT(DISTINCT v.id) FROM veiculos v
                WHERE {' AND '.join(where_clauses)}
                AND EXISTS (
                    SELECT 1 FROM itens_checklist it
                    WHERE it.veiculo_id = v.id
                    AND (it.status = 'Danificado' OR it.status IN ('Desgastado','Calibrar','Baixo','Alto'))
                )
            """
            cur.execute(crit_query, params)
        else:
            crit_query = """
                SELECT COUNT(DISTINCT v.id) FROM veiculos v
                WHERE EXISTS (
                    SELECT 1 FROM itens_checklist it
                    WHERE it.veiculo_id = v.id
                    AND (it.status = 'Danificado' OR it.status IN ('Desgastado','Calibrar','Baixo','Alto'))
                )
            """
            cur.execute(crit_query)
        total = cur.fetchone()[0] or 0

        # Busca paginada veículos críticos
        offset = (page - 1) * per_page
        if where_clauses:
            data_query = f"""
                SELECT v.id, v.condutor, v.placa, v.modelo, v.data, v.quilometragem, v.tipo
                FROM veiculos v
                WHERE {' AND '.join(where_clauses)}
                AND EXISTS (
                    SELECT 1 FROM itens_checklist it
                    WHERE it.veiculo_id = v.id
                    AND (it.status = 'Danificado' OR it.status IN ('Desgastado','Calibrar','Baixo','Alto'))
                )
                ORDER BY v.id DESC
                LIMIT ? OFFSET ?
            """
            cur.execute(data_query, params + [per_page, offset])
        else:
            data_query = """
                SELECT v.id, v.condutor, v.placa, v.modelo, v.data, v.quilometragem, v.tipo
                FROM veiculos v
                WHERE EXISTS (
                    SELECT 1 FROM itens_checklist it
                    WHERE it.veiculo_id = v.id
                    AND (it.status = 'Danificado' OR it.status IN ('Desgastado','Calibrar','Baixo','Alto'))
                )
                ORDER BY v.id DESC
                LIMIT ? OFFSET ?
            """
            cur.execute(data_query, [per_page, offset])
        rows = cur.fetchall()
    else:
        # total simples
        count_query = f"SELECT COUNT(*) FROM veiculos {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}"
        cur.execute(count_query, params)
        total = cur.fetchone()[0] or 0
        offset = (page - 1) * per_page
        data_query = f"""
            SELECT id, condutor, placa, modelo, data, quilometragem, tipo
            FROM veiculos
            {where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """
        cur.execute(data_query, params + [per_page, offset])
        rows = cur.fetchall()

    items = []

    # calcula indicador de troca de óleo por item (com base em quilometragem atual e oleo_km)
    def _to_int(val):
        try:
            s = str(val or "")
            nums = "".join(ch for ch in s if ch.isdigit())
            return int(nums) if nums else None
        except Exception:
            return None

    for r in rows:
        quil = _to_int(r["quilometragem"]) if "quilometragem" in r.keys() else None
        oleo_km = (
            _to_int(r["oleo_km"])
            if "oleo_km" in r.keys() and r["oleo_km"] is not None
            else None
        )
        if quil is not None and oleo_km is not None:
            diff = quil - oleo_km
            oleo_alert = diff >= 6000
            oleo_due_in = max(0, 6000 - diff)
        else:
            diff = None
            oleo_alert = False
            oleo_due_in = None

        items.append(
            {
                "id": r["id"],
                "condutor": r["condutor"],
                "placa": r["placa"],
                "modelo": r["modelo"],
                "data": r["data"],
                "quilometragem": r["quilometragem"],
                "tipo": r["tipo"],
                "oleo_km": (r["oleo_km"] if "oleo_km" in r.keys() else None),
                "oleo_data": (r["oleo_data"] if "oleo_data" in r.keys() else None),
                "oleo_alert": oleo_alert,
                "oleo_diff": diff,
                "oleo_due_in": oleo_due_in,
            }
        )

    conn.close()
    total_pages = max(1, math.ceil(total / per_page)) if total else 1

    return jsonify(
        {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        }
    )


# Rota administrativa para limpar uploads órfãos
@app.route("/admin/cleanup-uploads", methods=["GET"])
@admin_required
def cleanup_uploads():
    confirm = request.args.get("confirm") == "1"
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT foto_carro FROM veiculos
        UNION
        SELECT foto_clrv FROM veiculos
        UNION
        SELECT foto_cnh FROM veiculos
        UNION
        SELECT caminho_foto FROM itens_checklist
        UNION
        SELECT caminho_thumb FROM itens_checklist
    """
    )
    referenced = {row[0] for row in cur.fetchall() if row[0]}
    conn.close()

    all_files = set(os.listdir(ANEXOS_DIR))
    orphans = sorted(list(all_files - referenced))

    result = {
        "total_files": len(all_files),
        "referenced": len(referenced),
        "orphans_count": len(orphans),
        "orphans_sample": orphans[:200],
    }

    if confirm and orphans:
        removed = []
        errors = []
        for fname in orphans:
            path = os.path.join(ANEXOS_DIR, fname)
            try:
                os.remove(path)
                removed.append(fname)
            except Exception as e:
                errors.append({"file": fname, "error": str(e)})
        result["removed_count"] = len(removed)
        result["removed_sample"] = removed[:200]
        result["errors"] = errors

    return jsonify(result)


@app.route("/admin/cleanup-orphans", methods=["POST"])
@permission_required("sistema_limpar_orfaos", "Você não tem permissão para limpar órfãos")
def cleanup_orphans():
    """Remove registros órfãos de tabelas relacionadas a veículos (quando veiculo foi excluído)"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        removals = {}
        for table in ["manutencao", "transacoes_veiculo", "historico_manutencao", "notas_fiscais_veiculo", "documentos_veiculo", "alertas_veiculo", "itens_checklist", "condutor_veiculo"]:
            if not table_exists(cur, table):
                removals[table] = {"encontrados": 0, "removidos": 0}
                continue
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE veiculo_id NOT IN (SELECT id FROM veiculos)")
            count = cur.fetchone()[0] or 0
            removals[table] = {"encontrados": count}
            if count:
                cur.execute(f"DELETE FROM {table} WHERE veiculo_id NOT IN (SELECT id FROM veiculos)")
                removals[table]["removidos"] = count
            else:
                removals[table]["removidos"] = 0
        # Combustível: lidar com veiculo_id sem vínculo e registros antigos sem veiculo_id
        # Registros com veiculo_id inválido
        if table_exists(cur, "combustivel"):
            cur.execute("SELECT COUNT(*) FROM combustivel WHERE veiculo_id IS NOT NULL AND veiculo_id NOT IN (SELECT id FROM veiculos)")
            count_c1 = cur.fetchone()[0] or 0
            cur.execute("SELECT COUNT(*) FROM combustivel WHERE veiculo_id IS NULL AND (placa IS NULL OR placa NOT IN (SELECT placa FROM veiculos))")
            count_c2 = cur.fetchone()[0] or 0
            removals["combustivel"] = {"encontrados": count_c1 + count_c2}
            if count_c1:
                cur.execute("DELETE FROM combustivel WHERE veiculo_id IS NOT NULL AND veiculo_id NOT IN (SELECT id FROM veiculos)")
            if count_c2:
                cur.execute("DELETE FROM combustivel WHERE veiculo_id IS NULL AND (placa IS NULL OR placa NOT IN (SELECT placa FROM veiculos))")
            removals["combustivel"]["removidos"] = (count_c1 or 0) + (count_c2 or 0)
        else:
            removals["combustivel"] = {"encontrados": 0, "removidos": 0}
        conn.commit()
        conn.close()
        return jsonify({"success": True, "remocoes": removals})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/admin/backup", methods=["GET"])
@admin_required
def backup():
    try:
        from config import DB_FILE, APP_DIR
        from io import BytesIO

        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        # Criar arquivo ZIP em memória
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(DB_FILE, arcname="checklist.db")

            if os.path.exists(ANEXOS_DIR):
                for root, dirs, files in os.walk(ANEXOS_DIR):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, APP_DIR)
                        zipf.write(file_path, arcname=arcname)

        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=backup_filename,
            mimetype="application/zip",
        )
    except Exception as e:
        flash(f"Erro ao criar backup: {str(e)}", "error")
        return redirect(url_for("auth.edit_profile"))


@app.route("/admin/restore", methods=["POST"])
@admin_required
def restore():
    try:
        from config import DB_FILE, APP_DIR

        if "backup_file" not in request.files:
            flash("Nenhum arquivo foi enviado", "error")
            return redirect(url_for("auth.edit_profile"))

        file = request.files["backup_file"]

        if file.filename == "":
            flash("Nenhum arquivo foi selecionado", "error")
            return redirect(url_for("auth.edit_profile"))

        if not file.filename.endswith(".zip"):
            flash("O arquivo deve ser um arquivo ZIP", "error")
            return redirect(url_for("auth.edit_profile"))

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "backup.zip")
            file.save(zip_path)

            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(temp_dir)

            extracted_db = os.path.join(temp_dir, "checklist.db")
            if not os.path.exists(extracted_db):
                flash("Arquivo de backup inválido: não contém checklist.db", "error")
                return redirect(url_for("auth.edit_profile"))

            backup_db = DB_FILE + ".backup"
            if os.path.exists(DB_FILE):
                shutil.copy2(DB_FILE, backup_db)

            shutil.copy2(extracted_db, DB_FILE)

            if os.path.exists(os.path.join(temp_dir, "anexos")):
                backup_anexos = ANEXOS_DIR + ".backup"
                if os.path.exists(ANEXOS_DIR):
                    if os.path.exists(backup_anexos):
                        shutil.rmtree(backup_anexos)
                    shutil.copytree(ANEXOS_DIR, backup_anexos)

                if os.path.exists(ANEXOS_DIR):
                    shutil.rmtree(ANEXOS_DIR)
                shutil.copytree(os.path.join(temp_dir, "anexos"), ANEXOS_DIR)

        flash(
            "Backup restaurado com sucesso! O banco de dados foi atualizado.", "success"
        )
        return redirect(url_for("dashboard"))
    except Exception as e:
        flash(f"Erro ao restaurar backup: {str(e)}", "error")
        return redirect(url_for("auth.edit_profile"))


# Rotas para manutenção de veículos
@app.route("/api/analytics/manutencao")
@login_required
def api_analytics_manutencao():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM manutencao")
    total_manutencoes = cur.fetchone()[0] or 0

    cur.execute(
        """
        SELECT 
            SUM(COALESCE(valor_peca, 0) + COALESCE(mao_de_obra, 0)) as total_custos,
            COUNT(*) as qtd_mes
        FROM manutencao
        WHERE strftime('%m', data_manutencao) = strftime('%m', 'now')
        AND strftime('%Y', data_manutencao) = strftime('%Y', 'now')
    """
    )
    row = cur.fetchone()
    custo_mes = row[0] or 0.0
    qtd_mes = row[1] or 0

    cur.execute(
        """
        SELECT 
            strftime('%Y-%m', data_manutencao) as mes,
            COUNT(*) as qtd
        FROM manutencao
        WHERE data_manutencao IS NOT NULL AND data_manutencao <> ''
        GROUP BY mes
        ORDER BY mes ASC
        LIMIT 12
    """
    )
    manutencoes_mes = cur.fetchall()
    monthly_data = [{"mes": row[0], "quantidade": row[1]} for row in manutencoes_mes]

    cur.execute(
        """
        SELECT nome_peca, COUNT(*) as qtd
        FROM manutencao
        WHERE nome_peca IS NOT NULL AND nome_peca <> ''
        GROUP BY nome_peca
        ORDER BY qtd DESC
        LIMIT 10
    """
    )
    problemas = cur.fetchall()
    problemas_data = [{"problema": row[0], "ocorrencias": row[1]} for row in problemas]

    cur.execute(
        """
        SELECT v.placa, v.modelo, COUNT(*) as qtd_manutencoes
        FROM manutencao m
        JOIN veiculos v ON m.veiculo_id = v.id
        GROUP BY m.veiculo_id
        ORDER BY qtd_manutencoes DESC
        LIMIT 10
    """
    )
    veiculos = cur.fetchall()
    veiculos_data = [
        {"placa": row[0], "modelo": row[1], "quantidade": row[2]} for row in veiculos
    ]

    cur.execute(
        """
        SELECT 
            strftime('%Y-%m', data_manutencao) as mes,
            SUM(COALESCE(valor_peca, 0) + COALESCE(mao_de_obra, 0)) as custos
        FROM manutencao
        WHERE data_manutencao IS NOT NULL AND data_manutencao <> ''
        GROUP BY mes
        ORDER BY mes ASC
        LIMIT 12
    """
    )
    custos_mes = cur.fetchall()
    custos_data = [{"mes": row[0], "custos": row[1] or 0.0} for row in custos_mes]

    cur.execute(
        """
        SELECT m.id, v.placa, v.modelo, m.nome_peca, m.data_manutencao,
               COALESCE(m.valor_peca, 0) + COALESCE(m.mao_de_obra, 0) as custo_total
        FROM manutencao m
        JOIN veiculos v ON m.veiculo_id = v.id
        ORDER BY m.data_manutencao DESC
        LIMIT 5
    """
    )
    recentes = cur.fetchall()
    recentes_data = [
        {
            "id": row[0],
            "placa": row[1],
            "modelo": row[2],
            "peca": row[3],
            "data": row[4],
            "custo": row[5],
        }
        for row in recentes
    ]

    conn.close()

    return jsonify(
        {
            "total_manutencoes": total_manutencoes,
            "custo_mes": custo_mes,
            "qtd_mes": qtd_mes,
            "monthly_data": monthly_data,
            "problemas": problemas_data,
            "veiculos": veiculos_data,
            "custos": custos_data,
            "recentes": recentes_data,
        }
    )


@app.route("/manutencao/dashboard")
@admin_required
def manutencao_dashboard():
    """Dashboard inteligente de manutenção"""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM manutencao")
    total_manutencoes = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(DISTINCT veiculo_id) FROM manutencao")
    veiculos_monitorados = cur.fetchone()[0] or 0

    cur.execute(
        """
        SELECT 
            SUM(COALESCE(valor_peca, 0) + COALESCE(mao_de_obra, 0)) as total
        FROM manutencao
        WHERE strftime('%m', data_manutencao) = strftime('%m', 'now')
        AND strftime('%Y', data_manutencao) = strftime('%Y', 'now')
    """
    )
    custo_mes = cur.fetchone()[0] or 0.0

    # Buscar alertas ativos
    cur.execute(
        """
        SELECT v.placa, v.modelo, MAX(m.data_manutencao) as ultima_manutencao, 
               m.proxima_manutencao_km, MAX(m.quilometragem_atual) as km_atual
        FROM veiculos v
        LEFT JOIN manutencao m ON v.id = m.veiculo_id
        GROUP BY v.id
        ORDER BY v.placa
    """
    )
    veiculos_data = cur.fetchall()

    alertas = []
    proximas_revisoes = []

    for veiculo in veiculos_data:
        placa, modelo, ultima_manutencao, prox_km, km_atual = veiculo

        if ultima_manutencao and prox_km and km_atual:
            # Calcular dias desde última manutenção
            from datetime import datetime, timedelta

            try:
                ult_manut = datetime.strptime(ultima_manutencao, "%Y-%m-%d")
                dias_passados = (datetime.now() - ult_manut).days
                km_atual_int = int(km_atual) if km_atual else 0
                prox_km_int = int(prox_km) if prox_km else 0

                # Verificar se está atrasado
                if dias_passados > 90 or km_atual_int > prox_km_int:
                    status = "CRÍTICO" if dias_passados > 180 else "AVISO"
                    icon = (
                        "bi-exclamation-triangle" if status == "CRÍTICO" else "bi-clock"
                    )
                    alert_type = "danger" if status == "CRÍTICO" else "warning"

                    if dias_passados > 90:
                        alertas.append(
                            {
                                "placa": placa,
                                "modelo": modelo,
                                "tipo": alert_type,
                                "icon": icon,
                                "mensagem": f"{status}: {placa} ({modelo}) - Manutenção {dias_passados} dias atrás!",
                            }
                        )

                # Próxima revisão
                km_restante = prox_km_int - km_atual_int
                percentual = (
                    max(0, min(100, ((prox_km_int - km_restante) / prox_km_int * 100)))
                    if prox_km_int > 0
                    else 0
                )

                proximas_revisoes.append(
                    {
                        "placa": placa,
                        "modelo": modelo,
                        "proxima_km": prox_km_int,
                        "km_atual": km_atual_int,
                        "km_restante": max(0, km_restante),
                        "percentual": percentual,
                        "status": (
                            "ATRASADA" if km_atual_int > prox_km_int else "EM DIA"
                        ),
                    }
                )
            except:
                pass

    # Limitar alertas a 3 e próximas revisões a 3
    alertas = alertas[:3]
    proximas_revisoes = proximas_revisoes[:3]

    # Buscar itens críticos do checklist
    cur.execute(
        """
        SELECT ic.id, ic.veiculo_id, v.placa, ic.nome_item, ic.status
        FROM itens_checklist ic
        JOIN veiculos v ON ic.veiculo_id = v.id
        WHERE ic.status IN ('Não OK', 'crítico', 'crítica', 'CRÍTICO')
        ORDER BY ic.id DESC
        LIMIT 10
    """
    )
    itens_criticos_data = cur.fetchall()

    itens_criticos = []
    from datetime import datetime

    for item in itens_criticos_data:
        item_id, veiculo_id, placa, nome_item, status_item = item

        # Buscar manutenção relacionada
        cur.execute(
            """
            SELECT data_manutencao
            FROM manutencao
            WHERE veiculo_id = ? AND nome_peca LIKE ?
            ORDER BY data_manutencao DESC
            LIMIT 1
        """,
            (veiculo_id, f"%{nome_item}%"),
        )

        manutencao = cur.fetchone()

        # Determinar se foi resolvido
        resolvido = "Resolvido" if manutencao else "Pendente"
        data_resolucao_fmt = None
        tempo_medio = None

        if manutencao:
            data_resolucao = manutencao[0]
            try:
                if isinstance(data_resolucao, str):
                    data_resol_dt = datetime.strptime(
                        (
                            data_resolucao.split()[0]
                            if " " in data_resolucao
                            else data_resolucao
                        ),
                        "%Y-%m-%d",
                    )
                    data_resolucao_fmt = data_resol_dt.strftime("%d/%m/%Y")
                else:
                    data_resolucao_fmt = data_resolucao.strftime("%d/%m/%Y")
            except:
                data_resolucao_fmt = None

        itens_criticos.append(
            {
                "id": item_id,
                "veiculo_id": veiculo_id,
                "placa": placa,
                "nome_item": nome_item,
                "status": resolvido,
                "data_identificado": "-",
                "data_resolucao": data_resolucao_fmt,
                "tempo_medio": tempo_medio,
            }
        )

    conn.close()

    return render_template(
        "manutencao/dashboard.html",
        total_manutencoes=total_manutencoes,
        veiculos_monitorados=veiculos_monitorados,
        custo_mes=custo_mes,
        alertas=alertas,
        proximas_revisoes=proximas_revisoes,
        itens_criticos=itens_criticos,
    )


@app.route("/manutencao")
@admin_required
def manutencao():
    """Lista todas as manutenções"""
    manutencoes = Manutencao.get_all()
    return render_template("manutencao/listar.html", manutencoes=manutencoes)


@app.route("/manutencao/novo/<int:veiculo_id>", methods=["GET", "POST"])
@admin_required
def nova_manutencao(veiculo_id):
    """Adiciona uma nova manutenção para um veículo"""
    from services import obter_registro

    veiculo = obter_registro(veiculo_id)

    if not veiculo:
        flash("Veículo não encontrado.", "error")
        return redirect(url_for("historico"))

    if request.method == "POST":
        try:
            manutencao = Manutencao.create(
                veiculo_id=veiculo_id,
                nome_peca=request.form.get("nome_peca"),
                data_manutencao=request.form.get("data_manutencao"),
                quilometragem_atual=request.form.get("quilometragem_atual"),
                vida_util_km=request.form.get("vida_util_km") or None,
                proxima_manutencao_km=request.form.get("proxima_manutencao_km") or None,
                valor_peca=request.form.get("valor_peca") or None,
                mao_de_obra=request.form.get("mao_de_obra") or None,
                observacoes=request.form.get("observacoes") or None,
            )
            flash("Manutenção registrada com sucesso!", "success")
            return redirect(url_for("manutencoes_veiculo", veiculo_id=veiculo_id))
        except Exception as e:
            flash(f"Erro ao registrar manutenção: {e}", "error")

    return render_template("manutencao/novo.html", veiculo=veiculo)


@app.route("/manutencao/veiculo/<int:veiculo_id>")
@admin_required
def manutencoes_veiculo(veiculo_id):
    """Lista todas as manutenções de um veículo específico"""
    from services import obter_registro

    veiculo = obter_registro(veiculo_id)

    if not veiculo:
        flash("Veículo não encontrado.", "error")
        return redirect(url_for("historico"))

    manutencoes = Manutencao.get_by_veiculo(veiculo_id)
    return render_template(
        "manutencao/veiculo.html", veiculo=veiculo, manutencoes=manutencoes
    )


@app.route("/manutencao/editar/<int:manutencao_id>", methods=["GET", "POST"])
@admin_required
def editar_manutencao(manutencao_id):
    """Edita uma manutenção existente"""
    manutencao = Manutencao.get_by_id(manutencao_id)

    if not manutencao:
        flash("Manutenção não encontrada.", "error")
        return redirect(url_for("manutencao"))

    if request.method == "POST":
        try:
            manutencao.nome_peca = request.form.get("nome_peca")
            manutencao.data_manutencao = request.form.get("data_manutencao")
            manutencao.quilometragem_atual = request.form.get("quilometragem_atual")
            manutencao.vida_util_km = request.form.get("vida_util_km") or None
            manutencao.proxima_manutencao_km = (
                request.form.get("proxima_manutencao_km") or None
            )
            manutencao.valor_peca = request.form.get("valor_peca") or None
            manutencao.mao_de_obra = request.form.get("mao_de_obra") or None
            manutencao.observacoes = request.form.get("observacoes") or None

            manutencao.update()
            flash("Manutenção atualizada com sucesso!", "success")
            return redirect(
                url_for("manutencoes_veiculo", veiculo_id=manutencao.veiculo_id)
            )
        except Exception as e:
            flash(f"Erro ao atualizar manutenção: {e}", "error")

    return render_template("manutencao/editar.html", manutencao=manutencao)


@app.route("/manutencao/excluir/<int:manutencao_id>", methods=["POST"])
@admin_required
def excluir_manutencao(manutencao_id):
    """Exclui uma manutenção"""
    manutencao = Manutencao.get_by_id(manutencao_id)

    if not manutencao:
        flash("Manutenção não encontrada.", "error")
        return redirect(url_for("manutencao"))

    try:
        veiculo_id = manutencao.veiculo_id
        manutencao.delete()
        flash("Manutenção excluída com sucesso!", "success")
        return redirect(url_for("manutencoes_veiculo", veiculo_id=veiculo_id))
    except Exception as e:
        flash(f"Erro ao excluir manutenção: {e}", "error")
        return redirect(
            url_for("manutencoes_veiculo", veiculo_id=manutencao.veiculo_id)
        )


@app.route("/api/manutencao/<int:manutencao_id>/concluir", methods=["POST"])
@login_required
def concluir_manutencao(manutencao_id):
    """Conclui uma manutenção com baixa inteligente"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Buscar manutenção
        cur.execute(
            """
            SELECT id, veiculo_id, nome_peca, data_manutencao, valor_peca, mao_de_obra, status
            FROM manutencao
            WHERE id = ?
        """,
            (manutencao_id,),
        )

        manutencao = cur.fetchone()
        if not manutencao:
            conn.close()
            return (
                jsonify({"success": False, "error": "Manutenção não encontrada"}),
                404,
            )

        if manutencao["status"] == "concluida":
            conn.close()
            return (
                jsonify(
                    {"success": False, "error": "Esta manutenção já foi concluída"}
                ),
                400,
            )

        # Data de conclusão
        from datetime import datetime

        data_conclusao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mes_ano = datetime.now().strftime("%m/%Y")

        # Atualizar status da manutenção
        cur.execute(
            """
            UPDATE manutencao
            SET status = 'concluida', data_conclusao = ?
            WHERE id = ?
        """,
            (data_conclusao, manutencao_id),
        )

        # Salvar no histórico
        cur.execute(
            """
            INSERT INTO historico_manutencao 
            (manutencao_id, veiculo_id, nome_peca, valor_peca, mao_de_obra, data_manutencao, data_conclusao, mes_ano)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                manutencao_id,
                manutencao["veiculo_id"],
                manutencao["nome_peca"],
                manutencao["valor_peca"] or 0,
                manutencao["mao_de_obra"] or 0,
                manutencao["data_manutencao"],
                data_conclusao,
                mes_ano,
            ),
        )

        conn.commit()
        conn.close()

        valor_total = (manutencao["valor_peca"] or 0) + (manutencao["mao_de_obra"] or 0)

        return jsonify(
            {
                "success": True,
                "message": f"Manutenção concluída com sucesso! Valor de R$ {valor_total:.2f} movido para o histórico.",
                "valor_total": valor_total,
                "data_conclusao": data_conclusao,
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/manutencao/historico/<int:veiculo_id>")
@login_required
def manutencao_historico_pagina(veiculo_id):
    """Página com histórico de manutenções concluídas"""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, placa, modelo FROM veiculos WHERE id = ?", (veiculo_id,))
    veiculo = cur.fetchone()

    if not veiculo:
        flash("Veículo não encontrado.", "error")
        conn.close()
        return redirect(url_for("manutencao"))

    # Buscar histórico
    cur.execute(
        """
        SELECT id, nome_peca, valor_peca, mao_de_obra, data_manutencao, 
               data_conclusao, mes_ano
        FROM historico_manutencao
        WHERE veiculo_id = ?
        ORDER BY data_conclusao DESC
    """,
        (veiculo_id,),
    )

    historico = []
    for row in cur.fetchall():
        historico.append(
            {
                "id": row[0],
                "nome_peca": row[1],
                "valor_peca": row[2] or 0,
                "mao_de_obra": row[3] or 0,
                "valor_total": (row[2] or 0) + (row[3] or 0),
                "data_manutencao": row[4],
                "data_conclusao": row[5],
                "mes_ano": row[6],
            }
        )

    # Calcular resumo
    total_gasto = sum(h["valor_total"] for h in historico) if historico else 0
    total_pecas = sum(h["valor_peca"] for h in historico) if historico else 0
    total_mao_obra = sum(h["mao_de_obra"] for h in historico) if historico else 0

    conn.close()

    return render_template(
        "manutencao/historico.html",
        veiculo=dict(veiculo),
        historico=historico,
        total_gasto=total_gasto,
        total_pecas=total_pecas,
        total_mao_obra=total_mao_obra,
        quantidade=len(historico),
    )


@app.route("/api/manutencao/historico/<int:veiculo_id>", methods=["GET"])
@login_required
def historico_manutencao(veiculo_id):
    """Retorna histórico de manutenções concluídas de um veículo"""
    try:
        mes = request.args.get("mes")

        conn = get_conn()
        cur = conn.cursor()

        where_clause = "WHERE hm.veiculo_id = ?"
        params = [veiculo_id]

        if mes:
            where_clause += " AND hm.mes_ano = ?"
            params.append(mes)

        cur.execute(
            f"""
            SELECT 
                hm.id,
                hm.nome_peca,
                hm.valor_peca,
                hm.mao_de_obra,
                hm.data_manutencao,
                hm.data_conclusao,
                hm.mes_ano,
                v.placa,
                v.modelo
            FROM historico_manutencao hm
            JOIN veiculos v ON hm.veiculo_id = v.id
            {where_clause}
            ORDER BY hm.data_conclusao DESC
        """,
            params,
        )

        historico = []
        for row in cur.fetchall():
            historico.append(
                {
                    "id": row[0],
                    "nome_peca": row[1],
                    "valor_peca": row[2] or 0,
                    "mao_de_obra": row[3] or 0,
                    "valor_total": (row[2] or 0) + (row[3] or 0),
                    "data_manutencao": row[4],
                    "data_conclusao": row[5],
                    "mes_ano": row[6],
                    "placa": row[7],
                    "modelo": row[8],
                }
            )

        conn.close()
        return jsonify({"historico": historico})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/manutencao/<int:manutencao_id>/arquivos")
@login_required
def api_manutencao_arquivos(manutencao_id):
    """Retorna arquivos de uma manutenção"""
    manutencao = Manutencao.get_by_id(manutencao_id)
    if not manutencao:
        return jsonify({"error": "Manutenção não encontrada"}), 404

    arquivos = []
    if manutencao.nota_fiscal_foto:
        arquivo_path = os.path.join(ANEXOS_DIR, manutencao.nota_fiscal_foto)
        if os.path.exists(arquivo_path):
            arquivos.append(
                {
                    "nome": manutencao.nota_fiscal_foto,
                    "caminho": manutencao.nota_fiscal_foto,
                }
            )

    return jsonify({"arquivos": arquivos})


@app.route("/manutencao/<int:manutencao_id>/upload-nota-fiscal", methods=["POST"])
@login_required
def upload_nota_fiscal_manutencao(manutencao_id):
    """Upload de nota fiscal para manutenção"""
    from werkzeug.utils import secure_filename

    manutencao = Manutencao.get_by_id(manutencao_id)
    if not manutencao:
        return jsonify({"error": "Manutenção não encontrada"}), 404

    if "arquivo" not in request.files:
        return jsonify({"error": "Nenhum arquivo fornecido"}), 400

    file = request.files["arquivo"]
    if not file or file.filename == "":
        return jsonify({"error": "Arquivo inválido"}), 400

    allowed_extensions = {
        "pdf",
        "jpg",
        "jpeg",
        "png",
        "gif",
        "doc",
        "docx",
        "xls",
        "xlsx",
    }
    if not (
        "." in file.filename
        and file.filename.rsplit(".", 1)[1].lower() in allowed_extensions
    ):
        return jsonify({"error": "Tipo de arquivo não permitido"}), 400

    try:
        conn = get_conn()
        cur = conn.cursor()

        filename = f"manutencao_{manutencao_id}_{int(datetime.now().timestamp())}_{secure_filename(file.filename)}"
        filepath = os.path.join(ANEXOS_DIR, filename)
        file.save(filepath)

        cur.execute(
            "UPDATE manutencao SET nota_fiscal_foto = ? WHERE id = ?",
            (filename, manutencao_id),
        )
        conn.commit()
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": "Nota fiscal enviada com sucesso!",
                "filename": filename,
            }
        )
    except Exception as e:
        return jsonify({"error": f"Erro ao salvar arquivo: {str(e)}"}), 500


@app.route("/manutencao/<int:manutencao_id>/download-nota-fiscal")
@login_required
def download_nota_fiscal_manutencao(manutencao_id):
    """Download de nota fiscal de manutenção"""
    manutencao = Manutencao.get_by_id(manutencao_id)
    if not manutencao or not manutencao.nota_fiscal_foto:
        flash("Arquivo não encontrado.", "error")
        return redirect(url_for("manutencao"))

    try:
        filepath = os.path.join(ANEXOS_DIR, manutencao.nota_fiscal_foto)
        if not os.path.exists(filepath):
            flash("Arquivo não encontrado no servidor.", "error")
            return redirect(url_for("manutencao"))

        return send_file(
            filepath, as_attachment=True, download_name=manutencao.nota_fiscal_foto
        )
    except Exception as e:
        flash(f"Erro ao baixar arquivo: {str(e)}", "error")
        return redirect(url_for("manutencao"))


# ===================== ROTAS PARA MANUTENCAO SUGERIDA =====================

@app.route("/manutencao/pendentes")
@admin_required
def manutencao_pendentes():
    """Dashboard de manutenções pendentes de aprovação"""
    from manutencao_sugerida import obter_manutencoes_pendentes
    
    manutencoes = obter_manutencoes_pendentes()
    print(f"DEBUG: Manutenções pendentes encontradas: {len(manutencoes)}")
    for m in manutencoes:
        print(f"  - {m}")
    return render_template("manutencao_pendentes.html", manutencoes=manutencoes)


@app.route("/api/manutencao-sugerida/aprovar/<int:manutencao_id>", methods=["POST"])
@admin_required
def api_aprovar_manutencao_sugerida(manutencao_id):
    """API para aprovar uma manutenção sugerida"""
    from manutencao_sugerida import aprovar_manutencao
    
    try:
        aprovar_manutencao(manutencao_id)
        return jsonify({'success': True, 'message': 'Manutenção aprovada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/api/manutencao-sugerida/rejeitar/<int:manutencao_id>", methods=["POST"])
@admin_required
def api_rejeitar_manutencao_sugerida(manutencao_id):
    """API para rejeitar uma manutenção sugerida"""
    from manutencao_sugerida import rejeitar_manutencao
    
    try:
        rejeitar_manutencao(manutencao_id)
        return jsonify({'success': True, 'message': 'Manutenção rejeitada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/api/manutencao-sugerida/agendar/<int:manutencao_id>", methods=["POST"])
@admin_required
def api_agendar_manutencao_sugerida(manutencao_id):
    """API para agendar uma manutenção sugerida"""
    from manutencao_sugerida import agendar_manutencao
    
    try:
        data = request.get_json()
        data_manutencao = data.get('data_manutencao')
        
        if not data_manutencao:
            return jsonify({'success': False, 'error': 'Data não fornecida'}), 400
        
        agendar_manutencao(manutencao_id, data_manutencao)
        return jsonify({'success': True, 'message': 'Manutenção agendada'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/veiculo/<int:veiculo_id>/relatorio-completo")
@login_required
def relatorio_completo_veiculo(veiculo_id):
    """Gera relatório PDF completo do veículo com gastos, consumo, manutenções e documentos"""
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        PageBreak,
        Image as RLImage,
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from io import BytesIO

    reg = obter_registro(veiculo_id)
    if not reg:
        flash("Veículo não encontrado.", "error")
        return redirect(url_for("historico"))

    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, topMargin=0.5 * inch, bottomMargin=0.5 * inch
        )
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1f77b4"),
            spaceAfter=30,
            alignment=1,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#2ca02c"),
            spaceAfter=12,
            spaceBefore=12,
            borderColor=colors.HexColor("#2ca02c"),
            borderWidth=1,
            borderPadding=5,
        )

        elements.append(
            Paragraph(f"RELATÓRIO COMPLETO - VEÍCULO {reg['placa']}", title_style)
        )
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("1. INFORMAÇÕES GERAIS DO VEÍCULO", heading_style))
        vehicle_data = [
            ["Campo", "Valor"],
            ["Placa", reg.get("placa") or "-"],
            ["Modelo", reg.get("modelo") or "-"],
            ["Tipo", reg.get("tipo") or "-"],
            ["Condutor", reg.get("condutor") or "-"],
            ["Quilometragem", f"{reg.get('quilometragem') or '-'} km"],
            ["Data do Registro", reg.get("data") or "-"],
        ]

        vehicle_table = Table(vehicle_data, colWidths=[2 * inch, 4 * inch])
        vehicle_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f0f0f0")],
                    ),
                ]
            )
        )
        elements.append(vehicle_table)
        elements.append(Spacer(1, 0.3 * inch))

        indicadores = obter_todos_indicadores(veiculo_id)
        elements.append(Paragraph("2. INDICADORES DE PERFORMANCE", heading_style))

        perf_data = [["Indicador", "Valor"]]
        if indicadores.get("km_l", {}).get("km_l"):
            perf_data.append(["Consumo Médio", f"{indicadores['km_l']['km_l']} km/l"])
        if indicadores.get("custo_km", {}).get("custo_km"):
            perf_data.append(["Custo/KM", f"R$ {indicadores['custo_km']['custo_km']}"])
        if indicadores.get("tempo_manutencao", {}).get("tempo_km"):
            perf_data.append(
                [
                    "Intervalo de Manutenção",
                    f"{indicadores['tempo_manutencao']['tempo_km']} km",
                ]
            )
        if indicadores.get("taxa_danificacao", {}).get("taxa_danificacao") is not None:
            perf_data.append(
                [
                    "Taxa de Danos",
                    f"{indicadores['taxa_danificacao']['taxa_danificacao']}%",
                ]
            )

        if len(perf_data) > 1:
            perf_table = Table(perf_data, colWidths=[3 * inch, 3 * inch])
            perf_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2ca02c")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [colors.white, colors.HexColor("#f0f0f0")],
                        ),
                    ]
                )
            )
            elements.append(perf_table)
        elements.append(Spacer(1, 0.3 * inch))

        conn = get_conn()
        cur = conn.cursor()

        elements.append(Paragraph("3. HISTÓRICO DE COMBUSTÍVEL", heading_style))
        combustivel_list = listar_combustivel(veiculo_id=veiculo_id)

        if combustivel_list:
            comb_data = [["Data", "Litros", "Valor Total", "km"]]
            total_combustivel = 0
            for comb in combustivel_list[:10]:
                comb_data.append(
                    [
                        comb.get("data_abastecimento", "-"),
                        f"{comb.get('quantidade_litros', '-')} L",
                        f"R$ {comb.get('valor_total', '0.00')}",
                        f"{comb.get('quilometragem', '-')} km",
                    ]
                )
                try:
                    total_combustivel += float(comb.get("valor_total", 0) or 0)
                except:
                    pass

            cur.execute(
                "SELECT SUM(valor_total) FROM combustivel WHERE veiculo_id = ?",
                (veiculo_id,),
            )
            result = cur.fetchone()
            total_combustivel = result[0] or 0

            comb_data.append(["TOTAL", "", f"R$ {total_combustivel:.2f}", ""])
            comb_table = Table(
                comb_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch]
            )
            comb_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff7f0e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ffe6cc")),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -2),
                            [colors.white, colors.HexColor("#f0f0f0")],
                        ),
                    ]
                )
            )
            elements.append(comb_table)
        else:
            elements.append(
                Paragraph(
                    "Nenhum registro de combustível encontrado.", styles["Normal"]
                )
            )
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("4. HISTÓRICO DE MANUTENÇÃO", heading_style))
        manutencoes = Manutencao.get_by_veiculo(veiculo_id)

        if manutencoes:
            manu_data = [["Data", "Peça/Serviço", "Quilometragem", "Custo Total"]]
            total_manutencao = 0
            for manu in manutencoes[:10]:
                custo = (float(manu.valor_peca or 0) or 0) + (
                    float(manu.mao_de_obra or 0) or 0
                )
                total_manutencao += custo
                manu_data.append(
                    [
                        manu.data_manutencao,
                        manu.nome_peca,
                        f"{manu.quilometragem_atual} km",
                        f"R$ {custo:.2f}",
                    ]
                )

            cur.execute(
                """
                SELECT SUM(CAST(valor_peca AS REAL)) + SUM(CAST(mao_de_obra AS REAL))
                FROM manutencao WHERE veiculo_id = ?
            """,
                (veiculo_id,),
            )
            result = cur.fetchone()
            total_manutencao = result[0] or 0

            manu_data.append(["", "TOTAL", "", f"R$ {total_manutencao:.2f}"])
            manu_table = Table(
                manu_data, colWidths=[1.2 * inch, 2 * inch, 1.2 * inch, 1.6 * inch]
            )
            manu_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d62728")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#ffe6e6")),
                        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -2),
                            [colors.white, colors.HexColor("#f0f0f0")],
                        ),
                    ]
                )
            )
            elements.append(manu_table)
        else:
            elements.append(
                Paragraph("Nenhum registro de manutenção encontrado.", styles["Normal"])
            )
        elements.append(Spacer(1, 0.3 * inch))

        elements.append(Paragraph("5. RESUMO FINANCEIRO", heading_style))
        cur.execute(
            "SELECT SUM(valor_total) FROM combustivel WHERE veiculo_id = ?",
            (veiculo_id,),
        )
        total_comb = cur.fetchone()[0] or 0

        cur.execute(
            """
            SELECT SUM(CAST(valor_peca AS REAL)) + SUM(CAST(mao_de_obra AS REAL))
            FROM manutencao WHERE veiculo_id = ?
        """,
            (veiculo_id,),
        )
        total_manu = cur.fetchone()[0] or 0

        conn.close()

        fin_data = [
            ["Descrição", "Valor"],
            ["Gasto com Combustível", f"R$ {total_comb:.2f}"],
            ["Gasto com Manutenção", f"R$ {total_manu:.2f}"],
            ["CUSTO TOTAL", f"R$ {total_comb + total_manu:.2f}"],
        ]

        fin_table = Table(fin_data, colWidths=[3 * inch, 3 * inch])
        fin_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, -1), (-1, -1), 14),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#cce5ff")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -2),
                        [colors.white, colors.HexColor("#f0f0f0")],
                    ),
                ]
            )
        )
        elements.append(fin_table)
        elements.append(Spacer(1, 0.2 * inch))

        footer_text = f"<i>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</i>"
        elements.append(Paragraph(footer_text, styles["Normal"]))

        doc.build(elements)
        buffer.seek(0)

        filename = f"relatorio_{reg.get('placa', 'veiculo')}_{datetime.now().strftime('%d%m%Y_%H%M%S')}.pdf"
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        flash(f"Erro ao gerar relatório: {str(e)}", "error")
        return redirect(url_for("detalhes", veiculo_id=veiculo_id))


@app.route("/combustivel")
@permission_required('combustivel_relatorio')
def combustivel():
    """Lista registros de combustível com filtros opcionais"""
    resultados = []
    try:
        if request.method == "POST":
            placa = request.form.get("placa")
            data_ini = request.form.get("data_ini")
            data_fim = request.form.get("data_fim")
            resultados = listar_combustivel(placa, data_ini, data_fim)
        else:
            resultados = listar_combustivel()
    except Exception as e:
        flash(f"Erro ao buscar registros de combustível: {e}", "error")
    return render_template("combustivel/listar.html", resultados=resultados)


@app.route("/combustivel/novo", methods=["GET", "POST"])
@admin_required
def novo_combustivel():
    """Formulário para novo registro de combustível"""
    if request.method == "POST":
        try:
            # Validar campos obrigatórios
            placa = request.form.get("placa", "").strip()
            data = request.form.get("data_abastecimento", "").strip()
            litros = request.form.get("quantidade_litros", "").strip()
            valor = request.form.get("valor_total", "").strip()
            
            if not all([placa, data, litros, valor]):
                flash("Todos os campos obrigatórios devem ser preenchidos", "error")
                return render_template("combustivel/novo.html")
            
            # Validar valores numéricos
            try:
                float(litros)
                float(valor)
            except ValueError:
                flash("Litros e Valor devem ser números válidos", "error")
                return render_template("combustivel/novo.html")
            
            combustivel_id = salvar_combustivel(request.form, request.files)
            
            if combustivel_id:
                flash(
                    f"Registro de combustível salvo com sucesso! ID: {combustivel_id}",
                    "success",
                )
                return redirect(url_for("combustivel"))
            else:
                flash("Erro ao salvar registro de combustível: Dados inválidos", "error")
                return render_template("combustivel/novo.html")
                
        except Exception as e:
            import traceback
            print(f"Erro ao salvar combustível: {str(e)}")
            print(traceback.format_exc())
            flash(f"Erro ao salvar registro: {str(e)}", "error")
            return render_template("combustivel/novo.html")
    return render_template("combustivel/novo.html")


@app.route("/combustivel/editar/<int:combustivel_id>", methods=["GET", "POST"])
@admin_required
def editar_combustivel(combustivel_id):
    """Formulário para editar registro de combustível"""
    reg = obter_combustivel(combustivel_id)
    if not reg:
        flash("Registro de combustível não encontrado.", "error")
        return redirect(url_for("combustivel"))

    if request.method == "POST":
        try:
            atualizar_combustivel(combustivel_id, request.form, request.files)
            flash("Registro de combustível atualizado com sucesso!", "success")
            return redirect(url_for("combustivel"))
        except Exception as e:
            flash(f"Erro ao atualizar registro de combustível: {e}", "error")

    return render_template("combustivel/editar.html", reg=reg)


@app.route("/combustivel/deletar/<int:combustivel_id>", methods=["POST"])
@admin_required
def deletar_combustivel_rota(combustivel_id):
    """Deleta um registro de combustível"""
    try:
        deletar_combustivel(combustivel_id)
        flash("Registro de combustível deletado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao deletar registro de combustível: {e}", "error")
    return redirect(url_for("combustivel"))


@app.route("/combustivel/cupom/<int:combustivel_id>")
@login_required
def cupom_combustivel(combustivel_id):
    """Exibe cupom fiscal do abastecimento"""
    try:
        reg = obter_combustivel(combustivel_id)
        if not reg:
            flash("Registro de combustível não encontrado!", "error")
            return redirect(url_for("combustivel"))
        return render_template("combustivel/cupom.html", reg=reg, now=datetime.now())
    except Exception as e:
        flash(f"Erro ao exibir cupom: {e}", "error")
        return redirect(url_for("combustivel"))


@app.route("/combustivel/relatorio", methods=["GET", "POST"])
@login_required
def relatorio_combustivel():
    """Relatório de abastecimento em aba"""
    resultados = []
    try:
        if request.method == "POST":
            placa = request.form.get("placa")
            data_ini = request.form.get("data_ini")
            data_fim = request.form.get("data_fim")
            resultados = listar_combustivel(placa, data_ini, data_fim)
        else:
            resultados = listar_combustivel()
    except Exception as e:
        flash(f"Erro ao buscar registros de combustível: {e}", "error")
    
    # Agrupar por placa e calcular subtotais
    veiculos = {}
    for reg in resultados:
        placa = reg.get("placa") or "Sem Placa"
        if placa not in veiculos:
            veiculos[placa] = {
                "placa": placa,
                "tipo": reg.get("tipo_veiculo", "-"),
                "registros": [],
                "total_litros": 0.0,
                "total_valor": 0.0
            }
        veiculos[placa]["registros"].append(reg)
        
        # Converter para float com segurança
        try:
            litros = float(reg.get("quantidade_litros") or 0)
            valor = float(reg.get("valor_total") or 0)
            veiculos[placa]["total_litros"] += litros
            veiculos[placa]["total_valor"] += valor
        except (ValueError, TypeError) as e:
            print(f"Erro ao converter valores: {e}, reg: {reg}")
            # Usar valores padrão em caso de erro
            veiculos[placa]["total_litros"] += 0.0
            veiculos[placa]["total_valor"] += 0.0
    
    return render_template("combustivel/relatorio.html", veiculos=veiculos, resultados=resultados)


@app.route("/condutores", methods=["GET"])
@login_required
def listar_condutores_rota():
    """Lista todos os condutores cadastrados com paginação no banco"""
    page = request.args.get('page', 1, type=int)
    per_page = 25

    try:
        result = listar_condutores(page=page, per_page=per_page)

        return render_template(
            "condutores/listar.html",
            condutores=result['condutores'],
            page=result['page'],
            total_pages=result['total_pages'],
            total=result['total']
        )
    except Exception as e:
        flash(f"Erro ao listar condutores: {e}", "error")
        return render_template("condutores/listar.html", condutores=[], page=1, total_pages=0, total=0)


@app.route("/condutores/novo", methods=["GET", "POST"])
@login_required
def novo_condutor():
    """Cria um novo condutor"""
    if request.method == "POST":
        try:
            condutor_id = salvar_condutor(request.form, request.files)
            if condutor_id:
                flash("Condutor cadastrado com sucesso!", "success")
                return redirect(url_for("detalhes_condutor", condutor_id=condutor_id))
            else:
                flash("Erro ao cadastrar condutor.", "danger")
        except Exception as e:
            flash(f"Erro ao cadastrar condutor: {e}", "danger")

    return render_template("condutores/formulario.html", condutor=None)


@app.route("/condutores/<int:condutor_id>/editar", methods=["GET", "POST"])
@login_required
def editar_condutor(condutor_id):
    """Edita um condutor existente"""
    condutor = obter_condutor(condutor_id)
    if not condutor:
        flash("Condutor não encontrado.", "danger")
        return redirect(url_for("listar_condutores_rota"))

    if request.method == "POST":
        try:
            salvar_condutor(request.form, request.files)
            flash("Condutor atualizado com sucesso!", "success")
            return redirect(url_for("detalhes_condutor", condutor_id=condutor_id))
        except Exception as e:
            flash(f"Erro ao atualizar condutor: {e}", "danger")

    return render_template("condutores/formulario.html", condutor=condutor)


@app.route("/condutores/<int:condutor_id>", methods=["GET"])
@login_required
def detalhes_condutor(condutor_id):
    """Exibe os detalhes completos de um condutor"""
    condutor = obter_condutor(condutor_id)
    if not condutor:
        flash("Condutor não encontrado.", "danger")
        return redirect(url_for("listar_condutores_rota"))

    return render_template("condutores/detalhes.html", condutor=condutor)


@app.route("/condutores/<int:condutor_id>/desativar", methods=["POST"])
@admin_required
def desativar_condutor_rota(condutor_id):
    """Desativa um condutor"""
    try:
        desativar_condutor(condutor_id)
        flash("Condutor desativado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao desativar condutor: {e}", "danger")
    return redirect(url_for("listar_condutores_rota"))


@app.route("/condutores/<int:condutor_id>/ativar", methods=["POST"])
@admin_required
def ativar_condutor_rota(condutor_id):
    """Ativa um condutor desativado"""
    try:
        ativar_condutor(condutor_id)
        flash("Condutor ativado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao ativar condutor: {e}", "danger")
    return redirect(url_for("listar_condutores_rota"))


@app.route("/api/condutores/<int:condutor_id>", methods=["DELETE"])
@login_required
def deletar_condutor_api(condutor_id):
    """Deleta um condutor via API"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Verificar se o condutor existe
        cur.execute("SELECT id FROM condutores WHERE id = ?", (condutor_id,))
        if not cur.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Condutor não encontrado"}), 404
        
        # Deletar o condutor
        cur.execute("DELETE FROM condutores WHERE id = ?", (condutor_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Condutor deletado com sucesso"})
    except Exception as e:
        print(f"Erro ao deletar condutor: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/condutores/listar", methods=["GET"])
def api_listar_condutores():
    """API para retornar lista de condutores em JSON"""
    conn = get_conn()
    cur = conn.cursor()

    # Listar todos os condutores, independentemente do status
    cur.execute("SELECT id, nome_completo, cpf, telefone, email, ativo FROM condutores ORDER BY nome_completo ASC")
    condutores = cur.fetchall()
    conn.close()

    # Retornar todos os condutores com informações adicionais
    return jsonify([
        {
            "id": c["id"],
            "nome": c["nome_completo"],
            "cpf": c.get("cpf", ""),
            "telefone": c.get("telefone", ""),
            "email": c.get("email", ""),
            "status": "ativo" if c.get("ativo", 1) else "inativo"
        }
        for c in [dict(row) for row in condutores]
    ])


@app.route("/api/listar-combustivel", methods=["GET"])
@login_required
def api_listar_combustivel():
    """API para retornar lista de registros de combustível em JSON"""
    try:
        placa = request.args.get("placa")
        data_ini = request.args.get("data_ini")
        data_fim = request.args.get("data_fim")
        veiculo_id = request.args.get("veiculo_id")

        resultados = listar_combustivel(placa, data_ini, data_fim, veiculo_id)

        # Garantir ordenação por data decrescente (mais recentes primeiro) para cálculo correto do consumo
        resultados_ordenados = sorted(resultados, key=lambda x: x.get("data_abastecimento", ""), reverse=True)

        # Converter para formato JSON serializável
        return jsonify([
            {
                "id": r.get("id"),
                "placa": r.get("placa"),
                "tipo_veiculo": r.get("tipo_veiculo"),
                "data_abastecimento": r.get("data_abastecimento"),
                "quilometragem": r.get("quilometragem"),
                "quantidade_litros": r.get("quantidade_litros"),
                "valor_total": r.get("valor_total"),
                "observacoes": r.get("observacoes"),
                "nota_fiscal_foto": r.get("nota_fiscal_foto")
            }
            for r in resultados_ordenados
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/veiculos/listar", methods=["GET"])
@login_required
def api_listar_veiculos():
    """API para retornar lista de veículos em JSON (array puro)"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Listar todos os veículos - somente campos necessários
        cur.execute("SELECT id, placa, modelo, tipo FROM veiculos ORDER BY placa ASC")
        veiculos_rows = cur.fetchall()
        conn.close()

        # Converter para lista de dicionários simples
        veiculos_list = []
        for row in veiculos_rows:
            veiculo_dict = {
                "id": int(row["id"]),
                "placa": str(row["placa"] or ""),
                "modelo": str(row["modelo"] or ""),
                "tipo": str(row["tipo"] or "Carro")
            }
            veiculos_list.append(veiculo_dict)

        # Retornar EXATAMENTE um array JSON puro, sem envelopamento
        json_str = json.dumps(veiculos_list, ensure_ascii=False)
        response = Response(json_str, mimetype='application/json; charset=utf-8')
        return response
    except Exception as e:
        print(f"Erro ao listar veículos: {e}")
        import traceback
        traceback.print_exc()
        # Retornar array vazio em caso de erro
        response = Response(json.dumps([]), mimetype='application/json; charset=utf-8')
        return response


@app.route("/api/veiculos/debug", methods=["GET"])
@login_required
def api_debug_veiculos():
    """Endpoint de debug para verificar se há veículos no banco"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        # Contar veículos
        cur.execute("SELECT COUNT(*) as total FROM veiculos")
        total = cur.fetchone()["total"]
        
        # Pegar primeiros 5
        cur.execute("SELECT id, placa, modelo FROM veiculos LIMIT 5")
        veiculos = [dict(row) for row in cur.fetchall()]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "total_veiculos": total,
            "primeiros_5": veiculos,
            "autenticado": current_user.is_authenticated
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/condutores/<int:condutor_id>/infracoes/adicionar", methods=["POST"])
@login_required
def adicionar_multa(condutor_id):
    """Adiciona uma nova multa ao condutor"""
    try:
        tipo = request.form.get("tipo", "").strip()
        data_infracao = request.form.get("data_infracao", "").strip()
        descricao = request.form.get("descricao", "").strip()
        valor = request.form.get("valor", "").strip()
        responsavel_pagamento = request.form.get(
            "responsavel_pagamento", "condutor"
        ).strip()
        data_vencimento = request.form.get("data_vencimento", "").strip()

        if not all([tipo, data_infracao, descricao]):
            flash("Por favor, preencha todos os campos obrigatórios", "danger")
            return redirect(url_for("detalhes_condutor", condutor_id=condutor_id))

        valor = float(valor) if valor else None

        if responsavel_pagamento == "condutor" and not data_vencimento:
            flash("Data de vencimento é obrigatória para multas do condutor", "danger")
            return redirect(url_for("detalhes_condutor", condutor_id=condutor_id))

        adicionar_infracao(
            condutor_id=condutor_id,
            tipo=tipo,
            data_infracao=data_infracao,
            descricao=descricao,
            valor=valor,
            responsavel_pagamento=responsavel_pagamento,
            data_vencimento=(
                data_vencimento if responsavel_pagamento == "condutor" else None
            ),
        )

        flash("Multa registrada com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao registrar multa: {e}", "danger")

    return redirect(url_for("detalhes_condutor", condutor_id=condutor_id))


@app.route(
    "/condutores/<int:condutor_id>/infracoes/<int:infracao_id>/pagar", methods=["POST"]
)
@login_required
def marcar_multa_paga(condutor_id, infracao_id):
    """Marca uma multa como paga"""
    try:
        marcar_infracao_paga(infracao_id)
        flash("Multa marcada como paga!", "success")
    except Exception as e:
        flash(f"Erro ao marcar multa como paga: {e}", "danger")

    return redirect(url_for("detalhes_condutor", condutor_id=condutor_id))


@app.route(
    "/condutores/<int:condutor_id>/infracoes/<int:infracao_id>/deletar",
    methods=["POST"],
)
@login_required
def deletar_multa(condutor_id, infracao_id):
    """Deleta uma multa"""
    try:
        deletar_infracao(infracao_id)
        flash("Multa deletada com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao deletar multa: {e}", "danger")

    return redirect(url_for("detalhes_condutor", condutor_id=condutor_id))


@app.route("/financeiro/multas", methods=["GET"])
@admin_required
def multas_empresa():
    """Lista todas as multas que a empresa deve pagar"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        status = request.args.get("status", "").strip()
        
        # Query base para obter todas as multas
        query = """
            SELECT ci.* FROM condutor_infracoes ci
            JOIN condutores c ON ci.condutor_id = c.id
        """
        params = []
        
        # Filtrar por status se necessário
        if status == "pagas":
            query += " WHERE ci.pago_em IS NOT NULL"
        elif status == "pendentes":
            query += " WHERE ci.pago_em IS NULL"
        
        query += " ORDER BY ci.data_infracao DESC"
        
        cur.execute(query, params)
        multas = [dict(row) for row in cur.fetchall()]
        conn.close()

        total_pendente = sum(
            m.get("valor", 0) or 0 for m in multas if not m.get("pago_em")
        )
        total_pago = sum(m.get("valor", 0) or 0 for m in multas if m.get("pago_em"))

        return render_template(
            "financeiro/multas.html",
            multas=multas,
            status=status,
            total_pendente=total_pendente,
            total_pago=total_pago,
        )
    except Exception as e:
        flash(f"Erro ao listar multas: {e}", "danger")
        return redirect(url_for("dashboard"))


@app.route("/financeiro/multas/adicionar", methods=["POST"])
@login_required
def adicionar_multa_empresa():
    """Adiciona uma multa da empresa com documento"""
    try:
        condutor_id = request.form.get("condutor_id", "").strip()
        veiculo_id = request.form.get("veiculo_id", "").strip()
        tipo = request.form.get("tipo", "").strip()
        data_infracao = request.form.get("data_infracao", "").strip()
        localidade = request.form.get("localidade", "").strip()
        valor = request.form.get("valor", "").strip()
        descricao = request.form.get("descricao", "").strip()

        if not all([condutor_id, tipo, data_infracao, localidade, valor]):
            flash("Por favor, preencha todos os campos obrigatórios", "danger")
            return redirect(url_for("multas_empresa"))

        valor = float(valor)
        documento = None

        if "documento_multa" in request.files:
            file = request.files["documento_multa"]
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"multa_{timestamp}_{filename}"
                filepath = os.path.join(ANEXOS_DIR, filename)
                file.save(filepath)
                documento = filename

        descricao_completa = f"{localidade} - {descricao}" if descricao else localidade

        infracao_id = adicionar_infracao(
            condutor_id=int(condutor_id),
            tipo=tipo,
            data_infracao=data_infracao,
            descricao=descricao_completa,
            valor=valor,
            responsavel_pagamento="empresa",
            data_vencimento=None,
        )

        if documento:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE condutor_infracoes SET descricao = ? WHERE id = ?
            """,
                (f"{descricao_completa} [Documento: {documento}]", infracao_id),
            )
            conn.commit()
            conn.close()

        flash("Multa registrada com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao registrar multa: {e}", "danger")

    return redirect(url_for("multas_empresa"))


@app.route("/api/condutores/<int:condutor_id>/veiculos", methods=["GET"])
@login_required
def api_veiculos_condutor(condutor_id):
    """API para retornar veículos associados a um condutor"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT DISTINCT v.id, v.placa, v.modelo 
            FROM veiculos v
            JOIN condutor_veiculo cv ON v.id = cv.veiculo_id
            WHERE cv.condutor_id = ?
            ORDER BY v.placa
        """,
            (condutor_id,),
        )

        veiculos = [
            {"id": row[0], "placa": row[1], "modelo": row[2]} for row in cur.fetchall()
        ]
        conn.close()

        return jsonify(veiculos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/adicionar-marca", methods=["POST"])
@login_required
def api_adicionar_marca():
    """API para adicionar nova marca de veículo"""
    try:
        data = request.get_json()
        marca = data.get("marca", "").strip()
        tipo = data.get("tipo", "").strip()

        if not marca:
            return (
                jsonify({"success": False, "message": "Nome da marca é obrigatório"}),
                400,
            )

        if tipo not in ["Carro", "Moto"]:
            return (
                jsonify({"success": False, "message": "Tipo de veículo inválido"}),
                400,
            )

        if tipo == "Carro":
            veiculos_list = VEICULOS_CARRO
        else:
            veiculos_list = VEICULOS_MOTO

        marca_existe = any(v.get("marca") == marca for v in veiculos_list)
        if marca_existe:
            return jsonify({"success": False, "message": "Esta marca já existe"}), 400

        veiculos_list.append({"marca": marca, "modelo": "", "anos": []})

        return jsonify({"success": True, "message": "Marca adicionada com sucesso"})
    except Exception as e:
        print(f"Erro ao adicionar marca: {e}")
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500


@app.route("/api/veiculos-com-manutencao", methods=["GET"])
@login_required
def api_veiculos_com_manutencao():
    """API para retornar todos os veículos com registros de manutenção"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT DISTINCT 
                v.id,
                v.placa,
                v.modelo,
                v.tipo,
                v.condutor,
                COUNT(m.id) as total_manutencoes,
                MAX(m.data_manutencao) as ultima_manutencao,
                SUM(COALESCE(m.valor_peca, 0) + COALESCE(m.mao_de_obra, 0)) as custo_total
            FROM veiculos v
            LEFT JOIN manutencao m ON v.id = m.veiculo_id
            WHERE m.id IS NOT NULL
            GROUP BY v.id, v.placa, v.modelo, v.tipo, v.condutor
            ORDER BY MAX(m.data_manutencao) DESC, v.placa
        """
        )

        rows = cur.fetchall()
        veiculos = []

        for row in rows:
            veiculos.append(
                {
                    "id": row[0],
                    "placa": row[1],
                    "modelo": row[2],
                    "tipo": row[3],
                    "condutor": row[4],
                    "total_manutencoes": row[5] or 0,
                    "ultima_manutencao": row[6],
                    "custo_total": float(row[7]) if row[7] else 0.0,
                }
            )

        conn.close()
        return jsonify(veiculos)
    except Exception as e:
        print(f"Erro ao buscar veículos com manutenção: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/adicionar-modelo", methods=["POST"])
@login_required
def api_adicionar_modelo():
    """API para adicionar novo modelo de veículo"""
    try:
        data = request.get_json()
        marca = data.get("marca", "").strip()
        modelo = data.get("modelo", "").strip()
        ano = data.get("ano", "").strip()
        tipo = data.get("tipo", "").strip()

        if not marca or not modelo:
            return (
                jsonify(
                    {"success": False, "message": "Marca e modelo são obrigatórios"}
                ),
                400,
            )

        if tipo not in ["Carro", "Moto"]:
            return (
                jsonify({"success": False, "message": "Tipo de veículo inválido"}),
                400,
            )

        if tipo == "Carro":
            veiculos_list = VEICULOS_CARRO
        else:
            veiculos_list = VEICULOS_MOTO

        veiculo_encontrado = None
        for veiculo in veiculos_list:
            if veiculo.get("marca") == marca and veiculo.get("modelo") == modelo:
                veiculo_encontrado = veiculo
                break

        if veiculo_encontrado:
            if ano and ano not in veiculo_encontrado.get("anos", []):
                veiculo_encontrado["anos"].append(ano)
                veiculo_encontrado["anos"] = sorted(
                    veiculo_encontrado["anos"], reverse=True
                )
            return jsonify(
                {"success": True, "message": "Modelo já existe, ano adicionado"}
            )

        anos_list = [int(ano)] if ano else []
        veiculos_list.append({"marca": marca, "modelo": modelo, "anos": anos_list})

        return jsonify({"success": True, "message": "Modelo adicionado com sucesso"})
    except Exception as e:
        print(f"Erro ao adicionar modelo: {e}")
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500


@app.route("/api/veiculos-disponveis", methods=["GET"])
@login_required
def api_veiculos_disponveis():
    """API para retornar todos os veículos disponíveis para manutenção"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, placa, modelo, tipo, condutor
            FROM veiculos
            ORDER BY placa
        """
        )

        rows = cur.fetchall()
        veiculos = []

        for row in rows:
            veiculos.append(
                {
                    "id": row[0],
                    "placa": row[1],
                    "modelo": row[2],
                    "tipo": row[3],
                    "condutor": row[4],
                }
            )

        conn.close()
        return jsonify(veiculos)
    except Exception as e:
        print(f"Erro ao buscar veículos disponíveis: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/registrar-manutencao", methods=["POST"])
@login_required
def api_registrar_manutencao():
    """API para registrar manutenção com múltiplas peças e mão de obra"""
    try:
        data = request.get_json()
        veiculo_id = data.get("veiculo_id")
        data_manutencao = data.get("data_manutencao")
        quilometragem_atual = data.get("quilometragem_atual")
        descricao_servico = data.get("descricao_servico")
        tecnico = data.get("tecnico")
        valor_peca = data.get("valor_peca", 0)
        mao_de_obra_valor = data.get("mao_de_obra_valor", 0)
        observacoes = data.get("observacoes", "")

        if (
            not veiculo_id
            or not data_manutencao
            or not quilometragem_atual
            or not descricao_servico
            or not tecnico
        ):
            return (
                jsonify(
                    {"success": False, "error": "Campos obrigatórios não preenchidos"}
                ),
                400,
            )

        try:
            valor_peca = float(valor_peca)
            mao_de_obra_valor = float(mao_de_obra_valor)
            quilometragem_atual = int(quilometragem_atual)
        except (ValueError, TypeError):
            return (
                jsonify({"success": False, "error": "Valores numéricos inválidos"}),
                400,
            )

        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id FROM veiculos WHERE id = ?", (veiculo_id,))
            if not cur.fetchone():
                return (
                    jsonify({"success": False, "error": "Veículo não encontrado"}),
                    404,
                )
            conn.close()
        except Exception as e:
            print(f"Erro ao verificar veículo: {e}")
            return (
                jsonify({"success": False, "error": "Erro ao verificar veículo"}),
                500,
            )

        nome_peca = descricao_servico
        try:
            manutencao = Manutencao.create(
                veiculo_id=veiculo_id,
                nome_peca=nome_peca,
                data_manutencao=data_manutencao,
                quilometragem_atual=quilometragem_atual,
                valor_peca=valor_peca,
                mao_de_obra=mao_de_obra_valor,
                observacoes=observacoes,
            )

            return jsonify(
                {
                    "success": True,
                    "message": "Manutenção registrada com sucesso",
                    "manutencao_id": manutencao.id,
                }
            )
        except Exception as e:
            print(f"Erro ao criar manutenção: {e}")
            return (
                jsonify({"success": False, "error": f"Erro ao registrar: {str(e)}"}),
                500,
            )

    except Exception as e:
        print(f"Erro ao registrar manutenção: {e}")
        return jsonify({"success": False, "error": f"Erro: {str(e)}"}), 500


@app.route("/api/adicionar-veiculo-manutencao", methods=["POST"])
@login_required
def api_adicionar_veiculo_manutencao():
    """API para adicionar novo veículo para manutenção"""
    try:
        data = request.get_json()
        placa = data.get("placa", "").strip().upper()
        modelo = data.get("modelo", "").strip()
        tipo = data.get("tipo", "Carro").strip()
        condutor = data.get("condutor", "").strip()

        if not placa or not modelo:
            return (
                jsonify(
                    {"success": False, "message": "Placa e modelo são obrigatórios"}
                ),
                400,
            )

        if tipo not in ["Carro", "Moto"]:
            return jsonify({"success": False, "message": "Tipo inválido"}), 400

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT id FROM veiculos WHERE placa = ?", (placa,))
        existing = cur.fetchone()

        if existing:
            conn.close()
            return jsonify({"success": False, "message": "Este veículo já existe"}), 400

        cur.execute(
            """
            INSERT INTO veiculos (placa, modelo, tipo, condutor)
            VALUES (?, ?, ?, ?)
        """,
            (placa, modelo, tipo, condutor if condutor else None),
        )

        conn.commit()
        veiculo_id = cur.lastrowid
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": "Veículo adicionado com sucesso",
                "veiculo_id": veiculo_id,
            }
        )
    except Exception as e:
        print(f"Erro ao adicionar veículo: {e}")
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500


@app.route("/api/adicionar-condutor", methods=["POST"])
@login_required
def api_adicionar_condutor():
    """API para adicionar novo condutor"""
    try:
        data = request.get_json()
        nome = data.get("nome", "").strip()
        cpf = data.get("cpf", "").strip()
        telefone = data.get("telefone", "").strip()

        if not nome:
            return (
                jsonify(
                    {"success": False, "message": "Nome do condutor é obrigatório"}
                ),
                400,
            )

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT id FROM condutores WHERE nome_completo = ?", (nome,))
        existing = cur.fetchone()

        if existing:
            conn.close()
            return (
                jsonify({"success": False, "message": "Este condutor já existe"}),
                400,
            )

        cur.execute(
            """
            INSERT INTO condutores (nome_completo, cpf, telefone, ativo)
            VALUES (?, ?, ?, 1)
        """,
            (nome, cpf if cpf else None, telefone if telefone else None),
        )

        conn.commit()
        condutor_id = cur.lastrowid
        conn.close()

        return jsonify(
            {
                "success": True,
                "message": "Condutor adicionado com sucesso",
                "condutor_id": condutor_id,
            }
        )
    except Exception as e:
        print(f"Erro ao adicionar condutor: {e}")
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500


@app.route("/api/veiculo-por-placa", methods=["GET"])
@login_required
def api_veiculo_por_placa():
    """API para retornar dados do veículo pela placa"""
    try:
        placa = request.args.get("placa", "").strip().upper()
        tipo = request.args.get("tipo", "").strip()

        if not placa or not tipo:
            return jsonify({"error": "Placa e tipo são obrigatórios"}), 400

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, placa, modelo, tipo, condutor, quilometragem, foto_carro
            FROM veiculos
            WHERE placa = ? AND tipo = ?
        """,
            (placa, tipo),
        )

        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({})

        veiculo = {
            "id": row[0],
            "placa": row[1],
            "modelo": row[2],
            "tipo": row[3],
            "condutor": row[4],
            "quilometragem": row[5],
            "foto_carro": row[6],
        }

        return jsonify(veiculo)
    except Exception as e:
        print(f"Erro ao buscar veículo por placa: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/salvar-notas-fiscais-veiculo", methods=["POST"])
@login_required
def api_salvar_notas_fiscais_veiculo():
    """API para salvar múltiplas notas fiscais para um veículo"""
    try:
        veiculo_id = request.form.get("veiculo_id")

        if not veiculo_id:
            return jsonify({"success": False, "error": "Veículo não especificado"}), 400

        if "arquivos" not in request.files:
            return jsonify({"success": False, "error": "Nenhum arquivo fornecido"}), 400

        try:
            veiculo_id = int(veiculo_id)
        except ValueError:
            return jsonify({"success": False, "error": "ID do veículo inválido"}), 400

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT id FROM veiculos WHERE id = ?", (veiculo_id,))
        if not cur.fetchone():
            conn.close()
            return jsonify({"success": False, "error": "Veículo não encontrado"}), 404

        upload_folder = os.path.join("static", "uploads", "notas_fiscais")
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        arquivos = request.files.getlist("arquivos")
        saved_count = 0

        for arquivo in arquivos:
            if arquivo and arquivo.filename:
                try:
                    filename = secure_filename(arquivo.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                    filename = timestamp + filename
                    filepath = os.path.join(upload_folder, filename)

                    arquivo.save(filepath)

                    cur.execute(
                        """
                        INSERT INTO notas_fiscais_veiculo 
                        (veiculo_id, nome_arquivo, caminho_arquivo)
                        VALUES (?, ?, ?)
                    """,
                        (veiculo_id, arquivo.filename, filepath),
                    )

                    saved_count += 1
                except Exception as e:
                    print(f"Erro ao salvar arquivo {arquivo.filename}: {e}")
                    continue

        conn.commit()
        conn.close()

        if saved_count > 0:
            return jsonify(
                {
                    "success": True,
                    "message": f"{saved_count} arquivo(s) salvo(s) com sucesso",
                }
            )
        else:
            return jsonify({"success": False, "error": "Nenhum arquivo foi salvo"}), 400

    except Exception as e:
        print(f"Erro ao salvar notas fiscais: {e}")
        return jsonify({"success": False, "error": f"Erro: {str(e)}"}), 500


@app.route("/api/notas-fiscais-veiculo/<int:veiculo_id>", methods=["GET"])
@login_required
def api_obter_notas_fiscais_veiculo(veiculo_id):
    """API para obter notas fiscais de um veículo"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, nome_arquivo, data_upload
            FROM notas_fiscais_veiculo
            WHERE veiculo_id = ?
            ORDER BY data_upload DESC
        """,
            (veiculo_id,),
        )

        rows = cur.fetchall()
        conn.close()

        notas = []
        for row in rows:
            notas.append({"id": row[0], "nome_arquivo": row[1], "data_upload": row[2]})

        return jsonify({"success": True, "notas": notas})
    except Exception as e:
        print(f"Erro ao obter notas fiscais: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/download-nota-fiscal/<int:nota_id>", methods=["GET"])
@login_required
def api_download_nota_fiscal(nota_id):
    """API para fazer download de uma nota fiscal"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT caminho_arquivo, nome_arquivo FROM notas_fiscais_veiculo WHERE id = ?",
            (nota_id,),
        )
        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Arquivo não encontrado"}), 404

        caminho, nome = row[0], row[1]

        if not os.path.exists(caminho):
            return jsonify({"error": "Arquivo não existe no servidor"}), 404

        return send_file(caminho, as_attachment=True, download_name=nome)
    except Exception as e:
        print(f"Erro ao fazer download: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/deletar-nota-fiscal/<int:nota_id>", methods=["DELETE"])
@login_required
def api_deletar_nota_fiscal(nota_id):
    """API para deletar uma nota fiscal"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT caminho_arquivo FROM notas_fiscais_veiculo WHERE id = ?", (nota_id,)
        )
        row = cur.fetchone()

        if not row:
            conn.close()
            return jsonify({"success": False, "error": "Arquivo não encontrado"}), 404

        caminho = row[0]

        if os.path.exists(caminho):
            try:
                os.remove(caminho)
            except Exception as e:
                print(f"Erro ao remover arquivo: {e}")

        cur.execute("DELETE FROM notas_fiscais_veiculo WHERE id = ?", (nota_id,))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Nota fiscal deletada com sucesso"})
    except Exception as e:
        print(f"Erro ao deletar nota fiscal: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/financeiro/veiculo", methods=["GET"])
@login_required
def financeiro_veiculo():
    """Página de gestão financeira por veículo"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        busca = request.args.get("busca", "").strip()
        data_inicio = request.args.get("data_inicio", "").strip()
        data_fim = request.args.get("data_fim", "").strip()

        veiculo_selecionado = None
        transacoes = []
        resumo_financeiro = {}
        detalhes_manutencao = []
        detalhes_combustivel = []
        total_transacoes = 0
        manutencoes_pendentes = []
        veiculos_encontrados = []

        if busca:
            cur.execute(
                """
                SELECT id, placa, modelo, condutor, tipo, foto_carro, foto_clrv, foto_cnh
                FROM veiculos
                WHERE placa LIKE ? OR modelo LIKE ? OR condutor LIKE ? OR tipo LIKE ?
                ORDER BY placa ASC
            """,
                (f"%{busca}%", f"%{busca}%", f"%{busca}%", f"%{busca}%"),
            )

            veiculos_rows = cur.fetchall()

            # Montar lista de veículos encontrados
            for row in veiculos_rows:
                foto = row[5] or row[6] or row[7] or None
                veiculos_encontrados.append({
                    "id": row[0],
                    "placa": row[1],
                    "modelo": row[2],
                    "condutor": row[3],
                    "tipo": row[4],
                    "foto_carro": foto,
                })

            # Se encontrou apenas um, seleciona automaticamente
            if len(veiculos_encontrados) == 1:
                veiculo_selecionado = veiculos_encontrados[0]
            # Se encontrou mais de um, seleciona o primeiro para exibição, mas mostra os outros para seleção
            elif len(veiculos_encontrados) > 1:
                veiculo_selecionado = veiculos_encontrados[0]

        # Se há um veículo selecionado, carregar seus dados financeiros
        if veiculo_selecionado:
            veiculo_id = veiculo_selecionado["id"]

            where_clause = "WHERE veiculo_id = ?"
            params = [veiculo_id]

            if data_inicio and data_fim:
                where_clause += " AND data_transacao BETWEEN ? AND ?"
                params.extend([data_inicio, data_fim])
            elif data_inicio:
                where_clause += " AND data_transacao >= ?"
                params.append(data_inicio)
            elif data_fim:
                where_clause += " AND data_transacao <= ?"
                params.append(data_fim)

            cur.execute(
                f"""
                SELECT id, tipo, descricao, valor, data_transacao, categoria, nota_fiscal
                FROM transacoes_veiculo
                {where_clause}
                ORDER BY data_transacao DESC
            """,
                params,
            )

            transacoes_data = cur.fetchall()
            transacoes = [
                {
                    "id": row[0],
                    "tipo": row[1],
                    "descricao": row[2],
                    "valor": row[3],
                    "data_transacao": row[4],
                    "categoria": row[5],
                    "nota_fiscal": row[6],
                }
                for row in transacoes_data
            ]

            cur.execute(
                f"""
                SELECT m.id, m.nome_peca, COALESCE(m.valor_peca, 0) as valor_peca, COALESCE(m.mao_de_obra, 0) as mao_de_obra, COALESCE(m.status, 'pendente') as status
                FROM manutencao m
                WHERE m.veiculo_id = ?
                AND m.data_manutencao BETWEEN ? AND ?
                ORDER BY m.data_manutencao DESC
            """,
                [
                    veiculo_id,
                    data_inicio or "1900-01-01",
                    data_fim or datetime.now().strftime("%Y-%m-%d"),
                ],
            )

            detalhes_manutencao = [
                {
                    "id": row[0],
                    "nome_peca": row[1],
                    "valor_peca": row[2],
                    "mao_de_obra": row[3],
                    "valor_total": row[2] + row[3],
                    "status": row[4],
                }
                for row in cur.fetchall()
            ]
            
            # Buscar se há manutenções pendentes
            manutencoes_pendentes = [m for m in detalhes_manutencao if m.get('status') != 'concluida']

            cur.execute(
                f"""
                SELECT c.id, c.data_abastecimento, c.quantidade_litros, c.valor_total
                FROM combustivel c
                WHERE c.veiculo_id = ?
                AND c.data_abastecimento BETWEEN ? AND ?
                ORDER BY c.data_abastecimento DESC
            """,
                [
                    veiculo_id,
                    data_inicio or "1900-01-01",
                    data_fim or datetime.now().strftime("%Y-%m-%d"),
                ],
            )

            detalhes_combustivel = [
                {
                    "data_abastecimento": row[1],
                    "quantidade_litros": row[2],
                    "valor_total": row[3],
                }
                for row in cur.fetchall()
            ]

            total_manutencao = (
                sum(m["valor_total"] for m in detalhes_manutencao)
                if detalhes_manutencao
                else 0
            )
            total_combustivel = (
                sum(c["valor_total"] for c in detalhes_combustivel)
                if detalhes_combustivel
                else 0
            )
            total_outras = (
                sum(
                    t["valor"]
                    for t in transacoes
                    if t["tipo"] not in ["Manutenção", "Combustível"]
                )
                if transacoes
                else 0
            )

            total_transacoes = total_manutencao + total_combustivel + total_outras

            resumo_financeiro = {
                "total_despesas": total_transacoes,
                "manutencao": total_manutencao,
                "combustivel": total_combustivel,
                "outras": total_outras,
                "qty_manutencao": len(detalhes_manutencao),
                "qty_combustivel": len(detalhes_combustivel),
                "qty_outras": len(
                    [
                        t
                        for t in transacoes
                        if t["tipo"] not in ["Manutenção", "Combustível"]
                    ]
                ),
            }

        cur.close()

        return render_template(
            "financeiro/financeiro_veiculo.html",
            veiculo_selecionado=veiculo_selecionado,
            transacoes=transacoes,
            resumo_financeiro=resumo_financeiro,
            detalhes_manutencao=detalhes_manutencao,
            detalhes_combustivel=detalhes_combustivel,
            total_transacoes=total_transacoes,
            busca_veiculo=busca,
            data_inicio=data_inicio,
            data_fim=data_fim,
            manutencoes_pendentes=manutencoes_pendentes,
            veiculos_encontrados=veiculos_encontrados,
        )
    except Exception as e:
        print(f"Erro ao listar financeiro: {e}")
        flash(f"Erro ao listar financeiro: {e}", "danger")
        return redirect(url_for("dashboard"))


@app.route("/api/financeiro/veiculo/transacao", methods=["POST"])
@login_required
def adicionar_transacao_veiculo():
    """Adiciona uma nova transação financeira para um veículo"""
    try:
        veiculo_id = request.form.get("veiculo_id")
        tipo = request.form.get("tipo")
        descricao = request.form.get("descricao", "")
        valor = float(request.form.get("valor"))
        data_transacao = request.form.get("data_transacao")
        categoria = request.form.get("categoria", "")
        observacoes = request.form.get("observacoes", "")

        nota_fiscal = None
        if "nota_fiscal" in request.files:
            file = request.files["nota_fiscal"]
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"transacao_{timestamp}_{filename}"
                filepath = os.path.join(ANEXOS_DIR, filename)
                file.save(filepath)
                nota_fiscal = filename

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO transacoes_veiculo 
            (veiculo_id, tipo, descricao, valor, data_transacao, categoria, observacoes, nota_fiscal, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
            (
                veiculo_id,
                tipo,
                descricao,
                valor,
                data_transacao,
                categoria,
                observacoes,
                nota_fiscal,
            ),
        )

        conn.commit()

        cur.execute("SELECT placa FROM veiculos WHERE id = ?", (veiculo_id,))
        veiculo = cur.fetchone()
        placa = veiculo[0] if veiculo else ""
        conn.close()

        flash("Transação registrada com sucesso!", "success")
        return redirect(url_for("financeiro_veiculo", busca=placa))
    except Exception as e:
        print(f"Erro ao registrar transação: {e}")
        flash(f"Erro ao registrar transação: {e}", "danger")
        return redirect(url_for("financeiro_veiculo"))


@app.route("/api/financeiro/veiculo/transacao/obter", methods=["GET"])
@login_required
def obter_transacao_veiculo():
    """Obtém dados de uma transação para edição"""
    try:
        transacao_id = request.args.get("id")

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, tipo, descricao, valor, data_transacao, categoria, observacoes, nota_fiscal
            FROM transacoes_veiculo
            WHERE id = ?
        """,
            (transacao_id,),
        )

        row = cur.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Transação não encontrada"}), 404

        return jsonify(
            {
                "id": row[0],
                "tipo": row[1],
                "descricao": row[2],
                "valor": row[3],
                "data_transacao": row[4],
                "categoria": row[5],
                "observacoes": row[6],
                "nota_fiscal": row[7],
            }
        )
    except Exception as e:
        print(f"Erro ao obter transação: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/financeiro/veiculo/transacao/editar", methods=["POST"])
@login_required
def editar_transacao_veiculo():
    """Edita uma transação financeira"""
    try:
        transacao_id = request.form.get("transacao_id")
        tipo = request.form.get("tipo")
        descricao = request.form.get("descricao", "")
        valor = float(request.form.get("valor"))
        data_transacao = request.form.get("data_transacao")
        categoria = request.form.get("categoria", "")
        observacoes = request.form.get("observacoes", "")

        conn = get_conn()
        cur = conn.cursor()

        nota_fiscal = None
        if "nota_fiscal" in request.files:
            file = request.files["nota_fiscal"]
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"transacao_{timestamp}_{filename}"
                filepath = os.path.join(ANEXOS_DIR, filename)
                file.save(filepath)
                nota_fiscal = filename

                cur.execute(
                    "SELECT nota_fiscal FROM transacoes_veiculo WHERE id = ?",
                    (transacao_id,),
                )
                old_file = cur.fetchone()
                if old_file and old_file[0]:
                    old_path = os.path.join(ANEXOS_DIR, old_file[0])
                    if os.path.exists(old_path):
                        os.remove(old_path)

        if nota_fiscal:
            cur.execute(
                """
                UPDATE transacoes_veiculo
                SET tipo = ?, descricao = ?, valor = ?, data_transacao = ?, 
                    categoria = ?, observacoes = ?, nota_fiscal = ?, atualizado_em = datetime('now')
                WHERE id = ?
            """,
                (
                    tipo,
                    descricao,
                    valor,
                    data_transacao,
                    categoria,
                    observacoes,
                    nota_fiscal,
                    transacao_id,
                ),
            )
        else:
            cur.execute(
                """
                UPDATE transacoes_veiculo
                SET tipo = ?, descricao = ?, valor = ?, data_transacao = ?, 
                    categoria = ?, observacoes = ?, atualizado_em = datetime('now')
                WHERE id = ?
            """,
                (
                    tipo,
                    descricao,
                    valor,
                    data_transacao,
                    categoria,
                    observacoes,
                    transacao_id,
                ),
            )

        conn.commit()
        conn.close()

        flash("Transação atualizada com sucesso!", "success")
        return redirect(request.referrer or url_for("financeiro_veiculo"))
    except Exception as e:
        print(f"Erro ao editar transação: {e}")
        flash(f"Erro ao editar transação: {e}", "danger")
        return redirect(request.referrer or url_for("financeiro_veiculo"))


@app.route("/api/financeiro/veiculo/transacao/deletar", methods=["POST"])
@login_required
def deletar_transacao_veiculo():
    """Deleta uma transação financeira"""
    try:
        data = request.get_json()
        transacao_id = data.get("transacao_id")

        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT nota_fiscal FROM transacoes_veiculo WHERE id = ?", (transacao_id,)
        )
        row = cur.fetchone()

        if row and row[0]:
            filepath = os.path.join(ANEXOS_DIR, row[0])
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Erro ao remover arquivo: {e}")

        cur.execute("DELETE FROM transacoes_veiculo WHERE id = ?", (transacao_id,))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Transação deletada com sucesso"})
    except Exception as e:
        print(f"Erro ao deletar transação: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/validar-condutor/<field>/<value>", methods=["GET"])
@login_required
def validar_condutor(field, value):
    """Valida se um campo já existe no banco de dados"""
    try:
        if not value or len(value.strip()) == 0:
            return jsonify({"exists": False})
        
        conn = get_conn()
        cur = conn.cursor()
        
        if field == "cpf":
            cur.execute("SELECT id FROM condutores WHERE cpf = ?", (value,))
        elif field == "email":
            cur.execute("SELECT id FROM condutores WHERE email = ?", (value,))
        else:
            conn.close()
            return jsonify({"exists": False})
        
        exists = cur.fetchone() is not None
        conn.close()
        
        return jsonify({"exists": exists})
    except Exception as e:
        print(f"Erro ao validar condutor: {e}")
        return jsonify({"exists": False}), 500


@app.route("/salvar-condutor", methods=["POST"])
@login_required
def salvar_condutor():
    """Salva um novo condutor via formulário modal"""
    try:
        # O formulário envia como 'nome', não 'nome_completo'
        nome_completo = request.form.get("nome", "") or request.form.get("nome_completo", "")
        nome_completo = nome_completo.strip()
        cpf = request.form.get("cpf", "").strip() or None
        telefone = request.form.get("telefone", "").strip() or None
        email = request.form.get("email", "").strip() or None
        endereco = request.form.get("endereco", "").strip() or None

        if not nome_completo:
            return jsonify({"error": "Nome é obrigatório"}), 400

        conn = get_conn()
        cur = conn.cursor()
        
        # Verificar se CPF já existe (se fornecido)
        if cpf:
            cur.execute("SELECT id FROM condutores WHERE cpf = ?", (cpf,))
            if cur.fetchone():
                conn.close()
                return jsonify({"error": "Este CPF já está cadastrado"}), 400

        try:
            cur.execute(
                """
                INSERT INTO condutores (nome_completo, cpf, telefone, email, endereco, ativo)
                VALUES (?, ?, ?, ?, ?, 1)
            """,
                (nome_completo, cpf, telefone, email, endereco),
            )
            conn.commit()
            condutor_id = cur.lastrowid
            conn.close()
            return jsonify({"success": True, "condutor_id": condutor_id})
        except Exception as db_error:
            conn.close()
            # Captura erro de constraint
            if "UNIQUE constraint failed" in str(db_error):
                return jsonify({"error": "Este CPF já está cadastrado"}), 400
            raise db_error
            
    except Exception as e:
        print(f"Erro ao salvar condutor: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/cadastrar-veiculo", methods=["GET", "POST"])
@login_required
def cadastrar_veiculo():
    """Página de cadastro completo de veículo"""
    if request.method == "POST":
        try:
            tipo = (request.form.get("tipo") or "Carro").strip()
            condutor = (request.form.get("condutor") or "").strip()
            placa = (request.form.get("placa") or "").strip().upper()
            quilometragem = (request.form.get("quilometragem") or "0").strip()
            observacoes = (request.form.get("observacoes") or "").strip()
            modelo = (request.form.get("modelo") or "").strip() or None
            foto_carro = request.files.get("foto_carro")
            
            # Validações básicas
            if not placa:
                flash("Placa é obrigatória", "error")
                return render_template("cadastrar_veiculo.html")
            
            conn = get_conn()
            cur = conn.cursor()
            
            # Verificar se veículo já existe
            cur.execute("SELECT id FROM veiculos WHERE placa = ?", (placa,))
            if cur.fetchone():
                conn.close()
                flash("Veículo com esta placa já existe", "error")
                return render_template("cadastrar_veiculo.html")
            
            # Salvar foto se fornecida
            foto_filename = None
            if foto_carro and foto_carro.filename:
                from services import _save_file_storage
                foto_filename, _ = _save_file_storage(foto_carro, prefix="veiculo")
            
            # Inserir veículo no banco de dados (apenas colunas existentes)
            data = datetime.now().strftime("%d/%m/%Y %H:%M")
            cur.execute("""
                INSERT INTO veiculos (placa, tipo, condutor, quilometragem, data, observacoes, foto_carro, modelo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (placa, tipo, condutor or None, quilometragem, data, observacoes or None, foto_filename, modelo))
            
            conn.commit()
            conn.close()
            
            flash("Veículo cadastrado com sucesso!", "success")
            return redirect(url_for("dashboard"))
            
        except Exception as e:
            print(f"Erro ao cadastrar veículo: {e}")
            flash(f"Erro ao cadastrar veículo: {str(e)}", "error")
            return render_template("cadastrar_veiculo.html")
    
    return render_template("cadastrar_veiculo.html")


@app.route("/api/verificar-cpf", methods=["GET"])
@login_required
def verificar_cpf():
    """Verifica se o CPF já existe no sistema"""
    cpf = request.args.get('cpf', '').strip()
    
    if not cpf:
        return jsonify({'existe': False, 'mensagem': ''})
    
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM condutores WHERE cpf = ?", (cpf,))
        resultado = cur.fetchone()
        conn.close()
        
        if resultado:
            return jsonify({
                'existe': True,
                'mensagem': f'CPF já cadastrado para: {resultado[1]}'
            })
        else:
            return jsonify({'existe': False, 'mensagem': ''})
    except Exception as e:
        print(f"Erro ao verificar CPF: {e}")
        return jsonify({'existe': False, 'mensagem': '', 'erro': str(e)})

@app.route("/cadastrar-condutor", methods=["GET", "POST"])
@login_required
def cadastrar_condutor():
    """Página de cadastro completo de condutor"""
    if request.method == "POST":
        try:
            # Dados pessoais
            nome = request.form.get("nome", "").strip()
            cpf = request.form.get("cpf", "").strip()
            rg = request.form.get("rg", "").strip()
            data_nascimento = request.form.get("data_nascimento", "").strip()
            endereco = request.form.get("endereco", "").strip()
            telefone = request.form.get("telefone", "").strip()
            email = request.form.get("email", "").strip()
            
            # Foto do condutor
            foto_condutor = request.files.get("foto_condutor")
            
            # Dados da CNH
            numero_cnh = request.form.get("numero_cnh", "").strip()
            categoria_cnh = request.form.get("categoria_cnh", "").strip()
            data_emissao_cnh = request.form.get("data_emissao_cnh", "").strip()
            data_validade_cnh = request.form.get("data_validade_cnh", "").strip()
            observacoes = request.form.get("observacoes", "").strip()
            
            # Validações básicas
            if not nome or not cpf or not data_nascimento or not telefone or not email:
                flash("Nome, CPF, data de nascimento, telefone e e-mail são obrigatórios", "error")
                return render_template("cadastrar_condutor.html")
            
            if not numero_cnh or not categoria_cnh or not data_emissao_cnh or not data_validade_cnh:
                flash("Número da CNH, categoria, data de emissão e data de validade são obrigatórios", "error")
                return render_template("cadastrar_condutor.html")
            
            conn = get_conn()
            cur = conn.cursor()
            
            # Verificar se condutor já existe pelo CPF
            cur.execute("SELECT id FROM condutores WHERE cpf = ?", (cpf,))
            if cur.fetchone():
                conn.close()
                flash("Condutor com este CPF já existe", "error")
                return render_template("cadastrar_condutor.html")
            
            # Salvar foto se fornecida
            foto_filename = None
            if foto_condutor and foto_condutor.filename:
                from services import _save_file_storage
                foto_filename, _ = _save_file_storage(foto_condutor, prefix="condutor")
            
            # Inserir condutor no banco de dados
            cur.execute(
                """
                INSERT INTO condutores (
                    nome_completo, cpf, rg, data_nascimento, endereco, telefone, email, foto_condutor,
                    cnh_numero, cnh_categoria, cnh_data_emissao, cnh_data_validade, notas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    nome, cpf, rg, data_nascimento, endereco, telefone, email, foto_filename,
                    numero_cnh, categoria_cnh, data_emissao_cnh, data_validade_cnh, observacoes
                )
            )
            
            conn.commit()
            conn.close()
            
            flash("Condutor cadastrado com sucesso!", "success")
            return redirect(url_for("dashboard"))
            
        except Exception as e:
            print(f"Erro ao cadastrar condutor: {e}")
            flash(f"Erro ao cadastrar condutor: {str(e)}", "error")
            return render_template("cadastrar_condutor.html")
    
    return render_template("cadastrar_condutor.html")


@app.route("/salvar-veiculo", methods=["POST"])
@login_required
def salvar_veiculo():
    """Salva um novo veículo via formulário modal"""
    try:
        placa = request.form.get("placa", "").strip().upper()
        modelo = request.form.get("modelo", "").strip()
        tipo = request.form.get("tipo", "Carro").strip()
        condutor = request.form.get("condutor", "").strip() or None
        observacoes = request.form.get("observacoes", "").strip() or None

        if not placa or not modelo:
            return jsonify({"error": "Placa e modelo são obrigatórios"}), 400

        conn = get_conn()
        cur = conn.cursor()

        cur.execute("SELECT id FROM veiculos WHERE placa = ?", (placa,))
        if cur.fetchone():
            conn.close()
            return jsonify({"error": "Este veículo já existe"}), 400

        cur.execute(
            """
            INSERT INTO veiculos (placa, modelo, tipo, condutor, observacoes)
            VALUES (?, ?, ?, ?, ?)
        """,
            (placa, modelo, tipo, condutor, observacoes),
        )

        conn.commit()
        veiculo_id = cur.lastrowid
        conn.close()

        return jsonify({"success": True, "veiculo_id": veiculo_id})
    except Exception as e:
        print(f"Erro ao salvar veículo: {e}")
        return jsonify({"error": str(e)}), 500


def create_admin_user():
    """Cria o usuário administrador padrão se não existir"""
    admin = User.find_by_username("carlosme")

    if not admin:
        try:
            admin = User.create(
                username="carlosme", password="201127121981", email=None, is_admin=True
            )
            print("\n" + "=" * 60)
            print("USUÁRIO ADMINISTRADOR CRIADO COM SUCESSO")
            print("=" * 60)
            print(f"Usuário: carlosme")
            print(f"Senha: 201127121981")
            print("=" * 60 + "\n")
        except Exception as e:
            print(f"Erro ao criar usuário administrador: {e}")
    else:
        print("Usuário administrador 'carlosme' já existe no banco de dados.")


@app.route("/api/ml/predicao-custo/<int:veiculo_id>", methods=["GET"])
@login_required
def predicao_custo(veiculo_id):
    """API para previsão de custo usando ML"""
    try:
        km_estimado = request.args.get("km", 1500, type=int)
        resultado = prever_custo_veiculo(veiculo_id, km_estimado)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/ml/risco-falha/<int:veiculo_id>", methods=["GET"])
@login_required
def risco_falha(veiculo_id):
    """API para avaliação de risco de falha usando ML"""
    try:
        resultado = avaliar_risco_falha_veiculo(veiculo_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/ml/treinar/<int:veiculo_id>", methods=["POST"])
@admin_required
def treinar_modelo(veiculo_id):
    """API para treinar modelos de ML para um veículo"""
    try:
        resultado = treinar_modelo_ml_veiculo(veiculo_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/inteligencia-dados")
@login_required
def inteligencia_dados():
    """Página de inteligência de dados com previsões ML"""
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, placa, modelo, condutor, tipo
        FROM veiculos
        ORDER BY placa ASC
    """
    )

    veiculos_raw = cur.fetchall()
    conn.close()

    veiculos = []
    for row in veiculos_raw:
        veiculo_id, placa, modelo, condutor, tipo = row

        predicao_custo = prever_custo_veiculo(veiculo_id)
        risco_falha_resultado = avaliar_risco_falha_veiculo(veiculo_id)

        veiculos.append(
            {
                "id": veiculo_id,
                "placa": placa,
                "modelo": modelo,
                "condutor": condutor,
                "tipo": tipo,
                "predicao_custo": predicao_custo,
                "risco_falha": risco_falha_resultado,
            }
        )

    return render_template("inteligencia_dados.html", veiculos=veiculos)


@app.route("/indicadores-avancados")
@login_required
def indicadores_avancados():
    """Página de indicadores avançados"""
    benchmarking_veiculos = obter_benchmarking_veiculos(current_user.id)
    benchmarking_condutores = obter_benchmarking_condutores(current_user.id)

    return render_template(
        "indicadores_avancados.html",
        benchmarking_veiculos=benchmarking_veiculos,
        benchmarking_condutores=benchmarking_condutores,
    )


@app.route("/api/indicadores/custo-rota/<int:veiculo_id>", methods=["GET"])
@login_required
def api_custo_rota(veiculo_id):
    """API para obter custo por rota"""
    try:
        resultado = obter_custo_por_rota(veiculo_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/indicadores/eficiencia-condutor/<int:condutor_id>", methods=["GET"])
@login_required
def api_eficiencia_condutor(condutor_id):
    """API para obter eficiência do condutor"""
    try:
        resultado = obter_eficiencia_condutor(condutor_id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/indicadores/benchmarking-veiculos", methods=["GET"])
@login_required
def api_benchmarking_veiculos():
    """API para obter benchmarking de veículos"""
    try:
        resultado = obter_benchmarking_veiculos(current_user.id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/indicadores/benchmarking-condutores", methods=["GET"])
@login_required
def api_benchmarking_condutores():
    """API para obter benchmarking de condutores"""
    try:
        resultado = obter_benchmarking_condutores(current_user.id)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/veiculos/listar-detalhes", methods=["GET"])
@login_required
def api_listar_veiculos_detalhes():
    """API para retornar lista de veículos em JSON com detalhes"""
    conn = get_conn()
    cur = conn.cursor()
    
    # Listar todos os veículos
    cur.execute("SELECT id, placa, modelo, tipo, ano FROM veiculos ORDER BY placa ASC")
    veiculos = cur.fetchall()
    conn.close()
    
    # Retornar todos os veículos
    return jsonify([
        {
            "id": v["id"],
            "placa": v.get("placa", ""),
            "modelo": v.get("modelo", ""),
            "marca": "",  # A tabela não tem coluna marca
            "ano": v.get("ano", ""),
            "tipo": v.get("tipo", "")
        }
        for v in [dict(row) for row in veiculos]
    ])


# ===================== ROTAS PARA CONFIGURAÇÕES =====================

@app.route("/configuracoes")
@admin_required
def configuracoes():
    """Página de configurações do sistema"""
    twilio_config = get_twilio_config()
    users = User.get_all_users()
    return render_template("configuracoes.html", twilio_config=twilio_config, users=users)


@app.route("/configuracoes/<config_type>", methods=["POST"])
@admin_required
def atualizar_configuracoes(config_type):
    """Atualiza configurações do sistema"""
    try:
        if config_type == "twilio":
            config_data = {
                "TWILIO_ACCOUNT_SID": request.form.get("TWILIO_ACCOUNT_SID", ""),
                "TWILIO_AUTH_TOKEN": request.form.get("TWILIO_AUTH_TOKEN", ""),
                "TWILIO_WHATSAPP_FROM": request.form.get("TWILIO_WHATSAPP_FROM", ""),
                "ADMIN_WHATSAPP": request.form.get("ADMIN_WHATSAPP", ""),
            }

            if ConfigManager.update_twilio_config(config_data):
                flash("Configurações do Twilio atualizadas com sucesso!", "success")
            else:
                flash("Erro ao atualizar configurações do Twilio.", "error")

        elif config_type == "email":
            config_data = {
                "MAIL_SERVER": request.form.get("MAIL_SERVER", ""),
                "MAIL_PORT": request.form.get("MAIL_PORT", ""),
                "MAIL_USERNAME": request.form.get("MAIL_USERNAME", ""),
                "MAIL_PASSWORD": request.form.get("MAIL_PASSWORD", ""),
                "MAIL_DEFAULT_SENDER": request.form.get("MAIL_DEFAULT_SENDER", ""),
            }

            if ConfigManager.update_email_config(config_data):
                flash("Configurações de email atualizadas com sucesso!", "success")
            else:
                flash("Erro ao atualizar configurações de email.", "error")

        return redirect(url_for("configuracoes"))

    except Exception as e:
        flash(f"Erro ao atualizar configurações: {str(e)}", "error")
        return redirect(url_for("configuracoes"))


@app.route("/api/verificar-status-twilio", methods=["GET"])
@admin_required
def verificar_status_twilio():
    """API para verificar status da conexão com Twilio"""
    status = verify_twilio_connection()
    return jsonify(status)


# ===================== ROTAS PARA PERMISSÕES =====================

@app.route("/api/permissoes", methods=["GET"])
@admin_required
def get_permissoes():
    """API para obter todas as permissões"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.executemany(
            """
            INSERT OR IGNORE INTO permissions 
            (feature_key, feature_name, description, icon, category, admin_enabled, user_enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            [
                ("veiculos_excluir_placa", "Excluir por Placa", "Excluir veículo e vínculos pela placa", "bi-trash", "Veículos", 1, 0),
                ("sistema_limpar_orfaos", "Limpar Órfãos", "Remover registros órfãos do sistema", "bi-broom", "Sistema", 1, 0),
            ],
        )
        cur.execute("""
            SELECT id, feature_key, feature_name, description, icon, category, 
                   admin_enabled, user_enabled
            FROM permissions
            ORDER BY category, feature_name
        """)
        rows = cur.fetchall()
        permissoes = []
        for row in rows:
            permissoes.append({
                'id': row[0],
                'feature_key': row[1],
                'feature_name': row[2],
                'description': row[3],
                'icon': row[4],
                'category': row[5],
                'admin_enabled': bool(row[6]),
                'user_enabled': bool(row[7])
            })
        return jsonify(permissoes)
    except Exception as e:
        print(f"Erro ao obter permissões: {e}")
        return jsonify([])


# ===== ROTAS PARA GERENCIAMENTO DE ROLES =====

@app.route("/api/roles", methods=["GET"])
@admin_required
def api_get_roles():
    """API para obter todos os roles"""
    try:
        roles = get_all_roles()
        return jsonify({"roles": roles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/roles/<int:role_id>/permissions", methods=["GET"])
@admin_required
def api_get_role_permissions(role_id):
    """API para obter permissões de um role específico"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Buscar informações do role
        cur.execute("SELECT * FROM roles WHERE id = ?", (role_id,))
        role = cur.fetchone()

        if not role:
            return jsonify({"error": "Role não encontrado"}), 404

        # Buscar permissões do role
        cur.execute("""
            SELECT p.feature_key, p.feature_name, p.description, p.icon, p.category
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_key = p.feature_key
            WHERE rp.role_id = ?
            ORDER BY p.category, p.feature_name
        """, (role_id,))

        permissions = [dict(row) for row in cur.fetchall()]

        conn.close()

        return jsonify({
            "role": dict(role),
            "permissions": permissions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/roles/<int:role_id>/permissions", methods=["POST"])
@admin_required
def api_update_role_permissions(role_id):
    """API para atualizar permissões de um role"""
    try:
        data = request.get_json()
        permission_keys = data.get("permissions", [])

        conn = get_conn()
        cur = conn.cursor()

        # Verificar se role existe
        cur.execute("SELECT id FROM roles WHERE id = ?", (role_id,))
        if not cur.fetchone():
            return jsonify({"error": "Role não encontrado"}), 404

        # Limpar permissões atuais
        cur.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))

        # Adicionar novas permissões
        for permission_key in permission_keys:
            cur.execute("""
                INSERT INTO role_permissions (role_id, permission_key)
                VALUES (?, ?)
            """, (role_id, permission_key))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Permissões atualizadas"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>/roles", methods=["GET"])
@admin_required
def api_get_user_roles(user_id):
    """API para obter roles de um usuário"""
    try:
        roles = get_user_roles(user_id)
        return jsonify({"roles": roles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/roles", methods=["POST"])
@admin_required
def api_create_role():
    """API para criar um novo role"""
    try:
        data = request.get_json()

        conn = get_conn()
        cur = conn.cursor()

        # Verificar se role já existe
        cur.execute("SELECT id FROM roles WHERE name = ?", (data['name'],))
        if cur.fetchone():
            return jsonify({"error": "Já existe um grupo com este nome"}), 400

        # Inserir novo role
        cur.execute("""
            INSERT INTO roles (name, display_name, description, color, icon, is_system_role)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (
            data['name'],
            data['display_name'],
            data['description'] or '',
            data['color'] or '#6c757d',
            data['icon'] or 'bi-people'
        ))

        role_id = cur.lastrowid

        # Inserir permissões do role
        for permission_key in data.get('permissions', []):
            cur.execute("""
                INSERT INTO role_permissions (role_id, permission_key)
                VALUES (?, ?)
            """, (role_id, permission_key))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "role_id": role_id, "message": "Grupo criado com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/roles/<int:role_id>", methods=["PUT"])
@admin_required
def api_update_role(role_id):
    """API para atualizar um role existente"""
    try:
        data = request.get_json()

        conn = get_conn()
        cur = conn.cursor()

        # Verificar se role existe e não é sistema
        cur.execute("SELECT is_system_role FROM roles WHERE id = ?", (role_id,))
        role_data = cur.fetchone()
        if not role_data:
            return jsonify({"error": "Grupo não encontrado"}), 404
        if role_data[0]:  # is_system_role
            return jsonify({"error": "Não é possível editar grupos do sistema"}), 400

        # Atualizar dados do role
        cur.execute("""
            UPDATE roles
            SET display_name = ?, description = ?, color = ?, icon = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data['display_name'],
            data['description'] or '',
            data['color'] or '#6c757d',
            data['icon'] or 'bi-people',
            role_id
        ))

        # Limpar permissões atuais
        cur.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))

        # Inserir novas permissões
        for permission_key in data.get('permissions', []):
            cur.execute("""
                INSERT INTO role_permissions (role_id, permission_key)
                VALUES (?, ?)
            """, (role_id, permission_key))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Grupo atualizado com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/roles/<int:role_id>", methods=["DELETE"])
@admin_required
def api_delete_role(role_id):
    """API para deletar um role"""
    try:
        conn = get_conn()
        cur = conn.cursor()

        # Verificar se role existe e não é sistema
        cur.execute("SELECT is_system_role FROM roles WHERE id = ?", (role_id,))
        role_data = cur.fetchone()
        if not role_data:
            return jsonify({"error": "Grupo não encontrado"}), 404
        if role_data[0]:  # is_system_role
            return jsonify({"error": "Não é possível deletar grupos do sistema"}), 400

        # Verificar se há usuários neste role
        cur.execute("SELECT COUNT(*) FROM user_roles WHERE role_id = ?", (role_id,))
        user_count = cur.fetchone()[0]
        if user_count > 0:
            return jsonify({"error": f"Não é possível deletar grupo com {user_count} usuário(s) atribuído(s)"}), 400

        # Deletar permissões e depois o role
        cur.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
        cur.execute("DELETE FROM roles WHERE id = ?", (role_id,))

        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Grupo deletado com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/users/<int:user_id>/roles", methods=["POST"])
@admin_required
def api_assign_user_roles(user_id):
    """API para atribuir roles a um usuário"""
    try:
        data = request.get_json()
        role_ids = data.get("role_ids", [])

        conn = get_conn()
        cur = conn.cursor()

        # Verificar se usuário existe
        cur.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cur.fetchone():
            return jsonify({"error": "Usuário não encontrado"}), 404

        # Limpar roles atuais
        cur.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))

        # Atribuir novos roles
        for role_id in role_ids:
            assign_role_to_user(user_id, role_id, current_user.id)

        conn.close()

        return jsonify({"success": True, "message": "Roles atribuídos com sucesso"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/permissoes/atualizar", methods=["POST"])
@admin_required
def atualizar_permissao():
    """API para atualizar uma permissão"""
    try:
        data = request.get_json()
        permission_id = data.get('permission_id')
        role = data.get('role')  # 'admin' ou 'user'
        enabled = data.get('enabled')

        if not permission_id or not role:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400

        conn = get_conn()
        cur = conn.cursor()

        if role == 'admin':
            cur.execute("""
                UPDATE permissions 
                SET admin_enabled = ?
                WHERE id = ?
            """, (1 if enabled else 0, permission_id))
        elif role == 'user':
            cur.execute("""
                UPDATE permissions 
                SET user_enabled = ?
                WHERE id = ?
            """, (1 if enabled else 0, permission_id))
        else:
            return jsonify({'success': False, 'error': 'Role inválido'}), 400

        conn.commit()
        return jsonify({'success': True})

    except Exception as e:
        print(f"Erro ao atualizar permissão: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ===================== ROTAS PARA DOCUMENTOS E ALARMES =====================

@app.route("/documentos")
@login_required
def buscar_documentos():
    """Página de busca de documentos por placa"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        # Buscar últimos 5 veículos acessados
        cur.execute("SELECT id, placa, modelo FROM veiculos ORDER BY id DESC LIMIT 5")
        veiculos_recentes = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        return render_template(
            "buscar_documentos.html",
            veiculos_recentes=veiculos_recentes
        )
    except Exception as e:
        flash(f"Erro: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/documentos", methods=["POST"])
@login_required
def buscar_documentos_post():
    """Processa busca de documentos por placa"""
    placa = request.form.get("placa", "").strip().upper()
    
    if not placa:
        flash("Insira uma placa válida", "warning")
        return redirect(url_for("buscar_documentos"))
    
    # Remover hífen e caracteres especiais para busca
    placa_limpa = placa.replace("-", "").replace(" ", "")
    
    # Tentar encontrar por placa exata ou parcial
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, placa FROM veiculos WHERE placa LIKE ? OR REPLACE(placa, '-', '') LIKE ?", 
                (f"%{placa}%", f"%{placa_limpa}%"))
    resultado = cur.fetchone()
    conn.close()
    
    if resultado:
        veiculo_id = resultado[0]
        return redirect(url_for("listar_documentos", veiculo_id=veiculo_id))
    else:
        flash(f"Nenhum veículo encontrado com placa '{placa}'", "warning")
        return redirect(url_for("buscar_documentos"))


@app.route("/documentos/<int:veiculo_id>")
@login_required
def listar_documentos(veiculo_id):
    """Lista documentos de um veículo"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM veiculos WHERE id = ?", (veiculo_id,))
        veiculo = dict(cur.fetchone())
        conn.close()
        
        documentos = Documento.obter_por_veiculo(veiculo_id)
        alertas = Alerta.obter_por_veiculo(veiculo_id, apenas_nao_lidos=True)
        
        return render_template(
            "documentos.html",
            veiculo=veiculo,
            documentos=documentos,
            alertas=alertas
        )
    except Exception as e:
        flash(f"Erro ao listar documentos: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/documentos/placa/<placa>")
@login_required
def listar_documentos_placa(placa):
    """Lista documentos de um veículo pela placa"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM veiculos WHERE placa = ?", (placa.upper(),))
        veiculo_row = cur.fetchone()
        
        if not veiculo_row:
            flash(f"Veículo com placa {placa} não encontrado", "warning")
            return redirect(url_for("dashboard"))
        
        veiculo = dict(veiculo_row)
        conn.close()
        
        documentos = Documento.obter_por_veiculo(veiculo["id"])
        alertas = Alerta.obter_por_veiculo(veiculo["id"], apenas_nao_lidos=True)
        
        return render_template(
            "documentos.html",
            veiculo=veiculo,
            documentos=documentos,
            alertas=alertas
        )
    except Exception as e:
        flash(f"Erro ao listar documentos: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/documentos/novo/<int:veiculo_id>", methods=["GET", "POST"])
@login_required
def novo_documento(veiculo_id):
    """Cria um novo documento para um veículo"""
    if request.method == "POST":
        try:
            tipo_documento = request.form.get("tipo_documento")
            data_vencimento = request.form.get("data_vencimento")
            data_emissao = request.form.get("data_emissao")
            numero_documento = request.form.get("numero_documento")
            observacoes = request.form.get("observacoes")
            dias_antecedencia = int(request.form.get("dias_antecedencia", 15))
            estado_uf = request.form.get("estado_uf")
            
            foto_documento = None
            if "foto_documento" in request.files:
                file = request.files["foto_documento"]
                if file and file.filename:
                    filename = secure_filename(f"{veiculo_id}_{tipo_documento}_{datetime.now().timestamp()}.jpg")
                    file.save(os.path.join(ANEXOS_DIR, filename))
                    foto_documento = filename
            
            Documento.criar(
                veiculo_id=veiculo_id,
                tipo_documento=tipo_documento,
                data_vencimento=data_vencimento,
                data_emissao=data_emissao,
                numero_documento=numero_documento,
                foto_documento=foto_documento,
                observacoes=observacoes,
                dias_antecedencia=dias_antecedencia,
                estado_uf=estado_uf
            )
            
            flash(f"Documento {tipo_documento} adicionado com sucesso!", "success")
            return redirect(url_for("listar_documentos", veiculo_id=veiculo_id))
        
        except Exception as e:
            flash(f"Erro ao criar documento: {str(e)}", "error")
            return redirect(url_for("listar_documentos", veiculo_id=veiculo_id))
    
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM veiculos WHERE id = ?", (veiculo_id,))
    veiculo = dict(cur.fetchone())
    conn.close()
    
    tipos_documentos = [
        "CNH",
        "CRLV",
        "Seguro",
        "Revisão",
        "Inspeção Veicular",
        "Licenciamento",
        "Multas",
        "Rastreamento",
        "IPVA",
        "Outro"
    ]
    
    # Lista de estados brasileiros
    estados = sorted(list(VENCIMENTOS_POR_ESTADO.keys()))
    
    return render_template(
        "novo_documento.html",
        veiculo=veiculo,
        tipos_documentos=tipos_documentos,
        estados=estados,
        estado_padrao=veiculo.get("estado_uf", "")
    )


@app.route("/documentos/editar/<int:doc_id>", methods=["GET", "POST"])
@login_required
def editar_documento(doc_id):
    """Edita um documento existente"""
    documento = Documento.obter_por_id(doc_id)
    
    if not documento:
        flash("Documento não encontrado", "error")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":
        try:
            tipo_documento = request.form.get("tipo_documento")
            data_vencimento = request.form.get("data_vencimento")
            data_emissao = request.form.get("data_emissao")
            numero_documento = request.form.get("numero_documento")
            observacoes = request.form.get("observacoes")
            dias_antecedencia = int(request.form.get("dias_antecedencia", 15))
            
            foto_documento = documento.foto_documento
            if "foto_documento" in request.files:
                file = request.files["foto_documento"]
                if file and file.filename:
                    # Deletar foto anterior
                    if documento.foto_documento:
                        try:
                            os.remove(os.path.join(ANEXOS_DIR, documento.foto_documento))
                        except:
                            pass
                    
                    filename = secure_filename(f"{documento.veiculo_id}_{tipo_documento}_{datetime.now().timestamp()}.jpg")
                    file.save(os.path.join(ANEXOS_DIR, filename))
                    foto_documento = filename
            
            Documento.atualizar(
                doc_id,
                tipo_documento=tipo_documento,
                data_vencimento=data_vencimento,
                data_emissao=data_emissao,
                numero_documento=numero_documento,
                foto_documento=foto_documento,
                observacoes=observacoes,
                dias_antecedencia=dias_antecedencia
            )
            
            flash("Documento atualizado com sucesso!", "success")
            return redirect(url_for("listar_documentos", veiculo_id=documento.veiculo_id))
        
        except Exception as e:
            flash(f"Erro ao atualizar documento: {str(e)}", "error")
    
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM veiculos WHERE id = ?", (documento.veiculo_id,))
    veiculo = dict(cur.fetchone())
    conn.close()
    
    tipos_documentos = [
        "CNH",
        "CRLV",
        "Seguro",
        "Revisão",
        "Inspeção Veicular",
        "Licenciamento",
        "Multas",
        "Rastreamento",
        "Outro"
    ]
    
    return render_template(
        "editar_documento.html",
        veiculo=veiculo,
        documento=documento,
        tipos_documentos=tipos_documentos
    )


@app.route("/documentos/deletar/<int:doc_id>", methods=["POST"])
@login_required
def deletar_documento(doc_id):
    """Deleta um documento"""
    try:
        documento = Documento.obter_por_id(doc_id)
        
        if not documento:
            flash("Documento não encontrado", "error")
            return redirect(url_for("dashboard"))
        
        veiculo_id = documento.veiculo_id
        
        # Deletar foto se existir
        if documento.foto_documento:
            try:
                os.remove(os.path.join(ANEXOS_DIR, documento.foto_documento))
            except:
                pass
        
        Documento.deletar(doc_id)
        flash("Documento deletado com sucesso!", "success")
        return redirect(url_for("listar_documentos", veiculo_id=veiculo_id))
    
    except Exception as e:
        flash(f"Erro ao deletar documento: {str(e)}", "error")
        return redirect(url_for("dashboard"))


@app.route("/api/alertas")
@login_required
def obter_alertas():
    """API para obter alertas de vencimento de documentos"""
    try:
        alertas = obter_alertas_vencimento_documentos()
        return jsonify(alertas)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/alertas/marcar-lido/<int:alerta_id>", methods=["POST"])
@login_required
def marcar_alerta_lido(alerta_id):
    """Marca um alerta como lido"""
    try:
        Alerta.marcar_como_lido(alerta_id)
        return jsonify({"sucesso": True})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/vencimentos-estado")
@login_required
def api_vencimentos_estado():
    """API para obter tabela de vencimentos por estado"""
    try:
        return jsonify(VENCIMENTOS_POR_ESTADO)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route("/api/veiculos/alertas-resumo")
@login_required
def alertas_resumo():
    """API para obter resumo de alertas por veículo"""
    try:
        alertas_resumo = obter_alertas_vencimento_documentos()
        
        resumo = []
        for veiculo_id, dados in alertas_resumo.items():
            criticos = sum(1 for doc in dados['documentos'] if doc['status'] == 'vencido')
            avisos = sum(1 for doc in dados['documentos'] if doc['status'] == 'critico')
            
            if criticos > 0 or avisos > 0:
                resumo.append({
                    "veiculo_id": veiculo_id,
                    "placa": dados['placa'],
                    "modelo": dados['modelo'],
                    "documentos_vencidos": criticos,
                    "documentos_proximos_vencer": avisos
                })
        
        return jsonify(resumo)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# ============================================================================
# ROTAS DO MÓDULO FINANCEIRO
# ============================================================================

@app.route('/financeiro')
@permission_required('financeiro_view')
def financeiro_dashboard():
    """Dashboard principal financeiro"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT id, placa FROM veiculos ORDER BY placa")
    veiculos = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    # Selecionar primeiro veículo por padrão
    veiculo_selecionado = request.args.get('veiculo', None)
    if not veiculo_selecionado and veiculos:
        veiculo_selecionado = veiculos[0]['id']
    
    resumo = None
    consumo_medio = None
    custo_km = None
    
    if veiculo_selecionado:
        try:
            veiculo_selecionado = int(veiculo_selecionado)
            resumo = CalculosFinanceiros.resumo_custos_veiculo(veiculo_selecionado)
            consumo_medio = CalculosFinanceiros.consumo_medio(veiculo_selecionado)
            custo_km = CalculosFinanceiros.custo_por_km(veiculo_selecionado)
        except:
            pass
    
    # Obter alertas
    alertas = AlertasFinanceiros.verificar_todos_alertas()
    
    return render_template('financeiro/index.html',
                         veiculos=veiculos,
                         veiculo_selecionado=veiculo_selecionado,
                         resumo=resumo,
                         consumo_medio=consumo_medio,
                         custo_km=custo_km,
                         alertas=alertas)


@app.route('/api/financeiro/grafico-pizza/<int:veiculo_id>')
@login_required
def api_grafico_pizza(veiculo_id):
    """Retorna dados para gráfico pizza de distribuição de custos"""
    try:
        data = ChartData.pizza_custos_por_categoria(veiculo_id)
        return jsonify(data)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/financeiro/grafico-linha/<int:veiculo_id>')
@login_required
def api_grafico_linha(veiculo_id):
    """Retorna dados para gráfico linha de gastos mensais"""
    try:
        meses = request.args.get('meses', 12, type=int)
        data = ChartData.linha_gastos_mensais(veiculo_id, meses)
        return jsonify(data)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/financeiro/grafico-consumo/<int:veiculo_id>')
@login_required
def api_grafico_consumo(veiculo_id):
    """Retorna dados para gráfico de consumo"""
    try:
        registros = request.args.get('registros', 20, type=int)
        data = ChartData.linha_consumo_combustivel(veiculo_id, registros)
        return jsonify(data)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/financeiro/grafico-barras')
@login_required
def api_grafico_barras():
    """Retorna dados para gráfico barras comparativo entre veículos"""
    try:
        data = ChartData.barra_comparativo_veiculos()
        return jsonify(data)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/financeiro/consumo/<int:veiculo_id>')
@login_required
def api_consumo_analise(veiculo_id):
    """Retorna análise de consumo com alertas"""
    try:
        desvio = CalculosFinanceiros.detectar_desvios(veiculo_id)
        return jsonify(desvio)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500





@app.route('/api/financeiro/multa', methods=['POST'])
@login_required
def api_criar_multa():
    """Cria nova multa"""
    try:
        data = request.get_json()
        
        multa_id = Multa.criar(
            veiculo_id=data['veiculo_id'],
            numero_multa=data.get('numero_multa', ''),
            data_multa=data['data_multa'],
            valor=float(data['valor']),
            descricao=data.get('descricao', '')
        )
        
        return jsonify({'success': True, 'multa_id': multa_id})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/financeiro/multa/<int:multa_id>/pagar', methods=['POST'])
@login_required
def api_pagar_multa(multa_id):
    """Marca multa como paga"""
    try:
        data = request.get_json()
        Multa.marcar_paga(multa_id, data.get('data_pagamento'))
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/financeiro/documentos')
@login_required
def financeiro_documentos():
    """Página de gestão de documentos financeiros"""
    docs_vencendo = DocumentoFinanceiro.obter_vencendo_em_dias(dias=90)
    
    return render_template('financeiro/documentos.html',
                         documentos=docs_vencendo)


@app.route('/api/financeiro/documento', methods=['POST'])
@login_required
def api_criar_documento():
    """Cria novo documento financeiro"""
    try:
        data = request.get_json()
        
        doc_id = DocumentoFinanceiro.criar(
            veiculo_id=data['veiculo_id'],
            tipo=data['tipo'],
            data_vencimento=data['data_vencimento'],
            valor=float(data['valor'])
        )
        
        return jsonify({'success': True, 'documento_id': doc_id})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/financeiro/abastecimento')
@permission_required('combustivel_relatorio')
def financeiro_abastecimento():
    """Página de controle de abastecimento"""

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT id, placa FROM veiculos ORDER BY placa")
    veiculos = [dict(row) for row in cur.fetchall()]

    conn.close()

    return render_template('financeiro/abastecimento.html',
                         veiculos=veiculos)


@app.route('/financeiro/manutencoes')
@login_required
def financeiro_manutencoes():
    """Página de gestão de manutenções"""
    
    veiculos = CalculosFinanceiros.comparativo_veiculos()
    
    return render_template('financeiro/manutencoes.html',
                         veiculos=veiculos)


@app.route('/financeiro/relatorios')
@login_required
def financeiro_relatorios():
    """Página de relatórios financeiros"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT id, placa FROM veiculos ORDER BY placa")
    veiculos = [dict(row) for row in cur.fetchall()]
    
    conn.close()
    
    return render_template('financeiro/relatorios.html',
                         veiculos=veiculos)


@app.route('/api/financeiro/relatorio-pdf/<int:veiculo_id>')
@login_required
def api_relatorio_pdf(veiculo_id):
    """Gera PDF do relatório financeiro"""
    try:
        pdf_buffer = RelatorioFinanceiro.gerar_pdf_veiculo(veiculo_id)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'relatorio_veiculo_{veiculo_id}.pdf'
        )
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/financeiro/relatorio-csv/<int:veiculo_id>')
@login_required
def api_relatorio_csv(veiculo_id):
    """Gera CSV dos gastos"""
    try:
        csv_buffer = RelatorioFinanceiro.gerar_csv_gastos(veiculo_id)
        
        return send_file(
            csv_buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'gastos_veiculo_{veiculo_id}.csv'
        )
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/financeiro/resumo/<int:veiculo_id>')
@login_required
def api_resumo_financeiro(veiculo_id):
    """Retorna resumo financeiro de um veículo"""
    try:
        resumo = CalculosFinanceiros.resumo_custos_veiculo(veiculo_id)
        consumo = CalculosFinanceiros.consumo_medio(veiculo_id)
        custo_km = CalculosFinanceiros.custo_por_km(veiculo_id)
        previsao = CalculosFinanceiros.previsao_manutencao(veiculo_id)
        
        return jsonify({
            'resumo': resumo,
            'consumo_medio': consumo,
            'custo_km': custo_km,
            'previsao_manutencao': previsao
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/financeiro/alertas')
@login_required
def api_alertas_financeiros():
    """Retorna alertas financeiros"""
    try:
        alertas = AlertasFinanceiros.verificar_todos_alertas()
        return jsonify({'alertas': alertas})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route("/combustivel/modelo-nota")
@login_required
def modelo_nota_combustivel():
    """Modelo de nota fiscal padrão para abastecimento"""
    return render_template("combustivel/modelo_nota.html")


if __name__ == "__main__":
    with app.app_context():
        create_admin_user()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
