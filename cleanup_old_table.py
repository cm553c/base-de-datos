import sqlite3
import os

db_path = r'd:/proyecto acces/datos_búsqueda.sqlite'
old_table = 'Baja  California  Sur 19'

def cleanup():
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            conn.execute(f'DROP TABLE IF EXISTS "{old_table}"')
            conn.commit()
            print(f"Tabla '{old_table}' eliminada correctamente.")
        except Exception as e:
            print(f"Error al eliminar tabla: {e}")
        finally:
            conn.close()
    else:
        print("Base de datos no encontrada.")

if __name__ == "__main__":
    cleanup()
