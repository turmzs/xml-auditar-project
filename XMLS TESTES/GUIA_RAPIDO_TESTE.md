# 🧪 Guia Rápido de Teste - XML Auditar

## 📝 Checklist de Teste

### ✅ Teste 1: Validação de XMLs Corretos
Carregue estes arquivos e verifique se **nenhuma alteração** é feita:
```
✓ nfse_correto_01.xml
✓ nfse_correto_grande_valor_06.xml
✓ nfe_correto_04.xml
✓ nfe_com_deducoes_08.xml
✓ nfe_metalurgica_18.xml
```

**Resultado esperado**: 
- ✅ Status: "OK" (sem alterações)
- Nenhuma mensagem de erro
- Valores mantidos intactos

---

### ❌ Teste 2: Detecção e Correção de Erros
Carregue estes arquivos e verifique se os **erros são detectados e corrigidos**:
```
✗ nfse_sem_retencao_02.xml (Faltam PIS/COFINS)
✗ nfse_retencao_incorreta_03.xml (Valores divergentes)
✗ nfe_icms_incorreto_05.xml (vBC divergente)
✗ nfse_pis_cofins_errado_07.xml (Alíquotas erradas)
✗ nfe_pis_cofins_incorretos_10.xml (Bases divergentes)
✗ nfse_centavos_errados_17.xml (Centavos incorretos)
```

**Resultado esperado**:
- ⚠️ Status: "CORRIGIDO"
- Mensagens indicando valores ajustados
- Novos valores recalculados conforme alíquota 3.65%
- Arquivo salvo com sufixo `_corrigido`

---

### 🔒 Teste 3: Assinatura Digital
Carregue estes arquivos para testar a re-assinatura:
```
📝 nfse_pronto_assinatura_19.xml
📝 nfe_pronto_assinatura_20.xml
```

**Resultado esperado**:
- XML carregado sem assinatura prévia
- Após assinatura: `<ds:Signature>...</ds:Signature>` adicionado
- QRCode atualizado (NFe)
- Arquivo marcado como "ASSINADO"

---

### 📊 Teste 4: Performance com Grandes Valores
Carregue estes arquivos para testar cálculos em larga escala:
```
💰 nfse_correto_grande_valor_06.xml (R$ 50.000)
💰 nfe_grande_valor_12.xml (R$ 509.000)
💰 nfe_metalurgica_18.xml (R$ 303.125)
```

**Resultado esperado**:
- ✅ Sem erros de arredondamento
- Centavos calculados corretamente
- Performance aceitável

---

### 🏥 Teste 5: Casos Especiais
Carregue estes arquivos para testar cenários específicos:

#### 5a. Produto Isento de ICMS
```
nfe_alimentos_isento_16.xml (ICMS 60 - sem cobrança)
```
**Esperado**: vICMS = 0.00, mas PIS/COFINS = 0.00 também

#### 5b. ISS Retido pela Prefeitura
```
nfse_iss_retido_11.xml (IssRetido = 1)
```
**Esperado**: ISS subtraído do valor líquido (Prefeitura faz retenção)

#### 5c. NFe com Frete
```
nfe_frete_14.xml (vOutro = 200.00)
```
**Esperado**: Valor adicional incluído no cálculo corretamente

#### 5d. Deduções Significativas
```
nfse_deducoes_15.xml (Deduções = R$ 2.000)
```
**Esperado**: Valor lançado como dedução, reduzindo base de cálculo

---

## 🎯 Validações Automáticas

A ferramenta deve verificar:

### NFSe (NFS-e SPED)
- [ ] ValorServicos > 0
- [ ] ValorIss = ValorServicos × Aliquota (com tolerância de R$ 0,01)
- [ ] ValorPis calculado corretamente (1.65% padrão)
- [ ] ValorCofins calculado corretamente (7.60% padrão)
- [ ] ValorInss calculado corretamente (11% padrão)
- [ ] ValorLiquidoNfse = ValorServicos - (retenções) - ValorIss
- [ ] Se IssRetido = 1, então ValorIss não entra no líquido

### NFe (NF-e Padrão)
- [ ] vBC = base do ICMS
- [ ] vICMS = vBC × pICMS / 100
- [ ] vPIS = (valor_base_pis) × 1.65% / 100
- [ ] vCOFINS = (valor_base_cofins) × 7.60% / 100
- [ ] vNF = vProd - vDesc + vFrete + vOutro ± impostos
- [ ] Assinatura válida (se presente)

---

## 📈 Relatório Esperado

Após processar toda a pasta, o relatório deve mostrar:

```
====== RELATÓRIO DE PROCESSAMENTO ======
Total de arquivos: 20
✅ OK (sem alterações): 12
⚠️ CORRIGIDOS: 6
❌ ERROS: 0
📝 PRONTOS PARA ASSINATURA: 2

Detalhes:
✅ nfse_correto_01.xml - OK
⚠️ nfse_sem_retencao_02.xml - CORRIGIDO (PIS/COFINS ajustados)
⚠️ nfse_retencao_incorreta_03.xml - CORRIGIDO (Retenções recalculadas)
✅ nfe_correto_04.xml - OK
⚠️ nfe_icms_incorreto_05.xml - CORRIGIDO (ICMS ajustado)
...

Valores Totais:
- Valor original: R$ 1.234.567,89
- Correções aplicadas: R$ 45.678,90
- Taxa de erro: 3.7%
```

---

## 🔍 Checklist de Teste Completo

- [ ] Todos os XMLs **corretos** mantêm status "OK"
- [ ] Todos os XMLs com **erro** são corrigidos
- [ ] Centavos calculados com precisão (até 0,01)
- [ ] Alíquotas aplicadas conforme configurado (padrão 3.65%)
- [ ] Assinatura funcionando (A1 e A3)
- [ ] Relatório gera corretamente
- [ ] Não há travamentos ou crashes
- [ ] Performance aceitável (20 arquivos < 5 segundos)

---

## 🚀 Executando os Testes

### Opção 1: GUI
```bash
python run_gui.py
# 1. Selecione: c:\Users\artur.nascimento\Desktop\XML CORRECT\XMLS TESTES
# 2. Clique: "Processar"
# 3. Revise os arquivos gerados em: XMLS TESTES\CORRIGIDOS
```

### Opção 2: CLI (se disponível)
```bash
python -m xmls_gui_app.xml_processor XMLS TESTES/
```

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique se o certificado está carregado
2. Revise o log de erros
3. Valide o XML manualmente em: https://www.sefaz.gov.br/
4. Abra uma issue com o arquivo problemático

---

**Última atualização**: 26 de maio de 2026
**Versão de teste**: 1.0
**Compatibilidade**: XML Auditar 1.0+
