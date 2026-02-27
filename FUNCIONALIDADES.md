# 🚗 Sistema de Gestão de Frota de Veículos

## Lista Completa de Funcionalidades

---

## 📊 **PAINEL PRINCIPAL (Dashboard)**

### Estatísticas Gerais
- **Total de Checklists**: Exibição de todos os registros de inspeção realizados
- **Frota de Carros**: Quantidade total de veículos do tipo carro
- **Frota de Motos**: Quantidade total de veículos do tipo moto
- **Total de Veículos**: Contagem geral da frota

### Indicadores Críticos
- **Itens Críticos**: Listagem de problemas com prioridade máxima
- **Veículos Críticos**: Identificação de veículos com falhas importantes
- **Status em Tempo Real**: Alertas de manutenção urgente

### Resumo Financeiro
- **Gasto com Combustível**: Total gasto em abastecimentos
- **Gasto com Manutenção**: Total gasto em peças e serviços
- **Custo Total**: Soma de todos os gastos
- **Ticket Médio**: Valor médio por abastecimento

### Gráficos e Análises
- **Checklists por Mês**: Gráfico de registros ao longo dos meses
- **Distribuição de Críticos**: Visualização de problemas por tipo
- **Tabela de Veículos**: Lista completa com status e informações principais

---

## ✅ **CHECKLISTS & INSPEÇÕES**

### Novo Checklist
- Seleção de veículo
- Data da inspeção
- Quilometragem
- Validação de 20+ itens de segurança e manutenção
- Indicador visual de itens críticos
- Fotos/evidências dos problemas (upload de múltiplas imagens)

### Visualização de Histórico
- Filtros por tipo de veículo (Carro/Moto)
- Filtro por status do veículo
- Busca e filtro por placa
- Listagem de todos os checklists com datas
- Acesso rápido aos detalhes

### Detalhes do Checklist
- Informações completas do veículo
- Histórico de registros anteriores
- Status de cada item verificado
- Gráficos de tendências
- Comparação com inspeções anteriores
- Download de relatório em PDF

---

## 🚙 **GESTÃO DE VEÍCULOS**

### Informações do Veículo
- Placa
- Modelo
- Tipo (Carro/Moto)
- Condutor atribuído
- Quilometragem
- Data do primeiro registro
- Status geral

### Histórico do Veículo
- Todos os checklists realizados
- Histórico de combustível
- Histórico de manutenção
- Evolução da quilometragem

### Análise de Desempenho
- Consumo médio (km/l)
- Custo por quilômetro
- Taxa de danificação
- Intervalo de manutenção recomendado
- Relatório completo em PDF com gráficos

---

## ⛽ **GESTÃO DE COMBUSTÍVEL (Admin)**

### Registrar Abastecimento
- Data do abastecimento
- Seleção de veículo
- Quantidade de litros
- Valor total pago
- Quilometragem do veículo
- Cálculo automático de custo por litro

### Visualizar Histórico
- Lista de todos os abastecimentos
- Filtros por veículo
- Estatísticas de consumo por período
- Comparação entre veículos

### Análises
- Consumo médio histórico
- Ticket médio de abastecimento
- Tendências de gastos
- Identificação de anomalias de consumo

### Editar/Deletar
- Modificação de registros
- Exclusão de dados incorretos

---

## 🔧 **GESTÃO DE MANUTENÇÃO**

### Centro de Inteligência - Manutenção
- Dashboard com KPIs de manutenção
- Total de manutenções acumuladas
- Custo total do mês
- Manutenções do mês
- Veículos monitorados

### Registrar Manutenção
- Data da manutenção
- Seleção de veículo
- Descrição/tipo de serviço
- Peça substituída (nome e valor)
- Mão de obra (valor)
- Quilometragem atual
- Observações adicionais

### Notas Fiscais & Comprovantes
- **Upload de Arquivos**: Suporta PDF, JPG, PNG, DOC, DOCX, XLS, XLSX
- **Drag & Drop**: Interface intuitiva para arrastar arquivos
- **Download**: Recuperação dos comprovantes salvos
- **Validação**: Limite de 10MB por arquivo

### Histórico de Manutenção
- Lista completa de manutenções por veículo
- Filtros por período
- Resumo de custos (peças + mão de obra)
- Cálculo de média por manutenção
- Próximas manutenções programadas

### Editar/Deletar
- Modificação de registros de manutenção
- Exclusão de dados incorretos

### Alertas de Manutenção
- Alertas críticos de revisões vencidas
- Avisos de manutenção programada
- Informações sobre proximidade da próxima revisão
- Indicador visual de progresso

---

## 👥 **GESTÃO DE CONDUTORES (Admin)**

### Cadastro de Condutores
- Nome completo
- CPF
- CNH (número e validade)
- Contato telefônico
- Email
- Endereço
- Data de registro

### Visualizar Condutores
- Lista completa de condutores
- Perfil detalhado de cada condutor
- Histórico de veículos atribuídos
- Infrações registradas

### Editar/Deletar
- Atualização de informações
- Exclusão de registros

### Estatísticas por Condutor
- Quantidade de checklists realizados
- Histórico de infrações
- Desempenho geral

---

## 🚨 **GESTÃO DE INFRAÇÕES & MULTAS (Admin)**

### Registrar Multas
- Data da infração
- Seleção do condutor
- Local da infração
- Tipo de infração
- Valor da multa
- Data de vencimento
- Responsável pelo pagamento (condutor/empresa)
- Status de pagamento
- Data de pagamento

### Visualizar Infrações
- Lista completa de multas por condutor
- Filtros por status (pago/pendente)
- Listagem por período

### Gerenciar Pagamentos
- Marcar como pago
- Data de pagamento
- Histórico de infrações por condutor

### Alertas de Multas
- Notificação de multas vencidas
- Recordatórios de infrações pendentes

---

## 📈 **ANÁLISES & PERFORMANCE (Admin)**

### Dashboard de Performance
- Consumo de combustível por veículo
- Custos de manutenção comparativos
- Eficiência operacional
- Ranking de veículos com melhor/pior desempenho

### Indicadores de Desempenho
- **KM por Litro**: Eficiência de combustível
- **Custo por KM**: Gasto operacional
- **Taxa de Danificação**: Porcentagem de itens críticos
- **Intervalo de Manutenção**: Recomendação de ciclo

### Comparação de Dados
- Entre veículos
- Por período
- Por tipo de combustível

---

## 📄 **RELATÓRIOS & EXPORTAÇÃO**

### Relatório Completo do Veículo (PDF)
Contém:
- Informações gerais do veículo
- Indicadores de performance
- Histórico completo de combustível (últimos 10 registros)
- Histórico completo de manutenção (últimos 10 registros)
- Resumo financeiro total
- Gráficos e análises

### Relatório de Manutenção (PDF)
- Manutenções dos últimos 30 dias
- Detalhes de peças e serviços
- Custo total por veículo
- Cronograma de próximas revisões

### Exportação para Excel (Em Desenvolvimento)
- Custos por veículo
- Histórico de peças
- Listagem de infrações

### PDF por Veículo
- Dados estruturados
- Visualização profissional
- Pronto para impressão

---

## 🔐 **GERENCIAMENTO DE USUÁRIOS (Admin)**

### Cadastro de Usuários
- Nome
- Email
- Senha (com hash seguro)
- Definição de privilégios (Admin/Usuário comum)

### Autenticação
- Login com email e senha
- Sessão segura
- Logout

### Controle de Acesso
- **Admin**: Acesso total a todas as funcionalidades
- **Usuário Comum**: Acesso limitado (sem Performance, Abastecimento, Condutores, Multas)

### Gerenciamento de Conta
- Atualização de perfil
- Alteração de senha
- Histórico de login

---

## 💾 **GERENCIAMENTO DE DADOS (Admin)**

### Backup
- Exportação completa do banco de dados
- Arquivo em formato SQLite
- Agendamento automático (opcional)
- Download manual a qualquer momento

### Restauração
- Upload de arquivo de backup
- Restauração de dados anteriores
- Validação de integridade

### Limpeza de Arquivos
- Remoção de uploads não referenciados
- Limpeza automática de espaço em disco
- Relatório de limpeza realizada

---

## 📱 **FUNCIONALIDADES GERAIS**

### Interface Responsiva
- Design adaptável para desktop, tablet e celular
- Navigation menu intuitivo
- Ícones Bootstrap Icons para melhor UX

### Instalação como App
- Suporte a PWA (Progressive Web App)
- Instalação no smartphone
- Acesso offline (parcial)
- Atalho na tela inicial

### Notificações
- Alertas de manutenção crítica
- Avisos de multas vencidas
- Notificações de revisão próxima

### Busca e Filtros
- Busca por placa de veículo
- Filtro por tipo de veículo
- Filtro por status
- Filtro por data/período
- Filtro por condutor

### Validações
- Validação de dados em tempo real
- Verificação de campos obrigatórios
- Mensagens de erro claras
- Confirmação de ações críticas

---

## 🎨 **INTERFACE & DESIGN**

### Visual Moderno
- Tema com gradientes suaves
- Cards com sombras e efeitos hover
- Ícones intuitivos
- Paleta de cores consistente

### Resumos Visuais
- Resumo de custos com indicadores coloridos
- KPI cards com estatísticas em tempo real
- Gráficos interativos
- Tabelas com ordenação

### Feedback do Usuário
- Mensagens de sucesso/erro
- Loading indicators
- Progress bars
- Confirmações de ação

---

## 🛠️ **TECNOLOGIAS UTILIZADAS**

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Framework CSS**: Bootstrap 5
- **Ícones**: Bootstrap Icons
- **PDF**: ReportLab
- **Autenticação**: Flask-Login
- **ORM**: Operações SQL diretas

---

## 📋 **RESUMO DE PERMISSÕES**

| Funcionalidade | Admin | Usuário Comum |
|---|---|---|
| Dashboard | ✅ | ✅ |
| Checklists | ✅ | ✅ |
| Histórico de Veículos | ✅ | ✅ |
| Detalhes de Veículos | ✅ | ✅ |
| Abastecimento | ✅ | ❌ |
| Manutenção | ✅ | ✅ |
| Performance | ✅ | ❌ |
| Condutores | ✅ | ❌ |
| Multas | ✅ | ❌ |
| Relatórios | ✅ | ✅ |
| Backup/Restauração | ✅ | ❌ |
| Gestão de Usuários | ✅ | ❌ |

---

**Versão**: 1.0  
**Data**: Dezembro 2025  
**Desenvolvido para**: Gestão completa de frota de veículos
