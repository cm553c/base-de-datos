import sqlite3
conn = sqlite3.connect(r'd:\proyecto acces\datos_búsqueda.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT curp, sexo, edad FROM "Baja  California  Sur 19" LIMIT 10')
res = cursor.fetchall()
print("Muestra de datos (10 primeros):")
for r in res:
    print(f"CURP: {repr(r[0])}, SEXO: {repr(r[1])}, EDAD: {repr(r[2])}")

cursor.execute('SELECT COUNT(*) FROM "Baja  California  Sur 19" WHERE curp IS NULL OR curp = ""')
print("Total de registros con CURP vacío:", cursor.fetchone()[0])
conn.close()
