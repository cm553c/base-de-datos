import sqlite3
conn = sqlite3.connect(r'd:\proyecto acces\datos_búsqueda.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT sexo, LENGTH(sexo) FROM "Baja  California  Sur 19"')
res = cursor.fetchall()
for r in res:
    print(f"Value: {repr(r[0])}, Length: {r[1]}")
conn.close()
