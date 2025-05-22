# auth.py
import os
from dotenv import load_dotenv # load_dotenv é chamado dentro da função get_user_credentials

user_clearance_data = {
    "bernardo": {"level": "SECRET", "trusted": False},
    "admin": {"level": "TOP_SECRET", "trusted": True},
    "joao": {"level": "CONFIDENTIAL", "trusted": False},
    "default_user": {"level": "UNCLASSIFIED", "trusted": False} 
}

def get_user_credentials():
    # Mova load_dotenv para aqui para garantir que é chamado a cada vez
    # que as credenciais são pedidas, apanhando alterações no .env
    load_dotenv(override=True) 
    
    user_name = os.getenv("USER", "default_user") 
    # O print de debug já estava aqui, o que é bom.
    # print(f"[DEBUG] auth.py - Usuário autenticado: {user_name}") 
    
    credentials = user_clearance_data.get(user_name)
    
    if credentials:
        level = credentials.get("level", "UNCLASSIFIED")
        trusted = credentials.get("trusted", False)
        # print(f"[DEBUG] auth.py - Credenciais para '{user_name}': Nível={level}, Trusted={trusted}")
        return level, trusted
    else:
        # print(f"[DEBUG] auth.py - Usuário '{user_name}' não encontrado, usando UNCLASSIFIED/False.")
        return "UNCLASSIFIED", False