@echo off
setlocal enabledelayedexpansion

REM Garante que estamos no root do projeto
cd /d "%~dp0\.."

echo [BUILD_XMLS_GUI_APP] Limpando pastas...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo [BUILD_XMLS_GUI_APP] Criando pasta dist...
mkdir dist

echo [BUILD_XMLS_GUI_APP] Executando PyInstaller...
python -m PyInstaller packaging\pyinstaller.spec

echo.
echo [BUILD_XMLS_GUI_APP] Concluido.
echo Verifique: dist\xmls_gui_app\xmls_gui_app.exe
pause
