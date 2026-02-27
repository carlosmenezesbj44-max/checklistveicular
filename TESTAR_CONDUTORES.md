# Como Testar a Funcionalidade de Condutores

## 1. Verificar se há condutores cadastrados

```bash
python test_condutores.py
```

Este script mostará:
- Total de condutores no banco
- Lista dos primeiros 10 condutores

## 2. Se não houver condutores, criar alguns testes

Dentro do app Flask:

```python
from db import get_conn

conn = get_conn()
cur = conn.cursor()

# Inserir condutores de teste
cur.execute("""
    INSERT INTO condutores (nome_completo, cpf, ativo)
    VALUES 
    ('João Silva', '123.456.789-00', 1),
    ('Maria Santos', '987.654.321-11', 1),
    ('Pedro Oliveira', '456.789.123-22', 1),
    ('Ana Costa', '789.123.456-33', 1)
""")
conn.commit()
conn.close()
```

## 3. Testar a API direto

Acesse no navegador:
```
http://localhost:5000/api/condutores/listar
```

Você deve ver um JSON com os condutores.

## 4. Testar no formulário

1. Abra: http://localhost:5000/cadastrar_veiculo
2. Na seção "Informações Básicas", no campo "Condutor":
   - **Clique no botão lista** (ícone com 3 linhas) para ver todos
   - **Digite um nome** para filtrar

## 5. Verificar Console do Navegador

Pressione F12 e vá na aba "Console" para ver:
- "DOM carregado - iniciando carregamento de condutores"
- "Carregando condutores de: /api/condutores/listar"
- "Status da resposta: 200"
- "Condutores carregados: [...]"

## Possíveis Problemas

### 1. Erro 404 na API
- Verifique se a rota `/api/condutores/listar` existe no app.py
- ✓ Verificado - a rota existe na linha 2443

### 2. Erro 500
- Verifique se a tabela `condutores` existe
- Verifique se há condutores cadastrados

### 3. Dropdown não aparece
- Verifique se não há erros de JavaScript no console (F12)
- Verifique se os condutores foram carregados (veja o console)

### 4. Condutores carregam mas não mostram
- Verifique se o dropdown está visível (pode estar por trás de outro elemento)
- Aumentamos o z-index para 1000 no CSS

## Estrutura esperada da resposta JSON

```json
[
  {
    "id": 1,
    "nome": "João Silva",
    "cpf": "123.456.789-00",
    "telefone": "",
    "email": "",
    "status": "ativo"
  },
  ...
]
```
