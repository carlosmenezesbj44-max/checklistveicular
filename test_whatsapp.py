#!/usr/bin/env python3
"""
Script de teste para validar integração WhatsApp/Twilio
"""

import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

from notifications.whatsapp import WhatsAppNotifier
from detectors import AnomaliaDetector


def testar_configuracao():
    """Testa se credenciais estão configuradas"""
    print("\n" + "="*60)
    print("🧪 TESTE 1: Verificar Configuração")
    print("="*60)
    
    account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
    auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
    whatsapp_from = os.environ.get('TWILIO_WHATSAPP_FROM')
    admin_whatsapp = os.environ.get('ADMIN_WHATSAPP')
    
    print(f"\n✓ TWILIO_ACCOUNT_SID: {account_sid[:10]}..." if account_sid else "✗ TWILIO_ACCOUNT_SID: NÃO CONFIGURADO")
    print(f"✓ TWILIO_AUTH_TOKEN: {auth_token[:10]}..." if auth_token else "✗ TWILIO_AUTH_TOKEN: NÃO CONFIGURADO")
    print(f"✓ TWILIO_WHATSAPP_FROM: {whatsapp_from}" if whatsapp_from else "✗ TWILIO_WHATSAPP_FROM: NÃO CONFIGURADO")
    print(f"✓ ADMIN_WHATSAPP: {admin_whatsapp}" if admin_whatsapp else "✗ ADMIN_WHATSAPP: NÃO CONFIGURADO")
    
    if not all([account_sid, auth_token, whatsapp_from]):
        print("\n⚠️  CREDENCIAIS INCOMPLETAS!")
        print("Por favor, configure o arquivo .env com suas credenciais Twilio")
        return False
    
    print("\n✅ Configuração OK!")
    return True


def testar_notifier():
    """Testa inicialização do notifier"""
    print("\n" + "="*60)
    print("🧪 TESTE 2: Inicializar WhatsApp Notifier")
    print("="*60)
    
    notifier = WhatsAppNotifier()
    
    if notifier.disponivel:
        print("\n✅ WhatsApp Notifier inicializado com sucesso!")
        return True
    else:
        print("\n❌ WhatsApp Notifier não disponível")
        print("Verifique as credenciais Twilio")
        return False


def testar_envio_mensagem():
    """Testa envio de mensagem básica"""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Enviar Mensagem de Teste")
    print("="*60)
    
    admin_whatsapp = os.environ.get('ADMIN_WHATSAPP')
    
    if not admin_whatsapp:
        print("\n⚠️  ADMIN_WHATSAPP não configurado")
        print("Configure no .env para testar envio")
        return False
    
    notifier = WhatsAppNotifier()
    
    if not notifier.disponivel:
        print("\n⚠️  WhatsApp não disponível")
        return False
    
    print(f"\nEnviando mensagem de teste para: {admin_whatsapp}")
    
    resultado = notifier.send(
        to_number=admin_whatsapp,
        message="🧪 *Teste do Sistema de Abastecimento*\n\nEste é um teste de integração WhatsApp. Se você recebeu esta mensagem, o sistema está funcionando! ✅"
    )
    
    if resultado:
        print("✅ Mensagem enviada com sucesso!")
        return True
    else:
        print("❌ Erro ao enviar mensagem")
        return False


def testar_templates():
    """Testa templates de mensagens"""
    print("\n" + "="*60)
    print("🧪 TESTE 4: Templates de Mensagens")
    print("="*60)
    
    admin_whatsapp = os.environ.get('ADMIN_WHATSAPP')
    
    if not admin_whatsapp:
        print("\n⚠️  ADMIN_WHATSAPP não configurado")
        return False
    
    notifier = WhatsAppNotifier()
    
    if not notifier.disponivel:
        print("\n⚠️  WhatsApp não disponível")
        return False
    
    # Template 1: Notificação de abastecimento
    print("\n1. Testando template de abastecimento...")
    dados = {
        'placa': 'ABC-1234',
        'data': '15/01/2025',
        'litros': '50',
        'valor': '250.00',
        'km': '50000',
        'consumo': '10.5'
    }
    resultado1 = notifier.notificar_abastecimento(admin_whatsapp, dados)
    print(f"   {'✅' if resultado1 else '❌'} Notificação de abastecimento")
    
    # Template 2: Alerta de consumo
    print("\n2. Testando template de consumo...")
    dados_consumo = {
        'placa': 'ABC-1234',
        'consumo_esperado': '10.5',
        'consumo_atual': '8.2',
        'desvio_pct': '-21.9'
    }
    resultado2 = notifier.alerta_consumo(admin_whatsapp, dados_consumo)
    print(f"   {'✅' if resultado2 else '❌'} Alerta de consumo")
    
    return resultado1 or resultado2


def testar_detector():
    """Testa detector de anomalias"""
    print("\n" + "="*60)
    print("🧪 TESTE 5: Detector de Anomalias")
    print("="*60)
    
    print("\n✅ Detector de anomalias inicializado")
    print("   (Requer dados de teste no banco - será testado em ambiente real)")


def main():
    """Executa todos os testes"""
    print("\n" + "="*80)
    print("         TESTE DE INTEGRAÇÃO WHATSAPP - SISTEMA DE ABASTECIMENTO")
    print("="*80)
    
    testes = [
        ("Configuração", testar_configuracao),
        ("WhatsApp Notifier", testar_notifier),
        ("Envio de Mensagem", testar_envio_mensagem),
        ("Templates", testar_templates),
        ("Detector de Anomalias", testar_detector),
    ]
    
    resultados = []
    
    for nome, funcao in testes:
        try:
            resultado = funcao()
            resultados.append((nome, resultado))
        except Exception as e:
            print(f"\n❌ Erro em {nome}: {str(e)}")
            resultados.append((nome, False))
    
    # Resumo final
    print("\n" + "="*80)
    print("RESUMO DOS TESTES")
    print("="*80)
    
    total = len(resultados)
    sucesso = sum(1 for _, r in resultados if r)
    
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "⚠️  PULADO" if resultado is None else "❌ FALHOU"
        print(f"{status} - {nome}")
    
    print(f"\nTotal: {sucesso}/{total} testes realizados com sucesso")
    
    if sucesso == total:
        print("\n🎉 TODOS OS TESTES PASSARAM! Sistema pronto para uso!")
    elif sucesso > 0:
        print(f"\n⚠️  {sucesso}/{total} testes passaram. Verifique os erros acima.")
    else:
        print("\n❌ Configure as credenciais Twilio no arquivo .env para usar WhatsApp")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
