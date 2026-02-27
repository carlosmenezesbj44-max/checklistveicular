# Sistema de Documentos e Alarmes de Vencimento

## Visão Geral

Este sistema permite gerenciar documentos de veículos (CNH, CRLV, Seguro, etc.) com alarmes/notificações automáticas quando documentos estão próximos do vencimento.

## Funcionalidades

### 1. Cadastro de Documentos
- Adicionar documentos para cada veículo
- Tipos suportados:
  - CNH (Carteira Nacional de Habilitação)
  - CRLV (Certificado de Registro e Licenciamento do Veículo)
  - Seguro
  - Revisão
  - Inspeção Veicular
  - Licenciamento
  - Multas
  - Rastreamento
  - Outro (customizado)

### 2. Informações dos Documentos
Cada documento pode conter:
- **Tipo de Documento**: Categoria do documento
- **Número**: Número/ID do documento
- **Data de Emissão**: Quando o documento foi emitido
- **Data de Vencimento**: Quando o documento vence (obrigatório)
- **Foto/Cópia**: Upload de imagem ou PDF do documento
- **Observações**: Notas adicionais
- **Antecedência para Alerta**: Quantos dias antes do vencimento gerar alerta (padrão: 15 dias)

### 3. Sistema de Alarmes Automáticos

O sistema gera alarmes automaticamente baseado no status do documento:

#### Status do Documento:
- 🔴 **VENCIDO**: O documento já passou da data de vencimento
- 🔴 **VENCE HOJE**: O documento vence no dia atual
- 🟡 **VENCENDO**: O documento vence nos próximos 15 dias (configurável)
- ✅ **OK**: O documento ainda está válido

#### Tipos de Alertas:
- **Alerta Crítico**: Documento vencido ou vencendo hoje
- **Alerta de Aviso**: Documento vencendo em breve (dentro da antecedência configurada)
- **Informativo**: Documento ainda com tempo

### 4. Funcionalidades de Gerenciamento

#### Listar Documentos
```
GET /documentos/<veiculo_id>
```
- Visualiza todos os documentos de um veículo
- Mostra status de vencimento
- Exibe alertas não lidos

#### Criar Novo Documento
```
GET/POST /documentos/novo/<veiculo_id>
```
- Formulário para adicionar novo documento
- Validação automática de datas
- Upload de arquivo (opcional)

#### Editar Documento
```
GET/POST /documentos/editar/<doc_id>
```
- Modifica informações do documento
- Permite trocar foto/cópia

#### Deletar Documento
```
POST /documentos/deletar/<doc_id>
```
- Remove documento do sistema
- Deleta foto associada (se houver)

### 5. APIs de Alertas

#### Obter Alertas de Vencimento
```
GET /api/alertas
```
Retorna: Lista de alertas de documentos em risco

#### Resumo de Alertas por Veículo
```
GET /api/veiculos/alertas-resumo
```
Retorna: Contagem de documentos vencidos e próximos de vencer por veículo

#### Marcar Alerta como Lido
```
POST /api/alertas/marcar-lido/<alerta_id>
```
Marca um alerta específico como já notificado

## Estrutura do Banco de Dados

### Tabela: `documentos_veiculo`
```sql
CREATE TABLE documentos_veiculo (
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
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
)
```

### Tabela: `alertas_veiculo`
```sql
CREATE TABLE alertas_veiculo (
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
```

## Como Usar

### 1. Acessar Documentos de um Veículo
1. Ir para Dashboard
2. Selecionar um veículo
3. Clicar em "Documentos" ou no ícone de arquivo
4. Será exibida a lista de documentos e alertas

### 2. Adicionar um Novo Documento
1. Na página de documentos, clicar em "Adicionar Documento"
2. Preencher os campos:
   - Selecione o tipo
   - (Opcional) Número do documento
   - (Opcional) Data de emissão
   - Data de vencimento **obrigatória**
   - (Opcional) Upload da foto/cópia
   - (Opcional) Observações
   - Dias para alerta (padrão: 15)
3. Clicar em "Salvar Documento"

### 3. Configurar Antecedência de Alerta
Ao criar ou editar um documento:
- **Dias para Alerta**: Define quantos dias antes do vencimento o sistema deve alertar
- Exemplo: Se CNH vence em 30 dias e você configura 15 dias, receberá alerta em 15 dias

### 4. Interpretar Alertas
- 🔴 **Vermelho**: Ação imediata necessária (vencido ou vence hoje)
- 🟡 **Amarelo**: Atenção necessária (vence em breve)
- ✅ **Verde**: Tudo em dia

## Exemplo de Uso Prático

### Cenário: Gerenciar CNH de um Motorista
1. Adicionar documento:
   - Tipo: CNH
   - Número: 1234567890123
   - Data de Emissão: 15/01/2019
   - Data de Vencimento: 15/01/2027
   - Antecedência: 30 dias
   - Foto: Enviar cópia da CNH

2. Sistema gera alerta quando:
   - Faltam 30 dias para vencer
   - Faltam 15 dias para vencer
   - Falta 1 dia para vencer
   - Já venceu

3. Ao editar:
   - Atualizar data de vencimento quando renovar
   - Enviar foto atualizada

## Integração com Dashboard

Os alertas podem ser exibidos:
- Na página de documentos do veículo
- Em um widget no dashboard (futura integração)
- Em relatórios de frota
- Via email (futura integração)

## Módulo Python: `documentos.py`

### Classes Disponíveis

#### Classe `Documento`
```python
# Criar documento
Documento.criar(
    veiculo_id=1,
    tipo_documento="CNH",
    data_vencimento="15/01/2027",
    data_emissao="15/01/2019",
    numero_documento="1234567890123",
    foto_documento="caminho/arquivo.jpg",
    observacoes="Renovada",
    dias_antecedencia=15
)

# Obter documentos do veículo
documentos = Documento.obter_por_veiculo(veiculo_id=1)

# Obter documento específico
doc = Documento.obter_por_id(doc_id=5)

# Atualizar documento
Documento.atualizar(
    doc_id=5,
    data_vencimento="15/01/2029"
)

# Deletar documento
Documento.deletar(doc_id=5)
```

#### Classe `Alerta`
```python
# Criar alerta
Alerta.criar(
    veiculo_id=1,
    tipo_alerta="documento_vencimento",
    titulo="CNH vencendo em 10 dias",
    descricao="A CNH vence em 10 dias",
    atencao_requerida=True
)

# Obter alertas
alertas = Alerta.obter_por_veiculo(veiculo_id=1, apenas_nao_lidos=True)

# Marcar como lido
Alerta.marcar_como_lido(alerta_id=1)

# Deletar alerta
Alerta.deletar(alerta_id=1)
```

#### Funções Utilitárias
```python
# Verificar e gerar alerta automaticamente
verificar_e_gerar_alerta(
    veiculo_id=1,
    tipo_documento="CNH",
    data_vencimento="15/01/2027"
)

# Obter resumo de alertas por veículo
alertas = obter_alertas_vencimento_documentos()

# Renovar verificações (chamar periodicamente)
renovar_verificacoes_periodicas()
```

## Extensões Futuras

1. **Notificações por Email**: Enviar alertas via email
2. **SMS/Whatsapp**: Notificações via mensagem
3. **Dashboard Widget**: Exibir alertas no dashboard principal
4. **Relatórios**: Gerar relatórios de conformidade de documentos
5. **Integração com Calendário**: Sincronizar com calendário
6. **Renovação Automática**: Sugerir renovação com links para órgãos (DETRAN, etc)

## Troubleshooting

### Alerta não está sendo gerado
- Verifique se a data de vencimento está no formato correto (DD/MM/YYYY)
- Certifique-se de que a data é no futuro para documentos válidos
- Confirme que dias_antecedencia > 0

### Foto não está sendo salva
- Verifique permissões na pasta ANEXOS_DIR
- Confirme que o arquivo está em formato suportado (JPG, PNG, GIF, PDF)
- Verifique limite de tamanho (máximo 5MB)

### Alertas não desaparecem
- Alertas antigos não são deletados automaticamente
- Você pode marcar como "lido" para ocultá-los
- Implementar limpeza automática conforme necessário
