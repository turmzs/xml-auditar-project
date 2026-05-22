import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
import csv

BASE = os.getcwd()

PASTA_ENTRADA = os.path.join(BASE, "xmls")
PASTA_CORRIGIDOS = os.path.join(BASE, "xmls_corrigidos")
PASTA_OK = os.path.join(BASE, "xmls_ok")
PASTA_PROCESSADOS = os.path.join(BASE, "xmls_processados")
PASTA_BACKUP = os.path.join(BASE, "xmls_backup")

os.makedirs(PASTA_CORRIGIDOS, exist_ok=True)
os.makedirs(PASTA_OK, exist_ok=True)
os.makedirs(PASTA_PROCESSADOS, exist_ok=True)
os.makedirs(PASTA_BACKUP, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

log_txt = open(f"relatorio_{timestamp}.txt", "w", encoding="utf-8")
log_csv = open(f"relatorio_{timestamp}.csv", "w", newline="", encoding="utf-8")

writer = csv.writer(log_csv)
writer.writerow(["Arquivo", "Tipo", "Base", "Aliquota", "Antes", "Depois", "Status"])


# ================= UTIL =================


def tag_sem_ns(tag):
    return tag.split("}")[-1]


def buscar_tag(root_xml, nomes):
    for elem in root_xml.iter():
        if tag_sem_ns(elem.tag) in nomes:
            return elem
    return None


def tipo_xml(root_xml):
    for elem in root_xml.iter():
        tag = tag_sem_ns(elem.tag).lower()

        if "cte" in tag:
            return "CTE"

        if "nfse" in tag or "compnfse" in tag:
            return "NFSE"

    return "SIMPLES"


def log(arquivo, tipo, base, aliq, antes, depois, status):
    linha = f"{arquivo} | {tipo} | Base: {base} | Aliq: {aliq:.4f} | {antes} → {depois} | {status}"
    print(linha)
    log_txt.write(linha + "\n")
    writer.writerow([arquivo, tipo, base, aliq, antes, depois, status])


# ================= CÁLCULO =================


def calcular_correto(base):
    aliq = 0.0365
    return round(base * aliq, 2), aliq


# ================= PROCESSADORES =================


def processar_simples(root_xml, arquivo):
    vserv_tag = buscar_tag(root_xml, ["ValorServicos", "vServ"])
    outras_tag = buscar_tag(root_xml, ["OutrasRetencoes"])

    if vserv_tag is None or outras_tag is None:
        return False

    try:
        base = float(vserv_tag.text)
        antes = float(outras_tag.text or 0)
    except Exception:
        return False

    novo, aliq = calcular_correto(base)

    if round(antes, 2) != round(novo, 2):
        outras_tag.text = f"{novo:.2f}"
        log(arquivo, "SIMPLES", base, aliq, antes, novo, "CORRIGIDO")
        return True

    return False


# ================= LOOP =================

print(f"📂 Lendo pasta: {PASTA_ENTRADA}")

total = 0
corrigidos = 0

for nome_arquivo in os.listdir(PASTA_ENTRADA):

    if not nome_arquivo.lower().endswith(".xml"):
        continue

    total += 1
    caminho = os.path.join(PASTA_ENTRADA, nome_arquivo)

    try:
        tree = ET.parse(caminho)
        root_xml = tree.getroot()
    except Exception:
        print(f"❌ {nome_arquivo} inválido")
        continue

    tipo = tipo_xml(root_xml)

    shutil.copy(caminho, os.path.join(PASTA_BACKUP, nome_arquivo))

    if tipo == "SIMPLES":
        alterado = processar_simples(root_xml, nome_arquivo)
    else:
        alterado = False  # mantém teu padrão original

    if alterado:
        corrigidos += 1
        tree.write(
            os.path.join(PASTA_CORRIGIDOS, nome_arquivo),
            encoding="utf-8",
            xml_declaration=True,
        )
    else:
        shutil.copy(caminho, os.path.join(PASTA_OK, nome_arquivo))

    shutil.move(caminho, os.path.join(PASTA_PROCESSADOS, nome_arquivo))


log_txt.close()
log_csv.close()

print("\n🚀 FINALIZADO")
print(f"Total: {total} | Corrigidos: {corrigidos}")
input("Pressione Enter para sair...")
