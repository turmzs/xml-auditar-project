# Empacotamento (PyInstaller + Inno Setup)

## 1) Pré-requisitos
- Python 3.10+
- PyInstaller
- Inno Setup Compiler (para compilar o `.iss`)

## 2) Build do executável (folder-based)

### Opção A (manual)
No root do projeto (onde existe `run_gui.py`):

```bash
pip install -r xmls_gui_app/requirements.txt pyinstaller
pyinstaller packaging/pyinstaller.spec
```

Resultado esperado:
- `dist/xmls_gui_app/` contendo `xmls_gui_app.exe` e os arquivos necessários.

### Opção B (via BUILD.exe)
Você pode gerar um executável auxiliar (“BUILD.exe”) que cria o `dist/xmls_gui_app/`.

1) Gere o BUILD.exe (1 vez):
```bash
pyinstaller packaging/build_build_exe.spec
```

2) Rode o BUILD.exe:
- encontre o executável em `dist/build_exe/`
- execute `dist/build_exe/BUILD_xmls_gui_app.exe` (nome pode variar conforme PyInstaller)

Ele fará:
- limpeza de `dist/` e `build/`
- instalação de dependências (requirements do app + pyinstaller)
- build do app usando `packaging/pyinstaller.spec`
- validação da existência de `dist/xmls_gui_app/xmls_gui_app.exe`

## 3) Build do instalador (Inno Setup)
- Abra `packaging/InnoSetup/InstallXmlsAssinador.iss` no **Inno Setup Compiler**
- Compile

Resultado:
- um instalador gerado dentro da pasta configurada pelo Inno Setup (ex.: `packaging/dist_inno/`)

## 4) Observações importantes (A3 / PKCS#11)
- O driver PKCS#11 (DLL) é selecionado pelo usuário dentro do app.
- Não embutimos drivers proprietários no executável/instalador.
