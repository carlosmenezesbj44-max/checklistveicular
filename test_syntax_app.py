import py_compile
import sys

try:
    py_compile.compile('app.py', doraise=True)
    print("Sintaxe OK")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"Erro de sintaxe: {e}")
    sys.exit(1)
