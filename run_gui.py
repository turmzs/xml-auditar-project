#!/usr/bin/env python3
"""Script para executar o aplicativo GUI de assinador de XMLs."""

import sys
import os

# Adiciona a pasta xmls_gui_app ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "xmls_gui_app"))

from gui_app import main

if __name__ == "__main__":
    main()
