import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = r"d:\proyecto acces\datos_búsqueda.sqlite"
TABLA_PRINCIPAL = '"Baja  California  Sur 19"'

def test_logic(sexo=None, edad=None, q=None, solo_curp=False, limite=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get columns
    cursor.execute(f"PRAGMA table_info({TABLA_PRINCIPAL})")
    columnas = [info[1] for info in cursor.fetchall()]
    
    id_col = next((c for c in columnas if c.lower() == "curp"), columnas[0])
    
    condiciones = []
    params = []
    
    if q and q.strip():
        search_conds = " OR ".join([f"\"{col}\" LIKE ?" for col in columnas])
        condiciones.append(f"({search_conds})")
        params.extend([f"%{q.strip()}%"] * len(columnas))
    
    if sexo and sexo.strip():
        condiciones.append("\"sexo\" LIKE ?")
        params.append(f"%{sexo.strip()}%")
        
    if edad and edad.strip():
        condiciones.append("CAST(\"edad\" AS TEXT) LIKE ?")
        params.append(f"%{edad.strip()}%")

    where_clause = " WHERE " + " AND ".join(condiciones) if condiciones else " WHERE 1=1"
    sql_select = f'"{id_col}"' if solo_curp else "*"
    filtro_vacios = f" AND \"{id_col}\" IS NOT NULL AND \"{id_col}\" != ''" if solo_curp else ""
    
    sql = f"""
        SELECT {sql_select} FROM {TABLA_PRINCIPAL} 
        {where_clause} 
        {filtro_vacios}
        AND "{id_col}" NOT IN (SELECT registro_id FROM historial_exportacion)
        LIMIT ?
    """
    params.append(limite)
    
    print(f"Executing SQL: {sql}")
    print(f"With Params: {params}")
    
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        print(f"Results found: {len(df)}")
        if not df.empty:
            print("First 5 rows:")
            print(df.head())
        else:
            print("NO RESULTS FOUND.")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("--- Test 1: Solo CURP (no filters) ---")
    test_logic(solo_curp=True, limite=5)
    
    print("\n--- Test 2: Todo (no filters) ---")
    test_logic(solo_curp=False, limite=5)
