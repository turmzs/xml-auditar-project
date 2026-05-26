#!/usr/bin/env python3
"""Script para executar o aplicativo GUI de assinador de XMLs."""

import sys
import os

# Adiciona a pasta xmls_gui_app ao path
# Compatível com execução normal e com PyInstaller (layout pode mudar)
if hasattr(sys, "_MEIPASS"):
    base_dir = sys._MEIPASS  # caminho temporário do PyInstaller
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Possíveis layouts dentro do bundle (para garantir que gui_app.py e módulos dele existam no sys.path)
candidates = [
    os.path.join(base_dir, "xmls_gui_app"),  # quando a pasta vem intacta
    base_dir,                                  # quando os .py vão para o topo do bundle
]

for p in candidates:
    if p and p not in sys.path:
        sys.path.insert(0, p)

from gui_app import main

if __name__ == "__main__":
    main()
