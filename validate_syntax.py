import ast
import sys

files_to_check = [
    'app.py',
    'models.py',
    'db.py',
    'services.py'
]

for file in files_to_check:
    try:
        with open(file) as f:
            ast.parse(f.read())
        print(f'✓ {file}: Syntax OK')
    except SyntaxError as e:
        print(f'✗ {file}: {e}')
        sys.exit(1)
    except FileNotFoundError:
        print(f'⊘ {file}: Not found')

print('\nAll files have valid Python syntax!')
