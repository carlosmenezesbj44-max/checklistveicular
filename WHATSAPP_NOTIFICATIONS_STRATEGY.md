# Estratégia: Notificações por WhatsApp

## Visão Geral
Implementar envio de notificações automáticas via WhatsApp para alertas de manutenção, combustível, vencimento de documentos, etc.

---

## 1. Comparativo de Soluções

| Solução | Custo | Setup | Rate Limit | Melhor Para |
|---------|-------|-------|-----------|-----------|
| **Twilio** | $0.01-0.05/msg | Fácil | 1000/mês free | Produção, SMEs |
| **WhatsApp Business API** | $0.01-0.10/msg | Complexo | Ilimitado | Grande escala |
| **MessageBird** | $0.01-0.05/msg | Fácil | 100/dia free | Desenvolvimento |
| **Vonage (Nexmo)** | $0.01-0.06/msg | Fácil | Até 100/dia | Backup |

**Recomendação para seu caso**: **Twilio** (melhor custo-benefício + documentação excelente)

---

## 2. Setup Twilio

### A. Conta e Credentials

```bash
# 1. Criar conta em https://www.twilio.com/console
# 2. Obter credenciais:
#    - Account SID
#    - Auth Token
#    - WhatsApp Sandbox Number: +55 11 9 9999-9999

# 3. Instalar biblioteca
pip install twilio
```

### B. Variáveis de Ambiente (`.env`)

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+551199999999
TWILIO_WHATSAPP_TO_ADMIN=whatsapp:+5511987654321

# Ou usar variáveis de ambiente do sistema
```

---

## 3. Implementação - Estrutura

```
checklist-carros/
├── notifications/
│   ├── __init__.py
│   ├── whatsapp.py (envio de mensagens)
│   ├── templates.py (templates de mensagens)
│   └── scheduler.py (agendamento de notificações)
├── config.py (adicionar credenciais Twilio)
└── app.py (integrar rotas)
```

---

## 4. Código - Módulo de Notificações

### A. `notifications/whatsapp.py`

```python
import os
from twilio.rest import Client
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class WhatsAppNotifier:
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_number = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+5511999999999')
        
        if not self.account_sid or not self.auth_token:
            logger.warning("Credenciais Twilio não configuradas")
            self.client = None
        else:
            self.client = Client(self.account_sid, self.auth_token)
    
    def send(self, to_number: str, message: str) -> bool:
        """Envia mensagem WhatsApp"""
        if not self.client:
            logger.error("Cliente Twilio não inicializado")
            return False
        
        try:
            # Garantir formato correto: whatsapp:+55XXXXXXXXXX
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            message_obj = self.client.messages.create(
                from_=self.from_number,
                to=to_number,
                body=message
            )
            
            logger.info(f"WhatsApp enviado para {to_number}: {message_obj.sid}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp para {to_number}: {str(e)}")
            return False
    
    def send_bulk(self, recipients: List[str], message: str) -> Dict[str, bool]:
        """Envia para múltiplos destinatários"""
        results = {}
        for recipient in recipients:
            results[recipient] = self.send(recipient, message)
        return results
    
    def send_template(self, to_number: str, template_name: str, **kwargs) -> bool:
        """Envia mensagem usando template"""
        from .templates import get_template
        message = get_template(template_name, **kwargs)
        return self.send(to_number, message)

# Instância global
whatsapp = WhatsAppNotifier()
```

### B. `notifications/templates.py`

```python
from datetime import datetime, timedelta

def get_template(template_name: str, **kwargs) -> str:
    """Retorna template de mensagem formatado"""
    
    templates = {
        'checklist_criado': """
🚗 *CHECKLIST CRIADO*

Veículo: {placa}
Data: {data}
Itens verificados: {total_itens}

Acesse o sistema para mais detalhes.
        """,
        
        'item_danificado': """
⚠️ *ITEM DANIFICADO DETECTADO*

Veículo: {placa}
Item: {item}
Status: {status}
Data: {data}

Ação imediata recomendada!
        """,
        
        'manutencao_agendada': """
📅 *MANUTENÇÃO AGENDADA*

Veículo: {placa}
Tipo: {tipo_manutencao}
Data prevista: {data}
Responsável: {responsavel}

Confirmar presença?
        """,
        
        'documento_vencendo': """
📄 *DOCUMENTO VENCENDO*

Veículo: {placa}
Documento: {documento}
Vencimento: {data_vencimento}
Dias restantes: {dias_restantes}

Renovar agora!
        """,
        
        'combustivel_baixo': """
⛽ *NÍVEL DE COMBUSTÍVEL BAIXO*

Veículo: {placa}
Quilometragem: {quilometragem} km
Consumo estimado: {consumo_estimado} km/l

Abastecer em breve!
        """,
        
        'manutencao_concluida': """
✅ *MANUTENÇÃO CONCLUÍDA*

Veículo: {placa}
Tipo: {tipo_manutencao}
Data: {data}
Custo: R$ {custo}
Responsável: {responsavel}

Arquivo: {nota_fiscal_url}
        """,
        
        'alerta_rota': """
🗺️ *ALERTA DE ROTA*

Veículo: {placa}
Condutor: {condutor}
Rota: {rota}
Tempo estimado: {tempo_estimado}h

Status: {status}
        """,
        
        'relatorio_semanal': """
📊 *RELATÓRIO SEMANAL*

Período: {semana}

Checklists: {total_checklists}
Manutenções: {total_manutencoes}
Gasto combustível: R$ {gasto_combustivel}
Gasto total: R$ {gasto_total}

Eficiência: {eficiencia}%
        """
    }
    
    template = templates.get(template_name, "Notificação do sistema")
    return template.format(**kwargs)
```

---

## 5. Integração no Backend (`app.py`)

### A. Importar e configurar

```python
# No início do app.py
from notifications.whatsapp import whatsapp

# Usar em rotas existentes
```

### B. Exemplo: Enviar notificação ao criar checklist

```python
@app.route("/salvar-checklist", methods=["POST"])
@login_required
def salvar_checklist():
    """Salva checklist e envia notificação"""
    
    try:
        # ... código existente de salvar ...
        salvar_checklist(dados)
        
        # Enviar notificação WhatsApp
        veiculo = obter_registro(veiculo_id)
        user_phone = current_user.telefone  # adicionar campo no modelo User
        
        if user_phone:
            whatsapp.send_template(
                to_number=user_phone,
                template_name='checklist_criado',
                placa=veiculo['placa'],
                data=datetime.now().strftime("%d/%m/%Y"),
                total_itens=len(dados['itens'])
            )
        
        flash("Checklist salvo com sucesso!", "success")
        return redirect(url_for("historico"))
    
    except Exception as e:
        flash(f"Erro: {str(e)}", "danger")
        return redirect(url_for("historico"))
```

### C. Exemplo: Alertar item danificado

```python
@app.route("/item-danificado/<int:item_id>", methods=["POST"])
@login_required
def marcar_item_danificado(item_id):
    """Marca item como danificado e notifica"""
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "SELECT i.*, v.placa FROM itens_checklist i "
            "JOIN veiculos v ON i.veiculo_id = v.id WHERE i.id = ?",
            (item_id,)
        )
        item = cur.fetchone()
        
        if item:
            # Atualizar status
            cur.execute(
                "UPDATE itens_checklist SET status='Danificado' WHERE id=?",
                (item_id,)
            )
            conn.commit()
            
            # Notificar admin e responsável
            admin_phone = os.environ.get('ADMIN_WHATSAPP')
            if admin_phone:
                whatsapp.send_template(
                    to_number=admin_phone,
                    template_name='item_danificado',
                    placa=item['placa'],
                    item=item['nome_item'],
                    status='Danificado',
                    data=datetime.now().strftime("%d/%m/%Y %H:%M")
                )
        
        return jsonify({"success": True})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        conn.close()
```

### D. Exemplo: Alertar documento vencendo

```python
@app.route("/verificar-documentos-vencimento")
@login_required
def verificar_documentos_vencimento():
    """Verifica documentos com vencimento próximo"""
    
    from documentos import obter_alertas_vencimento_documentos
    
    alertas = obter_alertas_vencimento_documentos(dias=30)
    
    for alerta in alertas:
        user_phone = alerta['user'].telefone
        
        if user_phone and alerta['dias_para_vencer'] <= 7:
            whatsapp.send_template(
                to_number=user_phone,
                template_name='documento_vencendo',
                placa=alerta['placa'],
                documento=alerta['tipo_documento'],
                data_vencimento=alerta['data_vencimento'],
                dias_restantes=alerta['dias_para_vencer']
            )
    
    return jsonify({"notificacoes_enviadas": len(alertas)})
```

---

## 6. Agendamento de Notificações (`notifications/scheduler.py`)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def verificar_alertas_diarios():
    """Verifica alertas diariamente às 9h"""
    from app import get_conn
    from documentos import obter_alertas_vencimento_documentos
    from notifications.whatsapp import whatsapp
    
    logger.info("Verificando alertas diários...")
    
    try:
        # Verificar documentos vencendo
        alertas = obter_alertas_vencimento_documentos(dias=7)
        
        for alerta in alertas:
            user_phone = alerta['user'].telefone
            if user_phone:
                whatsapp.send_template(
                    to_number=user_phone,
                    template_name='documento_vencendo',
                    **alerta
                )
        
        logger.info(f"Alertas enviados: {len(alertas)}")
    
    except Exception as e:
        logger.error(f"Erro ao verificar alertas: {str(e)}")

def enviar_relatorio_semanal():
    """Envia relatório semanal às segundas 9h"""
    from app import get_conn, current_user
    from notifications.whatsapp import whatsapp
    
    logger.info("Enviando relatórios semanais...")
    
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Obter dados da semana anterior
        uma_semana_atras = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        cur.execute("""
            SELECT COUNT(*) FROM veiculos WHERE data >= ?
        """, (uma_semana_atras,))
        total_checklists = cur.fetchone()[0]
        
        # Enviar para todos os usuários
        cur.execute("SELECT id, telefone FROM user WHERE role IN ('usuario', 'admin')")
        usuarios = cur.fetchall()
        
        for user_id, telefone in usuarios:
            if telefone:
                whatsapp.send_template(
                    to_number=telefone,
                    template_name='relatorio_semanal',
                    semana=uma_semana_atras,
                    total_checklists=total_checklists,
                    # ... mais dados ...
                )
        
        logger.info(f"Relatórios enviados para {len(usuarios)} usuários")
    
    except Exception as e:
        logger.error(f"Erro ao enviar relatórios: {str(e)}")
    
    finally:
        conn.close()

def iniciar_scheduler():
    """Inicia agendador de tarefas"""
    scheduler = BackgroundScheduler()
    
    # Verificar alertas todos os dias às 9h
    scheduler.add_job(
        verificar_alertas_diarios,
        'cron',
        hour=9,
        minute=0,
        id='alertas_diarios'
    )
    
    # Relatório semanal segunda-feira às 9h
    scheduler.add_job(
        enviar_relatorio_semanal,
        'cron',
        day_of_week='mon',
        hour=9,
        minute=0,
        id='relatorio_semanal'
    )
    
    scheduler.start()
    return scheduler
```

### Adicionar ao `app.py` (antes de `app.run()`)

```python
from notifications.scheduler import iniciar_scheduler

# Iniciar scheduler
if __name__ != '__main__':
    scheduler = iniciar_scheduler()

if __name__ == '__main__':
    scheduler = iniciar_scheduler()
    app.run(debug=True)
```

---

## 7. Modelo de Dados - Adicionar telefone ao User

### Migração do Banco (`models.py`)

```python
from db import get_conn

def adicionar_telefone_ao_user():
    """Adiciona coluna telefone à tabela user"""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Verificar se coluna já existe
        cur.execute("PRAGMA table_info(user)")
        colunas = [col[1] for col in cur.fetchall()]
        
        if 'telefone' not in colunas:
            cur.execute("""
                ALTER TABLE user ADD COLUMN telefone VARCHAR(20)
            """)
            conn.commit()
            print("Coluna 'telefone' adicionada com sucesso")
    
    except Exception as e:
        print(f"Erro ao adicionar coluna: {str(e)}")
    
    finally:
        conn.close()

# Chamar na inicialização
adicionar_telefone_ao_user()
```

### Atualizar modelo User (`models.py`)

```python
class User(UserMixin):
    def __init__(self, id, username, email, role, telefone=None):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.telefone = telefone  # Adicionar
        self.is_admin = role == 'admin'
    
    @staticmethod
    def get(user_id):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, email, role, telefone FROM user WHERE id = ?",
            (user_id,)
        )
        u = cur.fetchone()
        conn.close()
        
        if u:
            return User(u[0], u[1], u[2], u[3], u[4])
        return None
```

---

## 8. UI - Adicionar campo de telefone

### Template de edição de perfil (`templates/profile.html`)

```html
<form method="POST" action="{{ url_for('atualizar_perfil') }}">
    <div class="form-group">
        <label for="username">Usuário</label>
        <input type="text" class="form-control" id="username" name="username" 
               value="{{ current_user.username }}" required>
    </div>
    
    <div class="form-group">
        <label for="email">E-mail</label>
        <input type="email" class="form-control" id="email" name="email" 
               value="{{ current_user.email }}" required>
    </div>
    
    <!-- NOVO -->
    <div class="form-group">
        <label for="telefone">Telefone WhatsApp</label>
        <input type="tel" class="form-control" id="telefone" name="telefone" 
               placeholder="+55 11 99999-9999" value="{{ current_user.telefone or '' }}">
        <small class="form-text text-muted">
            Formato: +55 com DDD (ex: +5511987654321)
        </small>
    </div>
    
    <button type="submit" class="btn btn-primary">Salvar</button>
</form>
```

### Rota de atualização

```python
@app.route("/perfil/atualizar", methods=["POST"])
@login_required
def atualizar_perfil():
    """Atualiza perfil do usuário incluindo telefone"""
    
    telefone = request.form.get('telefone', '').strip()
    email = request.form.get('email', '').strip()
    
    # Validar formato de telefone (básico)
    if telefone and not telefone.startswith('+55'):
        telefone = '+55' + telefone.replace(' ', '').replace('-', '')
    
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE user SET email = ?, telefone = ? WHERE id = ?
        """, (email, telefone, current_user.id))
        
        conn.commit()
        conn.close()
        
        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for("dashboard"))
    
    except Exception as e:
        flash(f"Erro ao atualizar perfil: {str(e)}", "danger")
        return redirect(url_for("dashboard"))
```

---

## 9. Arquivo `.env` - Exemplo

```env
# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+551199999999

# Admin
ADMIN_WHATSAPP=whatsapp:+5511987654321

# Flask
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta
```

---

## 10. Teste de Envio

### Script de teste (`test_whatsapp.py`)

```python
import os
from notifications.whatsapp import whatsapp

def test_whatsapp():
    """Testa envio de WhatsApp"""
    
    # Número de teste (usar seu número)
    test_number = "+5511987654321"
    
    print("Testando envio de WhatsApp...")
    
    # Teste 1: Mensagem simples
    resultado = whatsapp.send(
        to_number=test_number,
        message="🧪 Teste de mensagem do sistema de checklist veicular!"
    )
    print(f"Teste 1 (simples): {'✓' if resultado else '✗'}")
    
    # Teste 2: Template
    resultado = whatsapp.send_template(
        to_number=test_number,
        template_name='checklist_criado',
        placa='ABC-1234',
        data='15/01/2025',
        total_itens=25
    )
    print(f"Teste 2 (template): {'✓' if resultado else '✗'}")
    
    # Teste 3: Mensagem em lote
    resultados = whatsapp.send_bulk(
        recipients=[test_number],
        message="📊 Teste em lote"
    )
    print(f"Teste 3 (lote): {'✓' if all(resultados.values()) else '✗'}")

if __name__ == '__main__':
    test_whatsapp()
```

Executar:
```bash
python test_whatsapp.py
```

---

## 11. Requisitos (`requirements.txt`)

```
twilio>=8.0.0
APScheduler>=3.10.0
python-dotenv>=0.19.0
```

Instalar:
```bash
pip install -r requirements.txt
```

---

## 12. Fluxo Completo

```
┌─────────────────────────────────────────────────┐
│ Evento no Sistema                               │
│ (checklist criado, item danificado, etc)        │
└────────────┬────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────┐
│ Verificar se usuário tem telefone               │
│ Selecionar template apropriado                  │
└────────────┬────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────┐
│ WhatsAppNotifier.send_template()                │
│ Formatar mensagem com dados                     │
└────────────┬────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────┐
│ Twilio API                                      │
│ Enviar para WhatsApp                            │
└────────────┬────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────┐
│ Usuário recebe notificação no WhatsApp          │
└─────────────────────────────────────────────────┘
```

---

## 13. Tipos de Notificações Recomendadas

1. **Imediatas** (quando ocorrem):
   - Item danificado
   - Manutenção crítica
   - Combustível vazio

2. **Diárias** (9h da manhã):
   - Alertas de documentos vencendo
   - Itens pendentes

3. **Semanais** (segunda 9h):
   - Relatório de gastos
   - Resumo de manutenções
   - Eficiência de condutores

4. **Sob demanda**:
   - Confirmação de manutenção
   - Status de rota
   - Resposta a perguntas

---

## 14. Próximos Passos

- [ ] Criar credenciais Twilio
- [ ] Adicionar campo `telefone` ao modelo User
- [ ] Implementar módulo `notifications/`
- [ ] Integrar em rotas existentes
- [ ] Adicionar UI para editar telefone
- [ ] Configurar agendador de tarefas
- [ ] Testar envios
- [ ] Monitorar custos
- [ ] Adicionar webhook para receber respostas

