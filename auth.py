# auth.py
import os
from dotenv import load_dotenv

load_dotenv(override=True)

user_clearance = {
    "bernardo": "SECRET",
    "admin": "TOP_SECRET",
    "joao": "CONFIDENTIAL"
}

def get_user_clearance():
    user = os.getenv("USER", "default")
    print(f"[DEBUG] Usuário autenticado: {user}")
    return user_clearance.get(user, "UNCLASSIFIED")
