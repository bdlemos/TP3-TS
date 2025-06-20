import os
import json
from dotenv import load_dotenv
from logger import log_action

MOUNTPOINT = "/tmp/montagem" # Ponto de montagem para o sistema de ficheiros FUSE

# Variável global para o diretório de trabalho atual relativo ao MOUNTPOINT
current_relative_path = "" # Inicia na raiz do MOUNTPOINT

def get_full_path_in_os(path_relative_to_mountpoint):
    """Converte um caminho relativo ao MOUNTPOINT para um caminho absoluto no OS."""
    return os.path.join(MOUNTPOINT, path_relative_to_mountpoint)

def get_current_os_path():
    """Retorna o caminho absoluto no OS do diretório atual do cliente."""
    return get_full_path_in_os(current_relative_path)

def get_prompt():
    """Gera o prompt a ser exibido ao usuário, mostrando o diretório atual."""
    load_dotenv(override=True) # Carrega as variáveis de ambiente do .env
    display_path = "/" + current_relative_path if current_relative_path else "/"
    user = os.getenv("USER", "unknown")
    return f"{user}@{MOUNTPOINT}{display_path}$ "


def resolve_path(user_input_path):
    """
    Resolve o caminho fornecido pelo usuário.
    Se começar com '/', é absoluto a partir do MOUNTPOINT.
    Caso contrário, é relativo ao current_relative_path.
    Retorna o caminho normalizado relativo ao MOUNTPOINT.
    """
    global current_relative_path
    if user_input_path.startswith('/'):
        # Caminho absoluto a partir da raiz do MOUNTPOINT
        base = "" # Relativo ao MOUNTPOINT
        path_to_join = user_input_path[1:] # Remove a barra inicial
    else:
        # Caminho relativo ao diretório atual
        base = current_relative_path
        path_to_join = user_input_path

    combined_path = os.path.join(base, path_to_join)
    
    # Normaliza o caminho (resolve '..' e '.')
    normalized_path = os.path.normpath(combined_path)

    # Garante que o caminho não saia da raiz do MOUNTPOINT (ex: "cd ../../../../../tmp")
    if normalized_path == ".." and not current_relative_path: # Tentando sair da raiz
        return "" # Volta para a raiz
    if normalized_path.startswith(".."):
        print("[AVISO] Tentativa de aceder fora da raiz do ponto de montagem foi bloqueada.")
        return current_relative_path

    if normalized_path == ".":
        normalized_path = ""
        
    return normalized_path


# client.py
def login():
    """
    Solicita o nome de usuário e guarda-o no ficheiro .env para ser usado pelo auth.py.
    """
    global current_relative_path # Resetar o CWD no login
    current_relative_path = ""

    user = input("Usuário: ")
    try:
        with open(".env", "w") as f:
            f.write(f"USER={user}\n")
        print(f"Usuário '{user}' logado. As operações seguintes serão realizadas como este usuário.")
        print(f"Diretório atual: {get_prompt().split('@')[1].split('$')[0]}")
    except IOError as e:
        print(f"[ERRO] Não foi possível guardar as credenciais do usuário: {e}")

def list_files_current_dir():
    """
    Lista ficheiros e diretórios no diretório atual do cliente (current_relative_path).
    Não é recursivo.
    """
    global current_relative_path
    
    target_os_path = get_current_os_path()
    
    print(f"\nListando conteúdo de '{MOUNTPOINT}/{current_relative_path if current_relative_path else ''}':")
    
    try:

        entries = os.listdir(target_os_path)
        if not entries:
            print("  (Diretório vazio ou sem permissão para listar conteúdo)")
            return
            
        for entry_name in sorted(entries, key=lambda s: s.lower()):
            entry_os_path = os.path.join(target_os_path, entry_name)
            if os.path.isdir(entry_os_path):
                print(f"  [DIR]  {entry_name}/")
            elif os.path.isfile(entry_os_path):
                print(f"  [FILE] {entry_name}")
            else:
                print(f"  [OTHER] {entry_name}")
                
    except PermissionError:
        print(f"  [ERRO] Permissão negada para aceder ao diretório: {current_relative_path if current_relative_path else '/'}")
    except FileNotFoundError:
         print(f"  [ERRO] Diretório atual não encontrado no sistema de ficheiros: {current_relative_path if current_relative_path else '/'}")
    except Exception as e:
        print(f"  [ERRO] Não foi possível listar os ficheiros: {e}")


def change_directory(path_str):
    """
    Muda o diretório de trabalho atual do cliente.
    """
    global current_relative_path
    
    prospective_relative_path = resolve_path(path_str)
    prospective_os_path = get_full_path_in_os(prospective_relative_path)

    if not os.path.exists(prospective_os_path):
        print(f"[ERRO] Caminho não encontrado: {path_str} (resolvido para {prospective_os_path})")
        return
    if not os.path.isdir(prospective_os_path):
        print(f"[ERRO] Não é um diretório: {path_str} (resolvido para {prospective_os_path})")
        return
    if not os.access(prospective_os_path, os.R_OK | os.X_OK): # Precisa de permissão de leitura e execução
        print(f"[ERRO] Permissão negada para aceder ao diretório: {path_str} (resolvido para {prospective_os_path})")
        return

    current_relative_path = prospective_relative_path
    # print(f"Diretório atual alterado para: {MOUNTPOINT}/{current_relative_path if current_relative_path else ''}")


def read_file(path_input):
    """
    Solicita o caminho de um ficheiro e tenta ler e exibir o seu conteúdo.
    O caminho é resolvido a partir do diretório atual.
    """
    resolved_relative_path = resolve_path(path_input)
    full_os_path = get_full_path_in_os(resolved_relative_path)
    
    print(f"A tentar ler: {full_os_path}")
    try:
        with open(full_os_path, "r") as f:
            content = f.read()
            if content:
                print("\nConteúdo do ficheiro:")
                print("--------------------")
                print(content)
                print("--------------------")
            else:
                print("(Ficheiro vazio)")
    except FileNotFoundError:
        print(f"[ERRO] Ficheiro não encontrado: {path_input} (resolvido para {full_os_path})")
    except PermissionError:
        print(f"[ERRO] Permissão negada para ler o ficheiro: {path_input} (resolvido para {full_os_path})")
    except IsADirectoryError:
        print(f"[ERRO] O caminho especificado é um diretório, não um ficheiro: {path_input}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao ler o ficheiro: {e}")


def write_file_or_append(mode, path_input):
    """
    Função genérica para escrever ('w') ou anexar ('a') a um ficheiro.
    """
    action = "escrever em" if mode == "w" else "anexar a"
    action_gerund = "escrita" if mode == "w" else "anexação"
    action_past = "escrito" if mode == "w" else "anexado"

    # path_input = input(f"Caminho do ficheiro para {action}: ")
    resolved_relative_path = resolve_path(path_input)
    full_os_path = get_full_path_in_os(resolved_relative_path)

    # Verifica se o diretório pai existe e se temos permissão de escrita nele,
    # especialmente se o ficheiro não existir ainda (para 'w' e 'a').
    parent_dir_os_path = os.path.dirname(full_os_path)
    if not os.path.exists(parent_dir_os_path):
        print(f"[ERRO] Diretório pai não existe: {parent_dir_os_path}")
        return
    
    # Se o ficheiro já existe e é um diretório, não podemos escrever/anexar.
    if os.path.isdir(full_os_path):
        print(f"[ERRO] O caminho especificado é um diretório, não é possível {action}: {path_input}")
        return

    content = input(f"Conteúdo para {action_gerund}: ")
    print(f"A tentar {action}: {full_os_path}")
    
    try:
        with open(full_os_path, mode) as f:
            f.write(content)
            if mode == "a" and content: # Adiciona uma nova linha após anexar, se algo foi anexado
                 f.write("\n")
        print(f"Conteúdo {action_past} ao ficheiro '{resolved_relative_path}' com sucesso.")
    except PermissionError:
        print(f"[ERRO] Permissão negada para {action} o ficheiro: {path_input} (em {full_os_path})")
    except IsADirectoryError: 
        print(f"[ERRO] O caminho especificado é um diretório: {path_input}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro durante a {action_gerund} do ficheiro: {e}")


def delete_file():
    """
    Solicita o caminho de um ficheiro e tenta excluí-lo.
    O caminho é resolvido a partir do diretório atual.
    """
    path_input = input("Caminho do ficheiro para excluir: ")
    resolved_relative_path = resolve_path(path_input)
    full_os_path = get_full_path_in_os(resolved_relative_path)

    print(f"A tentar excluir: {full_os_path}")
    try:
        if not os.path.exists(full_os_path):
            print(f"[ERRO] Ficheiro não encontrado: {path_input} (em {full_os_path})")
            return
        if os.path.isdir(full_os_path): # Não permitir 'rm' em diretórios
            print(f"[ERRO] O caminho especificado é um diretório. Use 'rmdir' (não implementado) para diretórios: {path_input}")
            return

        os.remove(full_os_path)
        print(f"Ficheiro '{resolved_relative_path}' excluído com sucesso.")
    except FileNotFoundError: # Deve ser apanhado pelo os.path.exists, mas por segurança
        print(f"[ERRO] Ficheiro não encontrado: {path_input} (em {full_os_path})")
    except PermissionError:
        print(f"[ERRO] Permissão negada para excluir o ficheiro: {path_input} (em {full_os_path})")
    except IsADirectoryError: # Deve ser apanhado antes
         print(f"[ERRO] O caminho especificado é um diretório, não um ficheiro: {path_input}")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao excluir o ficheiro: {e}")


def set_trust(user, value):
    """
    Altera o estado 'trusted' de um utilizador no ficheiro users.json.
    """
    user_data_path = "data/users.json"
    try:
        with open(user_data_path, "r") as f:
            data = json.load(f)
        if user not in data:
            print(f"[ERRO] Utilizador '{user}' não encontrado.")
            return
        
        actually_user = os.getenv("USER", "unknown")
        user_level = data.get(actually_user, {}).get("level", "")
        if actually_user not in data:
            print(f"[ERRO] Utilizador atual '{actually_user}' não encontrado no ficheiro de utilizadores.")
            return
        
        if data[actually_user].get("level", "") != "TOP_SECRET" or not data[actually_user].get("trusted", False):
            print("[ERRO] Apenas utilizadores TOP_SECRET e de confiança podem alterar o estado de confiança.")
            log_action("set_trust", user_level, " ", f"User {actually_user} not authorized to change trust status of {user}")
            return

        if value.lower() not in ["true", "false"]:
            print(f"[ERRO] Valor inválido para trusted: '{value}'. Usa 'true' ou 'false'.")
            return

        data[user]["trusted"] = value.lower() == "true"

        with open(user_data_path, "w") as f:
            json.dump(data, f, indent=4)
        
        log_action("set_trust", user_level, " ", f"Trust status of {user} updated to {data[user]['trusted']}")
        print(f"[INFO] Estado de confiança de '{user}' atualizado para {data[user]['trusted']}.")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao atualizar o estado de confiança: {e}")


def set_clearance(user, value):
    """
    Altera 'nivel' de um utilizador no ficheiro users.json.
    """
    user_data_path = "data/users.json"
    try:
        with open(user_data_path, "r") as f:
            data = json.load(f)
        if user not in data:
            print(f"[ERRO] Utilizador '{user}' não encontrado.")
            return
        
        actually_user = os.getenv("USER", "unknown")
        user_level = data.get(actually_user, {}).get("level", "")
        if actually_user not in data:
            print(f"[ERRO] Utilizador atual '{actually_user}' não encontrado no ficheiro de utilizadores.")
            return
        
        if data[actually_user].get("level", "") != "TOP_SECRET" or not data[actually_user].get("trusted", False):
            log_action("set_clearance", user_level, " ", f"User {actually_user} not authorized to change clearance of {user}")
            print("[ERRO] Apenas utilizadores TOP_SECRET e de confiança podem alterar o estado de confiança.")
            return

        niveis_validos = ["UNCLASSIFIED", "CONFIDENTIAL", "SECRET", "TOP_SECRET"]
        if value.upper() not in niveis_validos:
            print(f"[ERRO] Nível de acesso inválido: '{value}'. Usa um dos seguintes: {', '.join(niveis_validos)}.")
            return

        data[user]["level"] = value.upper()

        with open(user_data_path, "w") as f:
            json.dump(data, f, indent=4)
        
        log_action("set_clearance", user_level, " ", f"Clearance level of {user} updated to {data[user]['level']}")
        print(f"[INFO] Nível de acesso de '{user}' atualizado para {data[user]['level']}.")
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro ao atualizar o nível de acesso: {e}")


def main():
    """
    Função principal do cliente: faz login e entra num loop de comandos.
    """
    global current_relative_path
    login()

    if not os.path.exists(MOUNTPOINT) or not os.path.isdir(MOUNTPOINT):
        print(f"[AVISO CRÍTICO] O ponto de montagem '{MOUNTPOINT}' não existe ou não é um diretório.")
        print("Por favor, certifique-se de que o sistema de ficheiros FUSE está montado corretamente ANTES de executar o cliente.")
        return

    while True:
        try:
            prompt = get_prompt()
            cmd_line = input(prompt).strip()
            if not cmd_line:
                continue
            
            parts = cmd_line.split()
            command = parts[0].lower()
            args = parts[1:]

            if command == "ls":
                list_files_current_dir()
            elif command == "cd":
                if not args:
                    print("Uso: cd <diretório>")
                else:
                    change_directory(args[0])
            elif command == "cat":
                if not args:
                    print("Uso: cat <ficheiro>")
                else:
                    read_file(args[0]) 
            elif command == "new":
                if not args:
                    print("Uso: new <ficheiro>")
                else:
                    write_file_or_append(mode="w", path_input=args[0]) 
            elif command == "add":
                if not args:
                    print("Uso: add <ficheiro>")
                else:
                    write_file_or_append(mode="a", path_input=args[0])
            elif command == "rm":
                delete_file()
            elif command == "login":
                login() 
            elif command == "pwd":
                print(f"{MOUNTPOINT}/{current_relative_path if current_relative_path else ''}")
            elif command == "settrust":
                if len(args) != 2:
                    print("Uso: settrust <utilizador> <true|false>")
                else:
                    set_trust(args[0], args[1])
            elif command == "setclearance":
                if len(args) != 2:
                    print("Uso: setclearence <utilizador> <PUBLIC|CONFIDENTIAL|SECRET|TOP_SECRET>")
                else:
                    set_clearance(args[0], args[1])
            elif command == "exit":
                print("A sair do cliente.")
                break
            else:
                print(f"Comando inválido: {command}")
        except KeyboardInterrupt:
            print("\nComando interrompido. A sair do cliente.")
            break
        except EOFError: # Ctrl+D
            print("\nEOF recebido. A sair do cliente.")
            break


if __name__ == "__main__":
    main()