import sys
import py_compile

try:
    py_compile.compile('app.py', doraise=True)
    py_compile.compile('services.py', doraise=True)
    py_compile.compile('db.py', doraise=True)
    print("All files compiled successfully!")
except py_compile.PyCompileError as e:
    print(f"Syntax error: {e}")
    sys.exit(1)
