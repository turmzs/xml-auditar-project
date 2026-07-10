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

try:
    import PyKCS11
    PKCS11_AVAILABLE = True
except ImportError:
    PKCS11_AVAILABLE = False

class NFeProcessor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        self.ns = {'nfe': self.root.tag.split('}')[0].strip('{')} if '}' in self.root.tag else {}

    def find_text(self, path: str) -> Optional[str]:
        for element in self.root.iter():
            if element.tag.endswith(path.split('/')[-1]):
                return element.text
        return None

    def find_element(self, path: str) -> Optional[ET.Element]:
        parts = path.split('/')
        url = self.ns.get('nfe', '')
        final_path = "".join([f"{{{url}}}{part}/" for part in parts if part]).rstrip('/')
        return self.root.find(f".//{final_path}")

    def map_fiscal_gaps(self) -> Dict[str, Any]:
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
                    old_bc = bc_elem.text
                    bc_elem.text = f"{net_base:.2f}"
                    
                    rate = config_rates.get(info["rate_key"], 0.0)
                    val_elem = elem.find(f"{{{url}}}{info['val_tag']}")
                    if val_elem is not None:
                        old_val = val_elem.text
                        new_val = f"{net_base * rate:.2f}"
                        val_elem.text = new_val
                        
                        results["corrections"].append({
                            "tax": tax,
                            "bc_before": old_bc,
                            "bc_after": bc_elem.text,
                            "val_before": old_val,
                            "val_after": new_val
                        })
                    results["modified"] = True
        return results

    def clean_signature(self) -> bool:
        url = self.ns.get('nfe', '')
        signatures = self.root.findall(f'.//{{{url}}}Signature') or self.root.findall('.//Signature')
        for sig in signatures:
            for parent in self.root.iter():
                if sig in parent:
                    parent.remove(sig)
                    return True
        return False

    def re_sign_xml(self, cert_path: str, cert_password: str) -> Dict[str, Any]:
        """Assinatura para Certificados A1 (.pfx)"""
        if not SIGNING_AVAILABLE:
            return {"error": "Bibliotecas de assinatura não instaladas."}
        try:
            self.clean_signature()
            xml_string = ET.tostring(self.root, encoding='utf-8')
            doc = etree.fromstring(xml_string)
            signer = XMLSigner()
            infnfe = doc.find('.//{http://www.portalnacional.pfe.fazenda.gov.br/nfe}infNFe') or doc.find('.//infNFe')
            signed_doc = signer.sign(doc, key=cert_path, cert=cert_path, passphrase=cert_password, reference_uri=f"#{infnfe.get('Id')}")
            self.root = etree.fromstring(etree.tostring(signed_doc))
            return {"success": True, "details": "XML re-assinado com A1."}
        except Exception as e:
            return {"error": f"Falha A1: {str(e)}"}

    def re_sign_xml_a3(self, dll_path: str, pin: str) -> Dict[str, Any]:
        """Assinatura para Certificados A3 (Token/Smartcard)"""
        if not PKCS11_AVAILABLE:
            return {"error": "Biblioteca PyKCS11 não instalada."}
        if not SIGNING_AVAILABLE:
            return {"error": "Biblioteca signxml/lxml não instalada."}

        try:
            self.clean_signature()
            
            # 1. Inicializar PKCS11
            pkcs11 = PyKCS11.PyKCS11Lib()
            pkcs11.load(dll_path)
            
            slots = pkcs11.getSlots()
            if not slots:
                return {"error": "Nenhum token A3 encontrado."}
            
            # Tenta abrir o primeiro slot disponível
            slot = slots[0]
            session = pkcs11.openSession(slot)
            session.login(pin)
            
            # 2. Localizar chave privada para assinatura
            # Nota: Em um cenário real, filtraríamos pelo Label do certificado
            priv_keys = session.findObjects([PyKCS11.CKA_CLASS: PyKCS11.CKO_PRIVATE_KEY])
            if not priv_keys:
                session.logout()
                session.closeSession()
                return {"error": "Chave privada não encontrada no token."}
            
            priv_key = priv_keys[0]
            
            # Para A3, o signxml precisa de um wrapper que chame o PKCS11 
            # para assinar o digest. Como isso é complexo de integrar via arquivo, 
            # a implementação de A3 geralmente exige o uso de ferramentas como 
            # 'xmldsig' via subprocesso ou bridge JNI. 
            # Abaixo simulamos a chamada de assinatura via hardware.
            
            # Implementação simplificada de fluxo:
            # O signxml.XMLSigner pode aceitar objetos de chave, mas para A3 
            # a assinatura ocorre dentro do token. 
            
            # TODO: Integrar com bridge de assinatura digital (como o assinador do governo)
            # ou implementar o wrapper de digest do PKCS11.
            
            session.logout()
            session.closeSession()
            
            return {"error": "Lógica de ponte PKCS11 -> signxml requer bridge de digest instalada."}
        except Exception as e:
            return {"error": f"Falha A3: {str(e)}"}

if __name__ == "__main__":
    mock_config = {"pis_rate": 0.0165, "cofins_rate": 0.076}
    try:
        processor = NFeProcessor("XMLS TESTES/nfe_pis_cofins_incorretos_10.xml")
        processor.apply_fiscal_corrections(mock_config)
        processor.tree.write("XMLS TESTES/nfe_SANEADA_SINE.xml", encoding="UTF-8", xml_declaration=True)
    except Exception as e:
        print(f"Erro: {e}")
```