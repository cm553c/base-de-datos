from fastapi import FastAPI, Query, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import uvicorn
import sqlite3
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import io
import glob
import openpyxl
from fastapi.responses import StreamingResponse

app = FastAPI(title="API de Búsqueda Aguascalientes v2", description="Servidor avanzado con filtros y exportación")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Configuración de base de datos dinámica
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DATABASE_URL", os.path.join(BASE_DIR, "datos_busqueda.sqlite"))
TABLA_PRINCIPAL = '"Aguscalientes 19"'

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    # Habilitar modo WAL para concurrencia y velocidad
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    # Crear tabla de historial si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_exportacion (
            registro_id TEXT PRIMARY KEY,
            fecha_exportacion DATETIME
        )
    """)
    conn.commit()
    
    # Limpiar entradas huérfanas del historial (de migraciones anteriores)
    try:
        tabla_clean = TABLA_PRINCIPAL.replace('"', '').replace("'", "")
        cursor.execute(f"PRAGMA table_info('{tabla_clean}')")
        columnas = [info[1] for info in cursor.fetchall()]
        if columnas:
            id_col = next((c for c in columnas if c.lower() == "curp"), columnas[0])
            # Eliminar del historial los que NO existen en la tabla actual
            cursor.execute(f'''
                DELETE FROM historial_exportacion
                WHERE registro_id NOT IN (
                    SELECT "{id_col}" FROM {TABLA_PRINCIPAL}
                    WHERE "{id_col}" IS NOT NULL AND "{id_col}" != ''
                )
            ''')
            eliminados = cursor.rowcount
            if eliminados > 0:
                print(f"[INIT] Limpieza: {eliminados} entradas huérfanas eliminadas del historial")
            conn.commit()
    except Exception as e:
        print(f"[INIT] Error limpiando historial huérfano: {e}")
    
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
    return {"mensaje": "API de Búsqueda y Exportación Aguascalientes Activa"}

@app.get("/estadisticas")
def obtener_estadisticas():
    # Usar timeout para evitar bloqueos
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    try:
        # Sanitizar nombre de tabla para PRAGMA
        tabla_clean = TABLA_PRINCIPAL.replace('"', '').replace("'", "")
        
        # Obtener la columna ID (CURP)
        cursor.execute(f"PRAGMA table_info('{tabla_clean}')")
        columnas = [info[1] for info in cursor.fetchall()]
        if not columnas:
             return {"error": f"La tabla {TABLA_PRINCIPAL} no existe en la base de datos."}
             
        id_col = next((c for c in columnas if c.lower() == "curp"), columnas[0])

        # Total de PERSONAS (ya deduplicadas en DB)
        cursor.execute(f"SELECT COUNT(*) FROM {TABLA_PRINCIPAL}")
        total_base = cursor.fetchone()[0]
        
        # Total de PERSONAS que ya han sido exportadas
        sql_usados = f"""
            SELECT COUNT(*) 
            FROM {TABLA_PRINCIPAL} t
            INNER JOIN historial_exportacion h ON t.\"{id_col}\" = h.registro_id
        """
        cursor.execute(sql_usados)
        total_usados = cursor.fetchone()[0]
        
        # Tamaño del archivo para diagnóstico
        db_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        
        return {
            "total_base": total_base,
            "total_usados": total_usados,
            "disponibles": total_base - total_usados,
            "db_size_mb": round(db_size_mb, 2)
        }
    except Exception as e:
        print(f"Error en estadísticas: {e}")
        return {"error": str(e)}
    finally:
        conn.close()

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
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        # Obtener columnas e ID (CURP)
        tabla_sanitizada = TABLA_PRINCIPAL.replace('"', '').replace("'", "")
        cursor.execute(f"PRAGMA table_info('{tabla_sanitizada}')")
        columnas_db = [info[1] for info in cursor.fetchall()]
        id_col = next((c for c in columnas_db if c.lower() == "curp"), columnas_db[0])

        # Construir WHERE con prefijos para el JOIN
        condiciones_con_prefijo = []
        if q and q.strip():
            search_conds = " OR ".join([f"t.\"{col}\" LIKE ?" for col in columnas_db])
            condiciones_con_prefijo.append(f"({search_conds})")
        if sexo and sexo.strip():
            condiciones_con_prefijo.append("t.\"sexo\" LIKE ?")
        if edad and edad.strip():
            condiciones_con_prefijo.append("CAST(t.\"edad\" AS TEXT) LIKE ?")
        
        where_sql = " AND ".join(condiciones_con_prefijo) if condiciones_con_prefijo else "1=1"

        # SQL que excluye ya exportados
        sql = f"""
            SELECT t.* 
            FROM {TABLA_PRINCIPAL} t
            LEFT JOIN historial_exportacion h ON t."{id_col}" = h.registro_id
            WHERE h.registro_id IS NULL AND {where_sql}
            LIMIT 100
        """
        
        print(f"DEBUG SQL: {sql} | Params: {params}")
        cursor.execute(sql, params)
        filas = cursor.fetchall()
        
        resultados = []
        for fila in filas:
            d = dict(fila)
            if "fecnac" in d and d["fecnac"]:
                d["fecnac"] = str(d["fecnac"]).split(" ")[0]
            
            d["exportado"] = False
            resultados.append(d)
            
        return {"total": len(resultados), "resultados": resultados, "columnas": columnas_db}
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return {"total": 0, "resultados": [], "columnas": [], "error": str(e)}
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
    
    # Construir WHERE con prefijos para el JOIN
    condiciones_con_prefijo = []
    if q and q.strip():
        search_conds = " OR ".join([f"t.\"{col}\" LIKE ?" for col in columnas])
        condiciones_con_prefijo.append(f"({search_conds})")
    if sexo and sexo.strip():
        condiciones_con_prefijo.append("t.\"sexo\" LIKE ?")
    if edad and edad.strip():
        condiciones_con_prefijo.append("CAST(t.\"edad\" AS TEXT) LIKE ?")
    
    where_sql = " AND ".join(condiciones_con_prefijo) if condiciones_con_prefijo else "1=1"
    
    # Evitar exportar CURPs vacíos si se pidió solo CURP
    filtro_vacios = f" AND t.\"{id_col}\" IS NOT NULL AND t.\"{id_col}\" != ''" if solo_curp else ""
    
    sql_select = f't."{id_col}"' if solo_curp else "t.*"
    
    sql = f"""
        SELECT {sql_select} FROM {TABLA_PRINCIPAL} t
        LEFT JOIN historial_exportacion h ON t."{id_col}" = h.registro_id
        WHERE h.registro_id IS NULL
        AND {where_sql}
        {filtro_vacios}
        LIMIT ?
    """
    params.append(limite)
    
    print(f"[EXPORT] SQL final: {sql}")
    
    conn = sqlite3.connect(DB_PATH, timeout=20)
    try:
        # 1. Obtener registros disponibles de forma atómica
        cursor = conn.cursor()
        # Asegurar modo WAL en esta conexión también
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("BEGIN TRANSACTION")
        
        # Primero identificamos los IDs que se van a exportar
        sql_ids = f"""
            SELECT t."{id_col}" FROM {TABLA_PRINCIPAL} t
            LEFT JOIN historial_exportacion h ON t."{id_col}" = h.registro_id
            WHERE h.registro_id IS NULL
            AND {where_sql}
            {filtro_vacios}
            LIMIT ?
        """
        cursor.execute(sql_ids, params)
        ids_a_exportar = [row[0] for row in cursor.fetchall()]

        if not ids_a_exportar:
            cursor.execute("ROLLBACK")
            msg = "No se encontraron registros NUEVOS con esos filtros."
            if solo_curp:
                msg = "No hay CURPs nuevos para exportar con estos filtros. Todos los registros coincidentes ya fueron exportados anteriormente."
            raise HTTPException(status_code=404, detail=msg)

        # 2. Insertar inmediatamente en el historial para "bloquearlos"
        ahora = datetime.now()
        data_to_insert = [(str(val_id), ahora) for val_id in ids_a_exportar]
        cursor.executemany("INSERT OR IGNORE INTO historial_exportacion (registro_id, fecha_exportacion) VALUES (?, ?)", 
                           data_to_insert)
        
        # 3. Commit de la reserva antes de generar el Excel
        conn.commit()

        # 4. Ahora sí, leer todos los datos de esos IDs específicos para el Excel
        id_placeholders = ",".join(["?"] * len(ids_a_exportar))
        sql_datos = f"SELECT * FROM {TABLA_PRINCIPAL} WHERE \"{id_col}\" IN ({id_placeholders})"
        df = pd.read_sql_query(sql_datos, conn, params=ids_a_exportar)
        
        # Si se pidió solo CURP, filtrar columnas
        if solo_curp:
            df = df[[id_col]]
            
        # Limpiar formato de fecha en el DataFrame
        if "fecnac" in df.columns:
            df["fecnac"] = df["fecnac"].astype(str).str.split(" ").str[0]
            
        # Generar nombre descriptivo con cantidad de CURPs
        cantidad = len(ids_a_exportar)
        partes = []
        if sexo:
            genero = "Hombre" if sexo == "H" else ("Mujer" if sexo == "M" else sexo)
            partes.append(f"{genero}")
        if edad: partes.append(f"Edad_{edad}")
        if solo_curp: partes.append("SoloCURP")
        if q: partes.append("Busqueda")
        partes.append(f"{cantidad}curps")
        
        prefijo = "_".join(partes) if partes else "Exportacion"
        fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"{prefijo}_{fecha_str}.xlsx"
        
        # Generar Excel en memoria (BytesIO) para evitar problemas de disco en Render
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        
        # Nombre del archivo para el header
        headers = {
            'Content-Disposition': f'attachment; filename="{nombre_archivo}"'
        }
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[EXPORT ERROR]: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar Excel: {str(e)}")
    finally:
        conn.close()

@app.post("/limpiar-historial")
def limpiar_historial():
    # Deshabilitado por orden estricta: No se pueden duplicar CURPs JAMÁS.
    raise HTTPException(status_code=403, detail="La limpieza de historial ha sido deshabilitada para garantizar la unicidad absoluta de los datos.")

@app.post("/importar-curps-excel")
def importar_curps_excel():
    """Escanea archivos Excel en el directorio y registra sus CURPs en el historial."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    cursor = conn.cursor()
    try:
        # Obtener columna CURP
        tabla_clean = TABLA_PRINCIPAL.replace('"', '').replace("'", "")
        cursor.execute(f"PRAGMA table_info('{tabla_clean}')")
        columnas = [info[1] for info in cursor.fetchall()]
        id_col = next((c for c in columnas if c.lower() == "curp"), columnas[0])
        
        # Escanear archivos Excel en el directorio del proyecto
        xlsx_files = glob.glob(os.path.join(BASE_DIR, "*.xlsx"))
        total_importados = 0
        total_ya_existentes = 0
        archivos_procesados = []
        
        for filepath in xlsx_files:
            try:
                wb = openpyxl.load_workbook(filepath, read_only=True)
                ws = wb.active
                rows = list(ws.iter_rows(values_only=True))
                if not rows:
                    wb.close()
                    continue
                
                header = rows[0]
                curp_col = None
                for i, h in enumerate(header):
                    if h and str(h).lower() == "curp":
                        curp_col = i
                        break
                if curp_col is None and len(header) == 1:
                    curp_col = 0
                
                if curp_col is not None:
                    curps_encontrados = []
                    for row in rows[1:]:
                        if row[curp_col]:
                            curp_val = str(row[curp_col]).strip()
                            if curp_val:
                                curps_encontrados.append(curp_val)
                    
                    # Solo importar CURPs que existan en la tabla principal
                    importados_archivo = 0
                    ahora = datetime.now()
                    for curp_val in curps_encontrados:
                        # Verificar que el CURP existe en la tabla actual
                        cursor.execute(f'SELECT COUNT(*) FROM {TABLA_PRINCIPAL} WHERE "{id_col}" = ?', (curp_val,))
                        if cursor.fetchone()[0] > 0:
                            cursor.execute(
                                "INSERT OR IGNORE INTO historial_exportacion (registro_id, fecha_exportacion) VALUES (?, ?)",
                                (curp_val, ahora)
                            )
                            if cursor.rowcount > 0:
                                importados_archivo += 1
                            else:
                                total_ya_existentes += 1
                    
                    total_importados += importados_archivo
                    nombre = os.path.basename(filepath)
                    archivos_procesados.append({
                        "archivo": nombre,
                        "curps_encontrados": len(curps_encontrados),
                        "nuevos_importados": importados_archivo
                    })
                
                wb.close()
            except Exception as e:
                archivos_procesados.append({
                    "archivo": os.path.basename(filepath),
                    "error": str(e)
                })
        
        conn.commit()
        return {
            "mensaje": f"Importación completada: {total_importados} CURPs nuevos registrados, {total_ya_existentes} ya existían.",
            "total_importados": total_importados,
            "total_ya_existentes": total_ya_existentes,
            "archivos": archivos_procesados
        }
    except Exception as e:
        print(f"[IMPORT ERROR]: {e}")
        raise HTTPException(status_code=500, detail=f"Error al importar: {str(e)}")
    finally:
        conn.close()

@app.get("/historial-resumen")
def historial_resumen():
    """Devuelve resumen del historial de exportaciones."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    cursor = conn.cursor()
    try:
        # Total en historial
        cursor.execute("SELECT COUNT(*) FROM historial_exportacion")
        total = cursor.fetchone()[0]
        
        # Últimas exportaciones agrupadas por fecha
        cursor.execute("""
            SELECT DATE(fecha_exportacion) as fecha, COUNT(*) as cantidad
            FROM historial_exportacion
            GROUP BY DATE(fecha_exportacion)
            ORDER BY fecha DESC
            LIMIT 20
        """)
        por_fecha = [{"fecha": row[0], "cantidad": row[1]} for row in cursor.fetchall()]
        
        # Últimos 10 CURPs exportados
        cursor.execute("""
            SELECT registro_id, fecha_exportacion
            FROM historial_exportacion
            ORDER BY fecha_exportacion DESC
            LIMIT 10
        """)
        recientes = [{"curp": row[0], "fecha": str(row[1])} for row in cursor.fetchall()]
        
        return {
            "total_historial": total,
            "exportaciones_por_fecha": por_fecha,
            "recientes": recientes
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    # Puerto dinámico para Render/Railway
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
