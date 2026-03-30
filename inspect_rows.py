import sqlite3
conn = sqlite3.connect(r'd:\proyecto acces\datos_búsqueda.sqlite')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT * FROM "Baja  California  Sur 19" WHERE sexo IS NOT NULL LIMIT 5')
rows = cursor.fetchall()
for row in rows:
    print(dict(row))
conn.close()
