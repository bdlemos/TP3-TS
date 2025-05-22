from datetime import datetime

def log_action(action, user, path, status):
    with open("audit.log", "a") as f:
        f.write(f"{datetime.now()} | {user} | {action} | {path} | {status}\n")
