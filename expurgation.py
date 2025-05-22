#!/usr/bin/env python3

import os
import sys
import errno

from fuse import FUSE, FuseOSError, Operations
from auth import get_user_clearance

SECURITY_LEVELS = ["UNCLASSIFIED", "CONFIDENTIAL", "SECRET", "TOP_SECRET"]

TRUSTED_USERS = ["admin"]  # ou venha de auth futuramente

def expurgate(self, source_path, dest_path):
    self.user_level = get_user_clearance()
    username = os.getenv("USER", "default")

    source_level = self.get_file_level(source_path)
    dest_level = self.get_file_level(dest_path)

    if username not in TRUSTED_USERS:
        print("[EXPURGATE] Usuário não confiável.")
        raise FuseOSError(errno.EACCES)

    if SECURITY_LEVELS.index(source_level) <= SECURITY_LEVELS.index(dest_level):
        print("[EXPURGATE] Expurgação inválida: destino não é de nível inferior.")
        raise FuseOSError(errno.EACCES)

    try:
        with open(self._full_path(source_path), 'r') as fsrc:
            content = fsrc.read()

        with open(self._full_path(dest_path), 'w') as fdest:
            fdest.write("[EXPURGADO]\n" + content)

        print(f"[EXPURGATE] Arquivo expurgado de {source_level} para {dest_level}")
    except Exception as e:
        print(f"[EXPURGATE] Erro: {e}")
        raise FuseOSError(errno.EIO)
