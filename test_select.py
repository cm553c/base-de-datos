import sqlite3
import pandas as pd

DB_PATH = r"d:\proyecto acces\datos_búsqueda.sqlite"
TABLA_PRINCIPAL = '"Baja  California  Sur 19"'

conn = sqlite3.connect(DB_PATH)
id_col = "curp"
limite = 5
solo_curp = True

sql_select = f'"{id_col}"' if solo_curp else "*"
sql = f'SELECT {sql_select} FROM {TABLA_PRINCIPAL} LIMIT {limite}'

print(f"SQL: {sql}")
df = pd.read_sql_query(sql, conn)
print(f"Columns found: {df.columns.tolist()}")
print(f"Shape: {df.shape}")
conn.close()
