import sqlite3, json
conn = sqlite3.connect(r'd:\proyecto acces\datos_búsqueda.sqlite')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info("Baja  California  Sur 19")')
print(json.dumps([info[1] for info in cursor.fetchall()]))
conn.close()
