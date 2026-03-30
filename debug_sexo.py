import sqlite3
conn = sqlite3.connect(r'd:\proyecto acces\datos_búsqueda.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM "Baja  California  Sur 19" WHERE sexo = "M"')
print("Count for M:", cursor.fetchone()[0])
cursor.execute('SELECT sexO, COUNT(*) FROM "Baja  California  Sur 19" GROUP BY sexO')
print("Group by sexO:", cursor.fetchall())
conn.close()
