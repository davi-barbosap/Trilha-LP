# Mudanças

As versões anteriores estão descritas no histórico do Git.

## 0.2.1 — um cliente fictício só (out/2026)

- **O exemplo documentado** passa a ser `exemplos/escola-exemplo/`, a Escola Exemplo de Inglês: o mesmo cliente fictício do Trilha-briefing, do Trilha-copy e do Trilha-ads.
  - **Origem:** o rascunho do briefing (`exportar --para lp --oferta conversacao-adultos`), reescrito como o assessor faria: frases inteiras na dor, objeções na voz do aluno, fechamento com título próprio.
  - **Revisão:** passa no `validar` e no `revisar-pagina` do Trilha-copy sem aviso de texto.
- **A página do lançamento imobiliário** vai para `tests/fixtures/residencial-exemplo/`. Continua exercitando as regras do segmento (registro profissional, preço "a partir de").

## 0.2.0 — padrão de texto da Trilha (out/2026)

- **A revisão do texto segue o padrão de texto da Trilha.** O arquivo canônico mora no Trilha-copy (`trilha_copy/regras/padrao.yaml`). A LP guarda a cópia dos vocabulários e parâmetros que usa em `trilha_lp/regras/padrao-vocabularios.yaml`, e `tests/test_padrao.py` confere essa cópia lista a lista contra o Trilha-copy na CI.
- **Três gravidades:** bloqueia, atenção e sugestão. Antes, tudo saía como "Atenção" e `validar` passava mesmo com termo proibido. Agora `validar` e `construir` saem com erro quando algo bloqueia.
- **Termos casam como palavra inteira:** "corra" não pega mais "ocorra".
- **Garantia de resultado** vale em qualquer segmento. Antes, só a valorização no imobiliário.
- **Preço pelo padrão do segmento:** no imobiliário, a página mostra "a partir de". Número de prova em reais não conta mais como preço. A regra comercial do próprio cliente é conferida no Trilha-copy (`revisar-pagina`), que tem o contrato.
- **Novas:** lista de promessas proibidas do segmento, título genérico também em objeções e fechamento, botão genérico, descrição de SEO longa.

## 0.1.1 — organização do ecossistema (out/2026)

Nenhuma mudança de comportamento.

- **Nomes:** o sistema de mídia passa a ser citado como Trilha-ads, e o README cita também o Trilha-briefing (de onde vem o rascunho da página) e o Trilha-copy.
- **Clientes reais** ficam no Trilha-clientes, pasta `lp/<id>/<pagina>/`.
- **README:** o que cada comando faz, a estrutura, a revisão, o rastreamento, o que a ferramenta não faz e a situação atual.

## 0.1.0 — primeira versão (out/2026)

Esquema e revisão do `pagina.yaml`, estrutura em 7 blocos com a ordem por origem do tráfego, rastreamento até o Kommo e montagem da página estática.
