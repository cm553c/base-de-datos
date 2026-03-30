import sqlite3
conn = sqlite3.connect(r'd:\proyecto acces\datos_búsqueda.sqlite')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT sexo, HEX(sexo), LENGTH(sexo) FROM "Baja  California  Sur 19"')
res = cursor.fetchall()
print("Valores únicos de sexo:")
for r in res:
    print(f"Valor: {repr(r[0])}, Hex: {r[1]}, Largo: {r[2]}")

# Probar búsqueda sin TRIM y con LIKE
cursor.execute('SELECT COUNT(*) FROM "Baja  California  Sur 19" WHERE sexo = "M"')
print('Con sexo = "M":', cursor.fetchone()[0])

cursor.execute('SELECT COUNT(*) FROM "Baja  California  Sur 19" WHERE sexo LIKE "%M%"')
print('Con sexo LIKE "%M%":', cursor.fetchone()[0])

conn.close()
