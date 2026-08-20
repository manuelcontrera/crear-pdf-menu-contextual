# Crear PDF (menú contextual de Windows)

Agrega la opción **"Crear PDF"** al menú contextual del Explorador de Windows.
Selecciona varias imágenes, documentos de texto y/o PDFs, haz clic derecho →
**Crear PDF**, y se genera un único PDF combinado en la misma carpeta, con el
nombre del primer archivo seleccionado. Todo ocurre sin abrir ninguna ventana,
similar a las Acciones Rápidas de macOS.

## Formatos soportados

- Imágenes: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tif`, `.tiff`, `.webp`
- Documentos de texto: `.txt`, `.docx`
- PDF: `.pdf` (se anexa tal cual)

Los archivos de tipos no soportados dentro de una selección se omiten en
silencio; el resto se combina igual.

## Requisitos

- Windows 10/11
- [Python](https://www.python.org/) 3.9+ (el instalador lo instala automáticamente
  con `winget` si no lo encuentra)

## Instalación

No requiere permisos de administrador; se instala solo para el usuario actual.

### Opción sencilla (recomendada para quien no usa la terminal)

Haz **doble clic en `Instalar.bat`**. Se abre una ventana negra (la terminal)
que hace todo el trabajo por ti: solo tienes que esperar a que termine y
presionar una tecla al final para cerrarla.

> Windows puede mostrar una advertencia tipo **"Windows protegió su PC"**
> por tratarse de un script sin firma digital de un editor reconocido. Es
> normal en scripts personales — haz clic en **"Más información"** →
> **"Ejecutar de todas formas"**.

Para desinstalar, doble clic en `Desinstalar.bat`.

### Opción manual (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File ".\Instalar-CrearPDF.ps1"
```

El instalador:

1. Busca Python en el equipo; si no lo encuentra, lo instala con `winget`.
2. Instala las dependencias de Python necesarias (`img2pdf`, `pypdf`,
   `reportlab`, `python-docx`).
3. Copia el script y el ícono a `%LOCALAPPDATA%\CrearPDF`.
4. Registra la entrada "Crear PDF" en el menú contextual (`HKEY_CURRENT_USER`).

> **Nota (Windows 11):** el nuevo menú contextual oculta las entradas de
> terceros bajo **"Mostrar más opciones"** (o `Shift` + clic derecho para
> saltar directo ahí). Es una limitación del propio Windows 11, no de este
> script.

Si descargaste este proyecto como `.zip`, desbloquéalo antes de instalar
(los archivos descargados de internet quedan marcados y PowerShell bloquea su
ejecución por defecto):

```powershell
Unblock-File .\Instalar-CrearPDF.ps1
```

## Desinstalación

Doble clic en `Desinstalar.bat`, o manualmente:

```powershell
powershell -ExecutionPolicy Bypass -File ".\Desinstalar-CrearPDF.ps1"
```

Elimina la entrada del menú contextual y los archivos instalados en
`%LOCALAPPDATA%\CrearPDF`.

## Personalizar el ícono

Reemplaza `crear_pdf.ico` por tu propio ícono (formato `.ico`, ideal 256×256
con fondo transparente) y vuelve a ejecutar el instalador. Se limpia
automáticamente la caché de íconos de Windows para que el cambio se vea de
inmediato.

## Solución de problemas

Los errores durante la fusión de archivos no se muestran en pantalla; quedan
registrados en:

```
%TEMP%\CrearPDF\errores.log
```
