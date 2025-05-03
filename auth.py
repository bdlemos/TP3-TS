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
    # stub para testes; depois integrar com autenticação real
    print(os.getenv("USER"))
    return user_clearance.get(os.getenv("USER"), "UNCLASSIFIED")
