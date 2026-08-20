@echo off
setlocal
title Instalar "Crear PDF"
cd /d "%~dp0"

echo ============================================
echo    Instalador de "Crear PDF"
echo ============================================
echo.
echo Este proceso puede tardar unos minutos si
echo necesita instalar Python. No cierres esta
echo ventana hasta que termine.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -Path '%~dp0' -Recurse -File | Unblock-File" >nul 2>&1

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0src\Instalar-CrearPDF.ps1"
set EXITCODE=%ERRORLEVEL%

echo.
if %EXITCODE% EQU 0 (
    echo Listo. La instalacion se completo correctamente.
    echo Ya puedes cerrar esta ventana y probar "Crear PDF"
    echo desde el menu contextual del Explorador de Windows.
) else (
    echo Ocurrio un problema durante la instalacion.
    echo Revisa los mensajes de arriba para mas detalles.
)
echo.
pause
endlocal
