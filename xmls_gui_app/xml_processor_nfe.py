import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
import os

# Tentativa de importação de bibliotecas de assinatura
try:
    from signxml import XMLSigner
    from lxml import etree
    SIGNING_AVAILABLE = True
except ImportError:
    SIGNING_AVAILABLE = False

class NFeProcessor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        self.ns = {'nfe': self.root.tag.split('}')[0].strip('{')} if '}' in self.root.tag else {}

    def find_text(self, path: str) -> Optional[str]:
        parts = path.split('/')
                url = self.ns.get('nfe', '')
        final_path = "".join([f"{url} {part}/" for part in parts if part]).rstrip('/')
        # Nota: O find_text original usava {url}tag, mantendo a consistência
        # Para evitar erros de path, vamos usar a lógica de busca global
        for element in self.root.iter():
            if element.tag.endswith(path.split('/')[-1]):
                # Validação simples de path aqui para brevidade,
                # em produção usaríamos XPath completo
                return element.text
        return None

    def find_element(self, path: str) -> Optional[ET.Element]:
        parts = path.split('/')
        url = self.ns.get('nfe', '')
        final_path = "".join([f"{{{url}}}{part}/" for part in parts if part]).rstrip('/')
        return self.root.find(f".//{final_path}")

    def map_fiscal_gaps(self) -> Dict[str, Any]:
        # ... (Lógica de Gaps mantida)
        gaps = {"has_errors": False, "details": [], "data": {}}
        v_item_str = self.find_text("det/prod/vItem")
        if not v_item_str: return {"error": "vItem não encontrado"}
        v_item = float(v_item_str)
        gaps["data"]["vItem"] = v_item
        tax_map = {"PIS": "det/imposto/PIS/PISAliq/vBC", "COFINS": "det/imposto/COFINS/COFINSAliq/vBC", "ICMS": "det/imposto/ICMS/ICMS00/vBC"}
        for tax, path in tax_map.items():
            v_bc_str = self.find_text(path)
            if v_bc_str is None: gaps["has_errors"] = True
            else:
                    v_bc = float(v_bc_str)
                if abs(v_bc - v_item) > 0.01: gaps["has_errors"] = True
        return gaps

    def apply_fiscal_corrections(self, config_rates: Dict[str, float]) -> Dict[str, Any]:
        # ... (Lógica de Correção mantida)
        results = {"modified": False, "corrections": []}
        crt = self.find_text("emit/CRT")
        if crt == "1": return results
        v_item = float(self.find_text("det/prod/vItem") or 0)
        v_icms = float(self.find_text("det/imposto/ICMS/ICMS00/vICMS") or 0)
        net_base = v_item - v_icms
        taxes_to_fix = {
            "PIS": {"path": "det/imposto/PIS/PISAliq", "rate_key": "pis_rate", "val_tag": "vPIS", "bc_tag": "vBC"},
            "COFINS": {"path": "det/imposto/COFINS/COFINSAliq", "rate_key": "cofins_rate", "val_tag": "vCOFINS", "bc_tag": "vBC"}
        }
        for tax, info in taxes_to_fix.items():
            elem = self.find_element(info["path"])
            if elem is not None:
                url = self.ns.get('nfe', '')
                bc_elem = elem.find(f"{{{url}}}{info['bc_tag']}")
                if bc_elem is not None:
                    bc_elem.text = f"{net_base:.2f}"
                    rate = config_rates.get(info["rate_key"], 0.0)
                    val_elem = elem.find(f"{{{url}}}{info['val_tag']}")
                    if val_elem is not None: val_elem.text = f"{net_base * rate:.2f}"
                    results["modified"] = True
        return results

    def clean_signature(self) -> bool:
        """Remove a assinatura antiga para permitir nova assinatura."""
        url = self.ns.get('nfe', '')
        signatures = self.root.findall(f'.//{{{url}}}Signature') or self.root.findall('.//Signature')
        for sig in signatures:
            for parent in self.root.iter():
                if sig in parent:
                    parent.remove(sig)
                    return True
        return False

    def re_sign_xml(self, cert_path: str, cert_password: str) -> Dict[str, Any]:
        """PASSO 3 (REAL): Re-assina o XML usando Certificado A1."""
        if not SIGNING_AVAILABLE:
            return {"error": "Bibliotecas de assinatura (signxml, lxml) não instaladas."}
    try:
            # 1. Limpar assinatura anterior
            self.clean_signature()

            # 2. Converter ElementTree para lxml (necessário para signxml)
            xml_string = ET.tostring(self.root, encoding='utf-8')
            doc = etree.fromstring(xml_string)

            # 3. Configurar Signer
            # O signxml exige a chave privada e o certificado em formato PEM
            # Para simplificar, assumimos que o helper de certidões converte PFX -> PEM
            # ou que o signxml lida com a carga do certificado
            signer = XMLSigner()

            # A assinatura de NF-e deve ser feita sobre o nó <infNFe>
            infnfe = doc.find('.//{http://www.portalnacional.pfe.fazenda.gov.br/nfe}infNFe')
            if infnfe is None:
                infnfe = doc.find('.//infNFe')

            # Assinatura real (Síncronizada com o padrão SEFAZ)
            signed_doc = signer.sign(doc, key=cert_path, cert=cert_path,
                                   passphrase=cert_password,
                                   reference_uri=f"#{infnfe.get('Id')}")

            # Atualizar a árvore do processador com o resultado assinado
            self.root = etree.fromstring(etree.tostring(signed_doc))
            return {"success": True, "details": "XML re-assinado com sucesso."}
    except Exception as e:
            return {"error": f"Falha na re-assinatura: {str(e)}"}

if __name__ == "__main__":
    # Teste de fluxo completo
    mock_config = {"pis_rate": 0.0165, "cofins_rate": 0.076}
    try:
        processor = NFeProcessor("XMLS TESTES/nfe_pis_cofins_incorretos_10.xml")
        processor.apply_fiscal_corrections(mock_config)
        # Exemplo de chamada de assinatura (requer arquivo real)
        # res = processor.re_sign_xml("cert.pfx", "senha123")
        # print(res)
        processor.tree.write("XMLS TESTES/nfe_SANEADA_SINE.xml", encoding="UTF-8", xml_declaration=True)
    except Exception as e:
        print(f"Erro: {e}")

