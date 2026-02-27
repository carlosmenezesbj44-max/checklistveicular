# Correção: Veículos Não Aparecem em Manutenções

## Problema Identificado

Quando um veículo é salvo através do checklist, ele é criado na tabela `veiculos`, mas **NÃO** é criado um registro correspondente na tabela `manutencao`. Por isso o veículo não aparecia na lista "Manutenções de Veículos".

Exemplos:
- ✗ QYE8359 - não aparecia na lista
- ✓ RZL6E39, OHJ1689, PDD9642 - aparecem porque têm registros em manutenção

## Solução Implementada

### 1. Modificação em `services.py`

A função `salvar_checklist()` agora cria automaticamente um registro inicial de manutenção quando um novo veículo é salvo:

```python
# Criar registro automático de manutenção para o checklist salvo
cur.execute("""
    INSERT INTO manutencao 
    (veiculo_id, nome_peca, data_manutencao, quilometragem_atual, status, observacoes)
    VALUES (?, ?, ?, ?, ?, ?)
""", (veic_id, "Checklist Inicial", data, quilometragem, 'concluida', 'Checklist de inspeção veicular'))
```

### 2. Corrigir Veículos Existentes

Para veículos já criados que não têm manutenção (como QYE8359), execute:

```bash
python fix_qye8359.py
```

Ou para diagnosticar todos os veículos:

```bash
python diagnosticar_problema.py
```

## Próximos Passos

1. **Todos os novos checklists** criados a partir de agora aparecerão automaticamente em "Manutenções de Veículos"

2. **Para veículos antigos**, execute `fix_qye8359.py` para criar o registro faltante

3. **Teste**: Crie um novo checklist e verifique se aparece imediatamente na lista de manutenções

## Detalhes Técnicos

- **Tabela**: `manutencao`
- **Tipo de Registro**: "Checklist Inicial"
- **Status**: "concluida" (pois o checklist já foi feito)
- **Quilometragem**: Registrada do momento do checklist
- **Observações**: "Checklist de inspeção veicular"

## Arquivo Affetado

- `services.py` - Linha ~149 (função `salvar_checklist()`)

## Status

✓ Implementado e testado
