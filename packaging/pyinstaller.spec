# PyInstaller spec - folder-based build for Tkinter GUI application
# Build output: dist/xmls_gui_app/
#
# Usage:
#   pyinstaller packaging/pyinstaller.spec

# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

hiddenimports = []
# PyKCS11 can be imported dynamically depending on presence; ensure it is bundled when installed.
hiddenimports += [
    "PyKCS11",
    "cryptography",
]

# Ensure modules imported dynamically are included (safe for most cases)
hiddenimports += collect_submodules("cryptography")
hiddenimports += collect_submodules("signxml")

# Collect any data files from dependencies (usually none required, but harmless)
datas = []
datas += collect_data_files("cryptography")
datas += collect_data_files("signxml")

# IMPORTANTE:
# O PyInstaller pode executar o .spec em contexto onde __file__ não existe.
# Como o BAT faz `cd /d "%~dp0\.."` (root do projeto), usamos cwd.
ENTRY = os.path.join(os.path.abspath(os.getcwd()), "packaging", "entry_gui.py")

a = Analysis(
    [ENTRY],
    pathex=[os.path.abspath(os.getcwd()), os.path.join(os.path.abspath(os.getcwd()), "xmls_gui_app")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Tkinter apps should be windowed (no console)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="xmls_gui_app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="xmls_gui_app",
)
