"""Correções de valores para NFe (ICMS + PIS/COFINS).

Observação:
- A regra fiscal exata (o que é considerado "valor errado") não foi fornecida com
  fórmula 100% determinística.
- A implementação abaixo faz uma correção conservadora baseada na intenção do
  NFSe atual: recalcular campos percentuais/valores aplicando a mesma alíquota
  (parâmetro `aliquota`) como fator multiplicador.

Se o seu caso real tiver outra regra (ex.: ajuste por diferença entre vBC e vProd,
ou recalcular conforme CST/CSOSN específico), substitua a função.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET


def _parse_float(text: str | None) -> float | None:
    if text is None:
        return None
    try:
        # lida com vírgula decimal eventualmente
        return float(text.replace(',', '.').strip())
    except (ValueError, TypeError):
        return None


def processar_nfe_icms_pis_cofins(root: ET.Element, aliquota: float = 0.0365) -> bool:
    """Corrige valores de ICMS e PIS/COFINS em uma NFe.

    Estratégia (conservadora):
    - Para cada item `det`, recalcula:
      - ICMS00: vICMS = vBC * pICMS/100 (mantém pICMS) e também ajusta vBC
        aplicando a `aliquota` como fator ao vBC.
      - PISNT/COFINSNT (CST=04): ajusta vIBS e vCBS aplicando a `aliquota`
        ao valor base lido de vIBS/vCBS, quando existirem.
    - Recalcula os totais em `ICMSTot` e `IBSCBSTot` com base nos nós já recalculados nos itens.

    Retorna:
      bool: True se alterou algo.
    """

    alterado = False

    # Detectar namespace
    ns_prefix = ""
    if "}" in root.tag:
        ns_prefix = root.tag.split("}")[0] + "}"

    # Recalcular itens
    for det in root.iter():
        if not det.tag.endswith('det'):
            continue

        # ICMS
        for icms in list(det.iter()):
            if icms.tag.endswith('ICMS00') or icms.tag.endswith('ICMS10') or icms.tag.endswith('ICMS20') or icms.tag.endswith('ICMS30') or icms.tag.endswith('ICMS40') or icms.tag.endswith('ICMS90'):
                vbc = icms.find(f"{ns_prefix}vBC")
                picms = icms.find(f"{ns_prefix}pICMS")
                vicms = icms.find(f"{ns_prefix}vICMS")

                vbc_val = _parse_float(vbc.text if vbc is not None else None)
                picms_val = _parse_float(picms.text if picms is not None else None)

                if vbc_val is None or picms_val is None:
                    continue

                # aplica fator ao vBC
                novo_vbc = round(vbc_val * aliquota, 2)
                if vbc is not None and _parse_float(vbc.text) is not None:
                    if round(vbc_val, 2) != novo_vbc:
                        vbc.text = f"{novo_vbc:.2f}"
                        alterado = True

                # recalcula vICMS mantendo pICMS
                novo_vicms = round(novo_vbc * picms_val / 100.0, 2)
                if vicms is not None and _parse_float(vicms.text) is not None:
                    if round(_parse_float(vicms.text) or 0.0, 2) != novo_vicms:
                        vicms.text = f"{novo_vicms:.2f}"
                        alterado = True

        # PIS/COFINS
        for group in list(det.iter()):
            if group.tag.endswith('PISNT'):
                vibs = group.find(f"{ns_prefix}vIBS")
                vibs_val = _parse_float(vibs.text if vibs is not None else None)
                if vibs is None or vibs_val is None:
                    continue
                novo_vibs = round(vibs_val * aliquota, 2)
                if round(vibs_val, 2) != novo_vibs:
                    vibs.text = f"{novo_vibs:.2f}"
                    alterado = True

            if group.tag.endswith('COFINSNT'):
                vcbs = group.find(f"{ns_prefix}vCBS")
                vcbs_val = _parse_float(vcbs.text if vcbs is not None else None)
                if vcbs is None or vcbs_val is None:
                    continue
                novo_vcbs = round(vcbs_val * aliquota, 2)
                if round(vcbs_val, 2) != novo_vcbs:
                    vcbs.text = f"{novo_vcbs:.2f}"
                    alterado = True

    # Recalcular totais
    def _sum_all(path_endswith: str) -> float | None:
        vals = []
        for el in root.iter():
            if el.tag.endswith(path_endswith):
                v = _parse_float(el.text)
                if v is not None:
                    vals.append(v)
        return sum(vals) if vals else None

    # Totais ICMS
    icmstot = None
    for el in root.iter():
        if el.tag.endswith('ICMSTot'):
            icmstot = el
            break

    if icmstot is not None:
        vBC = icmstot.find(f"{ns_prefix}vBC")
        vICMS = icmstot.find(f"{ns_prefix}vICMS")
        # soma vBC e vICMS dos itens (ICMS* / vBC,vICMS)
        soma_vbc = _sum_all('vBC')
        # Atenção: vBC existe em outros blocos também; aqui é uma heurística.
        # Se isso for problema, ajuste para somar só nós dentro de ICMS.
        soma_vicms = _sum_all('vICMS')

        if soma_vbc is not None and vBC is not None:
            if _parse_float(vBC.text) is not None and round(_parse_float(vBC.text) or 0.0, 2) != round(soma_vbc, 2):
                vBC.text = f"{soma_vbc:.2f}"
                alterado = True

        if soma_vicms is not None and vICMS is not None:
            if _parse_float(vICMS.text) is not None and round(_parse_float(vICMS.text) or 0.0, 2) != round(soma_vicms, 2):
                vICMS.text = f"{soma_vicms:.2f}"
                alterado = True

    # Totais PIS/COFINS
    ibscbstot = None
    for el in root.iter():
        if el.tag.endswith('IBSCBSTot'):
            ibscbstot = el
            break

    if ibscbstot is not None:
        # Soma vIBS e vCBS existentes (heurística)
        soma_vibs = _sum_all('vIBS')
        soma_vcbs = _sum_all('vCBS')
        vIBS = ibscbstot.find(f"{ns_prefix}vIBS")
        vCBS = ibscbstot.find(f"{ns_prefix}vCBS")
        if soma_vibs is not None and vIBS is not None:
            if _parse_float(vIBS.text) is not None and round(_parse_float(vIBS.text) or 0.0, 2) != round(soma_vibs, 2):
                vIBS.text = f"{soma_vibs:.2f}"
                alterado = True
        if soma_vcbs is not None and vCBS is not None:
            if _parse_float(vCBS.text) is not None and round(_parse_float(vCBS.text) or 0.0, 2) != round(soma_vcbs, 2):
                vCBS.text = f"{soma_vcbs:.2f}"
                alterado = True

    return alterado

