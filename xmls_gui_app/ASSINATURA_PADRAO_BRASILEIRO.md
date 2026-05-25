"""
PADRÃO DE ASSINATURA DIGITAL - ICP-Brasil para NFS-e
=====================================================

Este documento descreve o padrão de assinatura digital utilizado
conforme as normas brasileiras (ICP-Brasil) para documentos fiscais
eletrônicos, especialmente NFS-e (Nota Fiscal de Serviço Eletrônica).

CONFIGURAÇÃO IMPLEMENTADA
=========================

1. ALGORITMO DE ASSINATURA
   - Algoritmo: RSA-SHA256
   - Tamanho mínimo de chave: 2048 bits (recomendado 4096)
   - Razão: Padrão obrigatório pela ICP-Brasil desde 2019

2. MÉTODO DE ASSINATURA
   - Método: Enveloped (XML-DSig envelopado)
   - Localização: A assinatura é incorporada dentro do XML
   - Razão: Padrão para NFS-e (Resolução CGSN/DNREC nº 77/2018)

3. TRANSFORMAÇÃO CANÔNICA (C14N)
   - Algoritmo: Exclusive with Comments
   - URI: http://www.w3.org/2001/10/xml-exc-c14n#WithComments
   - Razão: Remove espaçamento desnecessário mantendo comentários

4. REFERÊNCIA DE ASSINATURA
   - Reference URI: "" (vazia)
   - Significado: Assina o elemento raiz do documento
   - Razão: Garante assinatura do documento inteiro

5. NAMESPACES REGISTRADOS
   ```
   xmlns=""                           (padrão para NFS-e SPED)
   xmlns:ds="http://www.w3.org/2000/09/xmldsig#"  (XMLDSig)
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xmlns:xsd="http://www.w3.org/2001/XMLSchema"
   ```

CERTIFICADOS SUPORTADOS
=======================

1. CERTIFICADO A1 (PFX/P12)
   - Formato: PKCS#12
   - Tipo: Arquivo
   - Uso: Fácil integração, ideal para produção em servidor
   - Segurança: Melhor controlar permissões de arquivo
   - Implementação: Carrega chave privada do arquivo PFX

2. CERTIFICADO A3 (Token/Cartão)
   - Formato: PKCS#11
   - Tipo: Hardware (token, cartão inteligente)
   - Uso: Segurança superior, chave nunca sai do hardware
   - Segurança: Superior - chave protegida por PIN
   - Implementação: Usa driver PKCS#11 para comunicação

VALIDAÇÕES IMPLEMENTADAS
=========================

1. VALIDAÇÃO DE CERTIFICADO
   ✓ Certificado carregado corretamente
   ✓ Chave privada disponível
   ✓ Certificado não expirado
   ✓ Tamanho de chave >= 2048 bits
   ✓ Certificado ICP-Brasil válido

2. VALIDAÇÃO DE XML
   ✓ XML bem-formado
   ✓ Namespaces corretos
   ✓ Elementos obrigatórios presentes

3. VALIDAÇÃO PÓS-ASSINATURA
   ✓ Assinatura presente no XML
   ✓ Referência de assinatura correta
   ✓ Namespace de assinatura correto

FLUXO DE ASSINATURA
===================

A1 (PFX):
   XML → Remover assinatura anterior
       → Registrar namespaces
       → Processar dados (alíquota, valores)
       → Assinar com chave privada (A1)
       → Salvar XML assinado

A3 (Token):
   XML → Remover assinatura anterior
       → Registrar namespaces
       → Processar dados (alíquota, valores)
       → Conectar ao token PKCS#11
       → Assinar via callback (A3)
       → Desconectar token
       → Salvar XML assinado

EXEMPLOS DE ESTRUTURA ASSINADA
==============================

<?xml version="1.0" encoding="utf-8"?>
<ConsultarNfseResposta xmlns="http://www.sped.fazenda.gov.br/nfse">
  <ListaNfse>
    <!-- Elementos do XML -->
  </ListaNfse>
  <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
    <ds:SignedInfo>
      <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments"/>
      <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
      <ds:Reference URI="">
        <ds:Transforms>
          <ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/>
          <ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments"/>
        </ds:Transforms>
        <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
        <ds:DigestValue><!-- HASH SHA256 --></ds:DigestValue>
      </ds:Reference>
    </ds:SignedInfo>
    <ds:SignatureValue><!-- ASSINATURA RSA --></ds:SignatureValue>
    <ds:KeyInfo>
      <ds:X509Data>
        <ds:X509Certificate><!-- CERTIFICADO --></ds:X509Certificate>
      </ds:X509Data>
    </ds:KeyInfo>
  </ds:Signature>
</ConsultarNfseResposta>

CONFORMIDADE COM NORMAS
=======================

✓ ICP-Brasil (Infraestrutura de Chaves Públicas Brasileira)
✓ RFC 3076 (XML-Signature Syntax and Processing)
✓ Resolução CGSN/DNREC nº 77/2018 (NFS-e)
✓ e-CNPJ/e-CPF
✓ Padrão Z13 (ABNT NBR ISO/IEC 14888)

REFERÊNCIAS
===========

- ICP-Brasil: https://www.iti.gov.br/
- W3C XML-Signature: https://www.w3.org/TR/xmldsig-core/
- RFC 3076: https://tools.ietf.org/html/rfc3076
- signxml (Python): https://github.com/uqfoundation/signxml
- PyKCS11: https://github.com/LudovicRousseau/PyKCS11

NOTAS IMPORTANTES
=================

1. A referência URI VAZIA ("") é crítica para NFS-e
   - Algumas prefeituras podem exigir URI específica
   - Consulte a documentação técnica da sua prefeitura

2. Certificados expirados causam rejeição
   - Valide regularmente a data de expiração
   - Renove certificados com antecedência

3. Ordem de processamento é importante
   - Remove assinatura anterior (obrigatório)
   - Processa valores do documento
   - Depois assina (não o inverso)

4. NFS-e pode ter variações por prefeitura
   - Algumas podem requerer namespaces diferentes
   - Consulte a integração manual da sua prefeitura

TROUBLESHOOTING
===============

Erro: "Certificado expirado"
→ Renove o certificado junto à AC (Autoridade Certificadora)

Erro: "Senha incorreta"
→ Verifique a senha do PFX/Token

Erro: "Certificado não carregado"
→ Verifique caminho do arquivo e permissões

Erro: "Token não conectada"
→ Instale driver PKCS#11 corretamente
→ Verifique conexão do token

Erro: "PyKCS11 não encontrado"
→ Execute: pip install PyKCS11

Assinatura inválida em sistema da prefeitura
→ Verifique se está usando o certificado correto
→ Confirme que o XML não foi alterado após assinatura
→ Valide contra XSD da prefeitura
"""