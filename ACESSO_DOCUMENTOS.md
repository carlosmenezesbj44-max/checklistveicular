# Acesso Rápido a Documentos por Placa

## Rotas Disponíveis

### 1. Página de Busca (Recomendado)
```
GET /documentos
```
- Interface amigável para buscar documentos
- Busca por placa do veículo
- Lista veículos acessados recentemente
- Auto-formata a placa enquanto digita

**Uso:**
1. Clique em "Documentos" no menu
2. Digite a placa (ex: ABC-1234)
3. Clique em "Buscar"

### 2. Acesso Direto pela Placa
```
GET /documentos/placa/ABC-1234
GET /documentos/placa/ABC1234
```
Acessa direto os documentos de um veículo pela placa (com ou sem hífen)

**Exemplo no navegador:**
```
https://seu-app.com/documentos/placa/ABC-1234
https://seu-app.com/documentos/placa/ABC1234
```

### 3. Acesso por ID (Tradicional)
```
GET /documentos/5
```
Acessa documentos pelo ID numérico do veículo (usado internamente)

## Busca Inteligente

A busca funciona de várias formas:

| Entrada | Resultado |
|---------|-----------|
| `ABC1234` | Encontra `ABC-1234` |
| `ABC-1234` | Encontra `ABC-1234` |
| `ABC` | Encontra todas com `ABC` |
| `1234` | Encontra todas com `1234` |

## Formatos de Placa Suportados

### Placa Antiga (Brasileira)
```
ABC-1234
```
- 3 letras + 4 números
- Hífen é opcional

### Placa Mercosul (Nova)
```
ABC-1D23
```
- 3 letras + 1 número + 1 letra + 2 números
- Hífen é opcional

## Exemplos de Uso

### Exemplo 1: Buscar CNH de um Motorista
1. Ir para `/documentos`
2. Digitar `ABC-1234`
3. Clicar em "Buscar"
4. Ver lista de documentos vencidos/próximos de vencer

### Exemplo 2: Link Direto no Aplicativo
Criar link direto na sua página:
```html
<a href="/documentos/placa/ABC-1234">
    Ver Documentos do Veículo ABC-1234
</a>
```

### Exemplo 3: Busca Parcial
- Digitar apenas `ABC` → mostra todos os veículos com placa iniciada em `ABC`
- Digitar apenas `1234` → mostra todos os veículos com esses números

## URLs Rápidas

### Bookmarks Úteis (adicione ao navegador)

**Buscar Documentos:**
```
https://seu-app.com/documentos
```

**Documentos de Veículos Específicos:**
```
https://seu-app.com/documentos/placa/ABC-1234
https://seu-app.com/documentos/placa/XYZ-9876
https://seu-app.com/documentos/placa/DEF-5678
```

## API - Resumo de Alertas por Placa

```
GET /api/veiculos/alertas-resumo
```

Retorna lista de veículos com alertas:
```json
[
  {
    "veiculo_id": 1,
    "placa": "ABC-1234",
    "modelo": "Fusca",
    "documentos_vencidos": 2,
    "documentos_proximos_vencer": 1
  },
  {
    "veiculo_id": 2,
    "placa": "XYZ-9876",
    "modelo": "Gol",
    "documentos_vencidos": 0,
    "documentos_proximos_vencer": 3
  }
]
```

## Fluxo Prático

### Cenário: Verificar Documentos ao Receber Veículo
1. **Receber placa do veículo**: `ABC-1234`
2. **Abrir URL**: `/documentos/placa/ABC-1234`
3. **Ver status**: 
   - 🔴 Documentos vencidos
   - 🟡 Documentos vencendo
   - ✅ Documentos em dia
4. **Atualizar**: Se necessário, clicar em "Editar" para renovar datas

### Cenário: Gerenciar Frota
1. **Acessar dashboard**: `/`
2. **Clicar em "Documentos"**: `/documentos`
3. **Ver veículos recentes**
4. **Digitar placa desejada**
5. **Buscar**

## Integrações Recomendadas

### 1. Link no Dashboard
Adicionar botão no dashboard:
```html
<a href="{{ url_for('buscar_documentos') }}" class="btn btn-primary">
    <i class="bi bi-file-earmark"></i> Documentos
</a>
```

### 2. Link em Página de Veículo
```html
<a href="{{ url_for('listar_documentos_placa', placa=veiculo.placa) }}">
    Gerenciar Documentos
</a>
```

### 3. Widget de Alerta
Mostrar alertas em tempo real:
```javascript
fetch('/api/veiculos/alertas-resumo')
    .then(r => r.json())
    .then(data => {
        console.log('Veículos com alertas:', data);
    });
```

## Troubleshooting

### "Nenhum veículo encontrado"
- Verifique se a placa está cadastrada
- Tente buscar apenas os números ou letras
- Certifique-se que a placa está escrita corretamente

### Placa não formata automaticamente
- A formatação é apenas visual
- A busca funciona com ou sem hífen
- Digite a placa normalmente

### Links não funcionam
- Certifique-se de que o servidor está rodando
- Verifique o caminho base da URL
- Confirme que o usuário está autenticado

## Segurança

- ✅ Todas as rotas exigem autenticação (`@login_required`)
- ✅ Busca usa prepared statements (proteção contra SQL injection)
- ✅ Case-insensitive (funciona maiúsculas e minúsculas)
- ✅ Caracteres especiais são tratados corretamente

## Resumo de Funcionalidades

| Funcionalidade | Rota | Acesso |
|---|---|---|
| Buscar por placa | `/documentos` | Interface amigável |
| Acesso direto | `/documentos/placa/ABC-1234` | URL direta |
| Acesso por ID | `/documentos/5` | Uso interno |
| Novo documento | `/documentos/novo/5` | Formulário |
| Editar documento | `/documentos/editar/10` | Formulário |
| Deletar documento | `/documentos/deletar/10` | POST |
| API de alertas | `/api/alertas` | JSON |
| Resumo alertas | `/api/veiculos/alertas-resumo` | JSON |
