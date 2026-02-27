# Funcionalidade: Deletar Checklist do Histórico

## Descrição

Adicionado botão de **Deletar** na aba de Histórico que permite remover permanentemente um checklist completo do veículo.

## Funcionalidades

### ✅ O que foi implementado:

1. **Botão Deletar no Histórico**
   - Posicionado ao lado do botão "Manutenção"
   - Ícone: `<i class="bi bi-trash"></i>`
   - Cor: Vermelho (btn-outline-danger)

2. **Modal de Confirmação**
   - Exibe a placa do veículo
   - Aviso sobre a ação ser irreversível
   - Dois botões: Cancelar e Deletar Permanentemente

3. **Rota de Delete**
   - Endpoint: `POST /checklist/deletar/<veiculo_id>`
   - Requer autenticação
   - Deleta veículo e todos os itens de checklist

4. **Limpeza Automática**
   - Remove fotos e anexos órfãos
   - Retorna confirmação via flash message

## Como Usar

### Passo 1: Acessar Histórico
```
1. Ir para: Dashboard > Histórico
2. Ou acessar diretamente: /historico
```

### Passo 2: Clicar em Deletar
```
1. Encontrar o veículo na lista
2. Clicar no botão vermelho "Deletar"
3. Confirmar no modal de confirmação
```

### Passo 3: Confirmação
```
Modal exibe:
- ⚠️ Confirmar Exclusão
- Placa do veículo
- Aviso de que não pode ser desfeito
- Botões: Cancelar | Deletar Permanentemente
```

### Passo 4: Conclusão
```
Se confirmado:
✅ "Checklist do veículo ABC-1234 deletado com sucesso!"

Se cancelado:
Modal fecha sem fazer nada
```

## O que é Deletado

### Dados Removidos:
- ✅ Todos os itens do checklist (itens_checklist)
- ✅ Registro do veículo (veiculos)
- ✅ Fotos e anexos órfãos (ANEXOS_DIR)

### Dados NÃO Removidos:
- ❌ Histórico de manutenção (manutencao)
- ❌ Registro de combustível (combustivel)
- ❌ Documentos (documentos_veiculo)
- ❌ Alertas (alertas_veiculo)

**Nota**: Se precisar deletar tudo, use as rotas específicas de cada módulo.

## Estrutura HTML

```html
<button type="button" 
        class="btn btn-outline-danger btn-sm" 
        onclick="confirmarDelecao({{ r.id }}, '{{ r.placa }}')"
        title="Deletar Checklist">
  <i class="bi bi-trash"></i> Deletar
</button>
```

## Estrutura Modal

```html
<div class="modal fade" id="deleteModal">
  <div class="modal-dialog">
    <div class="modal-content">
      <!-- Header (Vermelho) -->
      <!-- Body (Mensagem + Aviso) -->
      <!-- Footer (Botões) -->
    </div>
  </div>
</div>
```

## JavaScript

### Função: confirmarDelecao()
```javascript
function confirmarDelecao(veiculoId, placa) {
  // 1. Atualiza placa no modal
  // 2. Define ação do formulário
  // 3. Exibe o modal
}
```

### Fluxo:
```
Clique em Deletar
    ↓
confirmarDelecao()
    ↓
Modal exibido
    ↓
Usuário confirma
    ↓
POST /checklist/deletar/<id>
    ↓
Redireciona para /historico
```

## Rota Backend

### Endpoint: POST /checklist/deletar/<veiculo_id>

```python
@app.route("/checklist/deletar/<int:veiculo_id>", methods=["POST"])
@login_required
def deletar_checklist(veiculo_id):
    # 1. Busca veículo
    # 2. Deleta itens de checklist
    # 3. Deleta registro do veículo
    # 4. Limpa arquivos órfãos
    # 5. Retorna sucesso/erro
```

### Fluxo:
```
1. Verificar se veículo existe
2. Obter placa para mensagem
3. DELETE FROM itens_checklist WHERE veiculo_id = ?
4. DELETE FROM veiculos WHERE id = ?
5. Executar limpar_arquivos_orfaos()
6. Flash message de sucesso
7. Redirecionar para /historico
```

## Estados Possíveis

### ✅ Sucesso
```
Flash: "Checklist do veículo ABC-1234 deletado com sucesso!"
Tipo: success (verde)
```

### ❌ Erro - Veículo não encontrado
```
Flash: "Veículo não encontrado."
Tipo: error (vermelho)
```

### ❌ Erro - Exceção
```
Flash: "Erro ao deletar checklist: [mensagem do erro]"
Tipo: error (vermelho)
```

## Segurança

✅ **Autenticação**: @login_required (usuário deve estar logado)
✅ **Validação**: Verifica se veículo existe antes de deletar
✅ **Confirmação**: Modal exige confirmação explícita
✅ **Transação**: Usa commit/rollback para integridade
✅ **Aviso**: Mensagem clara sobre ação irreversível

## Atalhos de Acesso

### Histórico
```
URL: /historico
Botão: Dashboard > Histórico
```

### Delete Individual
```
Botão: [Deletar] no item do histórico
Confirmação: Modal com placa do veículo
```

## Exemplos de Uso

### Exemplo 1: Deletar Checklist Errado
```
1. Ir para /historico
2. Encontrar "ABC-1234" com data/dados errados
3. Clicar [Deletar]
4. Confirmar no modal
5. ✅ Deletado com sucesso
```

### Exemplo 2: Deletar Acidentalmente
```
1. Clicar [Deletar]
2. Ver modal de confirmação
3. Clicar [Cancelar]
4. Modal fecha, nada acontece
```

### Exemplo 3: Limpeza em Massa
```
Para deletar múltiplos checklists:
1. Ir para /historico
2. Repetir processo para cada veículo
3. (Ou criar rota de delete em massa no futuro)
```

## Próximas Melhorias

1. **Delete Múltiplo**: Checkboxes para deletar vários
2. **Soft Delete**: Mover para "Lixeira" em vez de deletar
3. **Backup Automático**: Antes de deletar, fazer backup
4. **Auditoria**: Registrar quem e quando deletou
5. **Recuperação**: Opção de restaurar de backup por 30 dias

## Troubleshooting

### Botão não aparece
- Verifique se está na aba /historico
- Reload da página
- Verificar console do navegador

### Modal não abre
- Verifique se Bootstrap está carregado
- Console: `bootstrap.Modal` deve estar disponível
- Verifique JavaScript errors (F12 > Console)

### Delete não funciona
- Verificar logs do servidor
- Verificar autenticação (login?)
- Verificar permissões do banco de dados

### Flash message não aparece
- Verificar se página redirect para /historico
- Verificar se sesão está ativa
- Verifique template base.html para flash messages

## Testes Recomendados

```bash
# 1. Verificar se botão aparece
- Acessar /historico
- Verificar existência de botão [Deletar]

# 2. Testar modal
- Clicar [Deletar]
- Verificar dados corretos no modal
- Testar fechar (X)
- Testar Cancelar

# 3. Testar delete
- Confirmar delete
- Verificar redirecionar para /historico
- Verificar mensagem de sucesso
- Verificar veículo foi deletado da lista

# 4. Testar limpeza
- Upload foto em checklist antes de deletar
- Deletar checklist
- Verificar foto foi removida
```

---

**Data de Implementação**: Janeiro 2026
**Status**: ✅ Implementado e Funcional
**Versão**: 1.0
