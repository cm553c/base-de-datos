@echo off
title Lanzador Buscador BCS
echo ==========================================
echo   Iniciando Sistema de Busqueda BCS 19
echo ==========================================

:: Iniciar Backend
echo [1/2] Iniciando API (FastAPI)...
start "Backend - API BCS" cmd /k "cd /d %~dp0 && if exist .venv\Scripts\activate (call .venv\Scripts\activate) && python main.py > backend.log 2>&1"

:: Esperar un momento para que el backend suba (opcional)
timeout /t 2 /nobreak > nul

:: Iniciar Frontend
echo [2/2] Iniciando Interfaz (React/Vite)...
start "Frontend - Vite" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ==========================================
echo   Servidores en ejecucion.
echo   - Backend: http://localhost:8000
echo   - Frontend: Revisa la consola de Vite
echo ==========================================
echo.
pause
