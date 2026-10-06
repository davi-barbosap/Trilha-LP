# Trilha-LP

Landing pages de mídia paga da Trilha (Meta Ads e Google Ads). Cada página segue uma estrutura que converte e devolve o lead ao Kommo com a origem completa. Assim a venda volta às plataformas, e o Trilha-ads mede a página pela régua da Trilha: qualificação, visita e venda, não CPL.

A ferramenta **não escreve o texto e não faz o design visual da marca**. O texto é do assessor e da criação. A estrutura, as regras, o rastreamento e a montagem são daqui.

Serve para qualquer segmento; as regras de um segmento só valem quando a página declara esse segmento. O exemplo (`exemplos/escola-exemplo/`) é a Escola Exemplo de Inglês, o mesmo cliente fictício do Trilha-briefing, do Trilha-copy e do Trilha-ads. As regras do imobiliário (registro profissional e preço "a partir de") são exercitadas pela página de teste em `tests/fixtures/residencial-exemplo/`.

## Ecossistema Trilha

| Etapa | Repositório | Papel |
|---|---|---|
| 1. Diagnóstico e planejamento | [Trilha-briefing](https://github.com/davi-barbosap/Trilha-briefing) | entende o cliente e decide a estratégia; é a fonte de tudo o que as outras ferramentas usam |
| 2. Copy | [Trilha-copy](https://github.com/davi-barbosap/Trilha-copy) | estrutura e revisa os textos dos anúncios, fiel ao briefing |
| 3. Página | **Trilha-LP (este)** | landing page com o rastreamento que leva a origem do lead até o Kommo |
| 4. Execução e medição | [Trilha-ads](https://github.com/davi-barbosap/Trilha-ads) | coleta, confere e calcula: raio-x do funil, conversão real, freio, material das reuniões |
| Dados dos clientes | Trilha-clientes (privado) | os arquivos reais de cada cliente; esta ferramenta usa a pasta `lp/` |

O código da célula da grade (`PT01`, `GB01`…) amarra as etapas. Ele vai no anúncio como `utm_content`, a página guarda e repassa as UTMs ao lead, e o botão de WhatsApp leva o código na mensagem.

## O que faz

| Comando | O que faz |
|---|---|
| `validar <pagina.yaml>` | Confere o esquema (blocos obrigatórios, quantidades, origem, HTTPS do webhook, registro profissional quando o segmento exige) e revisa o texto (lista abaixo). Sai com erro quando algo bloqueia. |
| `construir <pagina.yaml> [--origem meta\|google \| --todas]` | Monta a página estática em `dist/<id>/` (`index.html` com CSS embutido e `rastreio.js`). Gera a versão de outra origem de tráfego, porque a ordem dos blocos muda. |

## Como faz

**Texto antes do design.** Primeiro a oferta destrinchada em todos os componentes que a fazem valer, que vêm do briefing. Depois a página montada em volta dela.

**A estrutura** tem ordem fixa, e cada bloco tem uma função:

| # | Bloco | Função |
|---|---|---|
| 1 | **Topo** | título (resultado + prazo + ganho emocional), subtítulo (dor + como resolve), 1 ou 2 provas, um botão, redução de medo, imagem que mostra o produto ou a vida nele |
| 2 | **Dor** (Meta) ou **prova social** (Google) | tráfego frio precisa de motivo para agir; tráfego com intenção precisa de confiança |
| 3 | **Benefícios** (4 a 8) | benefício + característica; cada título se sustenta sozinho |
| 4 | o bloco 2 que não abriu a página | — |
| 5 | **Como funciona** (3 a 5 passos) | do contato ao resultado, sem esforço |
| 6 | **Objeções e garantias** | as objeções reais do time e os motivos de perda do Kommo |
| 7 | **Fechamento** | recapitulação, prova e formulário |

Regras de texto bloco a bloco em [docs/estrutura.md](docs/estrutura.md).

**A revisão do texto** segue o padrão de texto da Trilha. O arquivo canônico mora no Trilha-copy; aqui fica a cópia dos vocabulários, conferida na CI. Os avisos vêm em três gravidades, e `validar` e `construir` saem com erro quando algo bloqueia:
- **Bloqueia:**
  - termos e promessas proibidos pela marca ou pelo segmento (palavra inteira: "corra" não pega "ocorra");
  - garantia de resultado, em qualquer segmento;
  - preço onde o segmento não mostra.
- **Atenção:**
  - título de bloco genérico ("Depoimentos", "Como funciona");
  - título do topo longo para o celular e descrição de SEO longa;
  - preço fora da forma do segmento (no imobiliário, "a partir de"). Número de prova em reais, como "R$ 80 milhões em obras", não conta como preço.
  - imagem, webhook ou GTM faltando;
  - página sem prova social.
- **Sugestão:** botão genérico ("Enviar") e formulário sem pergunta de qualificação.

O texto inteiro também passa pelo padrão completo, com o contrato do cliente, no Trilha-copy: `python -m trilha_copy revisar-pagina lp/<id>/<pagina>/pagina.yaml`. Lá entram número sem lastro, urgência sem lastro, voz, legibilidade e objeção sem resposta.

**O rastreamento** ([docs/contrato.md](docs/contrato.md)):
- UTMs e identificadores de clique (`gclid`, `gbraid`, `wbraid`, `fbclid`…) ficam guardados por 90 dias. Um clique novo com campanha substitui o anterior; uma visita sem campanha não apaga a mídia paga.
- O lead vai ao webhook (n8n → Kommo) com esquema fixo e `event_id`.
- A conversão (`generate_lead` no GTM e `Lead` no pixel) só dispara **depois** que o webhook confirma, com o mesmo `event_id` que o servidor manda ao Meta.
- O botão de WhatsApp leva o código do criativo na mensagem.
- O WhatsApp é validado como celular brasileiro e gravado em E.164, sem duplicar o 55.
- Há pergunta de qualificação opcional, isca contra robô, modo de consentimento do Google e aviso de cookies.

**A página é leve:** sem framework, CSS embutido, imagens com tamanho declarado, celular primeiro e botão de WhatsApp fixo.

**Entradas:** o `pagina.yaml`. O rascunho vem do Trilha-briefing (`exportar --para lp`), com o que faltar marcado como `PENDENTE`; o texto final é escrito aqui.

**Saídas:** `dist/<id>/`, a página pronta para qualquer hospedagem de arquivos estáticos (Hostinger, GitHub Pages, Netlify, Cloudflare Pages), e o lead no Kommo com os campos de [contrato](docs/contrato.md).

## O que não faz

- **Não escreve o texto nem faz o design da marca.** O visual é simples e segue as cores e fontes do `pagina.yaml`; o design da marca é da equipe de criação.
- **Não hospeda nem publica.** Você sobe a pasta `dist/<id>/` e segue o [checklist de publicação](docs/checklist-publicacao.md).
- **Não configura o GTM, o pixel nem o n8n.** A página dispara os eventos; as tags e o fluxo que grava no Kommo são configurados à parte.
- **Não mede a página.** Quem compara versões e origens pela qualificação e pela venda é o Trilha-ads, que ainda não lê os campos `landing_page` e `event_id_lead` que esta página grava.

## Situação atual

Versão 0.2.1, sem cliente real ainda. Pontos em aberto:
- os exemplos da documentação de estrutura ainda são do imobiliário.

## Como usar

```bash
pip install -e .

# Clientes reais ficam no Trilha-clientes (privado), pasta lp/<id>/<pagina>/
cd ../Trilha-clientes
python -m trilha_briefing exportar briefing/minha-cliente --para lp --oferta X --saida lp/minha-cliente   # rascunho
python -m trilha_lp validar   lp/minha-cliente/X-meta/pagina.yaml
python -m trilha_copy revisar-pagina lp/minha-cliente/X-meta/pagina.yaml   # o texto pelo padrão completo (Trilha-copy)
python -m trilha_lp construir lp/minha-cliente/X-meta/pagina.yaml --todas      # dist/X-meta/ e dist/X-google/ (não versionar)
```

Neste repositório, sobre o exemplo:

```bash
python -m trilha_lp validar   exemplos/escola-exemplo/pagina.yaml
python -m trilha_lp construir exemplos/escola-exemplo/pagina.yaml --todas
```

Sem `webhook_url`, a página roda em **modo teste**: o formulário funciona e dispara o evento com `entrega: modo_teste`, mas nenhum lead é enviado.

## Estrutura

```
trilha_lp/           esquema, revisão do texto, montagem da página, linha de comando
trilha_lp/modelo/    estilo.css e rastreio.js (copiados para cada página)
exemplos/            página de exemplo (dados fictícios): a escola de inglês
docs/                estrutura, contrato de rastreamento, checklist de publicação
tests/               testes (Python e JavaScript); fixtures/ tem a página de teste do imobiliário
```

## Documentação

- [Estrutura e regras de texto](docs/estrutura.md)
- [Contrato de rastreamento](docs/contrato.md): o que a página envia e o que o n8n grava no Kommo.
- [Checklist de publicação](docs/checklist-publicacao.md)
- [Mudanças](CHANGELOG.md)

## Testes

```bash
python -m unittest discover -s tests -v
node --test tests/*.test.mjs
```

A CI roda os dois, valida e monta o exemplo a cada push. O Trilha-briefing confere, na CI dele, que a página que ele exporta passa no esquema daqui.
