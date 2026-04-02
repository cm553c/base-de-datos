import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Search, Database, AlertCircle, Info, Download, Filter, User, MapPin, Calculator } from 'lucide-react';

function App() {
    const [query, setQuery] = useState('');
    const [filtros, setFiltros] = useState({ sexo: '', edad: '' });
    const [limite, setLimite] = useState(50);
    const [resultados, setResultados] = useState([]);
    const [columnas, setColumnas] = useState([]);
    const [cargando, setCargando] = useState(false);
    const [exportando, setExportando] = useState(false);
    const [error, setError] = useState(null);
    const [total, setTotal] = useState(0);
    const [stats, setStats] = useState({ total_base: 0, total_usados: 0, disponibles: 0 });

    // Usar variable de entorno si existe, de lo contrario fallback a localhost
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    const buscar = useCallback(async () => {
        setCargando(true);
        setError(null);
        try {
            // Usar query simple si no hay filtros específicos
            const hasFiltros = Object.values(filtros).some(v => v !== '');
            const response = await axios.get(`${API_URL}/buscar`, {
                params: {
                    q: query || '',
                    sexo: filtros.sexo,
                    edad: filtros.edad
                }
            });

            setResultados(response.data.resultados || []);
            setColumnas(response.data.columnas || []);
            setTotal(response.data.total || 0);
        } catch (err) {
            setError('Error al conectar con el servidor.');
        } finally {
            setCargando(false);
        }
    }, [query, filtros]);

    const obtenerEstadisticas = useCallback(async () => {
        try {
            const response = await axios.get(`${API_URL}/estadisticas`);
            if (response.data && !response.data.error) {
                setStats(response.data);
            }
        } catch (err) {
            console.error("Error al obtener estadísticas:", err);
        }
    }, [API_URL]);

    useEffect(() => {
        const timeoutId = setTimeout(() => buscar(), 400);
        return () => clearTimeout(timeoutId);
    }, [query, buscar]);

    useEffect(() => {
        obtenerEstadisticas();
    }, [obtenerEstadisticas]);

    const handleExportar = async (soloCurp = false) => {
        setExportando(true);
        try {
            // Construimos el nombre en el cliente, sin depender de encabezados del servidor
            const fecha = new Date().toISOString().slice(0, 10).replace(/-/g, '');
            const hora = new Date().toTimeString().slice(0, 8).replace(/:/g, '');
            const genero = filtros.sexo === 'H' ? 'Hombre' : (filtros.sexo === 'M' ? 'Mujer' : '');
            const infoSexo = genero ? `_${genero}` : '';
            const infoEdad = filtros.edad ? `_Edad${filtros.edad}` : '';
            const tipo = soloCurp ? 'SoloCURP' : 'Exportacion';
            const nombreArchivo = `${tipo}${infoSexo}${infoEdad}_${fecha}_${hora}.xlsx`;

            const response = await axios.get(`${API_URL}/exportar`, {
                params: { q: query || '', sexo: filtros.sexo, edad: filtros.edad, limite: limite, solo_curp: soloCurp },
                responseType: 'arraybuffer'
            });

            // ⚠️ CLAVE: Verificar que la respuesta sea Excel antes de descargar
            const contentType = response.headers['content-type'] || '';
            const isExcel = contentType.includes('spreadsheet') || contentType.includes('octet-stream') || contentType.includes('excel');

            if (!isExcel) {
                // La respuesta es JSON (probablemente un error del servidor disfrazado de éxito)
                const text = new TextDecoder().decode(response.data);
                try {
                    const json = JSON.parse(text);
                    alert(`AVISO: ${json.detail || 'Sin registros nuevos. Cambia los filtros o resetea el historial.'}`);
                } catch {
                    alert('Error: El servidor no devolvió un archivo Excel válido.');
                }
                return;
            }

            // Crear el Blob con el tipo MIME de Excel correcto
            const blob = new Blob([response.data], {
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            });

            // El atributo link.download sobreescribe el nombre del servidor
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = nombreArchivo;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            alert(`✅ Descargado como: ${nombreArchivo}`);
            // Actualizar estadísticas después de exportar
            obtenerEstadisticas();
        } catch (err) {
            // Manejar errores que vienen como arraybuffer
            if (err.response?.data instanceof ArrayBuffer) {
                const text = new TextDecoder().decode(err.response.data);
                try {
                    const json = JSON.parse(text);
                    const msg = json.detail || 'Error del servidor';
                    if (err.response.status === 404) {
                        alert(`AVISO: ${msg}\n\nCambia los filtros o usa "Resetear historial" para volver a exportar los mismos.`);
                    } else {
                        alert(`Error: ${msg}`);
                    }
                } catch {
                    alert(`Error: ${err.message}`);
                }
            } else {
                alert(`Error: ${err.response?.data?.detail || err.message || 'Error desconocido'}`);
            }
        } finally {
            setExportando(false);
        }
    };


    const handleLimpiarHistorial = async () => {
        if (!confirm('¿Estás seguro? Esto borrará el registro de qué datos has mandado antes (permitirá repetirlos).')) return;
        try {
            const response = await axios.post(`${API_URL}/limpiar-historial`);
            alert(response.data.mensaje);
            obtenerEstadisticas(); // Actualizar contadores
        } catch (err) {
            alert('Error al conectar con el servidor.');
        }
    };

    return (
        <div className="container">
            <header style={{ background: '#f0f9ff', padding: '1.5rem', borderRadius: '1rem', borderBottom: '2px solid #3b82f6', marginBottom: '1.5rem' }}>
                <h1 style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#1e293b' }}>
                    Buscador Aguascalientes 19
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#e0f2fe', padding: '4px 12px', borderRadius: '8px', border: '1px solid #7dd3fc' }}>
                            <span style={{ fontSize: '0.7rem', color: '#0369a1', fontWeight: 'bold', textTransform: 'uppercase' }}>Total</span>
                            <span style={{ fontSize: '1.1rem', color: '#0369a1', fontWeight: '800' }}>{stats.total_base.toLocaleString()}</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#fee2e2', padding: '4px 12px', borderRadius: '8px', border: '1px solid #fecaca' }}>
                            <span style={{ fontSize: '0.7rem', color: '#b91c1c', fontWeight: 'bold', textTransform: 'uppercase' }}>Usados</span>
                            <span style={{ fontSize: '1.1rem', color: '#b91c1c', fontWeight: '800' }}>{stats.total_usados.toLocaleString()}</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', background: '#dcfce7', padding: '4px 12px', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                            <span style={{ fontSize: '0.7rem', color: '#15803d', fontWeight: 'bold', textTransform: 'uppercase' }}>Libres</span>
                            <span style={{ fontSize: '1.1rem', color: '#15803d', fontWeight: '800' }}>{stats.disponibles.toLocaleString()}</span>
                        </div>
                    </div>
                </h1>
                <p style={{ color: '#475569' }}>Seguimiento inteligente y exportación directa optimizada - Aguascalientes 19</p>
            </header>

            <section className="busqueda-container">
                <div className="busqueda-input-wrapper">
                    <Search className="busqueda-icon" size={20} />
                    <input
                        type="text"
                        placeholder="Búsqueda rápida..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                    />
                    <div className="botones-exportar">
                        <button
                            className="btn-exportar"
                            onClick={() => handleExportar(false)}
                            disabled={exportando}
                        >
                            {exportando ? '...' : <><Download size={18} /> Todo</>}
                        </button>
                        <button
                            className="btn-exportar btn-curp"
                            onClick={() => handleExportar(true)}
                            disabled={exportando}
                        >
                            {exportando ? '...' : <><Download size={18} /> Solo CURP</>}
                        </button>
                    </div>
                </div>

                <div className="filtros-grid">
                    <div className="filtro-item">
                        <User size={16} />
                        <select value={filtros.sexo} onChange={(e) => setFiltros({ ...filtros, sexo: e.target.value })}>
                            <option value="">Cualquier Sexo</option>
                            <option value="H">Hombre</option>
                            <option value="M">Mujer</option>
                        </select>
                    </div>
                    <div className="filtro-item">
                        <Calculator size={16} />
                        <input
                            type="number"
                            placeholder="Edad (ej. 20)"
                            value={filtros.edad}
                            onChange={(e) => setFiltros({ ...filtros, edad: e.target.value })}
                        />
                    </div>
                    <div className="filtro-item">
                        <Database size={16} />
                        <input
                            type="number"
                            placeholder="Cantidad a exportar (ej. 50)"
                            value={limite}
                            onChange={(e) => setLimite(e.target.value)}
                            title="Cantidad de registros para el Excel"
                        />
                    </div>
                </div>
            </section>

            <div className="resultados-stats">
                <span>{total} registros encontrados | Seguimiento de unicidad estricto activo</span>
            </div>

            <div className="table-container">
                <table className="excel-table">
                    <thead>
                        <tr>
                            {columnas.map(col => (
                                <th key={col}>{col}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {resultados.map((item, index) => (
                            <tr key={index} className={item._exportado ? 'row-exportado' : ''}>
                                {columnas.map(col => (
                                    <td key={col}>
                                        {String(item[col] || '')}
                                        {col.toLowerCase() === 'curp' && item._exportado &&
                                            <span className="badge-exportado" title="Este CURP ya fue exportado antes">✓</span>
                                        }
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
                {resultados.length === 0 && !cargando && (
                    <div className="no-results">No se encontraron registros</div>
                )}
            </div>

            <style>{`
        .botones-exportar {
          display: flex;
          gap: 0.5rem;
          margin-left: 1rem;
        }
        .btn-exportar {
          padding: 0.75rem 1.25rem;
          background: var(--primary);
          color: white;
          border: none;
          border-radius: 0.75rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: 600;
          transition: all 0.3s ease;
          white-space: nowrap;
        }
        .btn-exportar:hover { background: var(--primary-hover); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .btn-exportar:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-curp {
            background: #10b981; /* Un verde vibrante para diferenciar */
        }
        .btn-curp:hover {
            background: #059669;
        }
        .resultados-stats {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 1.5rem;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
          color: var(--text-muted);
        }
        .btn-limpiar {
          background: #fee2e2;
          border: 1px solid #fecaca;
          color: #ef4444;
          padding: 0.4rem 1rem;
          border-radius: 0.5rem;
          cursor: pointer;
          font-size: 0.85rem;
          font-weight: 600;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .btn-limpiar:hover {
          background: #fca5a5;
          color: white;
          border-color: #ef4444;
          transform: scale(1.05);
        }

        .filtros-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid var(--border);
        }
        .filtro-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          background: var(--bg);
          padding: 0.5rem;
          border-radius: 0.5rem;
          border: 1px solid var(--border);
        }
        .filtro-item select, .filtro-item input {
          background: var(--card-bg);
          border: none;
          color: var(--text);
          width: 100%;
          outline: none;
          font-size: 0.9rem;
          padding: 2px;
        }
        .filtro-item select option {
          background: var(--card-bg);
          color: var(--text);
        }
        
        /* Nuevos estilos para seguimiento */
        .row-exportado {
          opacity: 0.6;
          background: #f9fafb;
        }
        .badge-exportado {
          margin-left: 0.5rem;
          color: #10b981;
          font-weight: bold;
          font-size: 0.8rem;
          background: #ecfdf5;
          padding: 1px 6px;
          border-radius: 4px;
          border: 1px solid #10b981;
        }
      `}</style>
        </div>
    );
}

export default App;
