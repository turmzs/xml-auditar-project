# Pasta de Testes - XMLs TESTES

Esta pasta contém diversos arquivos XML para teste da ferramenta **XML Auditar** (Assinador de XMLs A1 & A3).

## 📋 Descrição dos Casos de Teste

### NFSe (Notas Fiscais de Serviço Eletrônica)

#### ✅ Casos Corretos (sem erros)
- **nfse_correto_01.xml**: NFSe padrão com todas as retenções corretas (PIS, COFINS, INSS, IR)
- **nfse_correto_grande_valor_06.xml**: NFSe com valor alto (R$ 50.000) - teste de escalabilidade

#### ❌ Casos com Erros (para correção)
- **nfse_sem_retencao_02.xml**: **ERRO**: Faltam retenções de PIS/COFINS
- **nfse_retencao_incorreta_03.xml**: **ERRO**: Valores de retenção calculados incorretamente
- **nfse_pis_cofins_errado_07.xml**: **ERRO**: PIS e COFINS com alíquotas divergentes
- **nfse_iss_retido_11.xml**: ISS retido pela Prefeitura - teste de retenção municipal
- **nfse_manutencao_13.xml**: Serviço de manutenção com múltiplas retenções
- **nfse_deducoes_15.xml**: NFSe com deduções significativas (R$ 2.000 em deduções)
- **nfse_centavos_errados_17.xml**: **ERRO**: Divergência de centavos nos cálculos
- **nfse_valor_zero_09.xml**: Valor pequeno (R$ 100) - teste de valores mínimos
- **nfse_pronto_assinatura_19.xml**: NFSe correta e pronta para ser assinada

### NFe (Notas Fiscais Eletrônicas)

#### ✅ Casos Corretos
- **nfe_correto_04.xml**: NFe padrão com ICMS 18%, PIS e COFINS corretos
- **nfe_frete_14.xml**: NFe com serviço de frete e valor adicional
- **nfe_metalurgica_18.xml**: NFe de grande valor (R$ 303.125) - produto industrial

#### ❌ Casos com Erros
- **nfe_icms_incorreto_05.xml**: **ERRO**: Base do ICMS (vBC) diverge do valor tributável
- **nfe_pis_cofins_incorretos_10.xml**: **ERRO**: Bases de PIS/COFINS diferentes do ICMS
- **nfe_com_deducoes_08.xml**: NFe com desconto e reduções de valor

#### 🏥 Casos Especiais
- **nfe_grande_valor_12.xml**: Valor muito alto (R$ 509.000) - teste de limite de valores
- **nfe_alimentos_isento_16.xml**: Produto alimentício isento (ICMS 60 - sem cobrança)
- **nfe_pronto_assinatura_20.xml**: NFe sem assinatura - pronta para assinar

---

## 🎯 Cenários de Teste

### 1. **Teste de Validação**
Use os arquivos **corretos** para validar se a ferramenta reconhece XMLs válidos.

### 2. **Teste de Correção**
Use os arquivos com **ERRO** para verificar se a ferramenta consegue:
- Detectar as inconsistências
- Corrigir os valores
- Recalcular impostos corretamente

### 3. **Teste de Assinatura**
Use os arquivos **pronto_assinatura** para:
- Carregar com certificado A1 ou A3
- Assinar corretamente o XML
- Validar a integridade da assinatura

### 4. **Teste de Performance**
Use os arquivos de **grande_valor** para:
- Verificar se a ferramenta trata valores altos corretamente
- Testar limites de cálculo
- Validar centavos em operações matemáticas

### 5. **Teste de Casos Especiais**
- **Alimentos Isentos**: Verificar ICMS 60 (sem cobrança)
- **ISS Retido**: Validar retenção municipal
- **Deduções**: Testar cálculos com reduções de base

---

## 📊 Resumo dos Arquivos

| Nome | Tipo | Valor | Status | Obs |
|------|------|-------|--------|-----|
| nfse_correto_01 | NFSe | R$ 1.000 | ✅ Correto | Padrão com retenções |
| nfse_sem_retencao_02 | NFSe | R$ 5.000 | ❌ Erro | Faltam PIS/COFINS |
| nfse_retencao_incorreta_03 | NFSe | R$ 2.500 | ❌ Erro | Valores divergentes |
| nfe_correto_04 | NFe | R$ 6.363 | ✅ Correto | ICMS 18% |
| nfe_icms_incorreto_05 | NFe | R$ 6.263 | ❌ Erro | vBC divergente |
| nfse_correto_grande_valor_06 | NFSe | R$ 50.000 | ✅ Correto | Grande valor |
| nfse_pis_cofins_errado_07 | NFSe | R$ 10.000 | ❌ Erro | Alíquotas diferentes |
| nfe_com_deducoes_08 | NFe | R$ 5.948 | ✅ Correto | Com desconto R$ 600 |
| nfse_valor_zero_09 | NFSe | R$ 100 | ✅ Correto | Valor mínimo |
| nfe_pis_cofins_incorretos_10 | NFe | R$ 303.125 | ❌ Erro | Bases divergentes |
| nfse_iss_retido_11 | NFSe | R$ 3.500 | ✅ Correto | ISS retido |
| nfe_grande_valor_12 | NFe | R$ 509.000 | ✅ Correto | Grande valor |
| nfse_manutencao_13 | NFSe | R$ 750 | ✅ Correto | Múltiplas retenções |
| nfe_frete_14 | NFe | R$ 9.536 | ✅ Correto | Com frete |
| nfse_deducoes_15 | NFSe | R$ 15.000 | ✅ Correto | Deduções R$ 2.000 |
| nfe_alimentos_isento_16 | NFe | R$ 30.000 | ✅ Correto | ICMS 60 - Isento |
| nfse_centavos_errados_17 | NFSe | R$ 1.000 | ❌ Erro | Centavos divergentes |
| nfe_metalurgica_18 | NFe | R$ 303.125 | ✅ Correto | Industrial |
| nfse_pronto_assinatura_19 | NFSe | R$ 2.000 | ✅ Pronto | Para assinar |
| nfe_pronto_assinatura_20 | NFe | R$ 100.000 | ✅ Pronto | Para assinar |

---

## 🚀 Como Usar

1. **Carregar na GUI**: Selecione a pasta `XMLS TESTES` na ferramenta
2. **Processar em Lote**: Clique em "Processar" para corrigir todos os XMLs
3. **Verificar Relatório**: Revise os arquivos corrigidos e logs de erro
4. **Assinar**: Use a aba de Assinatura para re-assinar com seu certificado

---

## 📌 Notas Importantes

- ✅ Os XMLs **corretos** devem passar sem alterações
- ❌ Os XMLs com **erro** devem ser detectados e corrigidos
- 🔒 Os XMLs **pronto_assinatura** não possuem assinatura digital - adicione depois
- 💰 Verificar cálculos especialmente em valores com centavos (2 casas decimais)
- 📊 Testar tanto em **ambiente de teste (SPED)** quanto em **ambiente de produção**

---

## 📂 Estrutura Esperada

```
XMLS TESTES/
├── nfse_*.xml (10 arquivos)
├── nfe_*.xml (10 arquivos)
└── README.md (este arquivo)
```

**Criado em**: 26 de maio de 2026
**Ferramenta**: XML Auditar - Assinador de XMLs A1 & A3
