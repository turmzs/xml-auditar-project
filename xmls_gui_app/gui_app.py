"""Interface GUI Tkinter para assinador de XMLs."""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import queue
import xml.etree.ElementTree as ET
from datetime import datetime
from certificate_handler import CertificateA1, CertificateA3
from xml_processor import XMLProcessor
from logging_setup import setup_logging, get_logger, get_gui_handler
from config import (
    WINDOW_TITLE,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    STATUS_DESCONECTADO,
    STATUS_CONECTADO_A1,
    STATUS_CONECTADO_A3,
    STATUS_PROCESSANDO,
    STATUS_CONCLUIDO,
    LOG_SEPARATOR,
)

# Tipos de mensagem na fila thread->GUI
MSG_LOG = "log"
MSG_DONE_OK = "done_ok"
MSG_DONE_ERR = "done_err"

logger = get_logger(__name__)


class XMLSignerGUI:
    """Interface gráfica para assinador de XMLs."""

    def __init__(self, root, log_level="INFO"):
        # Configura logging estruturado para toda a aplicação.
        # O GuiLogHandler é instalado e fica disponível via get_gui_handler().
        setup_logging(level=log_level)
        self.logger = logger
        self.gui_log_handler = get_gui_handler()

        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(True, True)

        self.cert_type = tk.StringVar(value="A1")
        self.cert_a1 = CertificateA1()
        self.cert_a3 = CertificateA3()

        self.pfx_path = tk.StringVar()
        self.pfx_password = tk.StringVar()
        self.dll_path = tk.StringVar()
        self.a3_pin = tk.StringVar()
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.xml_type = tk.StringVar(value="PREFEITURA")
        self.aliquota = tk.StringVar(value="0.0365")

        # Fila thread->GUI para comunicação segura
        self.gui_queue = None  # será inicializado em start_processing

        self.is_processing = False

        self.setup_ui()

    def setup_ui(self):
        """Configura layout da interface."""
        # Frame principal com scroll (se necessário)
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # =============== TIPO DE CERTIFICADO ===============
        cert_frame = tk.LabelFrame(
            main_frame, text="Tipo de Certificado", padx=10, pady=10
        )
        cert_frame.pack(fill=tk.X, pady=5)

        tk.Radiobutton(
            cert_frame,
            text="A1 (Arquivo PFX/P12)",
            variable=self.cert_type,
            value="A1",
            command=self.toggle_certificate_ui,
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            cert_frame,
            text="A3 (Token)",
            variable=self.cert_type,
            value="A3",
            command=self.toggle_certificate_ui,
        ).pack(side=tk.LEFT)

        # =============== CERTIFICADO A1 ===============
        self.a1_frame = tk.LabelFrame(
            main_frame, text="Certificado A1", padx=10, pady=10
        )
        self.a1_frame.pack(fill=tk.X, pady=5)

        tk.Button(
            self.a1_frame, text="Selecionar PFX/P12", command=self.select_pfx
        ).pack(side=tk.LEFT, padx=5)
        tk.Label(self.a1_frame, textvariable=self.pfx_path, wraplength=400).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        tk.Label(self.a1_frame, text="Senha:").pack(side=tk.LEFT, padx=(10, 5))
        tk.Entry(
            self.a1_frame, textvariable=self.pfx_password, show="*", width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            self.a1_frame, text="Carregar A1", command=self.load_a1_certificate
        ).pack(side=tk.LEFT, padx=5)

        # =============== CERTIFICADO A3 (Oculto por padrão) ===============
        self.a3_frame = tk.LabelFrame(
            main_frame, text="Certificado A3 (Token)", padx=10, pady=10
        )

        tk.Button(
            self.a3_frame, text="Selecionar Driver DLL", command=self.select_dll
        ).pack(side=tk.LEFT, padx=5)
        tk.Label(self.a3_frame, textvariable=self.dll_path, wraplength=400).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        tk.Label(self.a3_frame, text="PIN:").pack(side=tk.LEFT, padx=(10, 5))
        tk.Entry(
            self.a3_frame, textvariable=self.a3_pin, show="*", width=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            self.a3_frame, text="Conectar Token", command=self.connect_a3_token
        ).pack(side=tk.LEFT, padx=5)

        # =============== PASTAS ===============
        folder_frame = tk.LabelFrame(main_frame, text="Pastas", padx=10, pady=10)
        folder_frame.pack(fill=tk.X, pady=5)

        tk.Label(folder_frame, text="Pasta de Entrada (XMLs):").pack(anchor=tk.W)
        input_subfr = tk.Frame(folder_frame)
        input_subfr.pack(fill=tk.X, pady=3)
        tk.Button(
            input_subfr, text="Selecionar", command=self.select_input_folder
        ).pack(side=tk.LEFT, padx=5)
        tk.Label(input_subfr, textvariable=self.input_folder, wraplength=600).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        tk.Label(folder_frame, text="Pasta de Saída (XMLs Assinados):").pack(
            anchor=tk.W, pady=(10, 0)
        )
        output_subfr = tk.Frame(folder_frame)
        output_subfr.pack(fill=tk.X, pady=3)
        tk.Button(
            output_subfr, text="Selecionar", command=self.select_output_folder
        ).pack(side=tk.LEFT, padx=5)
        tk.Label(output_subfr, textvariable=self.output_folder, wraplength=600).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # =============== CONFIGURAÇÃO ===============
        config_frame = tk.LabelFrame(main_frame, text="Configuração", padx=10, pady=10)
        config_frame.pack(fill=tk.X, pady=5)

        tk.Label(config_frame, text="Tipo de XML:").pack(side=tk.LEFT, padx=5)
        tk.OptionMenu(config_frame, self.xml_type, "PREFEITURA", "NACIONAL").pack(
            side=tk.LEFT, padx=5
        )

        tk.Label(config_frame, text="Alíquota (%):").pack(side=tk.LEFT, padx=(20, 5))
        tk.Entry(config_frame, textvariable=self.aliquota, width=10).pack(
            side=tk.LEFT, padx=5
        )

        # =============== LOG ===============
        log_frame = tk.LabelFrame(
            main_frame, text="Log de Processamento", padx=5, pady=5
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            width=80,
            state=tk.DISABLED,
            font=("Arial", 11),
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # =============== AÇÕES ===============
        action_frame = tk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        self.process_btn = tk.Button(
            action_frame,
            text="Processar XMLs",
            command=self.start_processing,
            bg="green",
            fg="white",
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(
            action_frame, text=STATUS_DESCONECTADO, fg="red", font=("Arial", 10, "bold")
        )
        self.status_label.pack(side=tk.RIGHT, padx=5)

        # Inicializar UI
        self.toggle_certificate_ui()

    def toggle_certificate_ui(self):
        """Alterna entre UI A1 e A3."""
        if self.cert_type.get() == "A1":
            self.a1_frame.pack(fill=tk.X, pady=5)
            self.a3_frame.pack_forget()
        else:
            self.a1_frame.pack_forget()
            self.a3_frame.pack(fill=tk.X, pady=5)

    def select_pfx(self):
        """Seleciona arquivo PFX."""
        path = filedialog.askopenfilename(
            filetypes=[("PFX/P12 Files", "*.pfx *.p12"), ("All Files", "*.*")]
        )
        if path:
            self.pfx_path.set(path)

    def select_dll(self):
        """Seleciona driver DLL."""
        path = filedialog.askopenfilename(
            filetypes=[("DLL Files", "*.dll"), ("All Files", "*.*")]
        )
        if path:
            self.dll_path.set(path)

    def select_input_folder(self):
        """Seleciona pasta de entrada."""
        path = filedialog.askdirectory(title="Selecione pasta com XMLs")
        if path:
            self.input_folder.set(path)

    def select_output_folder(self):
        """Seleciona pasta de saída."""
        path = filedialog.askdirectory(title="Selecione pasta de saída")
        if path:
            self.output_folder.set(path)

    def load_a1_certificate(self):
        """Carrega certificado A1."""
        if not self.pfx_path.get():
            messagebox.showerror("Erro", "Selecione um arquivo PFX/P12")
            return

        if not self.pfx_password.get():
            messagebox.showerror("Erro", "Digite a senha do certificado")
            return

        password_bytes = self.pfx_password.get().encode()
        success, message = self.cert_a1.load(self.pfx_path.get(), password_bytes)

        if success:
            self.log_append(f"✓ {message}")
            self.log_append(f"\n{self.cert_a1.get_subject()}\n")
            self.status_label.config(text=STATUS_CONECTADO_A1, fg="green")
            messagebox.showinfo("Sucesso", message)
        else:
            self.log_append(f"✗ {message}")
            self.status_label.config(text=STATUS_DESCONECTADO, fg="red")
            messagebox.showerror("Erro", message)

    def connect_a3_token(self):
        """Conecta a token A3."""
        if not self.dll_path.get():
            messagebox.showerror("Erro", "Selecione um driver DLL")
            return

        pin = self.a3_pin.get()
        if not pin:
            messagebox.showerror("Erro", "Digite o PIN do Token")
            return

        success, message = self.cert_a3.load(self.dll_path.get(), pin)

        if success:
            self.log_append(f"✓ {message}")
            self.status_label.config(text=STATUS_CONECTADO_A3, fg="green")
            messagebox.showinfo("Sucesso", message)
        else:
            self.log_append(f"✗ {message}")
            self.status_label.config(text=STATUS_DESCONECTADO, fg="red")
            messagebox.showerror("Erro", message)

    def _log_safe(self, message):
        """Thread-safe: enfileira mensagem para a GUI processar via root.after()."""
        if self.gui_queue is not None:
            try:
                self.gui_queue.put_nowait((MSG_LOG, message))
            except queue.Full:
                # Fila cheia: descarta para não bloquear a thread de processamento
                pass

    def _poll_queue(self):
        """Drena a fila e atualiza widgets. Chamado periodicamente pela main thread.

        Drena tanto o ``gui_queue`` (mensagens do processador) quanto o
        :class:`GuiLogHandler` (registros de logging estruturado).
        """
        # 1. Drena logging_setup (registros de logger estruturado)
        if self.gui_log_handler is not None:
            try:
                while True:
                    levelno, msg = self.gui_log_handler.queue.get_nowait()
                    self._write_log_line(levelno, msg)
            except queue.Empty:
                pass

        # 2. Drena gui_queue (compatibilidade com log_append legada)
        if self.gui_queue is None:
            return
        try:
            while True:
                kind, payload = self.gui_queue.get_nowait()
                if kind == MSG_LOG:
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, payload + "\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state=tk.DISABLED)
                elif kind == MSG_DONE_OK:
                    self._on_done(success=True)
                    return  # para o polling; será reiniciado em start_processing
                elif kind == MSG_DONE_ERR:
                    self._on_done(success=False)
                    return
        except queue.Empty:
            pass
        # Re-agenda a próxima drenagem
        if self.is_processing:
            self.root.after(50, self._poll_queue)

    def _write_log_line(self, levelno: int, message: str) -> None:
        """Escreve uma linha no widget de log com cor conforme o n\u00edvel.

        ERROR/CRITICAL em vermelho, WARNING em laranja escuro, INFO/DEBUG em preto.
        """
        import logging as _logging
        if levelno >= _logging.ERROR:
            color = "#b00020"  # vermelho
        elif levelno >= _logging.WARNING:
            color = "#cc6600"  # laranja escuro
        else:
            color = "black"
        try:
            self.log_text.config(state=tk.NORMAL)
            tag_name = f"level_{levelno}"
            self.log_text.tag_configure(tag_name, foreground=color)
            self.log_text.insert(tk.END, message + "\n", tag_name)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except tk.TclError:
            # Widget pode ter sido destru\u00eddo; ignorar
            pass

    def log_append(self, message):
        """API pública de log. Segura para qualquer thread."""
        # Chamadas vindas da main thread (botões, etc.) entram direto
        if threading.current_thread() is threading.main_thread():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        else:
            self._log_safe(message)

    def validate_inputs(self):
        """Valida inputs do usuário."""
        if not self.input_folder.get():
            messagebox.showerror("Erro", "Selecione pasta de entrada")
            return False

        if not self.output_folder.get():
            messagebox.showerror("Erro", "Selecione pasta de saída")
            return False

        if not os.path.exists(self.input_folder.get()):
            messagebox.showerror("Erro", "Pasta de entrada não existe")
            return False

        # Cria pasta de saída automaticamente se não existir
        if not os.path.exists(self.output_folder.get()):
            try:
                os.makedirs(self.output_folder.get(), exist_ok=True)
            except OSError as e:
                messagebox.showerror(
                    "Erro", f"Não foi possível criar a pasta de saída: {e}"
                )
                return False

        # Validar certificado
        if self.cert_type.get() == "A1":
            valid, msg = self.cert_a1.validate()
            if not valid:
                messagebox.showerror("Erro", f"Certificado A1 inválido: {msg}")
                return False
        else:
            valid, msg = self.cert_a3.validate()
            if not valid:
                messagebox.showerror("Erro", f"Token A3 inválida: {msg}")
                return False

        return True

    def start_processing(self):
        """Inicia processamento em thread separada."""
        if not self.validate_inputs():
            return

        if self.is_processing:
            messagebox.showwarning("Aviso", "Processamento já está em andamento")
            return

        self.is_processing = True
        self.process_btn.config(state=tk.DISABLED, bg="gray")
        self.status_label.config(text=STATUS_PROCESSANDO, fg="blue")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Inicializa fila e inicia o polling na main thread
        self.gui_queue = queue.Queue(maxsize=10000)
        self.root.after(50, self._poll_queue)

        thread = threading.Thread(target=self.process_xmls, daemon=True)
        thread.start()

    def process_xmls(self):
        """Processa XMLs (executado em thread worker)."""
        # Salva referência ao processador para fechar sessão A3 depois
        processor = None
        try:
            self.log_append(LOG_SEPARATOR)
            self.log_append("PROCESSAMENTO DE XMLs INICIADO")
            self.log_append(
                f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
            )
            self.log_append(LOG_SEPARATOR)
            self.log_append("")

            input_folder = self.input_folder.get()
            output_folder = self.output_folder.get()

            xml_files = [
                f for f in os.listdir(input_folder) if f.lower().endswith(".xml")
            ]

            if not xml_files:
                self.log_append("⚠ Nenhum arquivo XML encontrado na pasta de entrada")
                self.gui_queue.put_nowait((MSG_DONE_ERR, None))
                return

            self.log_append(f"Total de XMLs encontrados: {len(xml_files)}")
            self.log_append("")

            # Seleciona certificado
            if self.cert_type.get() == "A1":
                cert_handler = self.cert_a1
            else:
                cert_handler = self.cert_a3

            # Converter alíquota
            try:
                aliquota = float(self.aliquota.get()) / 100
            except ValueError:
                aliquota = 0.0365

            # Processa XMLs
            processor = XMLProcessor(cert_handler, self.log_append)
            processor.process_batch(
                pasta_entrada=input_folder,
                pasta_corrigidos=output_folder,
                aliquota=aliquota,
                gerar_relatorio=True,
            )

            self.log_append("")
            self.log_append(LOG_SEPARATOR)
            self.log_append("PROCESSAMENTO CONCLUÍDO COM SUCESSO")
            self.log_append(LOG_SEPARATOR)

            self.gui_queue.put_nowait((MSG_DONE_OK, None))

        except (OSError, ValueError, ET.ParseError) as e:
            self.log_append(f"✗ Erro durante processamento: {str(e)}")
            self.gui_queue.put_nowait((MSG_DONE_ERR, None))
        except Exception as e:  # noqa: BLE001
            # Captura qualquer outra exceção (ex: erros do signxml) para não
            # matar a thread silenciosamente.
            self.log_append(f"✗ Erro inesperado: {type(e).__name__}: {e}")
            self.gui_queue.put_nowait((MSG_DONE_ERR, None))
        finally:
            # Garante limpeza de recursos do certificado (libera sessão A3, etc.)
            if processor is not None:
                try:
                    processor.close()
                except Exception:  # noqa: BLE001
                    pass

    def _on_done(self, success):
        """Finaliza processamento (executado na main thread)."""
        self.is_processing = False
        self.process_btn.config(state=tk.NORMAL, bg="green")

        if success:
            self.status_label.config(text=STATUS_CONCLUIDO, fg="green")
            messagebox.showinfo("Sucesso", "Processamento concluído com sucesso!")
        else:
            self.status_label.config(text=STATUS_DESCONECTADO, fg="red")
            messagebox.showerror(
                "Erro", "Houve erros durante o processamento. Verifique o log."
            )
        # Libera a fila para a próxima rodada
        self.gui_queue = None


def main():
    """Função principal."""
    root = tk.Tk()
    XMLSignerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
