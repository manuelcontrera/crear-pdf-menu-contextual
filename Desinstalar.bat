@echo off
setlocal
title Desinstalar "Crear PDF"
cd /d "%~dp0"

echo ============================================
echo    Desinstalador de "Crear PDF"
echo ============================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -Path '%~dp0' -Recurse -File | Unblock-File" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0src\Desinstalar-CrearPDF.ps1"
set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE% EQU 0 (
    echo Listo. "Crear PDF" se elimino del menu contextual.
) else (
    echo Ocurrio un problema durante la desinstalacion.
    echo Revisa los mensajes de arriba para mas detalles.
)
echo.
pause
endlocal
