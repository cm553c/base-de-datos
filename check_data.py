import sqlite3
conn = sqlite3.connect(r'd:\proyecto acces\datos_búsqueda.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT sexo, edad, COUNT(*) FROM "Baja  California  Sur 19" GROUP BY sexo, edad LIMIT 50')
print(cursor.fetchall())
conn.close()
