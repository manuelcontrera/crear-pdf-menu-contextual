# Combinar en PDF (menú contextual de Windows)

Agrega un botón **"Combinar en un solo PDF"** al menú contextual del
Explorador de Windows. Selecciona varios archivos (imágenes, PDF o TXT),
clic derecho, y se genera un único PDF con todos ellos. El orden de las
páginas se calcula siempre por nombre de archivo (orden alfanumérico
natural), sin depender del orden en que Windows entrega la selección.

## Instalación

1. Descarga `CrearPDF.exe` e `Instalar.exe` y colócalos en la misma carpeta.
2. Doble clic en **`Instalar.exe`**.
3. Selecciona varios archivos compatibles → clic derecho → **"Combinar en un
   solo PDF"**.

Se instala solo para tu usuario (no requiere permisos de administrador) y no
modifica nada fuera del registro de Windows (`HKCU`) y la carpeta
`%LOCALAPPDATA%\CrearPDFMenu`.

## Desinstalación

Doble clic en **`Desinstalar.exe`**. Quita el botón del menú contextual y
borra los archivos instalados.

## Compilar desde el código fuente

Requiere Python 3.9+.

```bash
cd src
build.bat
```

Genera `CrearPDF.exe`, `Instalar.exe` y `Desinstalar.exe` en la raíz del
proyecto.
