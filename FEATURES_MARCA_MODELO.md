# Adição de Marca e Modelo Dinâmicos - Novo Checklist

## Resumo das Alterações
Implementada a funcionalidade de adicionar novas marcas e modelos de veículos diretamente no formulário de **Novo Checklist**, sem necessidade de editar o código. Essa funcionalidade está disponível para **todos os usuários** (admin e usuários normais).

## Arquivos Modificados

### 1. **templates/index.html**
- **Adição de botões "+"**: Botões para adicionar marca e modelo ao lado dos campos select
- **Modais interativos**: 
  - Modal para adicionar nova marca (com seleção de tipo: Carro/Moto)
  - Modal para adicionar novo modelo (com auto-preenchimento da marca selecionada)
- **Funções JavaScript novas**:
  - `adicionarNovaMarca()`: Valida e envia a nova marca via API
  - `adicionarNovoModelo()`: Valida e envia o novo modelo via API
  - Atualização dinâmica dos dados na sessão sem recarregar a página

### 2. **app.py**
Adicionados dois novos endpoints de API:

#### **POST `/api/adicionar-marca`**
```
Parâmetros:
- marca (string): Nome da marca
- tipo (string): Tipo de veículo ('Carro' ou 'Moto')

Resposta:
{
  "success": true/false,
  "message": "Descrição do resultado"
}

Validações:
- Marca não pode estar vazia
- Tipo deve ser 'Carro' ou 'Moto'
- Marca não pode ser duplicada
- Requer login (@login_required)
```

#### **POST `/api/adicionar-modelo`**
```
Parâmetros:
- marca (string): Nome da marca
- modelo (string): Nome do modelo
- ano (string, opcional): Ano do modelo
- tipo (string): Tipo de veículo ('Carro' ou 'Moto')

Resposta:
{
  "success": true/false,
  "message": "Descrição do resultado"
}

Validações:
- Marca e modelo são obrigatórios
- Tipo deve ser 'Carro' ou 'Moto'
- Se modelo já existe na mesma marca, adiciona apenas o ano
- Requer login (@login_required)
```

## Fluxo de Uso

### Adicionar Nova Marca:
1. Usuário está no formulário de Novo Checklist
2. Clica no botão **"+"** ao lado do select de Marca
3. Preenche o formulário no modal:
   - Nome da Marca (ex: Tesla, BYD)
   - Tipo de Veículo (Carro ou Moto)
4. Clica em "Adicionar"
5. Marca é adicionada e automaticamente selecionada no select
6. Modelos desaparecem (marca nova não tem modelos)
7. Usuário pode adicionar modelos para essa marca

### Adicionar Novo Modelo:
1. Usuário seleciona uma marca
2. Clica no botão **"+"** ao lado do select de Modelo
3. Preenche o formulário no modal:
   - Marca (pré-preenchida automaticamente)
   - Nome do Modelo (ex: Tesla Model 3)
   - Ano (opcional, ex: 2023)
4. Clica em "Adicionar"
5. Modelo é adicionado e automaticamente selecionado no select
6. Campo de ano é preenchido automaticamente

## Dados Persistidos
- **Durante a sessão**: Os dados novos ficam em memória e disponíveis enquanto o usuário está na página
- **Ao salvar o checklist**: A marca e modelo são salvos normalmente no banco de dados
- **Para novas sessões**: As marcas e modelos adicionados estão disponíveis apenas durante a mesma sessão do navegador

## Permissões
- ✅ **Admin**: Pode adicionar marcas e modelos
- ✅ **Usuário Normal**: Pode adicionar marcas e modelos
- ✅ **Visitante (não autenticado)**: Não pode - redirecionado para login

## Dados Modificados
A constantes JavaScript que são modificadas em tempo real:
- `veiculosCarroData`: Array de veículos/marcas de carro
- `veiculosMotoData`: Array de veículos/marcas de moto
- `veiculosAtivos`: Referência ao array ativo (carro ou moto)

## Estrutura de Dados
```javascript
{
  marca: "Toyota",
  modelo: "Corolla",
  anos: [2023, 2022, 2021]
}
```

## Exemplo de Uso Prático

### Cenário 1: Novo veículo não está na lista
1. Usuário abre "Novo Checklist"
2. Seleciona tipo "Carro"
3. Tenta encontrar marca "BYD" - não encontra
4. Clica no "+" da marca
5. Adiciona "BYD"
6. Automaticamente seleciona "BYD"
7. Clica no "+" do modelo
8. Adiciona modelo "Song Plus DM-i" com ano 2023
9. Preenche o resto do formulário normalmente

### Cenário 2: Adicionar novo ano para modelo existente
1. Usuário seleciona marca "Toyota"
2. Seleciona modelo "Corolla"
3. Quer adicionar um modelo "Corolla 2024"
4. Clica no "+" do modelo
5. Deixa a marca "Toyota" (já preenchida)
6. Digite "Corolla"
7. Digite "2024"
8. Clica "Adicionar"
9. Ano 2024 é adicionado ao modelo Corolla existente

## Testes Recomendados

1. ✅ Adicionar marca sem preencher nome
2. ✅ Adicionar marca que já existe (validação de duplicata)
3. ✅ Adicionar modelo sem selecionar marca
4. ✅ Adicionar modelo com anos e sem anos
5. ✅ Verificar se dados novos aparecem nos selects
6. ✅ Alternar entre Carro e Moto
7. ✅ Salvar checklist com marca/modelo novos
8. ✅ Testar com usuário normal (não admin)

## Melhorias Futuras (Opcional)
- [ ] Persistir dados em banco de dados (não apenas sessão)
- [ ] Permitir editar/deletar marcas e modelos
- [ ] Validação de duplicatas no frontend
- [ ] Sugestões de autocompletar
- [ ] Histórico de marcas/modelos adicionados
- [ ] Permissões granulares por role (admin-only para marcas)
