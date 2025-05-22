from datetime import datetime
import os
from dotenv import load_dotenv

def log_action(action, level,path, status):
    load_dotenv(override=True)  # Load environment variables
    user = os.getenv("USER", "default_user")
    with open("audit.log", "a") as f:
        f.write(f"{datetime.now()} | {user} - {level} | {action} | {path} | {status}\n")
