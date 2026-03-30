import sqlite3
conn = sqlite3.connect(r'd:\proyecto acces\datos_búsqueda.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT fecnac FROM "Baja  California  Sur 19" LIMIT 5')
res = cursor.fetchall()
print("Muestra fecnac:")
for r in res:
    print(f"Original: {repr(r[0])}")
conn.close()
