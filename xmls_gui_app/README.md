# Assinador de XMLs - Interface GUI

Aplicativo gráfico Tkinter para corrigir valores em XMLs (NFS-e, NFe, CTe) e re-assinar com certificado digital A1 ou A3.

## 🎯 Funcionalidades

- ✅ Suporte a certificado **A1** (arquivo PFX/P12 com senha)
- ✅ Suporte a certificado **A3** (Token via PKCS#11)
- ✅ Seleção dinâmica de pastas de entrada/saída
- ✅ Correção automática de valores (OutrasRetencoes = ValorServicos × alíquota)
- ✅ Re-assinatura com certificado selecionado
- ✅ Log em tempo real no aplicativo
- ✅ Interface simples e intuitiva

## 📋 Pré-requisitos

- Python 3.10+
- Bibliotecas (veja `requirements.txt`):
  ```bash
  signxml>=2.10.0
  cryptography>=41.0.0
  ```

## 🚀 Como Usar

### 1. Instalar dependências

```bash
cd xmls_gui_app
pip install -r requirements.txt
```

### 2. Executar a aplicação

```bash
python ../run_gui.py
```

Ou de dentro da pasta `xmls_gui_app`:

```bash
python gui_app.py
```

### 3. Usar a interface

1. **Selecionar Certificado**
   - Escolha tipo (A1 ou A3)
   - Para A1: selecione arquivo PFX, digite senha, clique "Carregar A1"
   - Para A3: selecione driver DLL, clique "Conectar Token"

2. **Selecionar Pastas**
   - Pasta de Entrada: onde estão os XMLs a processar
   - Pasta de Saída: onde serão salvos os XMLs assinados

3. **Configurar Processamento** (opcional)
   - Tipo de XML: PREFEITURA ou NACIONAL
   - Alíquota: percentual para cálculo (padrão 3.65%)

4. **Processar**
   - Clique "Processar XMLs"
   - Acompanhe o progresso no log
   - Verifique os XMLs assinados na pasta de saída

## 📁 Estrutura de Arquivos

```
xmls_gui_app/
├── gui_app.py              # Interface Tkinter principal
├── xml_processor.py        # Lógica de processamento de XMLs
├── certificate_handler.py  # Gerenciador de certificados (A1/A3)
├── config.py               # Configurações e constantes
├── requirements.txt        # Dependências
├── __init__.py             # Pacote Python
└── README.md               # Este arquivo
```

## 🔧 Configuração

### Alterar Alíquota Padrão

Edite `config.py`:

```python
ALIQUOTA_PADRAO = 0.0365  # 3.65%
```

### Suportar Novos Tipos de XML

Edite `xml_processor.py`, método `detectar_tipo()`:

```python
def detectar_tipo(self, root):
    tag = root.tag.lower()
    if "seu_tipo" in tag:
        return "SEU_TIPO"
    # ...
```

## 📊 Saída

- **XMLs Assinados**: Salvos na pasta de saída selecionada
- **Log**: Exibido em tempo real no aplicativo
- **Validação**: Verifique com `openssl` ou ferramentas online

## ⚠️ Importante

- **NUNCA** armazene a senha do certificado no código
- A senha é digitada a cada execução (mais seguro)
- Certificados são carregados apenas em memória
- Faça backup dos XMLs originais antes de usar em produção

## 🐛 Troubleshooting

**"Certificado não encontrado"**
- Verifique se o arquivo PFX existe
- Confirme o caminho

**"Senha incorreta"**
- Verifique se a senha foi digitada corretamente
- Teste a senha no Windows (duplo-clique no PFX)

**"Nenhum XML encontrado"**
- Verifique se a pasta contém arquivos `.xml`
- Confirme que o caminho foi selecionado corretamente

**Erro de assinatura**
- Alguns XMLs podem ter estrutura diferente
- Verifique o log para detalhes
- Consulte o README original do `arrumador.py`

## 📝 Logs

Todos os processamentos são registrados no log do aplicativo. Você pode:
- Acompanhar em tempo real
- Identificar erros
- Validar sucessos

## 🔐 Segurança

- ✅ Certificados carregados apenas em memória
- ✅ Senha não é armazenada
- ✅ XMLs validados antes de assinatura
- ✅ Sem transmissão de dados pela internet

## 📞 Suporte

Para dúvidas ou relatórios de erro:
1. Verifique o log no aplicativo
2. Consulte este README
3. Compare com `arrumador.py` (versão CLI)

---

**Versão**: 1.0  
**Data**: 25/05/2026  
**Desenvolvido para**: KRUEGER ASSESSORIA
