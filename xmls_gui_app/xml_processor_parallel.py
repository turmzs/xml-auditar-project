"""
VERSÃO OTIMIZADA - Processamento paralelo de XMLs (Multiprocessing)

Para processar 479 XMLs em 5-10 minutos, implementar multiprocessing pode acelerar:
- Esperado: 1-2 minutos (4x cores)

INSTALAÇÃO:
    pip install PyKCS11  # Se usar A3
    pip install signxml cryptography
"""

import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial

try:
    from signxml import XMLSigner, methods
    from cryptography.hazmat.primitives import serialization
    HAS_SIGNXML = True
except ImportError:
    HAS_SIGNXML = False


class XMLProcessorParallel:
    """Processador paralelo de XMLs (usa multiprocessing)."""

    @staticmethod
    def processar_arquivo(arquivo, pasta_entrada, pasta_corrigidos, aliquota=0.0365):
        """
        Processa um único arquivo XML (função para multiprocessing).
        
        Args:
            arquivo: Nome do arquivo
            pasta_entrada: Pasta de entrada
            pasta_corrigidos: Pasta de saída
            aliquota: Alíquota de cálculo
            
        Returns:
            Tupla (status, nome_arquivo, mensagem)
        """
        caminho = os.path.join(pasta_entrada, arquivo)
        
        try:
            # Parse
            tree = ET.parse(caminho)
            root = tree.getroot()
            
            # Remover assinatura anterior
            for parent in root.iter():
                for child in list(parent):
                    if "Signature" in child.tag:
                        parent.remove(child)
            
            # Processar valores
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
                    else:
                        if valores_parent is not None:
                            nova_tag = ET.SubElement(valores_parent, f"{ns}OutrasRetencoes")
                            nova_tag.text = f"{novo:.2f}"
                except (ValueError, TypeError):
                    pass
            
            # Salvar (sem assinatura por enquanto - isso é feito em sequência)
            ET.ElementTree(root).write(
                os.path.join(pasta_corrigidos, arquivo),
                encoding="utf-8",
                xml_declaration=True,
            )
            
            return ("OK", arquivo, "Processado com sucesso")
            
        except Exception as e:
            return ("ERRO", arquivo, str(e)[:50])


def processar_lote_paralelo(pasta_entrada, pasta_corrigidos, num_workers=None):
    """
    Processa lote de XMLs em paralelo.
    
    Args:
        pasta_entrada: Pasta com XMLs
        pasta_corrigidos: Pasta de saída
        num_workers: Número de workers (padrão: número de cores)
    """
    if num_workers is None:
        num_workers = max(1, cpu_count() - 1)  # Deixar 1 core livre
    
    # Criar pasta de saída
    os.makedirs(pasta_corrigidos, exist_ok=True)
    
    # Listar arquivos
    arquivos = [f for f in os.listdir(pasta_entrada) if f.lower().endswith(".xml")]
    total = len(arquivos)
    
    print(f"\n[PARALELO] Processando {total} arquivos com {num_workers} workers")
    print(f"[PARALELO] Tempo estimado: {total * 0.15 / num_workers:.1f} segundos\n")
    
    # Criar função parcial com argumentos fixos
    func = partial(
        XMLProcessorParallel.processar_arquivo,
        pasta_entrada=pasta_entrada,
        pasta_corrigidos=pasta_corrigidos,
        aliquota=0.0365
    )
    
    # Processar em paralelo
    with Pool(num_workers) as pool:
        resultados = pool.imap_unordered(func, arquivos, chunksize=10)
        
        ok_count = 0
        erro_count = 0
        
        for idx, (status, arquivo, msg) in enumerate(resultados, 1):
            if status == "OK":
                ok_count += 1
                if (idx % 50) == 0:
                    print(f"[PROGRESSO] {idx}/{total} ({int(idx*100/total)}%)")
            else:
                erro_count += 1
                print(f"[ERRO] {arquivo}: {msg}")
    
    print(f"\n[CONCLUIDO] {ok_count} OK, {erro_count} ERROS")
    print(f"[SAIDA] {pasta_corrigidos}")


if __name__ == "__main__":
    # Exemplo de uso
    pasta_entrada = r"C:\Users\artur.nascimento\Desktop\ALL VS CODE\XMLS\XML CORRECT\xmls_ok"
    pasta_saida = r"C:\Users\artur.nascimento\Desktop\ALL VS CODE\XMLS\XML CORRECT\xmls_corrigidos"
    
    # Processar em paralelo (MUITO mais rápido!)
    processar_lote_paralelo(pasta_entrada, pasta_saida, num_workers=4)
