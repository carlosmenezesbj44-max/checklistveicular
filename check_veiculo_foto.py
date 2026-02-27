import sqlite3

conn = sqlite3.connect('data/ChecklistVeicular/checklist.db')
cur = conn.cursor()

cur.execute('SELECT id, placa, modelo, foto_carro FROM veiculos WHERE id = 8')
row = cur.fetchone()

if row:
    print(f'Veículo ID: {row[0]}')
    print(f'Placa: {row[1]}')
    print(f'Modelo: {row[2]}')
    print(f'Foto: {row[3]}')
else:
    print('Veículo 8 não encontrado')

conn.close()
