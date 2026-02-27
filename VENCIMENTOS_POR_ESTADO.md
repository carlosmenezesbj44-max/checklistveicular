# Tabela de Vencimentos por Estado

## Introdução

Cada estado brasileiro tem datas diferentes de vencimento para documentos como IPVA, Inspeção Veicular e Revisão. Esta tabela ajuda a rastrear quando cada documento vence em cada estado.

## Documentos Rastreados

- **IPVA**: Imposto sobre Propriedade de Veículos Automotores
- **INSPECAO**: Inspeção Veicular (DIE - Detran)
- **REVISAO**: Revisão Anual (Revisão Obrigatória)

## Tabela de Vencimentos

| Estado | UF | IPVA | Inspeção | Revisão |
|--------|----|----|----------|---------|
| Acre | AC | Fevereiro | Junho | Dezembro |
| Alagoas | AL | Março | Junho | Dezembro |
| Amapá | AP | Abril | Junho | Dezembro |
| Amazonas | AM | Maio | Junho | Dezembro |
| Bahia | BA | Setembro | Novembro | Dezembro |
| Ceará | CE | Julho | Novembro | Dezembro |
| Distrito Federal | DF | Dezembro | Dezembro | Dezembro |
| Espírito Santo | ES | Novembro | Dezembro | Dezembro |
| Goiás | GO | Dezembro | Junho | Dezembro |
| Maranhão | MA | Março | Junho | Dezembro |
| Mato Grosso | MT | Dezembro | Dezembro | Dezembro |
| Mato Grosso do Sul | MS | Dezembro | Dezembro | Dezembro |
| Minas Gerais | MG | Janeiro | Julho | Dezembro |
| Pará | PA | Janeiro | Junho | Dezembro |
| Paraíba | PB | Outubro | Junho | Dezembro |
| Paraná | PR | Dezembro | Dezembro | Dezembro |
| Pernambuco | PE | Dezembro | Dezembro | Dezembro |
| Piauí | PI | Dezembro | Junho | Dezembro |
| Rio de Janeiro | RJ | Dezembro | Dezembro | Dezembro |
| Rio Grande do Norte | RN | Outubro | Junho | Dezembro |
| Rio Grande do Sul | RS | Dezembro | Dezembro | Dezembro |
| Rondônia | RO | Dezembro | Junho | Dezembro |
| Roraima | RR | Setembro | Junho | Dezembro |
| Santa Catarina | SC | Dezembro | Dezembro | Dezembro |
| São Paulo | SP | Dezembro | Dezembro | Dezembro |
| Sergipe | SE | Dezembro | Junho | Dezembro |
| Tocantins | TO | Dezembro | Junho | Dezembro |

## Como Funciona no Sistema

### 1. Ao Cadastrar um Documento
```
1. Selecione o Estado (UF)
2. Selecione o Tipo de Documento (IPVA, Inspeção, etc)
3. O sistema mostra o mês padrão de vencimento
4. Você pode confirmar ou inserir data diferente
```

### 2. Exemplos Práticos

#### Exemplo 1: Veículo em São Paulo
- Estado: SP
- Documento: IPVA
- Vencimento Padrão: Dezembro
- Sugestão: Configurar para 15 de Dezembro

#### Exemplo 2: Veículo em Minas Gerais
- Estado: MG
- Documento: IPVA
- Vencimento Padrão: Janeiro
- Sugestão: Configurar para 15 de Janeiro

#### Exemplo 3: Veículo na Bahia
- Estado: BA
- Documento: Inspeção Veicular
- Vencimento Padrão: Novembro
- Sugestão: Configurar para 15 de Novembro

## Algoritmo de Alertas Considerando Estado

```python
def gerar_alerta_com_estado(veiculo_id, tipo_documento, estado_uf):
    # Buscar mês padrão de vencimento
    mes_vencimento = TABELA[estado_uf][tipo_documento]
    
    # Comparar data cadastrada com mês padrão
    if data_vencimento.month == mes_vencimento:
        # Data está alinhada com o estado
        gerar_alerta_normal()
    else:
        # Data fora do padrão (pode ser renovação ou caso especial)
        gerar_alerta_especial()
```

## Configuração no Formulário

### Novo Documento
1. **Estado (UF)**: Campo obrigatório
   - Se não informado, usa o estado cadastrado no veículo
   - Se veículo não tem estado, campo fica vazio

2. **Tipo de Documento**: Campo obrigatório
   - Tipos suportados: IPVA, Inspeção Veicular, Revisão, CNH, CRLV, Seguro, etc

3. **Dica de Vencimento**: Automática
   - Após selecionar estado e tipo, mostra o mês padrão
   - Ex: "IPVA em SP vence em Dezembro"

4. **Data de Vencimento**: Campo obrigatório
   - Você pode inserir a data exata (não é obrigado a seguir o mês padrão)
   - Exemplo: 15/12/2024 para IPVA em SP

## Notas Importantes

### CNH (Carteira Nacional de Habilitação)
- Não varia por estado (vence 10 anos após emissão)
- Estado não é relevante
- Configure com qualquer estado, o alarme é pela data de emissão

### CRLV (Certificado de Registro e Licenciamento)
- Segue o mesmo calendário do IPVA
- Renova junto com o IPVA

### Seguro Obrigatório (DPVAT)
- Vence em 31 de Dezembro em todos os estados
- Configure com qualquer estado

## Alterações Personalizadas

Se precisar atualizar os vencimentos (nova legislação), edite em `documentos.py`:

```python
VENCIMENTOS_POR_ESTADO = {
    "SP": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},
    # Adicione ou modifique conforme necessário
}
```

## API de Consulta

### Obter Tabela Completa
```
GET /api/vencimentos-estado
```

Retorna:
```json
{
  "SP": {"IPVA": "12", "INSPECAO": "12", "REVISAO": "12"},
  "MG": {"IPVA": "01", "INSPECAO": "07", "REVISAO": "12"},
  ...
}
```

### Obter Mês de Vencimento Específico
Use na sua aplicação Python:
```python
from documentos import obter_meses_vencimento_estado

info = obter_meses_vencimento_estado("SP", "IPVA")
print(info)
# {"mes": 12, "descricao": "Vence em Dezembro (SP)"}
```

## Futuras Melhorias

1. **Integração com DETRAN**: Buscar dados automáticos
2. **Alertas Automáticos**: Baseado em data de vencimento típica do estado
3. **Calendário Visual**: Mostrar calendário com vencimentos
4. **Histórico**: Rastrear renovações por ano
5. **Lembretes Periódicos**: Enviar aviso com antecedência

## Contato e Sugestões

Se encontrar informações incorretas ou desatualizado, por favor reporte:
- Data base: Janeiro de 2026
- Última atualização: Conforme legislação estadual

## Referências

- DETRAN: www.detran.sp.gov.br (e sites dos outros estados)
- Ministério do Meio Ambiente: Normas de inspeção veicular
- DENATRAN: Diretrizes de licenciamento
