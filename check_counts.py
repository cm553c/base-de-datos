import sqlite3

DB_PATH = r"d:\proyecto acces\datos_búsqueda.sqlite"
TABLA_PRINCIPAL = '"Baja  California  Sur 19"'

def check_counts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f'SELECT COUNT(*) FROM {TABLA_PRINCIPAL}')
    total = cursor.fetchone()[0]
    print(f"Total records in table: {total}")
    
    cursor.execute(f'SELECT COUNT(*) FROM {TABLA_PRINCIPAL} WHERE curp IS NOT NULL AND curp != ""')
    con_curp = cursor.fetchone()[0]
    print(f"Records with CURP: {con_curp}")
    
    cursor.execute('SELECT COUNT(*) FROM historial_exportacion')
    historial = cursor.fetchone()[0]
    print(f"Records in history: {historial}")
    
    cursor.execute(f'SELECT COUNT(*) FROM {TABLA_PRINCIPAL} WHERE curp IS NOT NULL AND curp != "" AND curp NOT IN (SELECT registro_id FROM historial_exportacion)')
    disponibles = cursor.fetchone()[0]
    print(f"AVAILABLE records for Solo CURP: {disponibles}")
    
    conn.close()

if __name__ == "__main__":
    check_counts()
