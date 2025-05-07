import os
import getpass
import shutil

MOUNTPOINT = "/tmp/montagem"

# cliente.py
def login():
    user = input("Usuário: ")
    with open(".env", "w") as f:
        f.write(f"USER={user}\n")
    print(f"Usuário '{user}' logado.")


def list_files():
    print("Arquivos visíveis:")
    for root, dirs, files in os.walk(MOUNTPOINT):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, MOUNTPOINT)
            print(f" - {rel_path}")

def read_file():
    path = input("Arquivo para ler (relativo): ")
    full_path = os.path.join(MOUNTPOINT, path)
    try:
        with open(full_path, "r") as f:
            print(f.read())
    except Exception as e:
        print(f"[ERRO] {e}")

def write_file():
    path = input("Nome do novo arquivo (relativo): ")
    content = input("Conteúdo: ")
    full_path = os.path.join(MOUNTPOINT, path)
    try:
        with open(full_path, "w") as f:
            f.write(content)
        print("Arquivo criado.")
    except Exception as e:
        print(f"[ERRO] {e}")

def delete_file():
    path = input("Arquivo para excluir: ")
    full_path = os.path.join(MOUNTPOINT, path)
    try:
        os.remove(full_path)
        print("Arquivo excluído.")
    except Exception as e:
        print(f"[ERRO] {e}")

def main():
    login()
    while True:
        cmd = input("\nComando [ls | cat | new | rm | exit]: ").strip()
        if cmd == "ls":
            list_files()
        elif cmd == "cat":
            read_file()
        elif cmd == "new":
            write_file()
        elif cmd == "rm":
            delete_file()
        elif cmd == "exit":
            print("Saindo.")
            break
        else:
            print("Comando inválido.")

if __name__ == "__main__":
    main()
