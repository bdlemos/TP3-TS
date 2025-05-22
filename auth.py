# auth.py
import os
from dotenv import load_dotenv

load_dotenv(override=True)

user_clearance_data = {
    "bernardo": {"level": "SECRET", "trusted": False},
    "admin": {"level": "TOP_SECRET", "trusted": True},
    "joao": {"level": "CONFIDENTIAL", "trusted": False},
    "default_user": {"level": "UNCLASSIFIED", "trusted": False} # Adicionado um usuário padrão para fallback
}

def get_user_credentials():
    user_name = os.getenv("USER", "default_user") # Faz fallback para default_user se USER não estiver definido
    # print(f"[DEBUG] Usuário autenticado: {user_name}")
    
    credentials = user_clearance_data.get(user_name)
    
    if credentials:
        return credentials.get("level", "UNCLASSIFIED"), credentials.get("trusted", False)
    else:
        # Se o usuário não estiver em user_clearance_data, retorna UNCLASSIFIED e não trusted
        # Isso pode acontecer se 'default_user' não estiver em user_clearance_data, embora tenhamos adicionado.
        print(f"[DEBUG] Usuário '{user_name}' não encontrado no dicionário de credenciais, usando UNCLASSIFIED/False.")
        return "UNCLASSIFIED", False