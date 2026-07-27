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


def main():
    """Inicializa logging e GUI."""
    import logging
    from logging_setup import setup_logging, get_logger

    # Em GUI: console OFF por padrão (logs só na GUI + arquivo)
    # Para ativar logs no console: XML_AUDITAR_LOG_CONSOLE=1
    # Para ativar DEBUG: XML_AUDITAR_LOG_LEVEL=DEBUG
    env_console = os.environ.get("XML_AUDITAR_LOG_CONSOLE", "").lower()
    env_level = os.environ.get("XML_AUDITAR_LOG_LEVEL", "INFO").upper()

    enable_console = env_console in ("1", "true", "yes")
    setup_logging(level=env_level, enable_console=enable_console)

    logger = get_logger(__name__)
    logger.info("XML Auditar iniciado (level=%s, console=%s)", env_level, enable_console)

    # Inicia a GUI
    import tkinter as tk
    from gui_app import XMLSignerGUI

    root = tk.Tk()
    # XMLSignerGUI pode reconfigurar logging internamente se quiser
    XMLSignerGUI(root, log_level=env_level)
    root.mainloop()


if __name__ == "__main__":
    main()