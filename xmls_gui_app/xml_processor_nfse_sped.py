"""Processador de NFSe SPED Nacional com correção de retenções.

Função especializada em corrigir valores de retenção em RPS (Recibos de Provisório de Serviço)
no padrão SPED Nacional (http://www.sped.fazenda.gov.br/nfse).

Aplica as alíquotas corretas para:
- PIS: 1.65%
- COFINS: 7.60%
- INSS: 11.00%
- IR: 1.50%
- CSLL: 3.00%
- ISS: 3.65% (configurável)
"""

import xml.etree.ElementTree as ET


def _parse_float(text):
    """Parse float com suporte a vírgula decimal."""
    if text is None:
        return None
    try:
        return float(str(text).replace(',', '.').strip())
    except (ValueError, TypeError):
        return None


def processar_nfse_sped_nacional(root, aliquota_iss=0.0365):
    """Processa e corrige valores de retenção em NFSe SPED Nacional.
    
    Estratégia:
    - Calcula PIS, COFINS, INSS, IR, CSLL com base no ValorServicos
    - Ajusta ValorLiquidoNfse = ValorServicos - Deduções - Retenções - ValorIss
    
    Args:
        root: Elemento raiz do XML (RPS)
        aliquota_iss: Alíquota de ISS (padrão 3.65%)
    
    Returns:
        bool: True se houve alteração
    """
    
    alterado = False
    
    # Detectar namespace
    ns = ""
    if "}" in root.tag:
        ns = root.tag.split("}")[0] + "}"
    
    # Alíquotas fixas
    ALIQUOTA_PIS = 0.0165      # 1.65%
    ALIQUOTA_COFINS = 0.0760   # 7.60%
    ALIQUOTA_INSS = 0.1100     # 11.00%
    ALIQUOTA_IR_BASE = 0.015   # 1.50%
    ALIQUOTA_CSLL_BASE = 0.03  # 3.00%
    
    # Procurar o bloco Valores
    valores_elem = None
    for elem in root.iter():
        if elem.tag.endswith("Valores"):
            valores_elem = elem
            break
    
    if valores_elem is None:
        return False
    
    # Extrair valores principais
    valor_servicos = None
    valor_deducoes = None
    valor_iss = None
    valor_liquido = None
    iss_retido = 0
    
    elementos_retenção = {
        "ValorPis": None,
        "ValorCofins": None,
        "ValorInss": None,
        "ValorIr": None,
        "ValorCsll": None,
    }
    
    for child in valores_elem:
        tag_name = child.tag.split("}")[-1]
        valor = _parse_float(child.text)
        
        if tag_name == "ValorServicos":
            valor_servicos = valor
        elif tag_name == "ValorDeducoes":
            valor_deducoes = valor
        elif tag_name == "ValorIss":
            valor_iss = valor
        elif tag_name == "ValorLiquidoNfse":
            valor_liquido = valor
        elif tag_name == "IssRetido":
            iss_retido = int(child.text or 0)
        elif tag_name in elementos_retenção:
            elementos_retenção[tag_name] = (child, valor)
    
    if valor_servicos is None:
        return False
    
    if valor_deducoes is None:
        valor_deducoes = 0.0
    
    # Calcular valores de retenção
    novo_pis = round(valor_servicos * ALIQUOTA_PIS, 2)
    novo_cofins = round(valor_servicos * ALIQUOTA_COFINS, 2)
    novo_inss = round(valor_servicos * ALIQUOTA_INSS, 2)
    
    # IR e CSLL são calculados sobre (ValorServicos - Deduções - INSS)
    base_ir_csll = valor_servicos - valor_deducoes - novo_inss
    novo_ir = round(base_ir_csll * ALIQUOTA_IR_BASE, 2)
    novo_csll = round(base_ir_csll * ALIQUOTA_CSLL_BASE, 2)
    
    # Calcular ISS
    novo_iss = round(valor_servicos * aliquota_iss, 2)
    
    # Total de retenções
    total_retencoes = novo_pis + novo_cofins + novo_inss + novo_ir + novo_csll
    
    # Novo valor líquido
    if iss_retido:
        # ISS é retido pela prefeitura, não entra no cálculo
        novo_valor_liquido = round(valor_servicos - valor_deducoes - total_retencoes, 2)
    else:
        # ISS é deduzido do valor líquido
        novo_valor_liquido = round(valor_servicos - valor_deducoes - total_retencoes - novo_iss, 2)
    
    # Atualizar elementos de retenção
    for tag_name in ["ValorPis", "ValorCofins", "ValorInss", "ValorIr", "ValorCsll"]:
        elem_tuple = elementos_retenção[tag_name]
        novo_valor = {
            "ValorPis": novo_pis,
            "ValorCofins": novo_cofins,
            "ValorInss": novo_inss,
            "ValorIr": novo_ir,
            "ValorCsll": novo_csll,
        }[tag_name]
        
        if elem_tuple is not None:
            elem, valor_antigo = elem_tuple
            valor_formatado = f"{novo_valor:.2f}"
            if elem.text != valor_formatado:
                elem.text = valor_formatado
                alterado = True
        else:
            # Criar elemento se não existir
            novo_elem = ET.SubElement(valores_elem, f"{ns}{tag_name}")
            novo_elem.text = f"{novo_valor:.2f}"
            alterado = True
    
    # Atualizar ISS
    iss_elem = None
    for child in valores_elem:
        if child.tag.split("}")[-1] == "ValorIss":
            iss_elem = child
            break
    
    novo_iss_formatado = f"{novo_iss:.2f}"
    if iss_elem is not None:
        if iss_elem.text != novo_iss_formatado:
            iss_elem.text = novo_iss_formatado
            alterado = True
    else:
        novo_elem = ET.SubElement(valores_elem, f"{ns}ValorIss")
        novo_elem.text = novo_iss_formatado
        alterado = True
    
    # Atualizar valor líquido
    valor_liquido_elem = None
    for child in valores_elem:
        if child.tag.split("}")[-1] == "ValorLiquidoNfse":
            valor_liquido_elem = child
            break
    
    novo_liquido_formatado = f"{novo_valor_liquido:.2f}"
    if valor_liquido_elem is not None:
        if valor_liquido_elem.text != novo_liquido_formatado:
            valor_liquido_elem.text = novo_liquido_formatado
            alterado = True
    else:
        novo_elem = ET.SubElement(valores_elem, f"{ns}ValorLiquidoNfse")
        novo_elem.text = novo_liquido_formatado
        alterado = True
    
    return alterado
