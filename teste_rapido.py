#!/usr/bin/env python3
"""
Teste rápido com número do Twilio
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

message = client.messages.create(
    from_=os.getenv('TWILIO_WHATSAPP_FROM'),
    body='Teste do sistema de checklist veicular',
    to='whatsapp:+14155238886'
)

print('✅ Mensagem enviada!')
print(f'SID: {message.sid}')
print(f'Status: {message.status}')
