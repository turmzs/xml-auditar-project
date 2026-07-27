"""Configuração centralizada de logging estruturado.

Este módulo fornece uma configuração única de logging usada por toda a
aplicação XML Auditar. Permite:

- Logs no console (stderr) com formato legível
- Logs em arquivo rotativo em ``~/.xml-auditar/logs/`` (mantém 5 backups de 5MB)
- Handler customizado para a GUI: envia registros para uma fila
  thread-safe que a ``gui_app.py`` drena via ``root.after()``.

A função pública principal é ``setup_logging()``, chamada uma vez no
início da aplicação (em ``gui_app.__init__`` ou ``run_gui.main``).

Exemplo de uso direto em outros módulos::

    from logging_setup import get_logger
    logger = get_logger(__name__)

    logger.debug("Detalhes de debug")
    logger.info("Arquivo processado com sucesso")
    logger.warning("Tag não encontrada, usando default")
    logger.error("Falha ao assinar XML")

Exemplo de uso com a GUI::

    from logging_setup import setup_logging, GuiLogHandler
    setup_logging(level="INFO")
    # O GuiLogHandler já é instalado em setup_logging; a gui_app.py
    # drena os registros via _poll_queue().
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import queue
import sys
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
LOG_DIR_NAME = ".xml-auditar"
LOGS_SUBDIR = "logs"
LOG_FILE_NAME = "xml-auditar.log"
LOG_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Níveis reconhecidos (case-insensitive)
VALID_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


# ---------------------------------------------------------------------------
# GuiLogHandler: envia registros para uma fila que a GUI drena
# ---------------------------------------------------------------------------
class GuiLogHandler(logging.Handler):
    """Handler que enfileira registros para a GUI processar na main thread.

    A GUI instala este handler via :func:`setup_logging`. Os registros
    são colocados em uma :class:`queue.Queue` interna, que a
    ``gui_app.py`` drena periodicamente usando ``root.after()``.

    Atributos:
        queue: fila thread-safe onde os registros são colocados.
    """

    def __init__(self, maxsize: int = 10_000):
        super().__init__()
        self.queue: "queue.Queue[tuple[int, str]]" = queue.Queue(maxsize=maxsize)
        # Define um formato simples (sem timestamp — a GUI adiciona visualmente)
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        """Coloca o registro na fila. Se a fila estiver cheia, descarta."""
        try:
            msg = self.format(record)
            # put_nowait nunca bloqueia; descarta se cheio para
            # não comprometer a thread que está logando.
            self.queue.put_nowait((record.levelno, msg))
        except queue.Full:
            # Falha silenciosa — não queremos que logging cause mais problemas
            pass
        except Exception:  # noqa: BLE001
            # Nunca deixe o handler levantar exceção
            self.handleError(record)


# ---------------------------------------------------------------------------
# Helpers de caminho
# ---------------------------------------------------------------------------
def _default_log_dir() -> Path:
    """Retorna o diretório padrão de logs: ``~/.xml-auditar/logs/``."""
    home = Path.home()
    log_dir = home / LOG_DIR_NAME / LOGS_SUBDIR
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


# ---------------------------------------------------------------------------
# Setup principal
# ---------------------------------------------------------------------------
_gui_handler: Optional[GuiLogHandler] = None


def get_gui_handler() -> Optional[GuiLogHandler]:
    """Retorna o GuiLogHandler instalado por :func:`setup_logging` (se houver)."""
    return _gui_handler


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_gui: bool = True,
    log_dir: Optional[str] = None,
) -> GuiLogHandler:
    """Configura logging estruturado para toda a aplicação.

    Args:
        level: Nível mínimo (``"DEBUG"``, ``"INFO"``, ``"WARNING"``,
            ``"ERROR"``, ``"CRITICAL"``).
        log_file: Caminho do arquivo de log. Se ``None``, usa
            ``~/.xml-auditar/logs/xml-auditar.log``.
        enable_console: Se True, instala StreamHandler para stderr.
        enable_gui: Se True, instala :class:`GuiLogHandler` no root.
        log_dir: Diretório alternativo onde criar o arquivo de log.
            Útil para testes.

    Returns:
        O :class:`GuiLogHandler` instalado, ou um novo handler descartável
        se ``enable_gui=False`` (compatibilidade).

    Note:
        Pode ser chamado múltiplas vezes — handlers antigos são removidos
        antes de instalar novos, evitando duplicação.
    """
    global _gui_handler

    # Resolve nível
    level_int = VALID_LEVELS.get(level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level_int)

    # Remove handlers antigos (idempotência)
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # 1. Console (stderr)
    if enable_console:
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(level_int)
        console.setFormatter(formatter)
        root.addHandler(console)

    # 2. Arquivo rotativo
    try:
        if log_dir is not None:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
            target_dir = Path(log_dir)
        else:
            target_dir = _default_log_dir()
        if log_file is None:
            log_file = str(target_dir / LOG_FILE_NAME)

        # RotatingFileHandler: 5MB por arquivo, mantém 5 backups
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level_int)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # Se falhar ao criar arquivo (ex: permissão negada), loga no console
        sys.stderr.write(f"[logging_setup] Falha ao criar arquivo de log: {e}\n")

    # 3. GUI
    global _gui_handler
    if enable_gui:
        _gui_handler = GuiLogHandler()
        _gui_handler.setLevel(level_int)
        root.addHandler(_gui_handler)
        return _gui_handler
    else:
        # Retorna handler descartável (compatibilidade com testes)
        return GuiLogHandler()


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger com o nome do módulo.

    Atalho para ``logging.getLogger(name)``. Conveniente para usar::

        from logging_setup import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)


def shutdown_logging() -> None:
    """Encerra logging de forma limpa (fecha handlers)."""
    logging.shutdown()


# ---------------------------------------------------------------------------
# Configuração automática via variável de ambiente
# ---------------------------------------------------------------------------
def _auto_configure_from_env() -> None:
    """Permite configurar via env var ``XML_AUDITAR_LOG_LEVEL``.

    Útil para debugging em produção sem alterar código::

        XML_AUDITAR_LOG_LEVEL=DEBUG python run_gui.py
    """
    level = os.environ.get("XML_AUDITAR_LOG_LEVEL", "").upper()
    if level in VALID_LEVELS:
        setup_logging(level=level)


if __name__ == "__main__":
    # Teste rápido de funcionamento
    setup_logging(level="DEBUG", log_dir="_test_logs")
    log = get_logger(__name__)
    log.debug("Mensagem de debug")
    log.info("Mensagem de info")
    log.warning("Mensagem de warning")
    log.error("Mensagem de error")
    log.critical("Mensagem de critical")
    print(f"\nLogs escritos em: {_default_log_dir()}")