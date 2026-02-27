#!/usr/bin/env python3
"""
Script para testar envio de mensagem WhatsApp via Twilio
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

# Carrega variáveis do .env
load_dotenv()

print("=" * 70)
print("TESTE DE ENVIO WHATSAPP - TWILIO")
print("=" * 70)
print()

# Obtém credenciais
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
whatsapp_from = os.getenv("TWILIO_WHATSAPP_FROM")
admin_whatsapp = os.getenv("ADMIN_WHATSAPP")

print("VERIFICANDO CREDENCIAIS:")
print("-" * 70)

if not account_sid:
    print("❌ TWILIO_ACCOUNT_SID não configurado")
    exit(1)
else:
    print(f"✅ Account SID: {account_sid[:10]}...")

if not auth_token:
    print("❌ TWILIO_AUTH_TOKEN não configurado")
    exit(1)
else:
    print(f"✅ Auth Token: {auth_token[:10]}...")

if not whatsapp_from:
    print("❌ TWILIO_WHATSAPP_FROM não configurado")
    exit(1)
else:
    print(f"✅ WhatsApp (De): {whatsapp_from}")

if not admin_whatsapp:
    print("❌ ADMIN_WHATSAPP não configurado")
    exit(1)
else:
    print(f"✅ Admin WhatsApp (Para): {admin_whatsapp}")

print()
print("CONECTANDO AO TWILIO:")
print("-" * 70)

try:
    client = Client(account_sid, auth_token)
    print("✅ Conectado ao Twilio com sucesso!")
    print()
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    exit(1)

print("ENVIANDO MENSAGEM DE TESTE:")
print("-" * 70)

try:
    message = client.messages.create(
        from_=whatsapp_from,
        body="🧪 Teste de conexão Twilio WhatsApp - Sistema de Checklist Veicular",
        to=admin_whatsapp
    )
    
    print(f"✅ Mensagem enviada com sucesso!")
    print(f"   SID: {message.sid}")
    print(f"   De: {whatsapp_from}")
    print(f"   Para: {admin_whatsapp}")
    print(f"   Status: {message.status}")
    print()
    print("=" * 70)
    print("✨ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 70)
    print()
    print("Verifique seu WhatsApp para confirmar o recebimento da mensagem.")
    print()
    
except Exception as e:
    print(f"❌ Erro ao enviar mensagem: {e}")
    print()
    print("Possíveis problemas:")
    print("  1. Número WhatsApp (De) não validado no Twilio")
    print("  2. Número Admin não validado ou em formato errado")
    print("  3. Conta Twilio em Sandbox (só aceita números pré-aprovados)")
    print()
    exit(1)
