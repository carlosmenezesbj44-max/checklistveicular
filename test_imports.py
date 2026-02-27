#!/usr/bin/env python
import sys
try:
    from db import get_conn, init_db
    print("✓ db.py imported successfully")
except Exception as e:
    print(f"✗ Error importing db.py: {e}")
    sys.exit(1)

try:
    from services import (
        salvar_condutor,
        listar_condutores,
        obter_condutor,
        adicionar_infracao,
        adicionar_treinamento,
        desativar_condutor,
        ativar_condutor
    )
    print("✓ All conductor services imported successfully")
except Exception as e:
    print(f"✗ Error importing services: {e}")
    sys.exit(1)

try:
    import app
    print("✓ app.py imported successfully")
except Exception as e:
    print(f"✗ Error importing app.py: {e}")
    sys.exit(1)

print("\nAll imports successful! The application is ready to run.")
