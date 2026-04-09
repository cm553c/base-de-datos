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
    const [mostrarAdmin, setMostrarAdmin] = useState(false);
    const [historial, setHistorial] = useState(null);
    const [importando, setImportando] = useState(false);

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

    const obtenerHistorial = useCallback(async () => {
        try {
            const response = await axios.get(`${API_URL}/historial-resumen`);
            if (response.data && !response.data.error) {
                setHistorial(response.data);
            }
        } catch (err) {
            console.error("Error al obtener historial:", err);
        }
    }, [API_URL]);

    useEffect(() => {
        const timeoutId = setTimeout(() => buscar(), 400);
        return () => clearTimeout(timeoutId);
    }, [query, buscar]);

    useEffect(() => {
        obtenerEstadisticas();
        obtenerHistorial();
    }, [obtenerEstadisticas, obtenerHistorial]);

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
                responseType: 'blob'
            });

            // Intentar obtener el nombre del archivo del encabezado del servidor
            let fileName = nombreArchivo;
            const contentDisposition = response.headers['content-disposition'];
            if (contentDisposition) {
                const fileNameMatch = contentDisposition.match(/filename="?([^"]*)"?/);
                if (fileNameMatch && fileNameMatch[1]) {
                    fileName = fileNameMatch[1];
                }
            }

            // Crear el enlace de descarga
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', fileName);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

            alert(`✅ Descargado como: ${fileName}`);
            // Actualizar estadísticas y historial después de exportar
            obtenerEstadisticas();
            obtenerHistorial();
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

    const handleImportarExcel = async () => {
        if (!confirm('¿Sincronizar historial con todos los archivos Excel? Esto registrará permanentemente cualquier CURP ya exportado.')) return;
        setImportando(true);
        try {
            const response = await axios.post(`${API_URL}/importar-curps-excel`);
            alert(response.data.mensaje);
            obtenerEstadisticas();
            obtenerHistorial();
        } catch (err) {
            alert(`Error al sincronizar: ${err.response?.data?.detail || err.message}`);
        } finally {
            setImportando(false);
        }
    };

    return (
        <div className="container">
            <header style={{ background: '#f0f9ff', padding: '1.5rem', borderRadius: '1rem', borderBottom: '2px solid #3b82f6', marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <h1 style={{ color: '#1e293b', margin: 0 }}>Buscador Aguascalientes 19</h1>
                    <div className="new-stats-container">
                        <div className="stat-card total-card">
                            <div className="stat-label">TOTAL BASE</div>
                            <div className="stat-value">{(stats.total_base || 0).toLocaleString()}</div>
                        </div>
                        <div className="stat-card used-card">
                            <div className="stat-label">USADOS</div>
                            <div className="stat-value">{(stats.total_usados || 0).toLocaleString()}</div>
                        </div>
                        <div className="stat-card free-card">
                            <div className="stat-label">LIBRES</div>
                            <div className="stat-value">{(stats.disponibles || 0).toLocaleString()}</div>
                        </div>
                    </div>
                </div>
                <p style={{ color: '#475569', margin: 0 }}>Seguimiento inteligente y exportación directa optimizada - Aguascalientes 19</p>
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

            {/* Panel de Administración de CURPs */}
            <section style={{ marginTop: '1.5rem' }}>
                <button
                    className="btn-admin-toggle"
                    onClick={() => { setMostrarAdmin(!mostrarAdmin); if (!mostrarAdmin && !historial) obtenerHistorial(); }}
                >
                    {mostrarAdmin ? '▲ Ocultar Administración de CURPs' : '▼ Administración de CURPs'}
                </button>

                {mostrarAdmin && (
                    <div className="admin-panel">
                        <div className="admin-header">
                            <h3>📊 Historial de Exportaciones</h3>
                            <button
                                className="btn-importar"
                                onClick={handleImportarExcel}
                                disabled={importando}
                            >
                                {importando ? 'Importando...' : '📥 Importar CURPs desde Excel'}
                            </button>
                        </div>

                        {historial && (
                            <>
                                <div className="admin-stat">
                                    <strong>Total CURPs en historial:</strong> {historial.total_historial?.toLocaleString()}
                                </div>

                                {historial.exportaciones_por_fecha?.length > 0 && (
                                    <div className="admin-section">
                                        <h4>Exportaciones por fecha</h4>
                                        <table className="admin-table">
                                            <thead><tr><th>Fecha</th><th>Cantidad</th></tr></thead>
                                            <tbody>
                                                {historial.exportaciones_por_fecha.map((e, i) => (
                                                    <tr key={i}><td>{e.fecha}</td><td>{e.cantidad}</td></tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}

                                {historial.recientes?.length > 0 && (
                                    <div className="admin-section">
                                        <h4>Últimos CURPs exportados</h4>
                                        <table className="admin-table">
                                            <thead><tr><th>CURP</th><th>Fecha</th></tr></thead>
                                            <tbody>
                                                {historial.recientes.map((r, i) => (
                                                    <tr key={i}><td style={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>{r.curp}</td><td>{r.fecha?.split('.')[0]}</td></tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}
            </section>

            <footer style={{ marginTop: '2rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.8rem', paddingBottom: '2rem' }}>
                <p>&copy; 2026 Buscador Aguascalientes 19 | Protección de Unicidad Activa</p>
            </footer>

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

        /* Estilos para los nuevos contadores */
        .new-stats-container {
            display: flex;
            gap: 12px;
            user-select: none;
        }
        .stat-card {
            background: #ffffff !important;
            padding: 8px 16px;
            border-radius: 12px;
            text-align: center;
            min-width: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border: 2px solid #d1d5db;
        }
        .total-card { border-color: #3b82f6 !important; }
        .used-card { border-color: #ef4444 !important; }
        .free-card { border-color: #10b981 !important; }

        .stat-label {
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
            display: block;
        }
        .total-card .stat-label { color: #3b82f6 !important; }
        .used-card .stat-label { color: #ef4444 !important; }
        .free-card .stat-label { color: #10b981 !important; }

        .stat-value {
            font-size: 1.3rem;
            color: #000000 !important;
            font-weight: 900;
            display: block;
            line-height: 1;
        }

        /* Panel de administraci\u00f3n */
        .btn-admin-toggle {
            width: 100%;
            padding: 0.75rem;
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid #334155;
            border-radius: 0.75rem;
            cursor: pointer;
            font-weight: 700;
            font-size: 0.95rem;
            transition: all 0.2s ease;
            letter-spacing: 0.02em;
        }
        .btn-admin-toggle:hover {
            background: #334155;
        }
        .admin-panel {
            margin-top: 0.75rem;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 0.75rem;
            padding: 1.25rem;
        }
        .admin-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .admin-header h3 {
            margin: 0;
            font-size: 1.1rem;
            color: #1e293b;
        }
        .btn-importar {
            padding: 0.6rem 1.2rem;
            background: #7c3aed;
            color: white;
            border: none;
            border-radius: 0.75rem;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }
        .btn-importar:hover {
            background: #6d28d9;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
        }
        .btn-importar:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .admin-stat {
            padding: 0.5rem 0;
            font-size: 0.95rem;
            color: #334155;
        }
        .admin-section {
            margin-top: 1rem;
        }
        .admin-section h4 {
            margin: 0 0 0.5rem;
            color: #475569;
            font-size: 0.9rem;
        }
        .admin-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }
        .admin-table th {
            background: #e2e8f0;
            padding: 0.4rem 0.75rem;
            text-align: left;
            font-weight: 700;
            color: #1e293b;
        }
        .admin-table td {
            padding: 0.35rem 0.75rem;
            border-bottom: 1px solid #e2e8f0;
            color: #334155;
        }
        .admin-table tr:hover td {
            background: #f1f5f9;
        }
      `}</style>
        </div>
    );
}

export default App;
