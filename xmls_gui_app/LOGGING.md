# Sistema de Logging — XML Auditar

Documentação do sistema de logging estruturado introduzido na FASE 3.2.

## Visão Geral

O projeto usa o módulo `logging` da stdlib do Python (built-in, sem dependências externas) configurado de forma centralizada pelo módulo `logging_setup.py`.

Toda a aplicação compartilha um único logger raiz, que despacha para três destinos:

| Destino | Handler | Uso |
| --------- | --------- | ----- |
| Console (stderr) | `StreamHandler` | Visível durante desenvolvimento |
| Arquivo rotativo | `RotatingFileHandler` | Persistência — sobrevive a crashes da GUI |
| GUI Tkinter | `GuiLogHandler` (customizado) | Renderiza colorido no widget de log |

## Onde os logs são gravados

```
~/.xml-auditar/logs/xml-auditar.log       # Linux/Mac
C:\Users\<voce>\.xml-auditar\logs\        # Windows
```

Configuração: **5 MB por arquivo, mantém 5 backups** (rotação automática).

## Níveis de Log

| Nível | Quando usar | Exemplo |
| ------- | ------------- | --------- |
| `DEBUG` | Diagnóstico fino — detalhes de implementação | "Procurando elemento PISAliq em NFE" |
| `INFO` | Eventos normais do fluxo | "Certificado A1 carregado com sucesso" |
| `WARNING` | Algo merece atenção, mas não é fatal | "Senha do certificado A1 incorreta" |
| `ERROR` | Falha recuperável | "Falha ao ler arquivo X: <erro>" |
| `CRITICAL` | Falha grave — app continua mas estado comprometido | "Banco de dados corrompido" |

Hierarquia: `DEBUG < INFO < WARNING < ERROR < CRITICAL`.

Definir nível `INFO` significa que `DEBUG` é filtrado (não aparece).

## Como usar em um módulo

```python
from logging_setup import get_logger

logger = get_logger(__name__)

# Níveis básicos
logger.debug("Detalhes de implementação")
logger.info("Usuário clicou em Processar")
logger.warning("Tag <ICMS00> não encontrada no XML")
logger.error("Falha ao ler arquivo X")
logger.critical("Sem espaço em disco!")

# Com formatação
logger.info("Processando %d arquivos em %s", n_files, folder)
```

## Ativando Modo DEBUG

Para diagnóstico avançado, ative o modo DEBUG:

**Opção 1 — Variável de ambiente:**

```bash
# Linux/Mac
XML_AUDITAR_LOG_LEVEL=DEBUG python run_gui.py

# Windows (PowerShell)
$env:XML_AUDITAR_LOG_LEVEL="DEBUG"; python run_gui.py
```

**Opção 2 — Programaticamente (em testes):**

```python
from logging_setup import setup_logging
setup_logging(level="DEBUG")
```

**Opção 3 — Na GUI (parâmetro de construtor):**

```python
from gui_app import XMLSignerGUI
XMLSignerGUI(root, log_level="DEBUG")
```

## Onde encontrar o arquivo de log

| Sistema | Caminho |
| --------- | --------- |
| Windows | `%USERPROFILE%\.xml-auditar\logs\xml-auditar.log` |
| Linux | `~/.xml-auditar/logs/xml-auditar.log` |
| macOS | `~/.xml-auditar/logs/xml-auditar.log` |

Formato de cada linha:

```
2026-07-27 14:32:11,234 [INFO    ] xml_processor: Processando 5 arquivos em C:\xmls
2026-07-27 14:32:11,567 [WARNING ] certificate_handler: Senha do certificado A1 incorreta
2026-07-27 14:32:12,001 [ERROR   ] xml_processor: Falha ao ler arquivo X: [Errno 2] No such file
```

## Para Desenvolvedores

### Adicionando log a um novo módulo

```python
# No topo do novo arquivo
from logging_setup import get_logger
logger = get_logger(__name__)

class MyNewService:
    def do_thing(self):
        logger.info("Iniciando operação")
        try:
            result = risky_operation()
            logger.debug("Resultado: %r", result)
            return result
        except Exception as e:
            logger.exception("Falha em risky_operation")
            raise
```

### Boas práticas

1. **Use o logger, não `print()`** — permite filtrar por nível, formatar, redirecionar
2. **Mensagens com contexto** — inclua o arquivo/recurso afetado: `"Falha ao ler X: <erro>"`
3. **Níveis apropriados** — INFO para "aconteceu algo", ERROR para "deu ruim mas app continua"
4. **`logger.exception()` em vez de `logger.error()` + traceback** — formatação automática
5. **Não logue dados sensíveis** — evite logar senhas, PINs, certificados completos

### Quando NÃO usar logging

- Em laços muito quentes (>1000x/segundo) — degrada performance
- Para comunicação entre módulos (use retornos de função)
- Para controle de fluxo (use exceções)

## Arquitetura

```
┌─────────────────────────────────────┐
│ Application code                    │
│   logger.info("...")                │
│   logger.error("...")               │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ logging.getLogger()                 │
│ (root logger compartilhado)         │
└────┬──────────┬──────────┬──────────┘
     │          │          │
     ▼          ▼          ▼
┌─────────┐ ┌──────────┐ ┌────────────┐
│ Stream  │ │ Rotating │ │ GuiLog     │
│ Handler │ │ File     │ │ Handler    │
│ stderr  │ │ Handler  │ │ (queue)    │
└─────────┘ └──────────┘ └─────┬──────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ root.after() │
                       │ (GUI main)   │
                       └──────┬───────┘
                              ▼
                       ┌──────────────┐
                       │ Tk Text      │
                       │ widget com   │
                       │ cores por    │
                       │ nível        │
                       └──────────────┘
```

## Testes

A suíte cobre 18 cenários em `tests/test_logging_setup.py`:

- setup_logging (config, idempotência, níveis)
- GuiLogHandler (queue, level preservation, comportamento quando fila cheia)
- RotatingFileHandler (escrita em arquivo)
- Integração com XMLProcessor

```bash
python -m pytest tests/test_logging_setup.py -v
```

## Retrocompatibilidade

A refatoração para logging **não quebrou** nenhuma chamada de código existente. O `XMLProcessor` ainda aceita o parâmetro legado `output_callback` que funciona em paralelo:

```python
# Funciona (novo)
proc = XMLProcessor(cert)              # usa logger

# Funciona (legado)
proc = XMLProcessor(cert, callback)    # logger + callback
```

Ambos os caminhos são chamados quando ambos estão configurados, garantindo que callers antigos continuem funcionando.

## Compatibilidade

| Plataforma | Testado | Notas |
| ------------ | --------- | ------- |
| Windows 10/11 | ✅ | Caminho `%USERPROFILE%\.xml-auditar` |
| Linux | ✅ (CI) | Caminho `~/.xml-auditar` |
| macOS | ✅ (CI) | Caminho `~/.xml-auditar` |
| Python 3.9+ | ✅ | Requerido pelas annotations `list[...]` |

---

**Última atualização:** 27 de julho de 2026
**Versão:** 1.0 (FASE 3.2)
