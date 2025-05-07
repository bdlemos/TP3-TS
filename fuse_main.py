#!/usr/bin/env python3

import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations
from auth import get_user_clearance

SECURITY_LEVELS = ["UNCLASSIFIED", "CONFIDENTIAL", "SECRET", "TOP_SECRET"]

class SecurePassthrough(Operations):
    def __init__(self, root):
        self.root = root
        self.user_level = get_user_clearance()
        print(f"[INFO] Usuário com nível: {self.user_level}")

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        return os.path.join(self.root, partial)

    def get_file_level(self, path):
        # print(f"[INFO] Verificando nível de segurança do arquivo: {path}")
        for level in SECURITY_LEVELS:
            if f"/{level.lower()}" in path.lower():
                return level
        return "UNCLASSIFIED"

    # Filesystem methods

    def access(self, path, mode):
        # Um usuário não pode acessar arquivos com nível superior ao seu
        # Se o arquivo não existir, o acesso é negado
        self.user_level = get_user_clearance()

        full_path = self._full_path(path)
        file_level = self.get_file_level(full_path)
        if SECURITY_LEVELS.index(self.user_level) < SECURITY_LEVELS.index(file_level):
            print(f"[INFO][Access] Acesso negado ao arquivo: {full_path} com nível: {file_level}")
            raise FuseOSError(errno.EACCES)
        if not os.access(full_path, mode):
            raise FuseOSError(errno.EACCES)

    def getattr(self, path, fh=None):
        # Um usuário pode saber os atributos de qualquer arquivos/diretorios 
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        print(f"[INFO][Getattr] Atributos do diretório: {full_path}")
        
        return dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime',
            'st_nlink', 'st_size', 'st_uid'))

    def readdir(self, path, fh):
        # Um usuário não pode listar arquivos/diretorios com nível superior ao seu
        self.user_level = get_user_clearance()

        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            file_level = self.get_file_level(full_path)
            if SECURITY_LEVELS.index(self.user_level) >= SECURITY_LEVELS.index(file_level):
                for name in os.listdir(full_path):
                    dirents.append(name)
            else:
                print(f"[INFO][Readdir] Acesso negado ao diretorio: {full_path} com nível: {file_level}")
        for r in dirents:
            yield r

    def read(self, path, length, offset, fh):
        # Um usuario pode ler arquivos com nível igual ou inferior ao seu, mas nao pode acessar arquivos/diretorios com nível superior
        self.user_level = get_user_clearance()

        file_level = self.get_file_level(path)
        print(f"[INFO][Read] Lendo arquivo: {path} com nível: {file_level}")
        if SECURITY_LEVELS.index(self.user_level) < SECURITY_LEVELS.index(file_level):
            raise FuseOSError(errno.EACCES)  # No read up
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        # Um usuario pode escrever em arquivos com nível igual ou superior ao seu, mas nao pode escrever arquivos/diretorios com nível superior
        self.user_level = get_user_clearance()

        file_level = self.get_file_level(path)
        if SECURITY_LEVELS.index(self.user_level) > SECURITY_LEVELS.index(file_level):
            print(f"[INFO][Write] Acesso negado ao arquivo: {path} com nível: {file_level}")
            raise FuseOSError(errno.EACCES)  # No write down
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def open(self, path, flags):
        # Um usuario pode abrir arquivos com nível igual ou inferior ao seu, mas nao pode acabriressar arquivos/diretorios com nível superior
        self.user_level = get_user_clearance()

        full_path = self._full_path(path)
        file_level = self.get_file_level(full_path)
        if SECURITY_LEVELS.index(self.user_level) < SECURITY_LEVELS.index(file_level):
            print(f"[INFO][Open] Acesso negado ao arquivo: {full_path} com nível: {file_level}")
            raise FuseOSError(errno.EACCES)
        return os.open(full_path, flags)

    def create(self, path, mode, fi=None):
        # Um usuario pode criar arquivos com nível igual ou superior ao seu, mas nao pode criar arquivos/diretorios com nível inferior
        self.user_level = get_user_clearance()

        file_level = self.get_file_level(path)
        if SECURITY_LEVELS.index(self.user_level) > SECURITY_LEVELS.index(file_level):
            print(f"[INFO][Create] Acesso negado ao arquivo: {path} com nível: {file_level}")
            raise FuseOSError(errno.EACCES) # No create down
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def unlink(self, path):
        self.user_level = get_user_clearance()
    
        file_level = self.get_file_level(path)
        if SECURITY_LEVELS.index(self.user_level) < SECURITY_LEVELS.index(file_level):
            raise FuseOSError(errno.EACCES)  # No delete up
        return os.unlink(self._full_path(path))

def main(mountpoint, root):
    FUSE(SecurePassthrough(root), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Uso: python fuse_main.py <diretório_de_origem> <ponto_de_montagem>")
        exit(1)
    main(sys.argv[2], sys.argv[1])
