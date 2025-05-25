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


def set_trust_status(current_user, target_user, new_status):
    # Verificar se o utilizador atual tem permissão para alterar confiança
    if not os.path.exists(USERS_FILE):
        print("Ficheiro de utilizadores não encontrado.")
        return False

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    # Verifica permissões do utilizador atual
    if (current_user not in users or not users[current_user].get("trusted", False) or users[current_user].get("level", "") != "TOP_SECRET"):
        print("[ERRO] Apenas utilizadores TOP_SECRET e de confiança podem alterar níveis de confiança.")
        return False

    # Validação do novo valor
    if new_status.lower() not in ("true", "false"):
        print("[ERRO] Valor de confiança inválido. Use 'true' ou 'false'.")
        return False

    new_trust_value = new_status.lower() == "true"

    if target_user not in users:
        print(f"Utilizador '{target_user}' não encontrado.")
        return False

    users[target_user]["trusted"] = new_trust_value

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    print(f"O utilizador '{target_user}' é agora {'trusted' if new_trust_value else 'não trusted'}.")
    return True


def set_clearance_level(current_user, target_user, new_level):
    # Verificar se o ficheiro existe
    if not os.path.exists(USERS_FILE):
        print("Ficheiro de utilizadores não encontrado.")
        return False

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    # Verifica se o utilizador atual é válido, trusted e existe
    if (current_user not in users or not users[current_user].get("trusted", False)):
        print("[ERRO] Apenas utilizadores de confiança podem alterar o nível de clearance.")
        return False

    current_level = users[current_user].get("level", "UNCLASSIFIED")
    clearance_hierarchy = ["UNCLASSIFIED", "CONFIDENTIAL", "SECRET", "TOP_SECRET"]

    if new_level.upper() not in clearance_hierarchy:
        print("[ERRO] Nível de clearance inválido. Use: UNCLASSIFIED, CONFIDENTIAL, SECRET, TOP_SECRET.")
        return False

    if target_user not in users:
        print(f"Utilizador '{target_user}' não encontrado.")
        return False

    target_level = users[target_user].get("level", "UNCLASSIFIED")

    # Verifica se o current_user tem clearance superior ao alvo e superior ou igual ao novo nível
    if (clearance_hierarchy.index(current_level) <= clearance_hierarchy.index(target_level) or
        clearance_hierarchy.index(current_level) < clearance_hierarchy.index(new_level.upper()) == False):
        print("[ERRO] Só é possível alterar o nível de utilizadores com clearance inferior ao seu, e para níveis iguais ou inferiores ao seu.")
        return False

    users[target_user]["level"] = new_level.upper()

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    print(f"O utilizador '{target_user}' tem agora nível de clearance '{new_level.upper()}'.")
    return True
