# -*- coding: utf-8 -*-
"""
Desinstalador de doble clic: quita el boton "Combinar en un solo PDF"
del menu contextual y borra los archivos instalados para el usuario actual.
"""

import os
import shutil
import winreg

SHELL_KEY_PATH = r"Software\Classes\*\shell\CombinarEnPDF"


def delete_key_tree(root, path):
    try:
        key = winreg.OpenKey(root, path, 0, winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        return
    while True:
        try:
            subkey_name = winreg.EnumKey(key, 0)
        except OSError:
            break
        delete_key_tree(root, path + "\\" + subkey_name)
    winreg.CloseKey(key)
    winreg.DeleteKey(root, path)


def main():
    print("Desinstalando 'Combinar en un solo PDF'...")
    print()

    try:
        delete_key_tree(winreg.HKEY_CURRENT_USER, SHELL_KEY_PATH)
        print("Entrada del menu contextual eliminada.")
    except Exception as e:
        print("Aviso: no se pudo eliminar la entrada del registro: {}".format(e))

    install_dir = os.path.join(os.environ["LOCALAPPDATA"], "CrearPDFMenu")
    if os.path.isdir(install_dir):
        try:
            shutil.rmtree(install_dir)
            print("Archivos instalados eliminados.")
        except Exception as e:
            print("Aviso: no se pudieron eliminar todos los archivos: {}".format(e))

    print()
    print("Desinstalacion completada.")
    input("\nPresiona Enter para salir...")


if __name__ == "__main__":
    main()
