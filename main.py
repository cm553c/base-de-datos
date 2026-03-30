from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uvicorn
import sqlite3
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

app = FastAPI(title="API de Búsqueda BCS v2", description="Servidor avanzado con filtros y exportación")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de base de datos dinámica
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DATABASE_URL", os.path.join(BASE_DIR, "datos_búsqueda.sqlite"))
TABLA_PRINCIPAL = '"Baja  California  Sur 19"'

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Crear tabla de historial si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_exportacion (
            registro_id TEXT PRIMARY KEY,
            fecha_exportacion DATETIME
        )
    """)
    conn.commit()
    conn.close()

inicializar_db()

def obtener_columnas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({TABLA_PRINCIPAL})")
    columnas = [info[1] for info in cursor.fetchall()]
    conn.close()
    return columnas

@app.get("/")
def inicio():
    return {"mensaje": "API de Búsqueda y Exportación BCS Activa"}

@app.get("/columnas")
def listar_columnas():
    return {"columnas": obtener_columnas()}

@app.get("/buscar")
def buscar(q: str = Query(None), sexo: str = None, edad: str = None):
    print(f"DEBUG: Búsqueda q={q}, sexo={sexo}, edad={edad}")
    columnas = obtener_columnas()
    condiciones = []
    params = []

    # Búsqueda general
    if q and q.strip():
        search_conds = " OR ".join([f"\"{col}\" LIKE ?" for col in columnas])
        condiciones.append(f"({search_conds})")
        params.extend([f"%{q.strip()}%"] * len(columnas))
    
    # Filtros específicos
    if sexo and sexo.strip():
        condiciones.append("\"sexo\" LIKE ?")
        params.append(f"%{sexo.strip()}%")
    if edad and edad.strip():
        condiciones.append("CAST(\"edad\" AS TEXT) LIKE ?")
        params.append(f"%{edad.strip()}%")

    where_clause = " WHERE " + " AND ".join(condiciones) if condiciones else ""
    sql = f"SELECT * FROM {TABLA_PRINCIPAL}{where_clause} LIMIT 100"
    
    print(f"DEBUG SQL: {sql} | Params: {params}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        filas = cursor.fetchall()
        
        # Obtener IDs ya exportados para marcar en la búsqueda
        cursor.execute("SELECT registro_id FROM historial_exportacion")
        historial = {row[0] for row in cursor.fetchall()}
        
        resultados = []
        for fila in filas:
            d = dict(fila)
            # Limpiar formato de fecha si existe
            if "fecnac" in d and d["fecnac"]:
                d["fecnac"] = str(d["fecnac"]).split(" ")[0]
            
            # Marcar si ya fue exportado
            val_id = str(d.get(columnas[0], "")) # Usamos la primera columna como ID por defecto para la marca visual
            # Si hay una columna CURP, preferimos esa para la marca visual
            id_para_marca = next((d[c] for c in d if c.lower() == "curp"), d.get(columnas[0]))
            d["_exportado"] = str(id_para_marca) in historial
            
            resultados.append(d)
            
        return {"total": len(resultados), "resultados": resultados, "columnas": columnas}
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return {"total": 0, "resultados": [], "columnas": columnas, "error": str(e)}
    finally:
        conn.close()

@app.get("/exportar")
def exportar(q: str = None, sexo: str = None, edad: str = None, limite: int = 50, solo_curp: bool = False):
    print(f"\n[EXPORT] Solicitado: q={q}, sexo={sexo}, edad={edad}, limite={limite}, solo_curp={solo_curp}")
    columnas = obtener_columnas()
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

    id_col = next((c for c in columnas if c.lower() == "curp"), columnas[0])
    where_clause = " WHERE " + " AND ".join(condiciones) if condiciones else " WHERE 1=1"
    sql_select = f'"{id_col}"' if solo_curp else "*"
    
    # Evitar exportar CURPs vacíos si se pidió solo CURP
    filtro_vacios = f" AND \"{id_col}\" IS NOT NULL AND \"{id_col}\" != ''" if solo_curp else ""
    
    sql = f"""
        SELECT {sql_select} FROM {TABLA_PRINCIPAL} 
        {where_clause} 
        {filtro_vacios}
        AND "{id_col}" NOT IN (SELECT registro_id FROM historial_exportacion)
        LIMIT ?
    """
    params.append(limite)
    
    print(f"[EXPORT] SQL final: {sql}")
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        if df.empty:
            msg = "No se encontraron registros NUEVOS con esos filtros."
            if solo_curp:
                msg = "No hay CURPs nuevos para exportar con estos filtros. Todos los registros coincidentes ya fueron exportados anteriormente."
            raise HTTPException(status_code=404, detail=msg)
        
        # Limpiar formato de fecha en el DataFrame
        if "fecnac" in df.columns:
            df["fecnac"] = df["fecnac"].astype(str).str.split(" ").str[0]
            
        # Generar nombre descriptivo
        partes = []
        if sexo:
            genero = "Hombre" if sexo == "H" else ("Mujer" if sexo == "M" else sexo)
            partes.append(f"{genero}")
        if edad: partes.append(f"Edad_{edad}")
        if solo_curp: partes.append("SoloCURP")
        if q: partes.append("Busqueda")
        
        prefijo = "_".join(partes) if partes else "Exportacion"
        fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"{prefijo}_{fecha_str}.xlsx"
        
        ruta_excel = os.path.join(os.getcwd(), nombre_archivo)
        df.to_excel(ruta_excel, index=False)
        
        cursor = conn.cursor()
        for val_id in df[id_col]:
            cursor.execute("INSERT OR IGNORE INTO historial_exportacion (registro_id, fecha_exportacion) VALUES (?, ?)", 
                           (str(val_id), datetime.now()))
        conn.commit()
        return FileResponse(ruta_excel, filename=nombre_archivo)
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[EXPORT ERROR]: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar Excel: {str(e)}")
    finally:
        conn.close()

@app.post("/limpiar-historial")
def limpiar_historial():
    print(">>> SOLICITUD: Limpiar historial de exportación")
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM historial_exportacion")
        conn.commit()
        return {"mensaje": "Historial de exportación limpiado con éxito. Ahora puedes volver a exportar los mismos datos."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    # Puerto dinámico para Render/Railway
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
