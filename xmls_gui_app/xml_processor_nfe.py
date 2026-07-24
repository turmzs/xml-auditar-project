"""Processador de NF-e (Nota Fiscal Eletrônica).

Este módulo implementa a classe NFeProcessor usada pelo orquestrador
(xml_processor.py) para corrigir valores de PIS/COFINS em NF-e.

A implementação usa xml.etree.ElementTree (stdlib) e busca elementos
por nome local, com validação simples de hierarquia quando necessário.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional


# Tenta importar signxml/lxml para a função de assinatura
try:
    from signxml import XMLSigner
    from lxml import etree

    SIGNING_AVAILABLE = True
except ImportError:
    SIGNING_AVAILABLE = False


class NFeProcessor:
    """Processa NF-e para correção de bases de PIS/COFINS."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        # Namespace da NF-e
        if "}" in self.root.tag:
            self.ns = {"nfe": self.root.tag.split("}")[0].strip("{")}
        else:
            self.ns = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _local_name(self, tag: str) -> str:
        """Retorna o nome local (sem namespace) de uma tag."""
        return tag.split("}")[-1] if "}" in tag else tag

    def find_text(self, path: str) -> Optional[str]:
        """Busca o texto de um elemento a partir de um path 'a/b/c'.

        Cada segmento do path é buscado em profundidade, mas validando
        a sequência completa da raiz até o segmento alvo. Usa o
        ``ElementPath`` do ElementTree para garantir a navegação correta
        da hierarquia.
        """
        parts = [p for p in path.split("/") if p]
        if not parts:
            return None

        # Caminho XPath relativo simples (caminha na hierarquia real)
        node = self.root
        for segment in parts:
            child_found = None
            # Tenta encontrar o segmento entre os filhos diretos de ``node``
            for child in node:
                if self._local_name(child.tag) == segment:
                    child_found = child
                    break
            if child_found is None:
                # Se não achou direto, busca em profundidade (mais lento,
                # mas necessário quando o caller não conhece a hierarquia
                # exata — ex.: ``det/imposto/PIS`` vs ``infNFe/det/...``)
                for descendant in node.iter():
                    if descendant is node:
                        continue
                    if self._local_name(descendant.tag) == segment:
                        # Verifica que é realmente descendente
                        # (já garantido por iter()) e tenta navegar dali
                        child_found = descendant
                        break
                if child_found is None:
                    return None
            node = child_found
        return node.text

    def find_element(self, path: str) -> Optional[ET.Element]:
        """Busca um elemento a partir de um path 'a/b/c'."""
        parts = [p for p in path.split("/") if p]
        if not parts:
            return None
        last = parts[-1]
        url = self.ns.get("nfe", "")

        if len(parts) == 1:
            needle = f"{{{url}}}{last}" if url else last
            return self.root.find(f".//{needle}")

        def _search(node: ET.Element, idx: int) -> Optional[ET.Element]:
            target = parts[idx]
            needle = f"{{{url}}}{target}" if url else target
            for child in node.iter(needle):
                if idx == len(parts) - 1:
                    return child
                found = _search(child, idx + 1)
                if found is not None:
                    return found
            return None

        return _search(self.root, 0)

    # ------------------------------------------------------------------
    # Auditoria / correção
    # ------------------------------------------------------------------
    def map_fiscal_gaps(self) -> Dict[str, Any]:
        """Mapeia divergências entre vItem e as bases de cálculo."""
        gaps: Dict[str, Any] = {
            "has_errors": False,
            "details": [],
            "data": {},
        }
        v_item_str = self.find_text("det/prod/vItem")
        if not v_item_str:
            return {"error": "vItem não encontrado", "has_errors": True, "data": {}}

        try:
            v_item = float(v_item_str)
        except (TypeError, ValueError):
            return {"error": f"vItem inválido: {v_item_str}", "has_errors": True, "data": {}}

        gaps["data"]["vItem"] = v_item
        tax_map = {
            "PIS": "det/imposto/PIS/PISAliq/vBC",
            "COFINS": "det/imposto/COFINS/COFINSAliq/vBC",
            "ICMS": "det/imposto/ICMS/ICMS00/vBC",
        }
        for tax, path in tax_map.items():
            v_bc_str = self.find_text(path)
            if v_bc_str is None:
                gaps["has_errors"] = True
                gaps["details"].append(f"{tax}: vBC não encontrado em {path}")
                continue
            try:
                v_bc = float(v_bc_str)
            except (TypeError, ValueError):
                gaps["has_errors"] = True
                gaps["details"].append(f"{tax}: vBC inválido '{v_bc_str}'")
                continue
            if abs(v_bc - v_item) > 0.01:
                gaps["has_errors"] = True
                gaps["details"].append(
                    f"{tax}: vBC {v_bc} diverge de vItem {v_item}"
                )
        return gaps

    def apply_fiscal_corrections(self, config_rates: Dict[str, float]) -> Dict[str, Any]:
        """Aplica correções fiscais de PIS/COFINS.

        Para cada item ``det``:
        - Calcula a base líquida como ``vItem - vICMS`` (se houver).
        - Ajusta ``vBC`` e ``vPIS``/``vCOFINS`` aplicando a alíquota.
        - Não processa Simples Nacional (CRT == 1).

        Retorna ``{"modified": bool, "corrections": [...]}`` no mesmo
        formato esperado pelo orquestrador ``xml_processor.py``.
        """
        results: Dict[str, Any] = {"modified": False, "corrections": []}

        crt = self.find_text("emit/CRT")
        if crt == "1":
            # Simples Nacional: sem correção
            return results

        # Recolhe os itens <det> uma única vez
        url = self.ns.get("nfe", "")
        det_tag = f"{{{url}}}det" if url else "det"

        for det in list(self.root.iter(det_tag)):
            v_item_text = None
            for child in det.iter():
                if self._local_name(child.tag) == "vItem":
                    v_item_text = child.text
                    break
            if v_item_text is None:
                continue
            try:
                v_item = float(v_item_text)
            except (TypeError, ValueError):
                continue

            v_icms = 0.0
            icms00 = None
            for child in det.iter():
                if self._local_name(child.tag) == "ICMS00":
                    icms00 = child
                    break
            if icms00 is not None:
                for sub in icms00.iter():
                    if self._local_name(sub.tag) == "vICMS":
                        try:
                            v_icms = float(sub.text or 0)
                        except (TypeError, ValueError):
                            v_icms = 0.0
                        break

            net_base = round(v_item - v_icms, 2)

            taxes_to_fix = {
                "PIS": {
                    "path": "imposto/PIS/PISAliq",
                    "rate_key": "pis_rate",
                    "val_tag": "vPIS",
                    "bc_tag": "vBC",
                },
                "COFINS": {
                    "path": "imposto/COFINS/COFINSAliq",
                    "rate_key": "cofins_rate",
                    "val_tag": "vCOFINS",
                    "bc_tag": "vBC",
                },
            }

            for tax, info in taxes_to_fix.items():
                parts = info["path"].split("/")
                group = det
                ok = True
                for p in parts:
                    found = None
                    needle = f"{{{url}}}{p}" if url else p
                    for child in group.iter(needle):
                        found = child
                        break
                    if found is None:
                        ok = False
                        break
                    group = found
                if not ok or group is None:
                    continue

                bc_tag = info["bc_tag"]
                val_tag = info["val_tag"]
                bc_needle = f"{{{url}}}{bc_tag}" if url else bc_tag
                val_needle = f"{{{url}}}{val_tag}" if url else val_tag

                bc_elem = None
                val_elem = None
                for child in group:
                    if child.tag == bc_needle:
                        bc_elem = child
                    elif child.tag == val_needle:
                        val_elem = child

                if bc_elem is None:
                    continue

                old_bc = bc_elem.text
                bc_elem.text = f"{net_base:.2f}"

                rate = config_rates.get(info["rate_key"], 0.0) or 0.0
                if val_elem is not None:
                    old_val = val_elem.text
                    new_val = f"{round(net_base * rate, 2):.2f}"
                    val_elem.text = new_val
                    results["corrections"].append(
                        {
                            "tax": tax,
                            "bc_before": old_bc,
                            "bc_after": bc_elem.text,
                            "val_before": old_val,
                            "val_after": new_val,
                        }
                    )
                else:
                    results["corrections"].append(
                        {
                            "tax": tax,
                            "bc_before": old_bc,
                            "bc_after": bc_elem.text,
                            "val_before": None,
                            "val_after": None,
                        }
                    )
                results["modified"] = True

        return results

    # ------------------------------------------------------------------
    # Assinatura (mantida para compatibilidade / uso standalone)
    # ------------------------------------------------------------------
    def clean_signature(self) -> bool:
        """Remove a assinatura antiga para permitir nova assinatura.

        A tag ``<Signature>`` vive no namespace XMLDSig
        (``http://www.w3.org/2000/09/xmldsig#``), que é diferente do
        namespace da NF-e. Procuramos por nome local ``Signature`` em
        todos os elementos, garantindo compatibilidade.
        """
        signatures = [
            elem for elem in self.root.iter()
            if self._local_name(elem.tag) == "Signature"
        ]
        if not signatures:
            return False
        # Remove apenas a primeira assinatura encontrada
        for sig in signatures:
            for parent in self.root.iter():
                if sig in list(parent):
                    parent.remove(sig)
                    return True
        return False

    def re_sign_xml(self, cert_path: str, cert_password: str) -> Dict[str, Any]:
        """Re-assina o XML usando Certificado A1 (PFX).

        Espera que ``cert_path`` aponte para um arquivo PEM contendo
        chave privada + certificado, ou que signxml consiga carregá-lo.
        """
        if not SIGNING_AVAILABLE:
            return {"error": "Bibliotecas de assinatura (signxml, lxml) não instaladas."}
        try:
            self.clean_signature()

            # Converte ElementTree para lxml (necessário para signxml)
            xml_string = ET.tostring(self.root, encoding="utf-8")
            doc = etree.fromstring(xml_string)

            signer = XMLSigner()

            # A assinatura de NF-e deve ser feita sobre o nó <infNFe>
            infnfe = doc.find(
                ".//{http://www.portalnacional.pfe.fazenda.gov.br/nfe}infNFe"
            )
            if infnfe is None:
                infnfe = doc.find(".//infNFe")

            if infnfe is None:
                return {"error": "Elemento <infNFe> não encontrado para assinar."}

            signed_doc = signer.sign(
                doc,
                key=cert_path,
                cert=cert_path,
                passphrase=cert_password,
                reference_uri=f"#{infnfe.get('Id')}",
            )

            self.root = etree.fromstring(etree.tostring(signed_doc))
            return {"success": True, "details": "XML re-assinado com sucesso."}
        except Exception as e:  # noqa: BLE001
            return {"error": f"Falha na re-assinatura: {e}"}


if __name__ == "__main__":
    # Teste de fluxo completo
    mock_config = {"pis_rate": 0.0165, "cofins_rate": 0.076}
    try:
        processor = NFeProcessor("XMLS TESTES/nfe_pis_cofins_incorretos_10.xml")
        res = processor.apply_fiscal_corrections(mock_config)
        print(f"Modified: {res['modified']}, corrections: {len(res['corrections'])}")
        # processor.tree.write("XMLS TESTES/nfe_SANEADA_SINE.xml", encoding="UTF-8", xml_declaration=True)
    except Exception as e:  # noqa: BLE001
        print(f"Erro: {e}")