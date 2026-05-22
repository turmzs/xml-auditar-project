# XML Auditar - Corretor Automático de XMLs com Assinatura Digital

Ferramenta automatizada para corrigir valores em XMLs de NFS-e e re-assinar com certificado digital A1 da empresa.

## 🎯 Funcionalidades

- ✅ **Leitura e validação** de XMLs (NFS-e, NFe, CTe)
- ✅ **Remoção de assinaturas antigas** para permitir alterações
- ✅ **Correção automática de valores** (OutrasRetencoes = ValorServicos × 3.65%)
- ✅ **Re-assinatura com certificado** A1 (PFX) da empresa
- ✅ **Geração de relatórios** detalhados em TXT
- ✅ **Processamento em lote** de até 779 XMLs

## 📋 Pré-requisitos

- Python 3.13+
- Bibliotecas necessárias:
  ```bash
  pip install signxml cryptography
  ```

## 🚀 Como Usar

### 1. Preparar o ambiente

Coloque o certificado A1 (arquivo .pfx) na pasta raiz do projeto:
```
KRUEGER ASSESSORIA DE IMPORTACAO E EXPORTACAO LTDA-VENC-09-09-2026-SENHA-Krueger@007.pfx
```

### 2. Organizar XMLs

Coloque os XMLs a processar na pasta **`xmls_ok/`**

### 3. Executar o script

```bash
python arrumador.py
```

### 4. Verificar resultados

- **XMLs corrigidos**: `xmls_corrigidos/`
- **Relatório**: `relatorio_YYYYMMDD_HHMMSS.txt`

## 📁 Estrutura de Pastas

```
XML CORRECT/
├── arrumador.py              # Script principal
├── script.py                 # Script adicional
├── README.md                 # Este arquivo
├── .gitignore               # Configurações Git
├── xmls/                    # XMLs originais para processar
├── xmls_ok/                 # XMLs prontos (sem alterações)
├── xmls_corrigidos/         # XMLs corrigidos e re-assinados ✓
├── xmls_assinados/          # XMLs já assinados (backup)
├── xmls_erro/               # XMLs com problemas
├── xmls_processados/        # XMLs processados (arquivo)
├── xmls_backup/             # Backup dos XMLs originais
├── relatorio_*.txt          # Relatórios de execução
└── CERTIFICADO.pfx          # Certificado digital (SECRETO - não commitar)
```

## 🔧 Configuração

### Certificado

Edite o arquivo `arrumador.py` para alterar o caminho e senha do certificado:

```python
CERT_PATH = "KRUEGER ASSESSORIA DE IMPORTACAO E EXPORTACAO LTDA-VENC-09-09-2026-SENHA-Krueger@007.pfx"
CERT_PASS = b"Krueger@007"
```

### Algoritmo de Correção

O script calcula automaticamente:
```
OutrasRetencoes = ValorServicos × 0.0365
```

Para alterar a alíquota, modifique em `arrumador.py`:
```python
def calcular_correto(base):
    aliq = 0.0365  # Altere aqui
    return round(base * aliq, 2), aliq
```

## 📊 Saída do Relatório

Exemplo de relatório gerado:

```
============================================================
RELATORIO DE PROCESSAMENTO DE XMLs
Data: 22/05/2026 16:45:57
============================================================

Total de arquivos processados: 779
Corrigidos e re-assinados: 479
Ja estavam OK: 300
Erros: 0

============================================================
CORRIGIDOS E RE-ASSINADOS:
============================================================
  [OK] 31260217098839000107550010001181481038114591.xml
  [OK] 31260217098839000107550010001182051449076446.xml
  ...
```

## ⚠️ Importante

- **NUNCA** commite o certificado (.pfx) no repositório
- O arquivo `.gitignore` já está configurado para ignorar certificados
- Todos os XMLs processados ficam salvos em `xmls_corrigidos/`
- Faça backup dos originais antes de usar em produção

## 🔐 Segurança

- Certificado carregado apenas em memória durante execução
- Senha armazenada de forma segura no código (considere usar variáveis de ambiente)
- XMLs processados validados antes de serem assinados

## 📝 Logs

Verifique os relatórios em `relatorio_*.txt` para:
- Arquivos processados com sucesso
- Valores corrigidos
- Assinaturas removidas e re-aplicadas
- Eventuais erros encontrados

## 🐛 Troubleshooting

**Erro: "Certificado não encontrado"**
- Verifique se o arquivo .pfx está na pasta raiz
- Confirme o caminho e nome do arquivo em `arrumador.py`

**Erro: "Senha incorreta"**
- Verifique se a senha do certificado está correta em `arrumador.py`

**Erro de assinatura**
- Alguns XMLs podem ter estrutura diferente
- Verifique o relatório para mais detalhes

## 📞 Suporte

Para relatórios de erro detalhados, verifique a saída no console durante a execução.

---

**Versão**: 1.0  
**Data**: 22/05/2026  
**Desenvolvido para**: KRUEGER ASSESSORIA
