# utils.py
import sys
import os

def resource_path(relative_path):
    """
    Retorna o caminho absoluto do recurso, funcionando tanto no desenvolvimento
    quanto no executável criado pelo PyInstaller.
    """
    try:
        # Se estiver rodando como .exe do PyInstaller
        base_path = sys._MEIPASS
    except AttributeError:
        # Se estiver rodando como script normal (dev)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
