# -*- coding: utf-8 -*-
"""
Instalador de doble clic: registra el boton "Combinar en un solo PDF"
en el menu contextual de Windows para el usuario actual (HKCU, sin admin).

Debe ejecutarse desde la misma carpeta donde esta CrearPDF.exe.
"""

import os
import shutil
import sys
import winreg

SHELL_KEY_PATH = r"Software\Classes\*\shell\CombinarEnPDF"
COMMAND_KEY_PATH = SHELL_KEY_PATH + r"\command"


def base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def fail(message):
    print()
    print("ERROR: " + message)
    input("\nPresiona Enter para salir...")
    sys.exit(1)


def main():
    print("Instalando 'Combinar en un solo PDF' en el menu contextual...")
    print()

    exe_source = os.path.join(base_dir(), "CrearPDF.exe")
    if not os.path.isfile(exe_source):
        fail(
            "no se encontro CrearPDF.exe junto a este instalador.\n"
            "Esperado en: {}".format(exe_source)
        )

    install_dir = os.path.join(os.environ["LOCALAPPDATA"], "CrearPDFMenu")
    try:
        os.makedirs(install_dir, exist_ok=True)
        exe_dest = os.path.join(install_dir, "CrearPDF.exe")
        shutil.copy2(exe_source, exe_dest)
    except Exception as e:
        fail("no se pudo copiar el ejecutable.\n{}".format(e))

    try:
        shell_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, SHELL_KEY_PATH)
        winreg.SetValueEx(shell_key, "", 0, winreg.REG_SZ, "Combinar en un solo PDF")
        winreg.SetValueEx(shell_key, "Icon", 0, winreg.REG_SZ, '"{}",0'.format(exe_dest))
        winreg.SetValueEx(shell_key, "MultiSelectModel", 0, winreg.REG_SZ, "Player")
        winreg.CloseKey(shell_key)

        command_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, COMMAND_KEY_PATH)
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, '"{}" "%1"'.format(exe_dest))
        winreg.CloseKey(command_key)
    except Exception as e:
        fail("no se pudo registrar el menu contextual.\n{}".format(e))

    print("Instalacion completada correctamente.")
    print()
    print("Selecciona varios archivos compatibles (imagenes, PDF, TXT),")
    print("clic derecho y elige 'Combinar en un solo PDF'.")
    input("\nPresiona Enter para salir...")


if __name__ == "__main__":
    main()
