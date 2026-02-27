#!/usr/bin/env python3
"""
Script para verificar o conteúdo do .env
"""

import os
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"

print("=" * 70)
print("VERIFICADOR DE ARQUIVO .ENV")
print("=" * 70)

if not ENV_FILE.exists():
    print(f"❌ Arquivo não existe: {ENV_FILE}")
else:
    print(f"✅ Arquivo existe: {ENV_FILE}")
    print()
    
    print("CONTEÚDO DO .ENV:")
    print("-" * 70)
    
    try:
        with open(str(ENV_FILE), 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content.strip():
            print("❌ Arquivo vazio!")
        else:
            # Lê o arquivo e mostra as linhas relevantes
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    # Não mostra valores sensíveis completamente
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if len(value) > 20:
                            masked = value[:10] + '...' + value[-5:]
                        else:
                            masked = value
                        print(f"{key}={masked}")
                    else:
                        print(line)
        
        print("-" * 70)
        print()
        print("VARIÁVEIS DE AMBIENTE CARREGADAS:")
        print("-" * 70)
        
        twilio_vars = [
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_WHATSAPP_FROM",
            "ADMIN_WHATSAPP"
        ]
        
        for var in twilio_vars:
            value = os.getenv(var, "NÃO CONFIGURADO")
            if value == "NÃO CONFIGURADO":
                print(f"❌ {var}: NÃO ENCONTRADO")
            else:
                if len(value) > 20:
                    masked = value[:10] + '...' + value[-5:]
                else:
                    masked = value
                print(f"✅ {var}: {masked}")
        
        print("-" * 70)
        
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")

print("=" * 70)
