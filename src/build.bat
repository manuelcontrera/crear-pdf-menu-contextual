@echo off
setlocal
cd /d "%~dp0"

echo Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 goto :error

echo.
echo Compilando CrearPDF.exe...
pyinstaller --onefile --noconsole --icon=crear_pdf.ico --name CrearPDF crear_pdf.py
if errorlevel 1 goto :error

echo.
echo Compilando Instalar.exe...
pyinstaller --onefile --icon=crear_pdf.ico --name Instalar instalar.py
if errorlevel 1 goto :error

echo.
echo Compilando Desinstalar.exe...
pyinstaller --onefile --icon=crear_pdf.ico --name Desinstalar desinstalar.py
if errorlevel 1 goto :error

echo.
echo Copiando ejecutables a la raiz del proyecto...
copy /Y dist\CrearPDF.exe "..\CrearPDF.exe" >nul
copy /Y dist\Instalar.exe "..\Instalar.exe" >nul
copy /Y dist\Desinstalar.exe "..\Desinstalar.exe" >nul

echo.
echo Compilacion completada.
echo Ejecuta Instalar.exe (en la raiz del proyecto) para instalar el boton del menu contextual.
pause
exit /b 0

:error
echo.
echo Ocurrio un error durante la compilacion.
pause
exit /b 1
