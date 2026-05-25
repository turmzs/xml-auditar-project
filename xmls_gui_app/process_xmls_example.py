"""
Exemplo de uso do XMLProcessor refatorado com todas as funcionalidades.

Este script demonstra como usar a classe XMLProcessor para processar
lotes de XMLs com múltiplas pastas de destino, geração de relatório e rastreamento.
"""

import os
from certificate_handler import CertificateA1
from xml_processor import XMLProcessor


def main():
    """Exemplo de uso do XMLProcessor."""
    
    # =============================================
    # CONFIGURAÇÃO
    # =============================================
    
    # Diretório base
    BASE = os.getcwd()
    
    # Pastas de entrada e saída
    PASTA_ENTRADA = os.path.join(BASE, "xmls_ok")
    PASTA_CORRIGIDOS = os.path.join(BASE, "xmls_corrigidos")
    PASTA_INVALIDOS = os.path.join(BASE, "xmls_invalidos")
    PASTA_ASSINADOS = os.path.join(BASE, "xmls_assinados")
    PASTA_ERRO = os.path.join(BASE, "xmls_erro_nao_recuperaveis")
    PASTA_PROCESSADOS = os.path.join(BASE, "xmls_processados")
    
    ALIQUOTA = 0.0365  # 3.65%
    
    # Caminho do certificado A1
    CERT_PATH = "KRUEGER ASSESSORIA DE IMPORTACAO E EXPORTACAO LTDA-VENC-09-09-2026-SENHA-Krueger@007.pfx"
    CERT_PASS = b"Krueger@007"
    
    # =============================================
    # INICIALIZAR PROCESSADOR
    # =============================================
    
    # Carregar certificado A1
    cert_handler = CertificateA1()
    cert_handler.load(CERT_PATH, CERT_PASS)
    
    # Criar processador com callback de log
    processor = XMLProcessor(cert_handler, output_callback=print)
    
    # =============================================
    # PROCESSAR LOTE
    # =============================================
    
    processor.process_batch(
        pasta_entrada=PASTA_ENTRADA,
        pasta_corrigidos=PASTA_CORRIGIDOS,
        pasta_invalidos=PASTA_INVALIDOS,
        pasta_assinados=PASTA_ASSINADOS,
        pasta_erro=PASTA_ERRO,
        pasta_processados=PASTA_PROCESSADOS,
        aliquota=ALIQUOTA,
        gerar_relatorio=True
    )
    
    # =============================================
    # ACESSAR RESULTADOS
    # =============================================
    
    print("\nResumo do processamento:")
    print(f"  • Corrigidos: {processor.corrigidos_lista}")
    print(f"  • OK: {processor.ok_lista}")
    print(f"  • Erros: {processor.erros_lista}")
    print(f"  • Assinados: {processor.assinados_lista}")
    print(f"  • Inválidos: {processor.invalidos_lista}")


if __name__ == "__main__":
    main()
    input("\nPressione Enter para sair...")
