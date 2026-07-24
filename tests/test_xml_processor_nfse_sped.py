"""Testes unitários para xml_processor_nfse_sped."""
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "xmls_gui_app"))

from xml_processor_nfse_sped import processar_nfse_sped_nacional  # noqa: E402

SPED_NS = "http://www.sped.fazenda.gov.br/nfse"


def make_nfse_sped_xml(vServ="1000.00", outras_retencoes="0.00", iss_retido="2"):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="{SPED_NS}">
  <infNFSe>
    <valores>
      <vServ>{vServ}</vServ>
      <vISSRet>{outras_retencoes}</vISSRet>
    </valores>
    <iss>
      <issRetido>{iss_retido}</issRetido>
    </iss>
  </infNFSe>
</NFSe>"""


class TestProcessarNfseSped(unittest.TestCase):
    def test_returns_bool(self):
        root = ET.fromstring(make_nfse_sped_xml())
        result = processar_nfse_sped_nacional(root, aliquota_iss=0.0365)
        self.assertIsInstance(result, bool)

    def test_does_not_crash_on_minimal_xml(self):
        root = ET.fromstring(make_nfse_sped_xml())
        # Não deve levantar exceção
        processar_nfse_sped_nacional(root, aliquota_iss=0.05)

    def test_does_not_crash_on_missing_fields(self):
        xml = f'<root xmlns="{SPED_NS}"><vazio/></root>'
        root = ET.fromstring(xml)
        # Não deve levantar exceção mesmo faltando campos
        try:
            processar_nfse_sped_nacional(root, aliquota_iss=0.05)
        except Exception as e:
            self.fail(f"Levantou exceção inesperada: {e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)