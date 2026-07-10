# 📐 Referência de Cálculos - XML Auditar

## 🎯 Alíquotas Padrão (Brasileiras)

### NFS-e (Padrão SPED - Município de São Paulo)

| Conceito | Alíquota | Observação |
|----------|----------|-----------|
| **ISS** | 3.65% | Imposto sobre Serviços (padrão São Paulo) |
| **PIS** | 1.65% | Programa Integração Social |
| **COFINS** | 7.60% | Contribuição para Financiamento Seguridade |
| **INSS** | 11.00% | Instituto Nacional Seguro Social (retém empregador) |
| **IR** | 1.50% a 7.50% | Imposto de Renda (varia conforme serviço) |
| **CSLL** | 3.00% | Contribuição Social Lucro Líquido |

### NFe (Padrão Nacional)

| Conceito | Alíquota | Observação |
|----------|----------|-----------|
| **ICMS** | 7% a 18% | Varia por estado e produto (padrão: 18%) |
| **IPI** | 0% a 35% | Imposto Produtos Industrializados (padrão: 0% isenção) |
| **PIS** | 1.65% ou 7.65% | Depende da CST |
| **COFINS** | 7.60% ou 2.76% | Depende da CST |
| **ICMS Diferencial (ST)** | Variável | Substituição Tributária |

---

## 🧮 Fórmulas de Cálculo

### NFS-e - Fórmula Principal

```
Valor Líquido = Valor Serviços - Deduções - Retenções + ISS*

Retenções = PIS + COFINS + INSS + IR + CSLL

Onde:
  PIS         = Valor Serviços × 1.65% / 100
  COFINS      = Valor Serviços × 7.60% / 100
  INSS        = Valor Serviços × 11.00% / 100
  IR          = (Valor Serviços - Deduções - INSS) × 1.50% / 100
  CSLL        = (Valor Serviços - Deduções - INSS) × 3.00% / 100
  ISS         = Valor Serviços × 3.65% / 100

* ISS é subtraído se IssRetido = 0
  ISS é retido pela prefeitura se IssRetido = 1
```

### NFe - Fórmula Principal

```
Valor Total NF = Valor Produtos + ICMS + PIS + COFINS + IPI - Descontos + Frete

Onde:
  ICMS        = Valor Base × Alíquota / 100
  PIS         = Valor Base × 1.65% / 100  (se CST = 01)
  COFINS      = Valor Base × 7.60% / 100  (se CST = 01)
  IPI         = Valor Base × Alíquota / 100 (se aplicável)
  
Base pode variar:
  - Padrão: vProd - vDesc
  - Com ICMS-ST: vBC pode ser diferente
```

---

## 📊 Exemplos Práticos

### Exemplo 1: NFSe Simples (Correto)

**Entrada:**
```
Valor Serviços: R$ 1.000,00
Deduções: R$ 0,00
Alíquota: 3.65%
```

**Cálculos:**
```
ISS         = 1.000,00 × 3.65% = R$ 36,50
PIS         = 1.000,00 × 1.65% = R$ 16,50
COFINS      = 1.000,00 × 7.60% = R$ 76,00
INSS        = 1.000,00 × 11.00% = R$ 110,00
IR          = (1.000,00 - 0 - 110,00) × 1.50% = R$ 13,35
CSLL        = (1.000,00 - 0 - 110,00) × 3.00% = R$ 26,70

Total Retenções = 16,50 + 76,00 + 110,00 + 13,35 + 26,70 = R$ 242,55
Valor Líquido = 1.000,00 - 242,55 - 36,50 = R$ 720,95
```

**Arquivo de teste**: `nfse_correto_01.xml`

---

### Exemplo 2: NFSe com Erro (Faltam PIS/COFINS)

**Entrada (ERRADA):**
```xml
<ValorServicos>5000.00</ValorServicos>
<ValorPis>0.00</ValorPis>
<ValorCofins>0.00</ValorCofins>
<ValorInss>0.00</ValorInss>
<ValorIr>0.00</ValorIr>
<ValorCsll>0.00</ValorCsll>
<ValorIss>182.50</ValorIss>
<ValorLiquidoNfse>4817.50</ValorLiquidoNfse>
```

**Corrigido:**
```
PIS        = 5.000,00 × 1.65% = R$ 82,50 ✓
COFINS     = 5.000,00 × 7.60% = R$ 380,00 ✓
INSS       = 5.000,00 × 11.00% = R$ 550,00 ✓
IR         = (5.000,00 - 550,00) × 1.50% = R$ 66,75 ✓
CSLL       = (5.000,00 - 550,00) × 3.00% = R$ 133,50 ✓

Novo Líquido = 5.000,00 - (82,50 + 380,00 + 550,00 + 66,75 + 133,50) - 182,50 = R$ 3.404,75
```

**Arquivo de teste**: `nfse_sem_retencao_02.xml`

---

### Exemplo 3: NFe com ICMS Incorreto

**Entrada (ERRADA):**
```xml
<vProd>5000.00</vProd>
<vBC>4500.00</vBC>        <!-- ERRO: Diverge do valor do produto -->
<pICMS>18.0000</pICMS>
<vICMS>800.00</vICMS>     <!-- ERRO: 4500 × 18% = 810, não 800 -->
```

**Corrigido:**
```
vBC Correto   = 5.000,00 (deve ser igual ao vProd)
vICMS Correto = 5.000,00 × 18% = R$ 900,00

Diferença: R$ 900,00 - R$ 800,00 = R$ 100,00 subestimado
```

**Arquivo de teste**: `nfe_icms_incorreto_05.xml`

---

### Exemplo 4: NFSe com Deduções

**Entrada (Correta):**
```xml
<ValorServicos>15000.00</ValorServicos>
<ValorDeducoes>2000.00</ValorDeducoes>
<Aliquota>0.0365</Aliquota>
```

**Cálculos:**
```
Base para ISS     = 15.000,00 - 2.000,00 = R$ 13.000,00
ISS               = 13.000,00 × 3.65% = R$ 474,50

Base para PIS     = 13.000,00
PIS               = 13.000,00 × 1.65% = R$ 214,50

Base para COFINS  = 13.000,00
COFINS            = 13.000,00 × 7.60% = R$ 988,00

... (outros valores)

Valor Líquido = 15.000,00 - Deduções - Retenções - ISS
```

**Arquivo de teste**: `nfse_deducoes_15.xml`

---

## 🔍 Verificações de Erro

A ferramenta deve alertar se encontrar:

### Alertas de Divergência

```python
# NFSe
if abs(ValorIss - (ValorServicos * Aliquota)) > 0.01:
    ERRO: "ISS calculado incorretamente"

if PIS == 0 and ValorServicos > 0:
    AVISO: "PIS zerado - verificar se é intencional"

if (PIS + COFINS + INSS + IR + CSLL) > ValorServicos * 0.5:
    AVISO: "Retenções muito altas (> 50% do valor)"

# NFe
if abs(vICMS - (vBC * pICMS / 100)) > 0.01:
    ERRO: "ICMS divergente de vBC"

if vBC > vProd:
    ERRO: "Base de cálculo maior que valor do produto"
```

---

## 📈 Tolerância de Cálculo

Arredondamentos aceitos:

- **Centavos**: ±R$ 0,01 (1 centavo)
- **Valores altos**: ±R$ 0,10 (10 centavos) para valores acima de R$ 10.000
- **Cálculos em cascata**: ±R$ 1,00 (1 real) se múltiplos cálculos

---

## 🧪 Dados de Teste

### Valores Típicos por Tipo de Serviço

| Serviço | Valor Típico | Alíquota | Observação |
|---------|--------------|----------|-----------|
| Consultoria | R$ 1.000 a R$ 50.000 | 3.65% | Sem retenção federal |
| Limpeza | R$ 500 a R$ 5.000 | 3.65% | Com INSS obrigatório |
| Assessoria Jurídica | R$ 2.000 a R$ 20.000 | 3.65% | IR e CSLL obrigatórios |
| Manutenção | R$ 300 a R$ 3.000 | 3.65% | INSS 11% |
| Transporte | R$ 1.000 a R$ 100.000 | 3.65% | Varia por distância |

---

## ⚙️ Configurações da Ferramenta

**Arquivo**: `xmls_gui_app/config.py`

```python
ALIQUOTA_PADRAO = 0.0365  # 3.65% - NFSe padrão SP

# Alíquotas adicionais (customizáveis)
ALIQUOTA_PIS = 0.0165      # 1.65%
ALIQUOTA_COFINS = 0.0760   # 7.60%
ALIQUOTA_INSS = 0.1100     # 11.00%
```

Para alterar, edite o arquivo acima.

---

**Documento de Referência**
**Data**: 26 de maio de 2026
**Versão**: 1.0
