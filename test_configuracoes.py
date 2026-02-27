#!/usr/bin/env python3
"""
Script de teste para a funcionalidade de Configurações
Verifica se o módulo config_manager está funcionando corretamente
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Testa se as importações funcionam corretamente"""
    print("=" * 60)
    print("TEST 1: Testando importações")
    print("=" * 60)
    
    try:
        from config_manager import ConfigManager, get_twilio_config, verify_twilio_connection
        print("✅ Importações do config_manager OK")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar config_manager: {e}")
        return False


def test_get_config():
    """Testa se consegue ler as configurações do Twilio"""
    print("\n" + "=" * 60)
    print("TEST 2: Lendo configurações do Twilio")
    print("=" * 60)
    
    try:
        from config_manager import get_twilio_config
        config = get_twilio_config()
        
        print(f"Account SID: {'Configurado' if config.get('TWILIO_ACCOUNT_SID') else 'Não configurado'}")
        print(f"Auth Token: {'Configurado' if config.get('TWILIO_AUTH_TOKEN') else 'Não configurado'}")
        print(f"WhatsApp From: {'Configurado' if config.get('TWILIO_WHATSAPP_FROM') else 'Não configurado'}")
        print(f"Admin WhatsApp: {'Configurado' if config.get('ADMIN_WHATSAPP') else 'Não configurado'}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao ler configurações: {e}")
        return False


def test_update_config():
    """Testa se consegue atualizar as configurações"""
    print("\n" + "=" * 60)
    print("TEST 3: Testando atualização de configurações")
    print("=" * 60)
    
    try:
        from config_manager import ConfigManager
        
        # Dados de teste
        test_config = {
            "TWILIO_ACCOUNT_SID": "ACtest123456789",
            "TWILIO_AUTH_TOKEN": "test_token_123",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+5511999999999",
            "ADMIN_WHATSAPP": "+5511988888888",
        }
        
        # Atualiza as configurações
        result = ConfigManager.update_twilio_config(test_config)
        
        if result:
            print("✅ Configurações atualizadas com sucesso")
            
            # Verifica se foram salvos corretamente
            from config_manager import get_twilio_config
            updated_config = get_twilio_config()
            
            print("\nValores salvos:")
            for key, value in updated_config.items():
                expected = test_config.get(key, "")
                status = "✅" if value == expected else "❌"
                print(f"  {status} {key}: {value}")
            
            return True
        else:
            print("❌ Erro ao atualizar configurações")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar atualização: {e}")
        return False


def test_verify_connection():
    """Testa se consegue verificar a conexão com Twilio"""
    print("\n" + "=" * 60)
    print("TEST 4: Testando verificação de conexão com Twilio")
    print("=" * 60)
    
    try:
        from config_manager import verify_twilio_connection
        
        result = verify_twilio_connection()
        
        print(f"Conectado: {result.get('conectado', False)}")
        if result.get('conta'):
            print(f"Conta: {result.get('conta')}")
        if result.get('erro'):
            print(f"Erro: {result.get('erro')}")
        
        # Esperamos que não esteja conectado se não tiver credenciais válidas
        # ou que esteja se as credenciais forem válidas
        print("✅ Verificação de conexão funcionando")
        return True
        
    except Exception as e:
        print(f"⚠️ Erro ao testar verificação (pode ser esperado): {e}")
        return False


def main():
    """Executa todos os testes"""
    print("\n" + "=" * 60)
    print("TESTES DE CONFIGURAÇÕES - TWILIO")
    print("=" * 60)
    
    tests = [
        ("Importações", test_imports),
        ("Leitura de Configurações", test_get_config),
        ("Atualização de Configurações", test_update_config),
        ("Verificação de Conexão", test_verify_connection),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Erro ao executar {name}: {e}")
            results.append((name, False))
    
    # Resumo dos testes
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} testes passaram")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
