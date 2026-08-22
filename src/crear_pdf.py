# -*- coding: utf-8 -*-
"""
Combina archivos seleccionados (imagenes, PDF y TXT) en un solo PDF.

Se invoca desde el menu contextual de Windows con la lista de archivos
seleccionados como argumentos. El orden de las paginas NO depende del
orden en que Windows entrega los archivos: siempre se recalcula con un
orden alfanumerico natural basado en el nombre de archivo.
"""

import ctypes
import io
import os
import re
import sys
import textwrap
import traceback
from datetime import datetime

from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}
PDF_EXTS = {".pdf"}
TEXT_EXTS = {".txt"}
COMPATIBLE_EXTS = IMAGE_EXTS | PDF_EXTS | TEXT_EXTS

LOG_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.environ.get("TEMP", ".")), "CrearPDFMenu")
LOG_PATH = os.path.join(LOG_DIR, "errores.log")

MB_ICONINFORMATION = 0x40
MB_ICONWARNING = 0x30
MB_ICONERROR = 0x10


def show_message(text, title="Combinar en PDF", icon=MB_ICONINFORMATION):
    try:
        ctypes.windll.user32.MessageBoxW(0, text, title, icon)
    except Exception:
        pass


def log_exception(context):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("\n[{}] {}\n".format(datetime.now().isoformat(), context))
            f.write(traceback.format_exc())
    except Exception:
        pass


def natural_sort_key(path):
    """Orden alfanumerico natural por nombre de archivo (2 antes que 10)."""
    stem = os.path.splitext(os.path.basename(path))[0]
    parts = re.split(r"(\d+)", stem)
    key = []
    for part in parts:
        if part.isdigit():
            key.append((1, int(part)))
        else:
            key.append((0, part.lower()))
    return key


def normalize_image(im):
    im = ImageOps.exif_transpose(im)
    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    if has_alpha:
        im = im.convert("RGBA")
        background = Image.new("RGB", im.size, (255, 255, 255))
        background.paste(im, mask=im.split()[-1])
        im = background
    elif im.mode != "RGB":
        im = im.convert("RGB")
    return im


def pages_from_pdf_bytes(writer, buf):
    buf.seek(0)
    reader = PdfReader(buf)
    for page in reader.pages:
        writer.add_page(page)


def append_pdf(writer, path):
    reader = PdfReader(path)
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            pass
    for page in reader.pages:
        writer.add_page(page)


def append_image(writer, path):
    with Image.open(path) as im:
        n_frames = getattr(im, "n_frames", 1)
        frames = []
        if im.format == "TIFF" and n_frames > 1:
            for i in range(n_frames):
                im.seek(i)
                frames.append(normalize_image(im.copy()))
        else:
            frames.append(normalize_image(im))

    for frame in frames:
        buf = io.BytesIO()
        frame.save(buf, format="PDF")
        pages_from_pdf_bytes(writer, buf)


def wrap_line(line, width):
    if line == "":
        return [""]
    return textwrap.wrap(line, width=width, break_long_words=True, break_on_hyphens=False) or [""]


def append_text(writer, path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    page_w, page_h = A4
    margin = 20 * mm
    font_size = 10
    line_height = font_size * 1.2
    max_width = page_w - 2 * margin
    max_chars_per_line = max(10, int(max_width / (font_size * 0.6)))

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Courier", font_size)
    y = page_h - margin

    lines = content.splitlines() or [""]
    for line in lines:
        for wline in wrap_line(line, max_chars_per_line):
            if y < margin:
                c.showPage()
                c.setFont("Courier", font_size)
                y = page_h - margin
            c.drawString(margin, y, wline)
            y -= line_height
    c.save()
    pages_from_pdf_bytes(writer, buf)


def build_output_path(folder):
    base = "PDF_Combinado"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = os.path.join(folder, "{}_{}.pdf".format(base, timestamp))
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(folder, "{}_{}_{}.pdf".format(base, timestamp, counter))
        counter += 1
    return candidate


def main():
    args = sys.argv[1:]
    selected = [a for a in args if os.path.isfile(a)]

    if not selected:
        show_message("No se selecciono ningun archivo valido.", icon=MB_ICONWARNING)
        return

    compatible = []
    skipped = []
    for path in selected:
        ext = os.path.splitext(path)[1].lower()
        if ext in COMPATIBLE_EXTS:
            compatible.append(path)
        else:
            skipped.append(path)

    if not compatible:
        show_message(
            "Ninguno de los archivos seleccionados es compatible.\n\n"
            "Formatos admitidos: imagenes (jpg, png, bmp, gif, tiff, webp), PDF y TXT.",
            icon=MB_ICONWARNING,
        )
        return

    compatible.sort(key=natural_sort_key)

    writer = PdfWriter()
    errors = []
    added = []
    for path in compatible:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in PDF_EXTS:
                append_pdf(writer, path)
            elif ext in IMAGE_EXTS:
                append_image(writer, path)
            elif ext in TEXT_EXTS:
                append_text(writer, path)
            added.append(path)
        except Exception as e:
            errors.append("{}: {}".format(os.path.basename(path), e))
            log_exception("Error procesando: {}".format(path))

    if not added:
        show_message(
            "No se pudo procesar ningun archivo.\n\n" + "\n".join(errors[:10]),
            icon=MB_ICONERROR,
        )
        return

    out_dir = os.path.dirname(os.path.abspath(compatible[0]))
    out_path = build_output_path(out_dir)

    try:
        with open(out_path, "wb") as f:
            writer.write(f)
    except Exception as e:
        log_exception("Error guardando: {}".format(out_path))
        show_message("No se pudo guardar el PDF:\n{}".format(e), icon=MB_ICONERROR)
        return

    msg_lines = [
        "PDF creado correctamente:",
        out_path,
        "",
        "Archivos incluidos: {}".format(len(added)),
    ]
    if skipped:
        msg_lines.append("Archivos ignorados (formato no compatible): {}".format(len(skipped)))
    if errors:
        msg_lines.append("Archivos con error (no se pudieron incluir): {}".format(len(errors)))
        msg_lines.append("Detalle en: {}".format(LOG_PATH))

    show_message(
        "\n".join(msg_lines),
        icon=MB_ICONWARNING if (skipped or errors) else MB_ICONINFORMATION,
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_exception("Error no controlado en main()")
        show_message(
            "Ocurrio un error inesperado:\n{}\n\nDetalle en: {}".format(e, LOG_PATH),
            icon=MB_ICONERROR,
        )
