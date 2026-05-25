"""
Processador de NFe (Nota Fiscal Eletrônica) - Estrutura Federal
"""

import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

try:
    from signxml import XMLSigner, methods
    from cryptography.hazmat.primitives import serialization
    HAS_SIGNXML = True
except ImportError:
    HAS_SIGNXML = False


class XMLProcessorNFe:
    """Processador especializado para NFe (Nota Fiscal Eletrônica)."""

    def __init__(self, cert_handler, output_callback=None):
        """
        Inicializa processador de NFe.
        
        Args:
            cert_handler: CertificateA1 ou CertificateA3
            output_callback: Função para logging (opcional)
        """
        self.cert_handler = cert_handler
        self.log = output_callback or print
        
        # Estatísticas
        self.stats = {
            'total': 0,
            'assinados': 0,
            'erros': 0,
            'ja_assinados': 0
        }

    def registrar_namespaces(self):
        """Registra namespaces padrão de NFe."""
        ns_map = {
            'ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsd': 'http://www.w3.org/2001/XMLSchema',
            '': 'http://www.portalfiscal.inf.br/nfe'  # Default namespace
        }
        
        for prefix, uri in ns_map.items():
            ET.register_namespace(prefix, uri)

    def remover_assinatura_nfe(self, root):
        """
        Remove assinatura anterior da NFe (dentro de Signature).
        
        Returns:
            bool: True se tinha assinatura anterior
        """
        tinha_assinatura = False
        
        # Procurar por Signature em qualquer namespace
        for parent in root.iter():
            for child in list(parent):
                if 'Signature' in child.tag:
                    parent.remove(child)
                    tinha_assinatura = True
        
        return tinha_assinatura

    def assinar_nfe(self, root):
        """
        Assina NFe com certificado A1.
        
        Padrão federal (ICP-Brasil):
        - Assinatura envolve (enveloped)
        - Referencia o elemento infNFe
        - RSA-SHA256
        
        Args:
            root: Elemento raiz <nfeProc>
            
        Returns:
            Raiz assinada ou original se erro
        """
        if not HAS_SIGNXML or self.cert_handler.private_key is None:
            return root

        try:
            # Converter chave e certificado para PEM
            pem_key = self.cert_handler.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            pem_cert = self.cert_handler.certificate.public_bytes(serialization.Encoding.PEM)

            # Encontrar elemento infNFe (é o que será assinado)
            inf_nfe = None
            nfe_ns = ''
            
            for elem in root.iter():
                if elem.tag.endswith('infNFe'):
                    inf_nfe = elem
                    if '}' in elem.tag:
                        nfe_ns = elem.tag.split('}')[0] + '}'
                    break
            
            if inf_nfe is None:
                self.log("  ✗ Elemento infNFe não encontrado")
                return root

            # Adicionar Id ao infNFe se não tiver
            if 'Id' not in inf_nfe.attrib:
                # Extrair chave NFe do atributo Id existente se houver
                chave_nfe = root.get('Id', 'NFe-id')
                inf_nfe.set('Id', chave_nfe)

            # Configuração padrão federal para NFe
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256",
                c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments",
            )

            # Assinar com referência ao infNFe
            inf_id = inf_nfe.get('Id')
            reference_uri = f"#{inf_id}" if inf_id else ""

            signed_root = signer.sign(
                inf_nfe,
                key=pem_key,
                cert=pem_cert,
                reference_uri=reference_uri
            )
            
            # Substituir elemento assinado na árvore
            nfe_parent = None
            for parent in root.iter():
                if signed_root in list(parent):
                    nfe_parent = parent
                    break
            
            if nfe_parent is None:
                # Substituir direto na raiz se for filho direto
                for i, child in enumerate(list(root)):
                    if child.tag.endswith('infNFe'):
                        root[i] = signed_root
                        break
            
            self.log("  ✓ NFe assinada com sucesso (A1 - Federal)")
            return root

        except Exception as e:
            self.log(f"  ✗ Erro ao assinar NFe: {str(e)[:60]}")
            return root

    def process_batch_nfe(self, pasta_entrada, pasta_saida, pasta_erro=None):
        """
        Processa lote de NFe para assinatura.
        
        Args:
            pasta_entrada: Pasta com NFe originais
            pasta_saida: Pasta para NFe assinadas
            pasta_erro: Pasta para NFe com erro (opcional)
        """
        # Criar pastas
        os.makedirs(pasta_saida, exist_ok=True)
        if pasta_erro:
            os.makedirs(pasta_erro, exist_ok=True)

        self.registrar_namespaces()

        self.log(f"\n[LENDO] Pasta: {pasta_entrada}")
        self.log(f"[TIPO] Processando NFe (Nota Fiscal Eletrônica Federal)\n")

        # Listar arquivos
        arquivos_nfe = [f for f in os.listdir(pasta_entrada) if f.lower().endswith(".xml")]
        total = len(arquivos_nfe)

        self.log(f"[TOTAL] {total} arquivos NFe encontrados\n")

        batch_size = 20
        batch_logs = []

        for idx, arquivo in enumerate(arquivos_nfe, 1):
            caminho = os.path.join(pasta_entrada, arquivo)
            self.stats['total'] += 1

            try:
                # Parse
                tree = ET.parse(caminho)
                root = tree.getroot()

                # Verificar se é NFe
                if 'nfeProc' not in root.tag:
                    batch_logs.append(f"[SKIP] {arquivo} - não é NFe")
                    continue

                # Remover assinatura anterior
                tinha_assinatura = self.remover_assinatura_nfe(root)

                # Assinar
                root_assinado = self.assinar_nfe(root)

                # Salvar
                ET.ElementTree(root_assinado).write(
                    os.path.join(pasta_saida, arquivo),
                    encoding="utf-8",
                    xml_declaration=True,
                )

                if tinha_assinatura:
                    batch_logs.append(f"[RE-ASSINADA] {arquivo}")
                else:
                    batch_logs.append(f"[ASSINADA] {arquivo}")
                
                self.stats['assinados'] += 1

            except (ET.ParseError, OSError) as e:
                batch_logs.append(f"[ERRO] {arquivo}")
                self.stats['erros'] += 1
                if pasta_erro:
                    shutil.copy(caminho, os.path.join(pasta_erro, arquivo))

            # Log em batch
            if idx % batch_size == 0 or idx == total:
                self.log(f"[PROGRESSO] {idx}/{total} ({int(idx*100/total)}%)")
                for msg in batch_logs:
                    self.log(f"  {msg}")
                batch_logs = []

        # Resumo
        self.log("\n" + "=" * 60)
        self.log("[RESUMO NFe]")
        self.log(f"  Total processado: {self.stats['total']}")
        self.log(f"  Assinadas: {self.stats['assinados']}")
        self.log(f"  Erros: {self.stats['erros']}")
        self.log("=" * 60)


if __name__ == "__main__":
    # Exemplo de uso
    from certificate_handler import CertificateA1
    
    cert = CertificateA1()
    cert.load("caminho/do/certificado.pfx", b"senha")
    
    processor = XMLProcessorNFe(cert, print)
    processor.process_batch_nfe(
        pasta_entrada="xmls_nfe_entrada",
        pasta_saida="xmls_nfe_assinadas",
        pasta_erro="xmls_nfe_erro"
    )
