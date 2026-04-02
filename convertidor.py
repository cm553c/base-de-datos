import pandas as pd
import sqlalchemy as sa
import pyodbc
import os

# Configuración de archivos
archivo_access = r"d:\proyecto acces\AGUSCALIENTES 19.accdb"
archivo_sqlite = r"d:\proyecto acces\datos_busqueda.sqlite"

def explorar_y_convertir():
    print(f"--- Iniciando proceso para: {archivo_access} ---")
    
    # Cadena de conexión para Access en Windows
    # Nota: Requiere el controlador Microsoft Access Database Engine
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={archivo_access};"
    )
    
    try:
        # Intentar conectar para listar tablas
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        tablas = [t.table_name for t in cursor.tables(tableType='TABLE')]
        print(f"Tablas encontradas: {tablas}")
        
        # Crear motor de SQLite
        engine_sqlite = sa.create_engine(f"sqlite:///{archivo_sqlite}")
        
        for tabla in tablas:
            print(f"Convirtiendo tabla: {tabla}...")
            # Leer tabla con pandas
            query = f"SELECT * FROM [{tabla}]"
            df = pd.read_sql(query, conn)
            
            # Guardar en SQLite
            df.to_sql(tabla, engine_sqlite, index=False, if_exists='replace')
            print(f"Tabla '{tabla}' convertida con éxito. ({len(df)} filas)")
            
        conn.close()
        print("\n--- Conversión finalizada con éxito ---")
        print(f"Archivo generado: {archivo_sqlite}")
        
    except Exception as e:
        print(f"\nError durante la conversión: {e}")
        print("\nSUGERENCIA: Asegúrate de tener instalado 'Microsoft Access Database Engine 2016 Redistributable'.")

if __name__ == "__main__":
    explorar_y_convertir()
