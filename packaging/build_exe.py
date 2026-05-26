#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cria o executável do app para consumo pelo Inno Setup.

Gera:
  dist/xmls_gui_app/xmls_gui_app.exe
(para build folder-based, conforme packaging/pyinstaller.spec)

Uso (recomendado):
  python packaging/build_exe.py

Também funciona quando empacotado como um BUILD.exe via PyInstaller.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"[BUILD] Executando: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def main() -> None:
    root = Path(__file__).resolve().parents[1]  # repo root (onde fica run_gui.py)
    spec_path = root / "packaging" / "pyinstaller.spec"
    dist_dir = root / "dist"
    build_dir = root / "build"

    # Limpeza para reduzir chance de artefatos inconsistentes
    if dist_dir.exists():
        print(f"[BUILD] Limpando: {dist_dir}")
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        print(f"[BUILD] Limpando: {build_dir}")
        shutil.rmtree(build_dir)

    # Garante que roda no python certo
    py = sys.executable

    # Instala PyInstaller (e depende do ambiente do usuário)
    # Obs: você pode remover se preferir instalar manualmente.
    req = root / "xmls_gui_app" / "requirements.txt"
    print("[BUILD] Instalando dependências necessárias (se faltarem)...")
    run([py, "-m", "pip", "install", "-r", str(req), "pyinstaller"])

    print("[BUILD] Rodando PyInstaller...")
    run([py, "-m", "PyInstaller", str(spec_path)], cwd=root)

    exe = root / "dist" / "xmls_gui_app" / "xmls_gui_app.exe"
    if not exe.exists():
        raise RuntimeError(f"Build falhou: não encontrei {exe}")

    print(f"[BUILD] OK: gerado em {exe}")


if __name__ == "__main__":
    main()
