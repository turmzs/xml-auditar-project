"""Testes unitários para xml_processor.XMLProcessor.

Cobre:
- detectar_tipo (NFe / NFSe SPED / NFSe Prefeitura / Desconhecido)
- remover_assinatura
- close() (liberação de recursos)
- process_batch end-to-end com certificado mock
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "xmls_gui_app"))

from certificate_handler import CertificateHandler  # noqa: E402
from xml_processor import XMLProcessor  # noqa: E402

# Namespaces
NFE_NS = "http://www.portalfiscal.inf.br/nfe"
SPED_NS = "http://www.sped.fazenda.gov.br/nfse"


class MockCert(CertificateHandler):
    """Certificado mock que simula um A1 carregado, sem PyKCS11/signxml."""

    def __init__(self):
        super().__init__()
        self.cert_type = "A1"
        self.loaded = True

    def validate(self):
        return self.loaded, "ok" if self.loaded else "not loaded"

    def get_subject(self):
        return "CN=Mock"


def make_minimal_nfe():
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="{NFE_NS}">
  <NFe xmlns="{NFE_NS}">
    <infNFe>
      <emit><CRT>3</CRT></emit>
      <det nItem="1">
        <prod><vItem>100.00</vItem></prod>
        <imposto>
          <PIS><PISAliq><vBC>100.00</vBC><vPIS>1.65</vPIS></PISAliq></PIS>
        </imposto>
      </det>
    </infNFe>
  </NFe>
</nfeProc>"""


def make_minimal_nfse_sped():
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rps xmlns="{SPED_NS}">
  <infRps>
    <valores>
      <vServ>1000.00</vServ>
    </valores>
  </infRps>
</rps>"""


def make_minimal_nfse_prefeitura():
    return """<?xml version="1.0" encoding="UTF-8"?>
<ConsultarNfseResposta xmlns="http://www.abrasf.org.br/nfse.xsd">
  <Nfse>
    <InfNfse>
      <Valores>
        <ValorServicos>1000.00</ValorServicos>
        <OutrasRetencoes>0.00</OutrasRetencoes>
      </Valores>
    </InfNfse>
  </Nfse>
</ConsultarNfseResposta>"""


class TestDetectarTipo(unittest.TestCase):
    def setUp(self):
        self.proc = XMLProcessor(MockCert())

    def test_detects_nfe(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(make_minimal_nfe())
        self.assertEqual(self.proc.detectar_tipo(root), "NFE")

    def test_detects_nfse_sped(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(make_minimal_nfse_sped())
        self.assertEqual(self.proc.detectar_tipo(root), "NFSE_SPED")

    def test_detects_nfse_prefeitura(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring(make_minimal_nfse_prefeitura())
        self.assertEqual(self.proc.detectar_tipo(root), "NFSE_PREFEITURA")

    def test_unknown_type(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring("<root/>")
        self.assertEqual(self.proc.detectar_tipo(root), "DESCONHECIDO")


class TestRemoverAssinatura(unittest.TestCase):
    def setUp(self):
        self.proc = XMLProcessor(MockCert())

    def test_removes_signature(self):
        import xml.etree.ElementTree as ET
        xml = f"""<root xmlns="{NFE_NS}">
            <Signature xmlns="http://www.w3.org/2000/09/xmldsig#"/>
            <other>foo</other>
        </root>"""
        root = ET.fromstring(xml)
        removeu = self.proc.remover_assinatura(root)
        self.assertTrue(removeu)
        # Não deve haver mais nenhuma Signature
        for elem in root.iter():
            self.assertNotIn("Signature", elem.tag)

    def test_no_signature_returns_false(self):
        import xml.etree.ElementTree as ET
        root = ET.fromstring("<root/>")
        self.assertFalse(self.proc.remover_assinatura(root))


class TestProcessBatch(unittest.TestCase):
    def setUp(self):
        self.proc = XMLProcessor(MockCert())

    def test_process_batch_empty_folder(self):
        with tempfile.TemporaryDirectory() as in_dir, tempfile.TemporaryDirectory() as out_dir:
            # pasta vazia: deve terminar com stats.total == 0
            self.proc.process_batch(
                pasta_entrada=in_dir,
                pasta_corrigidos=out_dir,
                aliquota=0.0365,
                gerar_relatorio=False,
            )
            self.assertEqual(self.proc.stats["total"], 0)

    def test_process_batch_with_nfse_prefeitura(self):
        """NFSe prefeitura com valor de retenção incorreto deve ser corrigido."""
        with tempfile.TemporaryDirectory() as in_dir, tempfile.TemporaryDirectory() as out_dir:
            src = os.path.join(in_dir, "nfse_01.xml")
            with open(src, "w", encoding="utf-8") as f:
                f.write(make_minimal_nfse_prefeitura())
            self.proc.process_batch(
                pasta_entrada=in_dir,
                pasta_corrigidos=out_dir,
                aliquota=0.05,  # 5%
                gerar_relatorio=False,
            )
            self.assertEqual(self.proc.stats["total"], 1)
            # vServ=1000 * 0.05 = 50 (OutrasRetencoes deve virar 50).
            # Nota: ElementTree usa prefixo ``ns0:`` ao reescrever, então
            # verificamos a presença do valor independentemente do prefixo.
            out_file = os.path.join(out_dir, "nfse_01.xml")
            self.assertTrue(os.path.exists(out_file))
            with open(out_file, encoding="utf-8") as f:
                content = f.read()
            import re as _re
            match = _re.search(
                r"<(?:\w+:)?OutrasRetencoes>(\d+\.\d+)</(?:\w+:)?OutrasRetencoes>",
                content,
            )
            self.assertIsNotNone(match, f"OutrasRetencoes nao encontrada em: {content}")
            self.assertEqual(match.group(1), "50.00")
            # Stats devem ter contabilizado
            self.assertIn(self.proc.stats["corrigidos"], (0, 1))


class TestClose(unittest.TestCase):
    def test_close_without_session_is_noop(self):
        proc = XMLProcessor(MockCert())
        # Não deve levantar exceção
        proc.close()

    def test_close_clears_attrs(self):
        class CertWithFakeSession(MockCert):
            def __init__(self):
                super().__init__()
                self.session = type("FakeSession", (), {
                    "logout": lambda self: None,
                    "closeSession": lambda self: None,
                })()

        cert = CertWithFakeSession()
        proc = XMLProcessor(cert)
        proc.close()
        # Após close, session deve ter sido limpa
        self.assertIsNone(cert.session)


if __name__ == "__main__":
    unittest.main(verbosity=2)