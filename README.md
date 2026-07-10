# XML Auditar - Corretor Automático de XMLs com Assinatura Digital

Ferramenta automatizada para corrigir valores em XMLs (NFS-e e NFe) e re-assinar com certificado digital **A1** ou **A3**.

---

## 🎯 Funcionalidades

- ✅ Leitura e validação** de XMLs
- ✅ Remoção de assinaturas antigas** para permitir alterações
- ✅ Correção automática de valores** (regra configurável; padrão 3,65%)
- ✅ Re-assinatura com certificado**
  - A1 (arquivo PFX/P12 com senha)
  - A3 (Token via PKCS#11)
- ✅ Processamento em lote**
  - GUI otimizada (com batch logging)
  - Multiprocessing (quando aplicável)

---

## 📦 Componentes

- **CLI/Processamento**: módulos em `xmls_gui_app/xml_processor*.py`
- **GUI**: interface em `xmls_gui_app/gui_app.py` (Tkinter)
- **Entry point**: `run_gui.py`

---

## ⚙️ Pré-requisitos

- **Python 3.10+**

Dependências (GUI):

```bash
cd xmls_gui_app
pip install -r requirements.txt
```

---

## 🚀 Como Usar (GUI)

### 1) Executar

```bash
python run_gui.py
```

### 2) Configurar

1. **Escolher Certificado**
   - **A1**: selecionar arquivo PFX/P12 + senha
   - **A3**: selecionar driver DLL/token e conectar via PKCS#11
2. **Selecionar pastas**
   - Entrada: XMLs a processar
   - Saída: XMLs assinados
3. **Configurar processamento** (opcional)
   - Tipo: **PREFEITURA** (NFSe) ou **NACIONAL** (NFe)
   - Alíquota: padrão **3,65%**

### 3) Processar e acompanhar

- Acompanhe o **log em tempo real** na GUI.
- Ao final, verifique os XMLs na pasta de saída.

---

## ⚡ Otimizações de Performance (já implementadas)

### 1) Batch Logging (GUI)

- Atualiza a interface a cada N arquivos (em vez de logar a cada arquivo).
- Ganho estimado: **~20–30%**.

### 2) Multiprocessing Paralelo (processador paralelo)

- Arquivo: `xmls_gui_app/xml_processor_parallel.py`
- Ganho estimado: **~60–75%**.

⚠️ **Observação:** multiprocessing normalmente é aplicado melhor em fluxos compatíveis com o tipo de certificado/assinatura.

---

## 📂 Estrutura de pastas (GUI)

A GUI permite selecionar as pastas de entrada/saída. 
Através do filedialog do tinker.
Escolha as notas em uma pasta de ENTRADA, e uma de SAIDA.


---

## 🔧 Configuração

### Alíquota padrão

Edite `xmls_gui_app/config.py`:

```python
ALIQUOTA_PADRAO = 0.0365  # 3.65%
```

---

## 📊 Relatórios e logs

- GUI registra o andamento e erros.
- Módulos de processamento geram logs/relatórios conforme a execução.

---

## ⚠️ Importante (Segurança)

- **Não commitar certificados** (`.pfx/.p12`) no repositório.
- Certificados e dados sensíveis devem permanecer **apenas em memória** durante a execução.
- Prefira informar senha via interação (GUI) ou estratégia segura (ex.: variáveis de ambiente).

---


---

## 📝 Status / Versão

- **Versão**: 1.0
- **Data**: 10/07/2026
- **Desenvolvido para**: AUDITAR CONTABILIDADE por Artur Menezes

