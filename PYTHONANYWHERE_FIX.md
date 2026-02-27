# Solução: Erro ao Salvar Combustível no PythonAnywhere

## Problema
```
Erro ao salvar registro de combustível: salvar_combustivel() missing 3 required positional arguments: 'quantidade_litros', 'valor_total', and 'data_abastecimento'
```

## Causa
O PythonAnywhere está carregando uma versão em cache da função `salvar_combustivel()` com assinatura antiga.

## Solução

### Opção 1: Reload Automático (Recomendado)

1. **No PythonAnywhere Web Admin:**
   - Vá para **Web** → **Your web apps**
   - Clique na sua aplicação
   - Clique no botão **Reload**
   - Aguarde 30 segundos

2. **Tente novamente adicionar combustível**

### Opção 2: Limpar Cache Manualmente

Se a Opção 1 não funcionar:

1. **Acesse o console do PythonAnywhere:**
   - Vá para **Consoles** → **Bash console**

2. **Execute:**
```bash
cd /home/seu_usuario/seu_projeto
python reload_app.py
```

3. **Depois faça reload da web app** (como na Opção 1)

### Opção 3: Verificar Assinatura da Função

Para confirmar que a função está correta:

```bash
# No console do PythonAnywhere
python -c "from app import salvar_combustivel; import inspect; print(inspect.signature(salvar_combustivel))"
```

Deve exibir: `(form, files)`

## Checklist de Validação

Após aplicar a solução, verifique:

- [ ] Campos obrigatórios estão preenchidos:
  - [ ] Placa do Veículo
  - [ ] Data do Abastecimento
  - [ ] Quantidade de Litros
  - [ ] Valor Total

- [ ] Valores numéricos estão válidos:
  - [ ] Litros deve ser um número (ex: 45.5)
  - [ ] Valor deve ser um número (ex: 250.50)

- [ ] Se envia arquivo de foto:
  - [ ] Arquivo é uma imagem (JPG, PNG, GIF, WEBP)
  - [ ] Tamanho é menor que 10MB

## Se o Erro Persistir

1. **Verifique os logs:**
   - Web → Your web apps → seu_app → **Error log**
   - Procure por mensagens de erro detalhadas

2. **Procure por:**
   - Erros de permissão ao salvar arquivo
   - Erros de banco de dados
   - Erros de import

3. **Se necessário, reverter commit anterior:**
```bash
git revert HEAD~1
```

## Contato
Se o problema persistir, verifique:
- Repositório: `https://github.com/carlosmenezesbj44-max/checklist-vip`
- Branch: `blackboxai/update`
- Commit: Procure por "melhorias na robustez"
