# Lista Completa de Veículos com Manutenção - Centro de Inteligência

## Resumo da Implementação
Adicionada uma nova seção visual no **Centro de Inteligência - Manutenção** que lista **TODOS os veículos com registros de manutenção**, com informações detalhadas e ações para gerar relatórios.

## Problema Resolvido
Anteriormente, na página do Centro de Manutenção, havia apenas um pequeno **dropdown** com veículos para seleção de relatório, mostrando apenas 3 carros. Agora há uma **tabela completa e visual** listando todos os veículos com manutenção.

## Arquivos Modificados

### 1. **app.py**
Adicionado novo endpoint de API:

#### **GET `/api/veiculos-com-manutencao`**
```
Descrição: Retorna todos os veículos que possuem registros de manutenção

Resposta (JSON):
[
  {
    "id": 1,
    "placa": "ABC-1234",
    "modelo": "Corolla",
    "tipo": "Carro",
    "condutor": "João Silva",
    "total_manutencoes": 5,
    "ultima_manutencao": "2024-12-21",
    "custo_total": 1250.50
  },
  ...
]

Informações retornadas:
- id: ID do veículo
- placa: Placa do veículo
- modelo: Modelo do veículo
- tipo: Carro ou Moto
- condutor: Nome do condutor
- total_manutencoes: Quantidade de manutenções realizadas
- ultima_manutencao: Data da última manutenção
- custo_total: Soma de todas as manutenções (peças + mão de obra)

Ordenação: Por data da última manutenção (mais recente primeiro)
Requer: Login (@login_required)
```

### 2. **templates/manutencao/dashboard.html**

#### **Nova Seção HTML**
- **Localização**: Após o gráfico de "Evolução de Custos" (novo item 4.5)
- **Título**: "Veículos com Manutenção"
- **Componente**: Tabela interativa com colunas:
  - Placa
  - Modelo
  - Tipo (badge colorido - azul para Carro, amarelo para Moto)
  - Condutor
  - Total Manutenções (badge azul com número)
  - Última Manutenção (data formatada em pt-BR)
  - Custo Total (formatado em R$)
  - Ações (Visualizar Detalhes e Gerar Relatório)

#### **Novas Funções JavaScript**
- `carregarVeiculosComManutencao()`: Carrega dados da API e preenche a tabela
- `formatarData(data)`: Formata datas para padrão brasileiro (dd/mm/yyyy)
- `formatarMoeda(valor)`: Formata valores em moeda brasileira (R$)
- `gerarRelatoriVeiculo(id, placa)`: Redireciona para geração de relatório

#### **Tratamento de Casos**
- Se nenhum veículo tiver manutenção: Mensagem "Nenhum veículo com manutenção registrada"
- Se houver erro ao carregar: Mensagem de erro com ícone
- Carregamento automático ao abrir a página: Função `carregarVeiculosComManutencao()` é chamada

## Funcionalidades

### Tabela de Veículos com Manutenção
- **Visualização Completa**: Lista todos os veículos com histórico de manutenção
- **Informações Principais**: Placa, modelo, tipo, condutor, quantidade e datas
- **Resumo Financeiro**: Exibe custo total de cada veículo
- **Ordenação**: Ordenada pela última manutenção mais recente

### Ações Disponíveis (por linha)
1. **Visualizar Detalhes** (ícone de olho)
   - Abre: `/manutencao/veiculo/{id}`
   - Permite: Ver histórico completo de manutenções do veículo

2. **Gerar Relatório** (ícone de download)
   - Abre: `/veiculo/{id}/relatorio-completo`
   - Permite: Baixar relatório em PDF com todas as informações

## Exemplo de Uso

### Cenário 1: Visualizar todos os veículos com manutenção
1. Usuário acessa "Centro de Inteligência - Manutenção"
2. Desce até a seção "Veículos com Manutenção"
3. Vê tabela completa de todos os veículos
4. Nota: Total de manutenções, custos e últimas datas

### Cenário 2: Gerar relatório de um veículo específico
1. Usuário encontra o veículo na tabela (ex: ABC-1234)
2. Clica no botão "Gerar Relatório" (download)
3. Sistema gera e baixa relatório em PDF
4. Relatório contém: Histórico, custos, peças, datas, etc.

### Cenário 3: Investigar detalhes de manutenção
1. Usuário clica no ícone de "Visualizar Detalhes"
2. Abre página dedicada ao veículo
3. Pode ver:
   - Listagem completa de manutenções
   - Datas e custos de cada serviço
   - Peças substituídas
   - Responsáveis/técnicos
   - Observações

## Dados Exibidos

### Por Veículo
| Campo | Fonte | Descrição |
|-------|-------|-----------|
| Placa | tabela `veiculos` | Identificação do veículo |
| Modelo | tabela `veiculos` | Modelo do veículo |
| Tipo | tabela `veiculos` | Carro ou Moto |
| Condutor | tabela `veiculos` | Responsável pelo veículo |
| Total Manutenções | tabela `manutencao` | COUNT(m.id) |
| Última Manutenção | tabela `manutencao` | MAX(data_manutencao) |
| Custo Total | tabela `manutencao` | SUM(valor_peca + mao_de_obra) |

## Formatação e Estilos

### Cores e Badges
- **Tipo Carro**: Badge azul (bg-primary)
- **Tipo Moto**: Badge amarelo (bg-warning)
- **Total Manutenções**: Badge informativo (bg-info)

### Tabela
- Cabeçalho fixo ao rolar
- Linhas com hover effect (background claro ao passar)
- Responsiva em dispositivos móveis
- Botões em grupo (button-group) para melhor espaço

### Formatação de Valores
- **Datas**: dd/mm/yyyy (padrão brasileiro)
- **Valores**: R$ 1.234,56 (moeda brasileira)
- **Números**: Inteiros simples (5, 10, etc.)

## Permissões
- ✅ **Admin**: Pode visualizar e gerar relatórios
- ✅ **Usuário Normal**: Pode visualizar e gerar relatórios
- ❌ **Visitante (não autenticado)**: Redirecionado para login

## Melhorias Futuras (Opcional)
- [ ] Filtro por tipo (Carro/Moto)
- [ ] Filtro por faixa de data
- [ ] Filtro por range de custo
- [ ] Ordenação por coluna (clicável)
- [ ] Busca por placa ou modelo
- [ ] Exportar tabela para Excel
- [ ] Gráfico de distribuição de custos
- [ ] Identificação de veículos com maiores custos
- [ ] Alerta para veículos sem manutenção recente (>30 dias)

## Performance
- Consulta otimizada com LEFT JOIN
- Agregações no banco (COUNT, MAX, SUM)
- Ordenação eficiente
- Carregamento inicial único (sem paginação)

## Testes Recomendados
1. ✅ Verificar se todos os veículos com manutenção aparecem
2. ✅ Validar formatação de datas (dd/mm/yyyy)
3. ✅ Validar formatação de moeda (R$ 1.234,56)
4. ✅ Testar botão de visualizar detalhes
5. ✅ Testar botão de gerar relatório
6. ✅ Testar mensagem quando não há veículos
7. ✅ Testar em diferentes resoluções (desktop/mobile)
8. ✅ Verificar permissões (login required)
