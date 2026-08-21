r"""
Combina imagenes, documentos de texto (.txt, .docx) y PDFs en un unico PDF.
Pensado para ejecutarse sin ventanas (via pythonw.exe) desde el menu contextual
del Explorador de archivos de Windows.

Uso: pythonw.exe crear_pdf.py "archivo1" "archivo2" ...

El PDF resultante se guarda en la misma carpeta que el primer archivo,
con el nombre de ese primer archivo (extension .pdf).

Los errores no se muestran en pantalla: quedan registrados en
%TEMP%\CrearPDF\errores.log
"""

import hashlib
import io
import os
import re
import sys
import textwrap
import time
import traceback
from datetime import datetime

import img2pdf
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
TEXT_EXTS = {".txt"}
DOCX_EXTS = {".docx"}
PDF_EXTS = {".pdf"}

LOG_DIR = os.path.join(os.environ.get("TEMP", "."), "CrearPDF")
LOG_FILE = os.path.join(LOG_DIR, "errores.log")


def log_error(msg):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {msg}\n")
    except Exception:
        pass


_NUM_RE = re.compile(r"(\d+)")


def natural_sort_key(path):
    """Ordena por nombre de archivo de forma 'natural': 1, 2, 3, 10 en vez de
    1, 10, 2, 3 (que es como quedaria con un orden alfabetico estricto)."""
    name = os.path.basename(path).lower()
    return [int(tok) if tok.isdigit() else tok for tok in _NUM_RE.split(name)]


def render_lines_to_pdf_bytes(lines):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    margin = 2 * cm
    line_height = 14
    y = height - margin
    c.setFont("Helvetica", 11)

    def new_page():
        nonlocal y
        c.showPage()
        c.setFont("Helvetica", 11)
        y = height - margin

    for raw_line in lines:
        wrapped = textwrap.wrap(raw_line, 95) or [""]
        for line in wrapped:
            if y < margin:
                new_page()
            c.drawString(margin, y, line)
            y -= line_height

    c.save()
    return buf.getvalue()


def text_to_pdf_bytes(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = [ln.rstrip("\n") for ln in f]
    return render_lines_to_pdf_bytes(lines)


def docx_to_pdf_bytes(path):
    from docx import Document

    doc = Document(path)
    lines = [p.text for p in doc.paragraphs]
    return render_lines_to_pdf_bytes(lines)


def image_to_pdf_bytes(path):
    return img2pdf.convert(path)


def unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f"{base} ({i}){ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1


BATCH_DIR = os.path.join(os.environ.get("TEMP", "."), "CrearPDF", "batches")
# BATCH_MIN_WAIT_SECONDS: espera minima OBLIGATORIA antes de considerar
# cerrar el lote, sin importar si todavia no ha llegado ningun rezagado. Es
# necesaria porque, con cachés de disco frias, varios procesos de Python
# lanzados casi a la vez pueden tardar mas de un segundo en terminar sus
# imports antes de alcanzar a anotarse en la lista compartida; sin este piso,
# el lider podria ver "silencio" desde el primer instante (porque nadie mas
# se ha anotado *todavia*) y cerrar el lote de forma prematura, perdiendo
# archivos.
# BATCH_DEBOUNCE_SECONDS: tiempo de silencio (sin cambios) requerido, una vez
# superado el piso anterior, para dar por terminada la seleccion.
# BATCH_MAX_WAIT_SECONDS: tope absoluto de espera por si algo se traba.
BATCH_MIN_WAIT_SECONDS = 4.0
BATCH_DEBOUNCE_SECONDS = 1.5
BATCH_MAX_WAIT_SECONDS = 25.0
BATCH_APPEND_RETRY_SECONDS = 5.0


def _append_with_retry(path, line, retry_seconds=BATCH_APPEND_RETRY_SECONDS):
    deadline = time.time() + retry_seconds
    while True:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            return
        except OSError:
            if time.time() >= deadline:
                raise
            time.sleep(0.1)


def collect_batch(argv_files):
    """Windows Explorer (y varios exploradores de terceros) a veces invocan
    el comando una vez por cada archivo seleccionado en lugar de una sola vez
    con todos. Aqui agrupamos esas invocaciones casi-simultaneas (misma
    carpeta, a milisegundos/segundos de diferencia) en un unico lote.

    Solo el primer proceso en tomar el "lock" (el lider) hace la fusion; el
    resto solo deja su archivo anotado en la lista compartida y termina.

    Para evitar perder archivos por una condicion de carrera entre "el lider
    deja de esperar y lee la lista" y "un rezagado todavia esta anotandose",
    el cierre del lote es atomico: se renombra el archivo de pendientes antes
    de leerlo, asi cualquier invocacion que llegue despues simplemente
    empieza un lote nuevo en vez de corromper el que ya se esta procesando.
    """
    if len(argv_files) != 1:
        return argv_files

    folder = os.path.dirname(argv_files[0]) or "."
    key = hashlib.md5(os.path.abspath(folder).lower().encode("utf-8")).hexdigest()
    os.makedirs(BATCH_DIR, exist_ok=True)
    pending_path = os.path.join(BATCH_DIR, key + ".pending")
    lock_path = os.path.join(BATCH_DIR, key + ".lock")

    _append_with_retry(pending_path, argv_files[0])

    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        return None  # ya hay un lider procesando este lote

    start = time.time()
    last_size = -1
    stable_since = start
    deadline = start + BATCH_MAX_WAIT_SECONDS
    while time.time() < deadline:
        time.sleep(0.2)
        try:
            size = os.path.getsize(pending_path)
        except OSError:
            size = last_size
        now = time.time()
        if size != last_size:
            last_size = size
            stable_since = now
        elif now - start >= BATCH_MIN_WAIT_SECONDS and now - stable_since >= BATCH_DEBOUNCE_SECONDS:
            break

    closed_path = pending_path + ".closed"
    try:
        os.replace(pending_path, closed_path)
    except OSError:
        closed_path = pending_path

    try:
        with open(closed_path, "r", encoding="utf-8") as f:
            files = [ln.strip() for ln in f if ln.strip()]
    finally:
        for p in (closed_path, lock_path):
            try:
                os.remove(p)
            except OSError:
                pass

    seen = set()
    result = []
    for f in files:
        if f not in seen:
            seen.add(f)
            result.append(f)
    return result


def main():
    args = collect_batch(sys.argv[1:])
    if not args:
        return
    valid_files = [a for a in args if os.path.isfile(a)]
    if not valid_files:
        log_error("No se recibieron archivos validos.")
        return

    valid_files = sorted(valid_files, key=natural_sort_key)
    log_error("Orden final: " + " | ".join(os.path.basename(p) for p in valid_files))

    first = valid_files[0]
    folder = os.path.dirname(first) or "."
    base_name = os.path.splitext(os.path.basename(first))[0]
    final_output = os.path.join(folder, base_name + ".pdf")

    writer = PdfWriter()
    open_streams = []
    used_any = False

    for path in valid_files:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in PDF_EXTS:
                stream = open(path, "rb")
                open_streams.append(stream)
                reader = PdfReader(stream)
                for page in reader.pages:
                    writer.add_page(page)
                used_any = True
            elif ext in IMAGE_EXTS:
                pdf_bytes = image_to_pdf_bytes(path)
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
                used_any = True
            elif ext in TEXT_EXTS:
                pdf_bytes = text_to_pdf_bytes(path)
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
                used_any = True
            elif ext in DOCX_EXTS:
                pdf_bytes = docx_to_pdf_bytes(path)
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for page in reader.pages:
                    writer.add_page(page)
                used_any = True
            else:
                log_error(f"Tipo no soportado, se omite: {path}")
        except Exception:
            log_error(f"Error procesando {path}:\n{traceback.format_exc()}")

    if not used_any:
        log_error("Ningun archivo valido para combinar (todos fallaron o no son soportados).")
        for s in open_streams:
            s.close()
        return

    tmp_output = final_output + ".tmp"
    try:
        with open(tmp_output, "wb") as f:
            writer.write(f)
    except Exception:
        log_error(f"Error al generar el PDF combinado:\n{traceback.format_exc()}")
        for s in open_streams:
            s.close()
        if os.path.exists(tmp_output):
            try:
                os.remove(tmp_output)
            except Exception:
                pass
        return
    finally:
        writer.close()
        for s in open_streams:
            try:
                s.close()
            except Exception:
                pass

    try:
        input_abspaths = {os.path.abspath(p) for p in valid_files}
        if os.path.exists(final_output) and os.path.abspath(final_output) not in input_abspaths:
            final_output = unique_path(final_output)
        os.replace(tmp_output, final_output)
    except Exception:
        log_error(f"Error al guardar el PDF final:\n{traceback.format_exc()}")
        if os.path.exists(tmp_output):
            try:
                os.remove(tmp_output)
            except Exception:
                pass


if __name__ == "__main__":
    main()
