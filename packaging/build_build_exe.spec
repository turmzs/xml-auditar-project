# PyInstaller spec para empacotar o BUILD.exe (gerador do seu app)
# Saída: dist/build_exe/build_exe.exe (ou similar)

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ["packaging/build_exe.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="BUILD_xmls_gui_app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # troque para True se quiser janela de console ao rodar
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="build_exe",
)
