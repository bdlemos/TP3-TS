# auth.py
import os
import json
from dotenv import load_dotenv # load_dotenv é chamado dentro da função get_user_credentials

USERS_FILE = "data/users.json"

def get_user_credentials():
    # Mova load_dotenv para aqui para garantir que é chamado a cada vez
    # que as credenciais são pedidas, apanhando alterações no .env
    load_dotenv(override=True) 
    
    user_name = os.getenv("USER", "default_user") 
    # print(f"[DEBUG] auth.py - Usuário autenticado: {user_name}") 
    
    #read users from a json file
    if not os.path.exists(USERS_FILE):
        return "UNCLASSIFIED", False
    
    with open(USERS_FILE, "r") as f:
        user_clearance_data = json.load(f)
    credentials = user_clearance_data.get(user_name)
    
    if credentials:
        level = credentials.get("level", "UNCLASSIFIED")
        trusted = credentials.get("trusted", False)
        # print(f"[DEBUG] auth.py - Credenciais para '{user_name}': Nível={level}, Trusted={trusted}")
        return level, trusted
    else:
        # print(f"[DEBUG] auth.py - Usuário '{user_name}' não encontrado, usando UNCLASSIFIED/False.")
        return "UNCLASSIFIED", False


def get_current_user():
    load_dotenv(override=True)
    return os.getenv("USER", "default_user")

