import os
import sys

# Este arquivo é o "entrypoint" para PyInstaller.
# Ele garante que os módulos (gui_app.py, certificate_handler.py, xml_processor.py)
# sejam importáveis independentemente do layout do bundle.

def _add_xmls_gui_app_to_path():
    # Quando empacotado, o PyInstaller usa _MEIPASS como diretório temporário
    base_dir = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))

    candidates = [
        os.path.join(base_dir, "xmls_gui_app"),  # caso a pasta venha intacta
        os.path.join(base_dir, "..", "xmls_gui_app"),  # caso o base_dir seja packaging/
        base_dir,  # fallback
    ]

    for p in candidates:
        p_norm = os.path.abspath(p)
        if os.path.isdir(p_norm) and p_norm not in sys.path:
            sys.path.insert(0, p_norm)

_add_xmls_gui_app_to_path()

from gui_app import main  # noqa: E402

if __name__ == "__main__":
    main()
