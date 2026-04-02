import pyodbc
import os

archivo_access = r"d:\proyecto acces\AGUSCALIENTES 19.accdb"

def list_tables():
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={archivo_access};"
    )
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        tablas = [t.table_name for t in cursor.tables(tableType='TABLE')]
        print(f"Tablas encontradas: {tablas}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_tables()
