import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime

# =========================
# ASSINATURA DIGITAL
# =========================
try:
    from signxml import XMLSigner, methods
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.primitives import hashes
    HAS_SIGNXML = True
except ImportError:
    HAS_SIGNXML = False

# Carregar o certificado A1 (PFX)
CERT_PATH = "KRUEGER ASSESSORIA DE IMPORTACAO E EXPORTACAO LTDA-VENC-09-09-2026-SENHA-Krueger@007.pfx"
CERT_PASS = b"Krueger@007"

PRIVATE_KEY = None
CERTIFICATE = None

if HAS_SIGNXML and os.path.exists(CERT_PATH):
    with open(CERT_PATH, "rb") as f:
        pfx_data = f.read()
    PRIVATE_KEY, CERTIFICATE, _ = pkcs12.load_key_and_certificates(pfx_data, CERT_PASS)

# =========================
# PROCESSAMENTO
# =========================

def registrar_namespaces():
    # Isso evita que o Python adicione "ns0:" e quebre a estrutura do Domínio
    ET.register_namespace('', 'http://www.sped.fazenda.gov.br/nfse')
    ET.register_namespace('ds', 'http://www.w3.org/2000/09/xmldsig#')
    
registrar_namespaces()


def processar_nfse_prefeitura(root):
    alterado = False
    
    # Identificar o namespace para não criar tags quebradas
    ns = ""
    if "}" in root.tag:
        ns = root.tag.split("}")[0] + "}"
        
    base_tag = None
    outras_tag = None
    valores_parent = None
    
    for elem in root.iter():
        nome = elem.tag.split("}")[-1].lower()
        if nome == "valores":
            valores_parent = elem  # A última tag 'valores' será usada (a que fica dentro do DPS)
        if nome in ["valorservicos", "vserv"]:
            base_tag = elem
        if nome in ["outrasretencoes", "vretoutras", "vretpis", "vretcofins"]:
            outras_tag = elem

    if base_tag is not None:
        try:
            base = float(base_tag.text)
            novo = round(base * 0.0365, 2)
            
            if outras_tag is not None:
                # Se a tag existe, só altera se o valor for diferente
                antes = float(outras_tag.text or 0)
                if round(antes, 2) != novo:
                    outras_tag.text = f"{novo:.2f}"
                    alterado = True
            else:
                # A tag NÃO EXISTE! Vamos criá-la e anexar dentro de <valores>
                if valores_parent is not None:
                    nova_tag = ET.SubElement(valores_parent, f"{ns}OutrasRetencoes")
                    nova_tag.text = f"{novo:.2f}"
                    alterado = True
        except:
            pass

    return alterado

# =========================
# CONFIGURAÇÕES
# =========================

BASE = os.getcwd()

PASTA_ENTRADA = os.path.join(BASE, "xmls_ok")  # Processa XMLs que estavam OK
PASTA_CORRIGIDOS = os.path.join(BASE, "xmls_corrigidos")
PASTA_INVALIDOS = os.path.join(BASE, "xmls_invalidos")
PASTA_ASSINADOS = os.path.join(BASE, "xmls_assinados")
PASTA_ERRO = os.path.join(BASE, "xmls_erro_nao_recuperaveis")
PASTA_PROCESSADOS = os.path.join(BASE, "xmls_processados")

os.makedirs(PASTA_CORRIGIDOS, exist_ok=True)
os.makedirs(PASTA_INVALIDOS, exist_ok=True)
os.makedirs(PASTA_ASSINADOS, exist_ok=True)
os.makedirs(PASTA_ERRO, exist_ok=True)
os.makedirs(PASTA_PROCESSADOS, exist_ok=True)

# =========================
# RELATÓRIO
# =========================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
relatorio_path = os.path.join(BASE, f"relatorio_{timestamp}.txt")


def remover_assinatura(root):
    removeu = False
    for parent in root.iter():
        for child in list(parent):
            if "Signature" in child.tag:
                parent.remove(child)
                removeu = True
    return removeu


def detectar_tipo(root):
    tag = root.tag.lower()
    if "nfse" in tag and "sped" in tag:
        return "NACIONAL"
    if "consultarnfseresposta" in tag:
        return "PREFEITURA"
    return "DESCONHECIDO"


# =========================
# ASSINAR XML
# =========================
def assinar_xml(root):
    if not HAS_SIGNXML or PRIVATE_KEY is None:
        return root
        
    try:
        # API do signxml versão recente
        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm="rsa-sha256",
            digest_algorithm="sha256",
            c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#WithComments"
        )
        
        signed_root = signer.sign(root, key=PRIVATE_KEY, cert=CERTIFICATE)
        return signed_root
        
    except Exception as e:
        print(f"Erro ao assinar XML: {e}")
        return root

# =========================
# LOOP PRINCIPAL
# =========================

total = 0
corrigidos_lista = []
ok_lista = []
erros_lista = []
assinados_lista = []

print(f"\n[LENDO] Pasta: {PASTA_ENTRADA}")
print(f"[CERT] Certificado carregado: {HAS_SIGNXML and PRIVATE_KEY is not None}\n")

for arquivo in os.listdir(PASTA_ENTRADA):
    if not arquivo.lower().endswith(".xml"):
        continue

    caminho = os.path.join(PASTA_ENTRADA, arquivo)
    total += 1

    try:
        tree = ET.parse(caminho)
        root = tree.getroot()
    except Exception as e:
        print(f"[ERRO_LEITURA] {arquivo} - Erro ao ler XML: {e}")
        erros_lista.append(f"{arquivo} (Erro leitura)")
        shutil.copy(caminho, os.path.join(PASTA_ERRO, arquivo))
        continue

    # Remove a assinatura em memória para podermos alterar e salvar o XML limpo
    tinha_assinatura = remover_assinatura(root)

    tipo = detectar_tipo(root)

    if tipo not in ["PREFEITURA", "NACIONAL", "DESCONHECIDO"]:
        print(f"[TIPO_DESCONHECIDO] {arquivo} - Tipo: {tipo}")
        ok_lista.append(arquivo)
        shutil.copy(caminho, os.path.join(PASTA_INVALIDOS, arquivo))
        continue

    # Tentar processar o XML
    alterado = processar_nfse_prefeitura(root)

    # Sempre re-assinar, mesmo que não haja alteração de valores
    print(f"[ASSINANDO] {arquivo}")
    
    try:
        # Re-assinar o arquivo se temos o certificado
        if HAS_SIGNXML and PRIVATE_KEY is not None:
            root_assinado = assinar_xml(root)
            ET.ElementTree(root_assinado).write(
                os.path.join(PASTA_CORRIGIDOS, arquivo),
                encoding="utf-8",
                xml_declaration=True,
            )
            
            if alterado:
                print(f"[OK_CORRIGIDO] {arquivo}")
                corrigidos_lista.append(arquivo)
            else:
                print(f"[OK] {arquivo}")
                ok_lista.append(arquivo)
                
            if tinha_assinatura:
                assinados_lista.append(arquivo)
        else:
            # Salvar sem assinatura se não temos certificado
            ET.ElementTree(root).write(
                os.path.join(PASTA_CORRIGIDOS, arquivo),
                encoding="utf-8",
                xml_declaration=True,
            )
            print(f"[AVISO] {arquivo} - Salvo sem assinatura (certificado indisponível)")
            ok_lista.append(arquivo)
    except Exception as e:
        print(f"[ERRO_ASSINATURA] {arquivo} - Erro: {str(e)[:50]}")
        erros_lista.append(f"{arquivo} (Erro assinatura)")
        shutil.copy(caminho, os.path.join(PASTA_ERRO, arquivo))
        continue

    try:
        os.remove(caminho)
    except:
        pass


with open(relatorio_path, "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("RELATORIO DE PROCESSAMENTO DE XMLs\n")
    f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    f.write("=" * 60 + "\n\n")
    
    f.write(f"Total de arquivos processados: {total}\n")
    f.write(f"Corrigidos e re-assinados: {len(corrigidos_lista)}\n")
    f.write(f"Ja estavam OK: {len(ok_lista)}\n")
    f.write(f"Erros: {len(erros_lista)}\n\n")

    f.write("=" * 60 + "\n")
    f.write("CORRIGIDOS E RE-ASSINADOS:\n")
    f.write("=" * 60 + "\n")
    for a in corrigidos_lista:
        f.write(f"  [OK] {a}\n")

    f.write("\n" + "=" * 60 + "\n")
    f.write("JA ESTAVAM OK:\n")
    f.write("=" * 60 + "\n")
    for a in ok_lista:
        f.write(f"  [OK] {a}\n")

    if assinados_lista:
        f.write("\n" + "=" * 60 + "\n")
        f.write("ASSINATURAS REMOVIDAS E RE-ASSINADAS:\n")
        f.write("=" * 60 + "\n")
        for a in assinados_lista:
            f.write(f"  [ASSINADO] {a}\n")

    if erros_lista:
        f.write("\n" + "=" * 60 + "\n")
        f.write("ERROS:\n")
        f.write("=" * 60 + "\n")
        for a in erros_lista:
            f.write(f"  [ERRO] {a}\n")

print("\n" + "=" * 60)
print("[FINALIZADO] Processamento concluído com sucesso!")
print("=" * 60)
print(f"[CORRIGIDOS] {len(corrigidos_lista)}")
print(f"[OK] {len(ok_lista)}")
print(f"[ERROS] {len(erros_lista)}")
print(f"[ASSINADOS] {len(assinados_lista)}")
print(f"[RELATORIO] {relatorio_path}")
print("=" * 60 + "\n")

input("Pressione Enter para sair...")
