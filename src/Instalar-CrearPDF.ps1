<#
Instala la opcion "Crear PDF" en el menu contextual del Explorador de Windows.

No requiere permisos de administrador: se instala solo para el usuario actual
(HKEY_CURRENT_USER). Si no encuentra Python en el equipo, intenta instalarlo
automaticamente usando winget (Instalador de aplicaciones de Windows), que
viene incluido por defecto en Windows 10/11 actualizados.

Al seleccionar varios archivos (imagenes, .txt, .docx, .pdf) y elegir
"Crear PDF", se genera un unico PDF en la misma carpeta, con el nombre
del primer archivo seleccionado. Todo ocurre sin mostrar ninguna ventana.
#>

$ErrorActionPreference = "Stop"

function Find-PythonW {
    $cmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @()
    $candidates += Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\pythonw.exe" -ErrorAction SilentlyContinue
    $candidates += Get-ChildItem "$env:ProgramFiles\Python3*\pythonw.exe" -ErrorAction SilentlyContinue
    $candidates += Get-ChildItem "${env:ProgramFiles(x86)}\Python3*\pythonw.exe" -ErrorAction SilentlyContinue

    if ($candidates.Count -gt 0) {
        return ($candidates | Sort-Object FullName -Descending | Select-Object -First 1).FullName
    }
    return $null
}

function Install-PythonViaWinget {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        Write-Error "No se encontro 'winget' en este equipo. Actualiza 'Instalador de aplicaciones' desde la Microsoft Store, o instala Python manualmente desde python.org, y vuelve a ejecutar este script."
        exit 1
    }

    $packageIds = @("Python.Python.3.13", "Python.Python.3.12", "Python.Python.3.11")
    foreach ($id in $packageIds) {
        Write-Host "Instalando Python ($id) con winget, esto puede tardar unos minutos..."
        & winget install --id $id -e --scope user --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        Write-Host "No se pudo instalar $id, probando la siguiente version disponible..."
    }
    return $false
}

$pythonw = Find-PythonW
if (-not $pythonw) {
    Write-Host "No se encontro Python instalado. Se intentara instalar automaticamente con winget..."
    $ok = Install-PythonViaWinget
    if (-not $ok) {
        Write-Error "No se pudo instalar Python automaticamente. Instalalo manualmente desde python.org (marcando 'Add python.exe to PATH') y vuelve a ejecutar este script."
        exit 1
    }
    $pythonw = Find-PythonW
    if (-not $pythonw) {
        Write-Error "Python se instalo pero no se pudo localizar pythonw.exe. Cierra esta ventana, abre una nueva terminal (para refrescar el PATH) y vuelve a ejecutar este script."
        exit 1
    }
}
$pythonExe = Join-Path (Split-Path $pythonw) "python.exe"
Write-Host "Usando Python en: $pythonExe"

$installDir = Join-Path $env:LOCALAPPDATA "CrearPDF"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

$scriptSource = Join-Path $PSScriptRoot "crear_pdf.py"
if (-not (Test-Path $scriptSource)) {
    Write-Error "No se encontro crear_pdf.py junto a este instalador."
    exit 1
}
$scriptDest = Join-Path $installDir "crear_pdf.py"
Copy-Item -Path $scriptSource -Destination $scriptDest -Force

$iconSource = Join-Path $PSScriptRoot "crear_pdf.ico"
$iconDest = Join-Path $installDir "crear_pdf.ico"
if (Test-Path $iconSource) {
    Copy-Item -Path $iconSource -Destination $iconDest -Force
} else {
    $iconDest = $pythonw
}

# Comprobar/instalar dependencias necesarias
$checkImports = [ordered]@{
    "img2pdf"     = "img2pdf"
    "pypdf"       = "pypdf"
    "reportlab"   = "reportlab"
    "python-docx" = "docx"
}
foreach ($pkg in $checkImports.Keys) {
    $importName = $checkImports[$pkg]
    & $pythonExe -c "import $importName" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Instalando dependencia faltante: $pkg ..."
        & $pythonExe -m pip install --quiet $pkg
        & $pythonExe -c "import $importName" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "No se pudo instalar '$pkg'. Revisa tu conexion a internet y vuelve a ejecutar este script."
        }
    }
}

# Registrar la entrada de menu contextual (solo para el usuario actual)
# OJO: %1 NO se envuelve en comillas propias. Con MultiSelectModel=Document,
# Windows sustituye %1 por una lista de rutas ya entrecomilladas (una por
# archivo seleccionado); si lo envolvemos ademas con nuestras propias
# comillas, el resultado queda mal formado (comillas duplicadas) y Windows
# puede truncar o perder archivos de la seleccion al interpretar la linea de
# comandos. Para una sola ruta, Windows ya la entrecomilla si tiene espacios.
$command = '"' + $pythonw + '" "' + $scriptDest + '" %1'

$regBase = "Registry::HKEY_CURRENT_USER\Software\Classes\*\shell\CrearPDF"
New-Item -Path $regBase -Force | Out-Null
Set-ItemProperty -Path $regBase -Name "(default)" -Value "Crear PDF"
Set-ItemProperty -Path $regBase -Name "MultiSelectModel" -Value "Document"
Set-ItemProperty -Path $regBase -Name "Icon" -Value $iconDest

$regCommand = "$regBase\command"
New-Item -Path $regCommand -Force | Out-Null
Set-ItemProperty -Path $regCommand -Name "(default)" -Value $command

# Windows cachea agresivamente los iconos del menu contextual: si el .ico
# cambio respecto a una instalacion previa, forzamos su reconstruccion para
# que el nuevo icono se vea de inmediato en vez de quedar el anterior.
try {
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    & ie4uinit.exe -ClearIconCache
    Remove-Item "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_*.db" -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:LOCALAPPDATA\IconCache.db" -Force -ErrorAction SilentlyContinue
} finally {
    Start-Sleep -Seconds 1
    Start-Process explorer
}

Write-Host ""
Write-Host "Listo. La opcion 'Crear PDF' ya deberia aparecer al hacer clic derecho"
Write-Host "sobre uno o varios archivos en el Explorador de Windows"
Write-Host "(en Windows 11 puede estar bajo 'Mostrar mas opciones')."
Write-Host ""
Write-Host "Formatos soportados: imagenes (jpg, png, bmp, gif, tif, webp), .txt, .docx y .pdf"
Write-Host "Si algo falla, se registra en: $env:TEMP\CrearPDF\errores.log"
