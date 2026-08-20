<#
Elimina la opcion "Crear PDF" del menu contextual del Explorador de Windows
y borra los archivos instalados en %LOCALAPPDATA%\CrearPDF.
#>

$ErrorActionPreference = "SilentlyContinue"

Remove-Item -Path "Registry::HKEY_CURRENT_USER\Software\Classes\*\shell\CrearPDF" -Recurse -Force
Remove-Item -Path (Join-Path $env:LOCALAPPDATA "CrearPDF") -Recurse -Force

Write-Host "La opcion 'Crear PDF' se ha desinstalado del menu contextual."
