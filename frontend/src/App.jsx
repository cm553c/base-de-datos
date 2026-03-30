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

    useEffect(() => {
        const timeoutId = setTimeout(() => buscar(), 400);
        return () => clearTimeout(timeoutId);
    }, [query, buscar]);

    const handleExportar = async (soloCurp = false) => {
        setExportando(true);
        try {
            // Usamos un método de descarga directo para que el navegador use 
            // los encabezados del servidor (filename y extension) correctamente.
            const params = new URLSearchParams({
                q: query || '',
                sexo: filtros.sexo,
                edad: filtros.edad,
                limite: limite,
                solo_curp: soloCurp
            });

            // Redirigir a la URL de exportación para que el navegador maneje la descarga nativamente
            window.location.href = `${API_URL}/exportar?${params.toString()}`;

            // Como no podemos saber cuándo termina con este método, desactivamos el estado después de un momento
            setTimeout(() => setExportando(false), 2000);

        } catch (err) {
            const detalle = err.response?.data?.detail || err.message || 'Error desconocido';
            alert(`Error: ${detalle}`);
            setExportando(false);
        }
    };

    const handleLimpiarHistorial = async () => {
        if (!confirm('¿Estás seguro? Esto borrará el registro de qué datos has mandado antes (permitirá repetirlos).')) return;
        try {
            const response = await axios.post(`${API_URL}/limpiar-historial`);
            alert(response.data.mensaje);
        } catch (err) {
            alert('Error al conectar con el servidor.');
        }
    };

    return (
        <div className="container">
            <header>
                <h1>Buscador BCS 19 <span style={{ fontSize: '0.8rem', verticalAlign: 'middle', background: '#e2e8f0', padding: '2px 8px', borderRadius: '12px', color: '#475569' }}>v2.1</span></h1>
                <p style={{ color: 'var(--text-muted)' }}>Seguimiento inteligente y exportación sin duplicados</p>
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
                <span>{total} registros encontrados | Seguimiento activo</span>
                <button onClick={handleLimpiarHistorial} className="btn-limpiar">
                    🔄 Resetear historial para pruebas
                </button>
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
