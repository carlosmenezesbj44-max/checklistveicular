"""
Gerenciador de Configurações do Sistema
Responsável por carregar e salvar configurações como credenciais do Twilio
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv, set_key, get_key

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Diretório de configurações
CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_DIR.mkdir(exist_ok=True)

# Caminho do arquivo .env
ENV_FILE = Path(__file__).parent / ".env"


class ConfigManager:
    """Gerencia configurações do sistema"""

    @staticmethod
    def get_twilio_config():
        """Retorna as configurações do Twilio"""
        return {
            "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID", ""),
            "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN", ""),
            "TWILIO_WHATSAPP_FROM": os.getenv("TWILIO_WHATSAPP_FROM", ""),
            "ADMIN_WHATSAPP": os.getenv("ADMIN_WHATSAPP", ""),
        }

    @staticmethod
    def update_twilio_config(config_data):
        """
        Atualiza as configurações do Twilio no arquivo .env
        
        Args:
            config_data (dict): Dicionário com as configurações a atualizar
            
        Returns:
            bool: True se atualizado com sucesso, False caso contrário
        """
        try:
            # Garante que o arquivo .env existe
            if not ENV_FILE.exists():
                ENV_FILE.touch()

            # Atualiza cada variável (sem aspas!)
            for key, value in config_data.items():
                # Remove aspas se existirem
                value = value.strip("'\"")
                set_key(str(ENV_FILE), key, value)

            # Recarrega as variáveis de ambiente - IMPORTANTE!
            # Limpa o cache primeiro para garantir que o arquivo seja relido
            for key in list(config_data.keys()):
                if key in os.environ:
                    del os.environ[key]
            
            # Recarrega do arquivo
            load_dotenv(str(ENV_FILE), override=True)
            
            # Verifica se foi salvo corretamente
            for key, expected_value in config_data.items():
                actual_value = os.getenv(key, "")
                if actual_value != expected_value:
                    print(f"Aviso: {key} pode não ter sido salvo corretamente")
                    print(f"  Esperado: {expected_value}")
                    print(f"  Obtido: {actual_value}")

            return True
        except Exception as e:
            print(f"Erro ao atualizar configurações: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    @staticmethod
    def get_email_config():
        """Retorna as configurações de email"""
        return {
            "MAIL_SERVER": os.getenv("MAIL_SERVER", ""),
            "MAIL_PORT": os.getenv("MAIL_PORT", ""),
            "MAIL_USERNAME": os.getenv("MAIL_USERNAME", ""),
            "MAIL_DEFAULT_SENDER": os.getenv("MAIL_DEFAULT_SENDER", ""),
        }

    @staticmethod
    def update_email_config(config_data):
        """
        Atualiza as configurações de email
        
        Args:
            config_data (dict): Dicionário com as configurações a atualizar
            
        Returns:
            bool: True se atualizado com sucesso, False caso contrário
        """
        try:
            if not ENV_FILE.exists():
                ENV_FILE.touch()

            for key, value in config_data.items():
                set_key(str(ENV_FILE), key, value)

            load_dotenv(str(ENV_FILE), override=True)

            return True
        except Exception as e:
            print(f"Erro ao atualizar configurações de email: {str(e)}")
            return False

    @staticmethod
    def verify_twilio_connection():
        """
        Verifica se as credenciais do Twilio são válidas
        
        Returns:
            dict: {'conectado': bool, 'conta': str, 'erro': str}
        """
        try:
            from twilio.rest import Client

            account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")

            if not account_sid or not auth_token:
                return {
                    "conectado": False,
                    "conta": None,
                    "erro": "Credenciais não configuradas",
                }

            # Tenta conectar ao Twilio
            client = Client(account_sid, auth_token)
            account = client.api.accounts(account_sid).fetch()

            return {
                "conectado": True,
                "conta": account.friendly_name,
                "erro": None,
            }
        except Exception as e:
            return {
                "conectado": False,
                "conta": None,
                "erro": str(e),
            }


# Função auxiliar global
def get_twilio_config():
    """Atalho para obter configurações do Twilio"""
    return ConfigManager.get_twilio_config()


def update_twilio_config(config_data):
    """Atalho para atualizar configurações do Twilio"""
    return ConfigManager.update_twilio_config(config_data)


def verify_twilio_connection():
    """Atalho para verificar conexão com Twilio"""
    return ConfigManager.verify_twilio_connection()
