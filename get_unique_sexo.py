import sqlite3
conn = sqlite3.connect(r'd:\proyecto acces\datos_búsqueda.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT sexo FROM "Baja  California  Sur 19"')
print(cursor.fetchall())
conn.close()
