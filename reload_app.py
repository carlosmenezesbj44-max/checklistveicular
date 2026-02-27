#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para limpar cache e recarregar a aplicação"""

import os
import sys
import shutil
from pathlib import Path

# Diretório da aplicação
APP_DIR = Path(__file__).parent

# Limpar __pycache__
for pycache_dir in APP_DIR.rglob('__pycache__'):
    print(f"Removendo: {pycache_dir}")
    shutil.rmtree(pycache_dir, ignore_errors=True)

# Limpar arquivos .pyc
for pyc_file in APP_DIR.rglob('*.pyc'):
    print(f"Removendo: {pyc_file}")
    pyc_file.unlink(missing_ok=True)

print("[OK] Cache limpo com sucesso!")
print("\nProximos passos no PythonAnywhere:")
print("1. Vá para o painel de Web Apps")
print("2. Clique em 'Reload'")
print("3. Tente novamente adicionar combustível")
