"""
Módulo para envio de notificações via WhatsApp usando Twilio
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class WhatsAppNotifier:
    """Gerencia envio de mensagens via WhatsApp/Twilio"""
    
    def __init__(self):
        """Inicializa cliente Twilio"""
        try:
            from twilio.rest import Client
            
            self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            self.from_number = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+5511999999999')
            
            if self.account_sid and self.auth_token:
                self.client = Client(self.account_sid, self.auth_token)
                self.disponivel = True
                logger.info("✅ WhatsApp Notifier inicializado com sucesso")
            else:
                self.client = None
                self.disponivel = False
                logger.warning("⚠️ Credenciais Twilio não configuradas em .env")
        except ImportError:
            self.client = None
            self.disponivel = False
            logger.error("❌ Twilio não instalado")
    
    def send(self, to_number: str, message: str) -> bool:
        """
        Envia mensagem WhatsApp
        
        Args:
            to_number: Número do destinatário (com ou sem +55)
            message: Conteúdo da mensagem
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        if not self.disponivel:
            logger.warning(f"⚠️ WhatsApp não disponível. Mensagem não enviada para {to_number}")
            return False
        
        try:
            # Garantir formato correto
            if not to_number.startswith('whatsapp:'):
                if not to_number.startswith('+'):
                    to_number = f'+{to_number}'
                to_number = f'whatsapp:{to_number}'
            
            msg = self.client.messages.create(
                from_=self.from_number,
                to=to_number,
                body=message
            )
            
            logger.info(f"✅ WhatsApp enviado para {to_number} (SID: {msg.sid})")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erro ao enviar WhatsApp para {to_number}: {str(e)}")
            return False
    
    def notificar_abastecimento(self, to_number: str, dados: dict) -> bool:
        """Notifica abastecimento registrado com sucesso"""
        mensagem = f"""✅ *ABASTECIMENTO REGISTRADO*

🚗 Veículo: {dados.get('placa', 'N/A')}
📅 Data: {dados.get('data', 'N/A')}
⛽ Litros: {dados.get('litros', 'N/A')}L
💰 Valor: R$ {dados.get('valor', 'N/A')}
📍 KM: {dados.get('km', 'N/A')} km
📊 Consumo: {dados.get('consumo', 'Calculando...')} km/l
📸 Foto: ✓ Recebida"""
        
        return self.send(to_number, mensagem)
    
    def alerta_consumo(self, to_number: str, dados: dict) -> bool:
        """Alerta de consumo anormal detectado"""
        mensagem = f"""⚠️ *ALERTA: CONSUMO ANORMAL*

🚗 Veículo: {dados.get('placa', 'N/A')}
📊 Esperado: {dados.get('consumo_esperado', 'N/A')} km/l
❌ Actual: {dados.get('consumo_atual', 'N/A')} km/l
📈 Desvio: {dados.get('desvio_pct', 'N/A')}%

⚠️ Verificar possível vazamento ou consumo diferente do padrão."""
        
        return self.send(to_number, mensagem)
    
    def alerta_quilometragem(self, to_number: str, dados: dict) -> bool:
        """Alerta de quilometragem suspeita"""
        mensagem = f"""🚨 *ALERTA: QUILOMETRAGEM SUSPEITA*

🚗 Veículo: {dados.get('placa', 'N/A')}
⏮️ Anterior: {dados.get('km_anterior', 'N/A')} km
❌ Atual: {dados.get('km_atual', 'N/A')} km

⚠️ Quilometragem DIMINUIU!
Verificar se houve erro no registro."""
        
        return self.send(to_number, mensagem)
    
    def alerta_valor(self, to_number: str, dados: dict) -> bool:
        """Alerta de valor fora do padrão"""
        mensagem = f"""💰 *ALERTA: VALOR ACIMA DO NORMAL*

🚗 Veículo: {dados.get('placa', 'N/A')}
📊 Preço médio: R$ {dados.get('valor_medio', 'N/A')}
❌ Pago: R$ {dados.get('valor_pago', 'N/A')}
📈 Diferença: +{dados.get('diferenca_pct', 'N/A')}%

Verificar se preço está realmente acima da média."""
        
        return self.send(to_number, mensagem)
    
    def relatorio_semanal(self, to_number: str, dados: dict) -> bool:
        """Envia relatório semanal consolidado"""
        mensagem = f"""📊 *RELATÓRIO SEMANAL*

📅 Período: {dados.get('periodo', 'N/A')}

📋 RESUMO:
• Abastecimentos: {dados.get('total_abastec', '0')}
• Gasto combustível: R$ {dados.get('gasto_combustivel', '0')}
• Gasto total: R$ {dados.get('gasto_total', '0')}
• Consumo médio: {dados.get('consumo_medio', 'N/A')} km/l

🚗 TOP 3 VEÍCULOS:
1. {dados.get('top1', 'N/A')}
2. {dados.get('top2', 'N/A')}
3. {dados.get('top3', 'N/A')}

⚠️ ALERTAS: {dados.get('total_alertas', '0')}

Acesse o sistema para mais detalhes!"""
        
        return self.send(to_number, mensagem)
    
    def confirmacao_login(self, to_number: str, usuario: str) -> bool:
        """Confirmação de login"""
        mensagem = f"""🔐 *LOGIN CONFIRMADO*

Usuário: {usuario}
Hora: {datetime.now().strftime('%H:%M:%S')}
Data: {datetime.now().strftime('%d/%m/%Y')}

Se não foi você, altere a senha imediatamente!"""
        
        return self.send(to_number, mensagem)


# Instância global para usar em qualquer lugar
notifier = WhatsAppNotifier()
