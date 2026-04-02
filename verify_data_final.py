import sqlite3

archivo_sqlite = r"d:\proyecto acces\datos_búsqueda.sqlite"

def verify_data():
    conn = sqlite3.connect(archivo_sqlite)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = [row[0] for row in cursor.fetchall()]
        print(f"Tablas en SQLite: {tablas}")
        
        if 'Aguscalientes 19' in tablas:
            cursor.execute('SELECT COUNT(*) FROM "Aguscalientes 19"')
            count = cursor.fetchone()[0]
            print(f"Total de registros en 'Aguscalientes 19': {count}")
            
            cursor.execute('SELECT * FROM "Aguscalientes 19" LIMIT 5')
            rows = cursor.fetchall()
            print("Primeros 5 registros:")
            for row in rows:
                print(row)
        else:
            print("ERROR: La tabla 'Aguscalientes 19' no se encuentra.")
            
        if 'historial_exportacion' in tablas:
            cursor.execute('SELECT COUNT(*) FROM historial_exportacion')
            count_h = cursor.fetchone()[0]
            print(f"Total de registros en 'historial_exportacion' (usados): {count_h}")
        else:
            print("Advertencia: 'historial_exportacion' no encontrada.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_data()
