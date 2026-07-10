# 🏗️ Estrutura XML - Referência Rápida

## NFSe (RPS - Recibo Provisório de Serviço)

### Estrutura Mínima

```xml
<?xml version="1.0" encoding="utf-8"?>
<RPS xmlns="http://www.sped.fazenda.gov.br/nfse" 
     xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <InfRPS Id="RPS1">
    <Identificacao>
      <Numero>1</Numero>
      <Serie>A</Serie>
      <Tipo>1</Tipo>
    </Identificacao>
    <DataEmissao>2026-05-26T10:30:00</DataEmissao>
    <Status>1</Status>
    <Servico>
      <Valores>
        <ValorServicos>1000.00</ValorServicos>
        <ValorDeducoes>0.00</ValorDeducoes>
        <ValorPis>16.50</ValorPis>
        <ValorCofins>76.00</ValorCofins>
        <ValorInss>110.00</ValorInss>
        <ValorIr>0.00</ValorIr>
        <ValorCsll>0.00</ValorCsll>
        <IssRetido>0</IssRetido>
        <ValorIss>36.50</ValorIss>
        <ValorLiquidoNfse>760.00</ValorLiquidoNfse>
        <Aliquota>0.0365</Aliquota>
      </Valores>
      <ItemListaServico>17.01</ItemListaServico>
      <Descricao>Serviço de consultoria</Descricao>
      <CodigoMunicipio>3550308</CodigoMunicipio>
    </Servico>
    <Prestador>
      <CpfCnpj><Cnpj>11222333000181</Cnpj></CpfCnpj>
      <InscricaoMunicipal>123456789</InscricaoMunicipal>
    </Prestador>
    <Tomador>
      <Identificacao>
        <CpfCnpj><Cnpj>12345678000191</Cnpj></CpfCnpj>
      </Identificacao>
      <RazaoSocial>Empresa Tomadora</RazaoSocial>
      <Endereco>
        <Endereco>Rua das Flores</Endereco>
        <Numero>100</Numero>
        <Bairro>Centro</Bairro>
        <Cidade>3550308</Cidade>
        <Uf>SP</Uf>
        <Cep>01310100</Cep>
      </Endereco>
    </Tomador>
  </InfRPS>
</RPS>
```

### Elementos Obrigatórios (NFS-e)

| Elemento | Descrição | Formato | Exemplo |
|----------|-----------|---------|---------|
| Numero | Número sequencial | 1-15 dígitos | 123456 |
| Serie | Série da RPS | 1-5 caracteres | A, B, C |
| Tipo | Tipo (1=RPS) | 1 dígito | 1 |
| DataEmissao | Data/hora | ISO 8601 | 2026-05-26T10:30:00 |
| Status | Status (1=Normal) | 1 dígito | 1 |
| ValorServicos | Valor base | Decimal 2 casas | 1000.00 |
| Aliquota | Alíquota ISS | Decimal 4 casas | 0.0365 |
| CNPJ (Prestador) | CNPJ com 14 dígitos | 14 dígitos | 11222333000181 |
| CNPJ (Tomador) | CNPJ com 14 dígitos | 14 dígitos | 12345678000191 |

---

## NFe (Nota Fiscal Eletrônica)

### Estrutura Mínima

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
  <infNFe Id="NFe35260526123456780123456789012345678901244569" versao="4.00">
    <ide>
      <cUF>35</cUF>
      <AAMM>202605</AAMM>
      <CNPJ>11222333000181</CNPJ>
      <mod>55</mod>
      <serie>1</serie>
      <nNF>123456</nNF>
      <dhEmi>2026-05-26T09:30:00-03:00</dhEmi>
      <tpNF>1</tpNF>
      <idDest>1</idDest>
      <cMunFG>3550308</cMunFG>
      <tpImp>1</tpImp>
      <tpEmis>1</tpEmis>
      <cDV>9</cDV>
      <tpAmb>2</tpAmb>
      <finNFe>1</finNFe>
      <indFinal>1</indFinal>
      <indPres>1</indPres>
      <procEmi>0</procEmi>
    </ide>
    <emit>
      <CNPJ>11222333000181</CNPJ>
      <xNome>Empresa Fornecedora LTDA</xNome>
      <xFant>Fornecedora</xFant>
      <enderEmit>
        <xLgr>Rua da Indústria</xLgr>
        <nro>500</nro>
        <xBairro>Bom Retiro</xBairro>
        <cMun>3550308</cMun>
        <xMun>São Paulo</xMun>
        <UF>SP</UF>
        <CEP>01234567</CEP>
      </enderEmit>
      <IE>123456789119</IE>
      <CRT>3</CRT>
    </emit>
    <dest>
      <CNPJ>12345678000191</CNPJ>
      <xNome>Empresa Compradora LTDA</xNome>
      <enderDest>
        <xLgr>Rua das Compras</xLgr>
        <nro>250</nro>
        <xBairro>Centro</xBairro>
        <cMun>3550308</cMun>
        <xMun>São Paulo</xMun>
        <UF>SP</UF>
        <CEP>01310100</CEP>
      </enderDest>
      <IE>987654321098</IE>
      <indIEDest>1</indIEDest>
    </dest>
    <det nItem="1">
      <prod>
        <code>0001</code>
        <xProd>Produto Teste</xProd>
        <NCM>12345678</NCM>
        <CFOP>5102</CFOP>
        <u>UN</u>
        <qCom>100.0000</qCom>
        <vUnCom>50.00</vUnCom>
        <vItem>5000.00</vItem>
        <indTot>1</indTot>
      </prod>
      <imposto>
        <ICMS>
          <ICMS00>
            <orig>0</orig>
            <CST>00</CST>
            <modBC>0</modBC>
            <vBC>5000.00</vBC>
            <pICMS>18.0000</pICMS>
            <vICMS>900.00</vICMS>
          </ICMS00>
        </ICMS>
        <PIS>
          <PISAliq>
            <CST>01</CST>
            <vBC>5000.00</vBC>
            <pPIS>1.65</pPIS>
            <vPIS>82.50</vPIS>
          </PISAliq>
        </PIS>
        <COFINS>
          <COFINSAliq>
            <CST>01</CST>
            <vBC>5000.00</vBC>
            <pCOFINS>7.60</pCOFINS>
            <vCOFINS>380.00</vCOFINS>
          </COFINSAliq>
        </COFINS>
      </imposto>
    </det>
    <total>
      <ICMSTot>
        <vBC>5000.00</vBC>
        <vICMS>900.00</vICMS>
        <vProd>5000.00</vProd>
        <vPIS>82.50</vPIS>
        <vCOFINS>380.00</vCOFINS>
        <vNF>6362.50</vNF>
      </ICMSTot>
    </total>
    <transp>
      <modFrete>0</modFrete>
    </transp>
    <pag>
      <detPag>
        <tPag>01</tPag>
        <vPag>6362.50</vPag>
      </detPag>
    </pag>
  </infNFe>
</NFe>
```

### Elementos Críticos (NFe)

| Elemento | Descrição | Formato | Observação |
|----------|-----------|---------|-----------|
| Id (infNFe) | Identificador único | NFe + CNPJ + modelo + série + número | Máximo 44 caracteres |
| cUF | Código UF | 2 dígitos | 35 = SP |
| CNPJ (emit) | CNPJ Emitente | 14 dígitos | Obrigatório |
| mod | Modelo | 55 ou 65 | 55 = NF-e |
| nNF | Número NF | 1-9 dígitos | Sequencial |
| dhEmi | Data/hora emissão | ISO 8601 com TZ | 2026-05-26T09:30:00-03:00 |
| vBC | Base ICMS | Decimal 2 casas | Deve = vProd - vDesc |
| pICMS | Alíquota ICMS | Decimal 4 casas | Ex: 18.0000 |
| vICMS | Valor ICMS | Decimal 2 casas | = vBC × pICMS / 100 |
| vNF | Valor Total | Decimal 2 casas | Soma final |

---

## 🔐 Assinatura Digital (ds:Signature)

Após assinatura, será adicionado:

```xml
<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <ds:SignedInfo>
    <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
    <ds:SignatureMethod Algorithm="http://www.w3.org/2000/09/xmldsig#rsa-sha1"/>
    <ds:Reference URI="#NFe35260526123456780123456789012345678901244569">
      <ds:Transforms>
        <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
        <ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/>
      </ds:Transforms>
      <ds:DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
      <ds:DigestValue>3ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef123456==</ds:DigestValue>
    </ds:Reference>
  </ds:SignedInfo>
  <ds:SignatureValue>MIIFZAYJKoZIhvc... (certificado base64)</ds:SignatureValue>
  <ds:KeyInfo>
    <ds:X509Data>
      <ds:X509Certificate>MIIFXTCCBEWg... (chave pública base64)</ds:X509Certificate>
    </ds:X509Data>
  </ds:KeyInfo>
</ds:Signature>
```

---

## 💾 Namespaces Importantes

```xml
<!-- NFS-e SPED (Padrão Nacional) -->
xmlns="http://www.sped.fazenda.gov.br/nfse"
xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"

<!-- NF-e (Padrão SEFAZ) -->
xmlns="http://www.portalfiscal.inf.br/nfe"
xmlns:ds="http://www.w3.org/2000/09/xmldsig#"
```

---

## 🎯 Códigos Comuns

### Tipo de Nota Fiscal (tpNF)
- `1` = Saída
- `0` = Entrada

### Modelo (mod)
- `55` = NF-e (Eletrônica)
- `65` = NFC-e (Consumidor)

### Tipo de Emissão (tpEmis)
- `1` = Normal
- `2` = Contingência

### Ambiente (tpAmb)
- `1` = Produção
- `2` = Homologação (Testes)

### CST ICMS
- `00` = Tributada integralmente
- `10` = Tributada com ST
- `20` = Com redução de base
- `40` = Isenta
- `60` = ICMS 60 (sem cobrança)

### CST PIS/COFINS
- `01` = Alíquota normal
- `08` = Isento

---

## 📝 Validações de Campo

### CNPJ
- Exatamente 14 dígitos
- Válido (algoritmo de verificação)
- Ativo na Receita Federal

### Data/Hora
- Formato ISO 8601: `YYYY-MM-DDTHH:mm:ss-TZ`
- Com timezone: `-03:00` para São Paulo
- Não pode ser data futura

### Valores Monetários
- Máximo 2 casas decimais
- Separador decimal: ponto (.)
- Sem separador de milhar
- Exemplo: `1234567.89`

### Códigos Municipais
- 7 dígitos (IBGE)
- São Paulo: 3550308

---

## ✅ Checklist de Validação

- [ ] XML bem formado (sem erros de sintaxe)
- [ ] Namespaces corretos
- [ ] Todos os campos obrigatórios presentes
- [ ] Valores formatados corretamente (2 casas decimais)
- [ ] CNPJ válido
- [ ] Data não futura
- [ ] Somas verificadas (vNF = somatório correto)
- [ ] Assinatura válida (se presente)

---

**Documento de Referência**
**Data**: 26 de maio de 2026
