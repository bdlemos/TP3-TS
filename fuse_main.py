import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations
from auth import get_user_credentials
from logger import log_action

SECURITY_LEVELS = ["UNCLASSIFIED", "CONFIDENTIAL", "SECRET", "TOP_SECRET"]

class SecurePassthrough(Operations):
    def __init__(self, root):
        self.root = root
        # As credenciais do usuário são obtidas por operação para refletir mudanças no .env

    def _get_current_user_credentials(self):
        # Helper para buscar as credenciais atuais
        user_level, is_trusted = get_user_credentials()
        return user_level, is_trusted

    def _full_path(self, partial):
        # Converte um caminho parcial (relativo ao mountpoint) para um caminho completo no sistema de ficheiros subjacente.
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def get_file_level(self, path):
        """
        Determina o nível de segurança de um ficheiro/diretório com base no seu caminho.
        Assume que o nível de segurança está presente no nome do caminho
        (ex: '/mnt/secret_files/top_secret/doc.txt' -> TOP_SECRET).
        Se nenhum nível for encontrado no caminho, assume UNCLASSIFIED.
        O 'path' aqui pode ser o full_path ou o path relativo ao mountpoint.
        Para consistência, é melhor usar o full_path do sistema de ficheiros real.
        """
        # Normaliza o caminho para evitar problemas com barras extras ou relativas
        normalized_path = os.path.normpath(path).lower()
        
        # Itera dos níveis mais altos para os mais baixos para evitar correspondências parciais incorretas
        # (ex: /top_secret/secretaria -> deve ser top_secret, não secret)
        for level in reversed(SECURITY_LEVELS): 
            if f"/{level.lower()}/" in normalized_path or \
               normalized_path.endswith(f"/{level.lower()}") or \
               (f"/{level.lower()}_" in normalized_path) : # Adiciona variações como /secret_folder/
                # print(f"[DEBUG][get_file_level] Path: {path} -> Nível Encontrado: {level}")
                return level
        # print(f"[DEBUG][get_file_level] Path: {path} -> Nível Padrão: UNCLASSIFIED")
        return "UNCLASSIFIED"

    # --- Métodos do Sistema de Ficheiros ---

    def access(self, path, mode):
        # Verifica se o usuário pode aceder a um ficheiro/diretório com um determinado modo.
        user_level, _ = self._get_current_user_credentials() # is_trusted não é diretamente usado aqui

        full_path = self._full_path(path)
        
        # Para verificar o acesso ao ficheiro real, precisamos do nível do ficheiro
        file_level = self.get_file_level(full_path)
        
        # Política BLP: "No Read Up" - não pode ler/aceder a níveis superiores
        if SECURITY_LEVELS.index(user_level) < SECURITY_LEVELS.index(file_level):
            log_action("access", f"{user_level} (user)", full_path, f"DENIED (File Level: {file_level} - Higher)")
            raise FuseOSError(errno.EACCES)
        
        
        log_action("access", f"{user_level} (user)", full_path, "GRANTED")
        return 0 # Sucesso

    def getattr(self, path, fh=None):
        user_level, _ = self._get_current_user_credentials()
        full_path = self._full_path(path)

        # Política: Usuário pode obter atributos de ficheiros/diretórios de qualquer nivel, mas nao consegue aceder o conteudo

        try:
            st = os.lstat(full_path)
        except FileNotFoundError:
            # log_action("getattr", f"{user_level} (user)", full_path, "DENIED (File Not Found)")
            raise FuseOSError(errno.ENOENT)
            
        # log_action("getattr", f"{user_level} (user)", full_path, "GRANTED")
        
        return dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime',
            'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        # Lista o conteúdo de um diretório.
        user_level, _ = self._get_current_user_credentials()
        full_path = self._full_path(path)
    

        # Usuário pode listar diretórios diretorios com qualquer nivel, para caso queira escrever para cima

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            try:
                entries = os.listdir(full_path)
                for name in entries:
                    entry_full_path = os.path.join(full_path, name)
                    entry_level = self.get_file_level(entry_full_path)
                    # Adiciona à listagem sempre, mas se o nível do usuário for inferior ao nível do diretório, adiciona um log
                    if SECURITY_LEVELS.index(user_level) >= SECURITY_LEVELS.index(entry_level):
                        dirents.append(name)
                    else:
                        log_action("readdir_entry_filter", f"{user_level} (user)", entry_full_path, f"GRANTED (Entry Level: {entry_level} - Higher)")
                        dirents.append(f"{name}")
                log_action("readdir", f"{user_level} (user)", full_path, "GRANTED")
            except OSError as e:
                log_action("readdir", f"{user_level} (user)", full_path, f"ERROR_OS (Listing failed: {e.strerror})")
                raise FuseOSError(e.errno)
        else:
            log_action("readdir", f"{user_level} (user)", full_path, "FAILED (Not a directory)")
            raise FuseOSError(errno.ENOTDIR)

        for r in dirents:
            yield r

    def open(self, path, flags):
        # Abre um ficheiro.
        user_level, is_trusted = self._get_current_user_credentials()
        full_path = self._full_path(path)
        file_level = self.get_file_level(full_path) # Nível do ficheiro a ser aberto

        # Determinar a intenção: leitura, escrita/anexação
        is_reading = (flags & os.O_ACCMODE == os.O_RDONLY) or \
                     (flags & os.O_ACCMODE == os.O_RDWR)
        is_writing = (flags & os.O_ACCMODE == os.O_WRONLY) or \
                     (flags & os.O_ACCMODE == os.O_RDWR)
        is_appending = bool(flags & os.O_APPEND) # Verifica se a flag O_APPEND está presente

        # Política de Leitura: "No Read Up"
        if is_reading and SECURITY_LEVELS.index(user_level) < SECURITY_LEVELS.index(file_level):
            log_action("open (read intent)", f"{user_level} (user)", full_path, f"DENIED (No Read Up - File Level: {file_level})")
            raise FuseOSError(errno.EACCES)

        # Política de Escrita/Anexação
        if is_writing or is_appending: # O_APPEND implica escrita
            is_write_down_attempt = SECURITY_LEVELS.index(user_level) > SECURITY_LEVELS.index(file_level)
            
            if is_write_down_attempt: # Tentativa de escrever/anexar para um nível inferior
                if not is_trusted:
                    log_action("open (write/append intent)", f"{user_level} (user)", full_path, f"DENIED (No Write/Append Down - Not Trusted - File Level: {file_level})")
                    raise FuseOSError(errno.EACCES)
                else:
                    # Usuário "trusted" pode fazer "write down" ou "append down"
                    log_action("open (write/append intent)", f"{user_level} (Trusted User)", full_path, f"GRANTED (Trusted Write/Append Down - File Level: {file_level})")
            else: # Tentativa de escrever/anexar no mesmo nível ou para um nível superior ("write up")
                  # "Write up" é permitido por BLP para confidencialidade.
                log_action("open (write/append intent)", f"{user_level} (user)", full_path, f"GRANTED (Same Level or Write/Append Up - File Level: {file_level})")
        
        # Se chegou aqui, as permissões de nível de segurança foram satisfeitas.
        # Agora, tenta abrir o ficheiro no sistema de ficheiros subjacente.
        try:
            fd = os.open(full_path, flags)
            return fd # Retorna o file descriptor
        except FileNotFoundError:
            # Se O_CREAT não estiver nas flags e o ficheiro não existir.
            # Se O_CREAT estiver, este erro não deve acontecer aqui, mas sim em create().
            log_action("open", f"{user_level} (user)", full_path, "DENIED (OS Open Failed - File Not Found)")
            raise FuseOSError(errno.ENOENT)
        except OSError as e:
            log_action("open", f"{user_level} (user)", full_path, f"DENIED (OS Open Failed - {e.strerror})")
            raise FuseOSError(e.errno)


    def read(self, path, length, offset, fh):
        # Lê dados de um ficheiro aberto. 'fh' é o file descriptor retornado por open().
        # As verificações de permissão de nível já foram feitas em open().
        user_level, _ = self._get_current_user_credentials() # Para logging
        
        try:
            os.lseek(fh, offset, os.SEEK_SET)
            data = os.read(fh, length)
            log_action("read", f"{user_level} (user) fh:{fh}", f"path hint:{path}", f"GRANTED (Read {len(data)} bytes)")
            return data
        except OSError as e:
            log_action("read", f"{user_level} (user) fh:{fh}", f"path hint:{path}", f"ERROR_OS ({e.strerror})")
            raise FuseOSError(e.errno)

    def write(self, path, buf, offset, fh):
        # Escreve dados num ficheiro aberto. 'fh' é o file descriptor.
        # As verificações de permissão de nível já foram feitas em open().
        user_level, _ = self._get_current_user_credentials() # Para logging

        try:
            os.lseek(fh, offset, os.SEEK_SET) # O kernel lida com O_APPEND aqui.
            bytes_written = os.write(fh, buf)
            log_action("write", f"{user_level} (user) fh:{fh}", f"path hint:{path}", f"GRANTED (Wrote {bytes_written} bytes)")
            return bytes_written
        except OSError as e:
            log_action("write", f"{user_level} (user) fh:{fh}", f"path hint:{path}", f"ERROR_OS ({e.strerror})")
            raise FuseOSError(e.errno)

    def create(self, path, mode, fi=None):
        # Cria um novo ficheiro.
        user_level, is_trusted = self._get_current_user_credentials()
        full_path = self._full_path(path)
        
        # O nível do ficheiro é determinado pelo diretório onde a criação é tentada.
        # Para isso, obtemos o nível do diretório pai.
        parent_dir_path = os.path.dirname(full_path)
        file_intended_level = self.get_file_level(full_path) # Nível inferido do caminho completo do novo ficheiro

        is_create_down_attempt = SECURITY_LEVELS.index(user_level) > SECURITY_LEVELS.index(file_intended_level)

        if is_create_down_attempt: # Tentativa de criar num nível inferior
            if not is_trusted:
                log_action("create", f"{user_level} (user)", full_path, f"DENIED (No Create Down - Not Trusted - Intended Level: {file_intended_level})")
                raise FuseOSError(errno.EACCES)
            else:
                log_action("create", f"{user_level} (Trusted User)", full_path, f"GRANTED (Trusted Create Down - Intended Level: {file_intended_level})")
        else: # Tentativa de criar no mesmo nível ou num nível superior ("create up")
            log_action("create", f"{user_level} (user)", full_path, f"GRANTED (Same Level or Create Up - Intended Level: {file_intended_level})")
            
        # Se as permissões de nível estiverem OK, tenta criar o ficheiro.
        try:
            # O_TRUNC é importante para que 'create' se comporte como esperado (ficheiro novo/vazio)
            fd = os.open(full_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
            return fd # Retorna o file descriptor
        except OSError as e:
            log_action("create", f"{user_level} (user)", full_path, f"ERROR_OS ({e.strerror})")
            raise FuseOSError(e.errno)

    def unlink(self, path):
        # Exclui um ficheiro.
        user_level, _ = self._get_current_user_credentials() # is_trusted não é diretamente relevante para a política de unlink aqui
        full_path = self._full_path(path)
        file_level = self.get_file_level(full_path)
        
        # Política: "No Delete Up" - Um usuário não pode excluir ficheiros com nível superior ao seu.
        if SECURITY_LEVELS.index(user_level) < SECURITY_LEVELS.index(file_level):
            log_action("unlink", f"{user_level} (user)", full_path, f"DENIED (No Delete Up - File Level: {file_level})")
            raise FuseOSError(errno.EACCES)
    
        # Para este projeto, focar no BLP: se user_level >= file_level, a exclusão é permitida para confidencialidade.
        
        try:
            result = os.unlink(full_path)
            log_action("unlink", f"{user_level} (user)", full_path, "SUCCESS (OS Unlink Succeeded)")
            return result # Geralmente 0 em sucesso
        except FileNotFoundError:
            log_action("unlink", f"{user_level} (user)", full_path, "ERROR_OS (File Not Found)")
            raise FuseOSError(errno.ENOENT)
        except OSError as e:
            log_action("unlink", f"{user_level} (user)", full_path, f"ERROR_OS ({e.strerror})")
            raise FuseOSError(e.errno)


def main(mountpoint, root):
    print(f"[INFO] A montar o diretório '{root}' em '{mountpoint}'")
    print(f"[INFO] Níveis de Segurança Definidos no FUSE: {SECURITY_LEVELS}")
    
    # Uma chamada inicial para get_user_credentials para verificar o estado ao iniciar o FUSE.
    # O usuário real para as operações FUSE será determinado pelo .env no momento da operação.
    initial_user_env = os.getenv('USER', 'NÃO DEFINIDO')
    if initial_user_env != 'NÃO DEFINIDO':
        initial_level, initial_trusted = get_user_credentials() # Usa o .env se existir
        print(f"[INFO] Usuário no ambiente no arranque do FUSE ('USER={initial_user_env}'): Nível '{initial_level}', Trusted: {initial_trusted}")
    else:
        print("[INFO] Variável de ambiente USER não definida no arranque do FUSE. O login via cliente definirá o usuário para as operações.")

    FUSE(SecurePassthrough(root), mountpoint, nothreads=True, foreground=True)
    print("[INFO] Sistema de ficheiros FUSE desmontado.")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python fuse_main.py <diretório_de_origem_real> <ponto_de_montagem_fuse>")
        print("Exemplo: python fuse_main.py ./data/secure_files /tmp/montagem")
        exit(1)
    
    real_root_dir = sys.argv[1]
    mount_point_dir = sys.argv[2]

    if not os.path.exists(real_root_dir) or not os.path.isdir(real_root_dir):
        print(f"[ERRO] O diretório de origem '{real_root_dir}' não existe ou não é um diretório.")
        exit(1)
        
    if not os.path.exists(mount_point_dir) or not os.path.isdir(mount_point_dir):
        print(f"[AVISO] O ponto de montagem '{mount_point_dir}' não existe ou não é um diretório.")
        print(f"Por favor, crie o diretório: mkdir -p {mount_point_dir}")

    main(mount_point_dir, real_root_dir)
