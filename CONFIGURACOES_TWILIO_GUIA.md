# Guia de Uso - Configurações do Twilio

## Acesso à Interface de Configurações

A nova interface de configurações do Twilio está disponível apenas para **administradores** da aplicação.

### Como Acessar

1. Faça login como **administrador**
2. Na **barra lateral esquerda**, procure pelo botão **"Configurações"** com ícone de engrenagem ⚙️
3. Clique para abrir a página de configurações
4. Acesse a aba **"Twilio"**

## Campos do Formulário

A aba do Twilio possui um formulário com os seguintes campos:

### 1. **Account SID** (obrigatório)
- **Formato esperado**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- **Onde obter**: [Twilio Console](https://www.twilio.com/console)
- Este é o identificador único da sua conta Twilio

### 2. **Auth Token** (obrigatório)
- **Formato esperado**: String alfanumérica
- **Onde obter**: [Twilio Console](https://www.twilio.com/console)
- Token de autenticação para acessar a API do Twilio
- **⚠️ Importante**: Mantenha este valor seguro e confidencial

### 3. **Número WhatsApp (De)** (obrigatório)
- **Formato esperado**: `whatsapp:+551199999999`
- Este é o número WhatsApp configurado no Twilio que será usado para **enviar mensagens**
- **Formato**: `whatsapp:` seguido do número com código de país (+55 para Brasil)

### 4. **Número do Admin** (obrigatório)
- **Formato esperado**: `+5511987654321`
- Número WhatsApp do administrador que receberá **notificações**
- **Formato**: `+55` com DDD (ex: `+5511987654321`)

## Salvando as Configurações

1. Preencha todos os campos corretamente
2. Clique no botão **"Salvar Configurações"** (verde)
3. Uma mensagem de sucesso será exibida se tudo correu bem

## Status da Conexão

Logo abaixo do formulário, há uma seção **"Status da Conexão"** que:

- **Carrega automaticamente** quando a página é aberta (se houver credenciais salvas)
- **Exibe verificação** da conexão com o Twilio
- Mostra:
  - ✅ **Verde**: Conectado com sucesso
  - ⚠️ **Amarelo**: Desconectado ou credenciais inválidas
  - ❌ **Vermelho**: Erro ao verificar status

## Validações

O formulário valida:

- **Todos os campos são obrigatórios**
- **Account SID**: Deve começar com "AC"
- **Número WhatsApp (De)**: Deve começar com "whatsapp:" e um número válido
- **Número Admin**: Deve começar com "+" seguido de dígitos

## Dados Sensíveis

⚠️ **Segurança**:
- As credenciais são armazenadas no arquivo `.env`
- Não compartilhe suas credenciais com terceiros
- Se suspeitar de comprometimento, regenere seus tokens no Twilio

## Modificando .env Diretamente

Se preferir editar o arquivo `.env` manualmente:

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com seu editor preferido
nano .env  # ou code .env, vim .env, etc.
```

Adicione ou modifique:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+551199999999
ADMIN_WHATSAPP=+5511987654321
```

## Troubleshooting

### Status sempre mostra "Desconectado"

1. Verifique se as credenciais estão corretas no [Twilio Console](https://www.twilio.com/console)
2. Verifique se o Token não expirou
3. Tente gerar um novo Token no Twilio
4. Verifique se há conexão com a internet

### Erro ao salvar

1. Certifique-se de que o arquivo `.env` tem permissões de escrita
2. Verifique se todos os campos foram preenchidos
3. Verifique o formato dos números telefônicos

### WhatsApp não recebe mensagens

1. Verifique se o número WhatsApp (De) está configurado no Twilio
2. Verifique se a Sandbox ou Business Account foi aprovada
3. Teste usando o [Twilio Console](https://www.twilio.com/console)

## Próximos Passos

Após configurar o Twilio:

1. Teste a conexão usando a verificação de status
2. Envie uma mensagem de teste
3. Verifique se as notificações estão funcionando

---

Para mais informações, acesse:
- [Documentação do Twilio](https://www.twilio.com/docs)
- [Twilio Console](https://www.twilio.com/console)
- [WhatsApp Business API](https://www.twilio.com/whatsapp)
