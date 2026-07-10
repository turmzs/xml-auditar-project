"""Processador de XMLs com re-assinatura digital."""

import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

try:
    # Execução como pacote (ex.: `python -m xmls_gui_app...`)
    from .xml_processor_nfe_values import processar_nfe_icms_pis_cofins
    from .xml_processor_nfse_sped import processar_nfse_sped_nacional
except ImportError:
    # Execução solta via `run_gui.py` (path inserido no sys.path)
    from xml_processor_nfe_values import processar_nfe_icms_pis_cofins
    from xml_processor_nfse_sped import processar_nfse_sped_nacional


try:
    from signxml import XMLSigner, methods
    from cryptography.hazmat.primitives import serialization

    HAS_SIGNXML = True
except ImportError:
    HAS_SIGNXML = False


class XMLProcessor:
    """Processa e re-assina XMLs com certificado digital."""

    def __init__(self, certificate_handler, output_callback=None):
        """
        Inicializa processador.

        Args:
            certificate_handler: Instância de CertificateA1 ou CertificateA3
            output_callback: Função para enviar logs (output_callback(mensagem))
        """
        self.cert_handler = certificate_handler
        self.output_callback = output_callback or self._default_output
        self.stats = {"total": 0, "corrigidos": 0, "ok": 0, "erros": 0}
        # Listas de rastreamento
        self.corrigidos_lista = []
        self.ok_lista = []
        self.erros_lista = []
        self.assinados_lista = []
        self.invalidos_lista = []

    def _default_output(self, message):
        """Callback padrão (apenas print)."""
        print(message)

    def log(self, message):
        """Envia mensagem ao callback."""
        self.output_callback(message)

    def registrar_namespaces(self):
        """
        Registra namespaces para evitar prefixos quebrados.

        Padrão brasileiro (ICP-Brasil) para NFS-e:
        - Namespace vazio para elementos principais
        - Namespace 'ds' para assinatura digital
        """
        ET.register_namespace("", "http://www.sped.fazenda.gov.br/nfse")
        ET.register_namespace("ds", "http://www.w3.org/2000/09/xmldsig#")
        # Adicionar namespaces comuns em NFS-e
        ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
        ET.register_namespace("xsd", "http://www.w3.org/2001/XMLSchema")

    def remover_assinatura(self, root):
        """Remove assinaturas anteriores do XML."""
        removeu = False
        for parent in root.iter():
            for child in list(parent):
                if "Signature" in child.tag:
                    parent.remove(child)
                    removeu = True
        return removeu

    def detectar_tipo(self, root):
        """Detecta tipo de XML (NFE/NFSE_SPED/PREFEITURA/DESCONHECIDO)."""
        tag = root.tag.lower()
        
        # NFe (Nota Fiscal Eletrônica)
        if "nfe" in tag:
            return "NFE"
        
        # NFSe SPED Nacional (tag RPS com namespace SPED)
        if "rps" in tag and "sped" in tag:
            return "NFSE_SPED"
        
        # NFSe Prefeitura (padrão antigo)
        if "consultarnfseresposta" in tag:
            return "NFSE_PREFEITURA"
        
        # NFSe com namespace SPED genericamente
        if "nfse" in tag and "sped" in tag:
            return "NFSE_SPED"
        
        return "DESCONHECIDO"

    def processar_nfse_prefeitura(self, root, aliquota=0.0365):
        """

        Processa e corrige valores no XML.

        Args:
            root: Raiz do XML
            aliquota: Alíquota de cálculo (padrão 3.65%)

        Returns:
            bool: True se foi alterado
        """
        alterado = False

        ns = ""
        if "}" in root.tag:
            ns = root.tag.split("}")[0] + "}"

        base_tag = None
        outras_tag = None
        valores_parent = None

        for elem in root.iter():
            nome = elem.tag.split("}")[-1].lower()
            if nome == "valores":
                valores_parent = elem
            if nome in ["valorservicos", "vserv"]:
                base_tag = elem
            if nome in ["outrasretencoes", "vretoutras", "vretpis", "vretcofins"]:
                outras_tag = elem

        if base_tag is not None:
            try:
                base = float(base_tag.text)
                novo = round(base * aliquota, 2)

                if outras_tag is not None:
                    antes = float(outras_tag.text or 0)
                    if round(antes, 2) != novo:
                        outras_tag.text = f"{novo:.2f}"
                        alterado = True
                else:
                    if valores_parent is not None:
                        nova_tag = ET.SubElement(valores_parent, f"{ns}OutrasRetencoes")
                        nova_tag.text = f"{novo:.2f}"
                        alterado = True
            except (ValueError, TypeError):
                pass

        return alterado

    def assinar_xml(self, root):
        """
        Assina XML com certificado digital (A1 ou A3).

        Args:
            root: Raiz do XML

        Returns:
            Raiz assinada ou original se erro
        """
        if not HAS_SIGNXML:
            return root

        # Verificar se é certificado A1 ou A3
        cert_type = getattr(self.cert_handler, "cert_type", "DESCONHECIDO")

        if cert_type == "A1":
            return self._assinar_a1(root)
        elif cert_type == "A3":
            return self._assinar_a3(root)
        else:
            self.log(f"  ✗ Tipo de certificado desconhecido: {cert_type}")
            return root

    def _assinar_a1(self, root):
        """
        Assina XML com certificado A1 (PFX).

        Padrão brasileiro (ICP-Brasil) para NFS-e:
        - Algoritmo: RSA-SHA256
        - Método: Enveloped
        - C14N: Exclusive with Comments
        - Reference: Vazia (assina elemento raiz)
        """
        if self.cert_handler.private_key is None:
            return root

        try:
            # Converter chave e certificado para PEM (signxml requer este formato)
            pem_key = self.cert_handler.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            pem_cert = self.cert_handler.certificate.public_bytes(
                serialization.Encoding.PEM
            )

            # Adicionar ID ao elemento raiz se não tiver (necessário para referência)
            if "id" not in root.attrib and "ID" not in root.attrib:
                root.set("id", "xades-root-id")

            # Obter o ID para referência
            root_id = root.get("id") or root.get("ID")
            reference_uri = f"#{root_id}" if root_id else ""

            # Configuração conforme padrão brasileiro ICP-Brasil para NFS-e
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256",
                c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments",
            )

            # Assinar com referência do elemento raiz
            signed_root = signer.sign(
                root, key=pem_key, cert=pem_cert, reference_uri=reference_uri
            )

            self.log("  ✓ Assinado com sucesso (A1 - ICP-Brasil)")  # noqa
            return signed_root

        except (ValueError, TypeError, OSError) as e:
            self.log(f"  ✗ Erro ao assinar (A1): {str(e)[:50]}")
            return root

    def _assinar_a3(self, root):
        """
        Assina XML com certificado A3 (Token PKCS#11).

        Padrão brasileiro (ICP-Brasil) para NFS-e com token.
        """
        try:
            import PyKCS11
        except ImportError:
            self.log("  ✗ PyKCS11 não disponível. Instale: pip install PyKCS11")
            return root

        if self.cert_handler.certificate is None or not hasattr(
            self.cert_handler, "session"
        ):
            self.log("  ✗ Token A3 não conectada ou certificado não carregado")
            return root

        try:
            # Usar signxml com callback de assinatura da token
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256",
                c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments",
            )

            # Converter certificado para PEM
            pem_cert = self.cert_handler.certificate.public_bytes(
                serialization.Encoding.PEM
            )

            # Adicionar ID ao elemento raiz se não tiver
            if "id" not in root.attrib and "ID" not in root.attrib:
                root.set("id", "xades-root-id")

            # Obter o ID para referência
            root_id = root.get("id") or root.get("ID")
            reference_uri = f"#{root_id}" if root_id else ""

            # Para A3, usamos um callback de assinatura que chama a token
            def sign_callback(data_to_sign):
                """Callback para assinar dados usando a token (padrão ICP-Brasil)."""
                mechanism = PyKCS11.Mechanism(PyKCS11.CKM_SHA256_RSA_PKCS, None)
                signature = bytes(
                    self.cert_handler.session.sign(
                        self.cert_handler.key_object, data_to_sign, mechanism
                    )
                )
                return signature

            # Assinar com ID do elemento raiz
            signed_root = signer.sign(
                root, key=sign_callback, cert=pem_cert, reference_uri=reference_uri
            )

            self.log("  ✓ Assinado com sucesso (A3 - ICP-Brasil)")
            return signed_root

        except (PyKCS11.PyKCS11Error, ValueError, OSError) as e:
            self.log(f"  ✗ Erro ao assinar (A3): {str(e)[:50]}")
            return root

    def process_batch(
        self,
        pasta_entrada,
        pasta_corrigidos,
        pasta_invalidos=None,
        pasta_assinados=None,
        pasta_erro=None,
        pasta_processados=None,
        aliquota=0.0365,
        gerar_relatorio=True,
    ):
        """
        Processa lote de XMLs com suporte a múltiplas pastas de saída.

        Args:
            pasta_entrada: Pasta com XMLs de entrada
            pasta_corrigidos: Pasta para XMLs corrigidos/re-assinados
            pasta_invalidos: Pasta para XMLs inválidos (opcional)
            pasta_assinados: Pasta para rastrear XMLs que foram re-assinados
            pasta_erro: Pasta para XMLs com erro não recuperável
            pasta_processados: Pasta para XMLs originais após processamento (opcional)
            aliquota: Alíquota de cálculo
            gerar_relatorio: Se True, gera arquivo .txt com relatório
            verbose: Se False (padrão), reduz logging para melhor performance
        """
        self.registrar_namespaces()

        # Reset das listas
        self.stats = {"total": 0, "corrigidos": 0, "ok": 0, "erros": 0}
        self.corrigidos_lista = []
        self.ok_lista = []
        self.erros_lista = []
        self.assinados_lista = []
        self.invalidos_lista = []

        # Criar pastas de destino
        os.makedirs(pasta_corrigidos, exist_ok=True)
        if pasta_invalidos:
            os.makedirs(pasta_invalidos, exist_ok=True)
        if pasta_assinados:
            os.makedirs(pasta_assinados, exist_ok=True)
        if pasta_erro:
            os.makedirs(pasta_erro, exist_ok=True)
        if pasta_processados:
            os.makedirs(pasta_processados, exist_ok=True)

        self.log(f"\n[LENDO] Pasta: {pasta_entrada}")
        self.log(
            f"[CERT] Certificado carregado: {HAS_SIGNXML and self.cert_handler.private_key is not None}\n"
        )

        # Contar arquivos uma única vez
        arquivos_xml = [
            f for f in os.listdir(pasta_entrada) if f.lower().endswith(".xml")
        ]
        total_arquivos = len(arquivos_xml)

        self.log(f"[TOTAL] {total_arquivos} arquivos XML encontrados\n")

        # Batch logging para melhor performance
        batch_size = 20  # Atualizar GUI a cada 20 arquivos
        batch_logs = []

        for idx, arquivo in enumerate(arquivos_xml, 1):
            caminho = os.path.join(pasta_entrada, arquivo)
            self.stats["total"] += 1

            # Tentar ler o arquivo
            try:
                tree = ET.parse(caminho)
                root = tree.getroot()
            except (ET.ParseError, OSError):  # noqa: F841
                batch_logs.append(f"[ERRO_LEITURA] {arquivo}")
                self.erros_lista.append(f"{arquivo} (Erro leitura)")
                self.stats["erros"] += 1
                if pasta_erro:
                    shutil.copy(caminho, os.path.join(pasta_erro, arquivo))
                continue

            # Remover assinatura anterior
            tinha_assinatura = self.remover_assinatura(root)

            # Detectar tipo de XML
            tipo = self.detectar_tipo(root)

            # Verificar se é um tipo desconhecido ou inválido
            if tipo == "DESCONHECIDO":
                batch_logs.append(f"[INVALIDO] {arquivo}")
                self.invalidos_lista.append(arquivo)
                self.ok_lista.append(arquivo)
                if pasta_invalidos:
                    shutil.copy(caminho, os.path.join(pasta_invalidos, arquivo))

                # Log em batch
                if idx % batch_size == 0 or idx == total_arquivos:
                    self.log(f"[PROGRESSO] {idx}/{total_arquivos} arquivos processados")
                    for log_msg in batch_logs[-min(5, len(batch_logs)) :]:
                        self.log(log_msg)
                continue

            # Processar o XML conforme seu tipo
            if tipo == "NFSE_PREFEITURA":
                alterado = self.processar_nfse_prefeitura(root, aliquota)
            elif tipo == "NFSE_SPED":
                alterado = processar_nfse_sped_nacional(root, aliquota)
            elif tipo == "NFE":
                # Usando o novo processador com auditoria de valores
                nfe_proc = NFeProcessor(caminho)
                # Atualiza a árvore interna do processador com o root atual
                nfe_proc.root = root
                
                # Configura as alíquotas (ajustando a lógica de nomes de chaves)
                config_rates = {"pis_rate": aliquota, "cofins_rate": aliquota}
                res = nfe_proc.apply_fiscal_corrections(config_rates)
                alterado = res["modified"]
                
                if alterado:
                    for c in res["corrections"]:
                        self.log(f"  -> {c['tax']}: BC {c['bc_before']} -> {c['bc_after']} | Val {c['val_before']} -> {c['val_after']}")
                    # Atualiza o root do loop principal com as mudanças feitas pelo processador
                    root = nfe_proc.root
            else:
                alterado = False

            # Re-assinar e salvar

            try:
                root_assinado = self.assinar_xml(root)
                ET.ElementTree(root_assinado).write(
                    os.path.join(pasta_corrigidos, arquivo),
                    encoding="utf-8",
                    xml_declaration=True,
                )

                if alterado:
                    batch_logs.append(f"[OK_CORRIGIDO] {arquivo}")
                    self.corrigidos_lista.append(arquivo)
                    self.stats["corrigidos"] += 1
                else:
                    batch_logs.append(f"[OK] {arquivo}")
                    self.ok_lista.append(arquivo)
                    self.stats["ok"] += 1

                if tinha_assinatura:
                    self.assinados_lista.append(arquivo)

                # Remover arquivo original após processar com sucesso
                try:
                    if pasta_processados:
                        shutil.move(caminho, os.path.join(pasta_processados, arquivo))
                    else:
                        os.remove(caminho)
                except OSError:
                    pass  # Ignorar erros silenciosamente para melhor performance

            except (IOError, ValueError, OSError):  # noqa: F841
                batch_logs.append(f"[ERRO] {arquivo}")
                self.erros_lista.append(f"{arquivo} (Erro assinatura)")
                self.stats["erros"] += 1
                if pasta_erro:
                    shutil.copy(caminho, os.path.join(pasta_erro, arquivo))

            # Log em batch a cada 20 arquivos
            if idx % batch_size == 0 or idx == total_arquivos:
                self.log(
                    f"[PROGRESSO] {idx}/{total_arquivos} ({int(idx*100/total_arquivos)}%)"
                )
                # Mostrar apenas últimos 3 logs para não sobrecarregar GUI
                if batch_logs:
                    for log_msg in batch_logs[-min(3, len(batch_logs)) :]:
                        self.log(f"  {log_msg}")
                batch_logs = []

        # Gerar relatório
        if gerar_relatorio:
            self._gerar_relatorio(pasta_corrigidos)

        # Log final
        self.log("\n" + "=" * 60)
        self.log("[FINALIZADO] Processamento concluído com sucesso!")
        self.log("=" * 60)
        self.log(f"[CORRIGIDOS] {len(self.corrigidos_lista)}")
        self.log(f"[OK] {len(self.ok_lista)}")
        self.log(f"[ERROS] {len(self.erros_lista)}")
        self.log(f"[ASSINADOS] {len(self.assinados_lista)}")
        self.log("=" * 60 + "\n")

    def _gerar_relatorio(self, pasta_saida):
        """Gera arquivo de relatório em texto."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relatorio_path = os.path.join(
            os.path.dirname(pasta_saida), f"relatorio_{timestamp}.txt"
        )

        try:
            with open(relatorio_path, "w", encoding="utf-8") as f:  # noqa: E501
                f.write("=" * 60 + "\n")
                f.write("RELATORIO DE PROCESSAMENTO DE XMLs\n")
                f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")

                f.write(f"Total de arquivos processados: {self.stats['total']}\n")
                f.write(f"Corrigidos e re-assinados: {len(self.corrigidos_lista)}\n")
                f.write(f"Ja estavam OK: {len(self.ok_lista)}\n")
                f.write(f"Erros: {len(self.erros_lista)}\n\n")

                f.write("=" * 60 + "\n")
                f.write("CORRIGIDOS E RE-ASSINADOS:\n")
                f.write("=" * 60 + "\n")
                for a in self.corrigidos_lista:
                    f.write(f"  [OK] {a}\n")

                f.write("\n" + "=" * 60 + "\n")
                f.write("JA ESTAVAM OK:\n")
                f.write("=" * 60 + "\n")
                for a in self.ok_lista:
                    f.write(f"  [OK] {a}\n")

                if self.assinados_lista:
                    f.write("\n" + "=" * 60 + "\n")
                    f.write("ASSINATURAS REMOVIDAS E RE-ASSINADAS:\n")
                    f.write("=" * 60 + "\n")
                    for a in self.assinados_lista:
                        f.write(f"  [ASSINADO] {a}\n")

                if self.invalidos_lista:
                    f.write("\n" + "=" * 60 + "\n")
                    f.write("TIPOS DESCONHECIDOS:\n")
                    f.write("=" * 60 + "\n")
                    for a in self.invalidos_lista:
                        f.write(f"  [INVALIDO] {a}\n")

                if self.erros_lista:
                    f.write("\n" + "=" * 60 + "\n")
                    f.write("ERROS:\n")
                    f.write("=" * 60 + "\n")
                    for a in self.erros_lista:
                        f.write(f"  [ERRO] {a}\n")

            self.log(f"[RELATORIO] {relatorio_path}")
        except OSError as e:
            self.log(f"  ✗ Erro ao gerar relatório: {e}")
