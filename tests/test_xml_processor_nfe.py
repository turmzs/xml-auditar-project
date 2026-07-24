"""Testes unitários para xml_processor_nfe.NFeProcessor.

Cobre:
- find_text / find_element (busca hierárquica)
- map_fiscal_gaps (auditoria de bases de cálculo)
- apply_fiscal_corrections (correção de PIS/COFINS)
- clean_signature (remoção de assinaturas antigas)
"""
import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

# Adiciona xmls_gui_app ao path para importar diretamente
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "xmls_gui_app"))

from xml_processor_nfe import NFeProcessor  # noqa: E402

# Namespace real da NF-e 4.00
NFE_NS = "http://www.portalfiscal.inf.br/nfe"


def make_nfe_xml(
    vItem="100.00",
    vICMS="0.00",
    vBC_PIS="50.00",
    vPIS="0.00",
    vBC_COFINS="50.00",
    vCOFINS="0.00",
    crt="3",
) -> str:
    """Gera XML NF-e mínimo para testes."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="{NFE_NS}" versao="4.00">
  <NFe xmlns="{NFE_NS}">
    <infNFe Id="NFe123" versao="4.00">
      <ide>
        <cUF>35</cUF>
        <natOp>VENDA</natOp>
      </ide>
      <emit>
        <CNPJ>12345678000199</CNPJ>
        <CRT>{crt}</CRT>
      </emit>
      <det nItem="1">
        <prod>
          <cProd>P1</cProd>
          <vItem>{vItem}</vItem>
        </prod>
        <imposto>
          <ICMS>
            <ICMS00>
              <vBC>{vItem}</vBC>
              <vICMS>{vICMS}</vICMS>
            </ICMS00>
          </ICMS>
          <PIS>
            <PISAliq>
              <CST>01</CST>
              <vBC>{vBC_PIS}</vBC>
              <pPIS>1.65</pPIS>
              <vPIS>{vPIS}</vPIS>
            </PISAliq>
          </PIS>
          <COFINS>
            <COFINSAliq>
              <CST>01</CST>
              <vBC>{vBC_COFINS}</vBC>
              <pCOFINS>7.60</pCOFINS>
              <vCOFINS>{vCOFINS}</vCOFINS>
            </COFINSAliq>
          </COFINS>
        </imposto>
      </det>
    </infNFe>
  </NFe>
</nfeProc>
"""


class TestNFeProcessorFindText(unittest.TestCase):
    def test_finds_simple_path(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(make_nfe_xml())
            path = f.name
        try:
            proc = NFeProcessor(path)
            self.assertEqual(proc.find_text("emit/CNPJ"), "12345678000199")
        finally:
            os.unlink(path)

    def test_finds_nested_path(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(make_nfe_xml())
            path = f.name
        try:
            proc = NFeProcessor(path)
            self.assertEqual(proc.find_text("emit/CRT"), "3")
            self.assertEqual(proc.find_text("det/prod/vItem"), "100.00")
            self.assertEqual(
                proc.find_text("det/imposto/PIS/PISAliq/vBC"),
                "50.00",
            )
        finally:
            os.unlink(path)

    def test_returns_none_for_missing(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(make_nfe_xml())
            path = f.name
        try:
            proc = NFeProcessor(path)
            self.assertIsNone(proc.find_text("emit/IE"))
        finally:
            os.unlink(path)


class TestNFeProcessorMapGaps(unittest.TestCase):
    def test_no_gap_when_bc_equals_vItem(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(make_nfe_xml(vItem="100.00", vBC_PIS="100.00", vBC_COFINS="100.00"))
            path = f.name
        try:
            proc = NFeProcessor(path)
            gaps = proc.map_fiscal_gaps()
            self.assertFalse(gaps.get("has_errors", False), gaps)
            self.assertEqual(gaps["data"]["vItem"], 100.00)
        finally:
            os.unlink(path)

    def test_detects_divergence(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            # vItem=100 mas vBC_PIS=50 (divergência!)
            f.write(make_nfe_xml(vItem="100.00", vBC_PIS="50.00", vBC_COFINS="100.00"))
            path = f.name
        try:
            proc = NFeProcessor(path)
            gaps = proc.map_fiscal_gaps()
            self.assertTrue(gaps.get("has_errors"))
            details = " ".join(gaps.get("details", []))
            self.assertIn("PIS", details)
        finally:
            os.unlink(path)


class TestNFeProcessorApplyCorrections(unittest.TestCase):
    def test_corrections_returns_proper_format(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(make_nfe_xml(
                vItem="100.00", vICMS="18.00",
                vBC_PIS="50.00", vPIS="0.83",
                vBC_COFINS="50.00", vCOFINS="3.80",
            ))
            path = f.name
        try:
            proc = NFeProcessor(path)
            res = proc.apply_fiscal_corrections({"pis_rate": 0.0165, "cofins_rate": 0.076})
            # Estrutura esperada pelo orquestrador
            self.assertIn("modified", res)
            self.assertIn("corrections", res)
            self.assertIsInstance(res["modified"], bool)
            self.assertIsInstance(res["corrections"], list)
            self.assertTrue(res["modified"])
            # Deve ter 2 correções (PIS e COFINS)
            self.assertEqual(len(res["corrections"]), 2)
            for c in res["corrections"]:
                self.assertIn("tax", c)
                self.assertIn("bc_before", c)
                self.assertIn("bc_after", c)
                self.assertIn("val_before", c)
                self.assertIn("val_after", c)
                # Base deve ter sido corrigida para 100 - 18 = 82
                self.assertEqual(c["bc_after"], "82.00")
        finally:
            os.unlink(path)

    def test_simples_nacional_skipped(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(make_nfe_xml(crt="1"))  # Simples Nacional
            path = f.name
        try:
            proc = NFeProcessor(path)
            res = proc.apply_fiscal_corrections({"pis_rate": 0.0165, "cofins_rate": 0.076})
            self.assertFalse(res["modified"])
            self.assertEqual(res["corrections"], [])
        finally:
            os.unlink(path)

    def test_correction_pis_value(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(make_nfe_xml(
                vItem="200.00", vICMS="0.00",
                vBC_PIS="100.00", vPIS="1.65",
                vBC_COFINS="100.00", vCOFINS="7.60",
            ))
            path = f.name
        try:
            proc = NFeProcessor(path)
            res = proc.apply_fiscal_corrections({"pis_rate": 0.0165, "cofins_rate": 0.076})
            pis_corr = next(c for c in res["corrections"] if c["tax"] == "PIS")
            # Base líquida: 200 - 0 = 200
            self.assertEqual(pis_corr["bc_after"], "200.00")
            # Valor PIS: 200 * 0.0165 = 3.30
            self.assertEqual(pis_corr["val_after"], "3.30")
        finally:
            os.unlink(path)


class TestNFeProcessorCleanSignature(unittest.TestCase):
    def test_removes_signature(self):
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="{NFE_NS}">
  <NFe>
    <infNFe>
      <Signature xmlns="http://www.w3.org/2000/09/xmldsig#">
        <SignedInfo><SigValue>FAKE</SigValue></SignedInfo>
      </Signature>
    </infNFe>
  </NFe>
</nfeProc>"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(xml)
            path = f.name
        try:
            proc = NFeProcessor(path)
            removed = proc.clean_signature()
            self.assertTrue(removed)
            # Aplica de novo: já não há signature
            self.assertFalse(proc.clean_signature())
        finally:
            os.unlink(path)

    def test_no_signature_returns_false(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
            f.write(make_nfe_xml())
            path = f.name
        try:
            proc = NFeProcessor(path)
            self.assertFalse(proc.clean_signature())
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)