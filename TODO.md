# TODO

## NFe: correção de valores
- [x] Ler/entender onde a correção de NFSe acontece hoje (`processar_nfse_prefeitura`) e reproduzir para NFe.

- [ ] Definir a regra de correção para NFe: quais nós devem ser recalculados (ex.: `ICMSTot/vProd`, `ICMSTot/vNF`, `ICMS/*/vBC`/`vICMS`, PIS/COFINS etc.) e como tratar arredondamento.
- [ ] Implementar função `processar_nfe(...)` em `xmls_gui_app/xml_processor.py` (ou criar novo processador), chamada quando `detectar_tipo` retornar NACIONAL.
- [ ] Atualizar `process_batch` para usar a função correta por tipo (NFSe vs NFe).
- [ ] Garantir que assinatura de NFSe/NFe continue funcionando: NFSe usa `assinar_xml` existente; NFe pode continuar usando `XMLProcessorNFe` (se houver integração) ou adaptar assinatura no mesmo fluxo.
- [ ] Rodar um teste local em um subset de XMLs (ex.: `xmls_teste_saida_2`) e verificar se valores e assinatura ficam consistentes. 

