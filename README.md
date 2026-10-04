# Trilha LP

Landing pages de mídia paga da Trilha (Meta Ads e Google Ads). Cada página segue uma estrutura que converte e devolve o lead ao Kommo com a origem completa, para a venda voltar às plataformas e o raio-x do [Trilha](https://github.com/davi-barbosap/Trilha) medir a página pela régua da Trilha: qualificação, visita e venda, não CPL.

## O que é

Uma página é um arquivo `pagina.yaml` com o texto da oferta. O sistema confere o texto, monta uma página estática leve (HTML, CSS e um script de rastreamento) e gera a versão para cada origem de tráfego. O texto é do assessor e da criação; a estrutura, as regras e o rastreamento são do sistema.

**Texto antes do design.** Primeiro a oferta destrinchada em todos os seus componentes (a ficha da oferta do Trilha já tem isso); depois a página montada em volta dela.

## A estrutura (ordem fixa, cada bloco com uma função)

| # | Bloco | Função |
|---|---|---|
| 1 | **Topo** | título (resultado + prazo + ganho emocional), subtítulo (dor + como resolve), 1–2 provas, um botão, redução de medo, imagem que mostra o produto ou a vida nele |
| 2 | **Dor** (Meta) ou **prova social** (Google) | tráfego frio precisa de motivo para agir; tráfego com intenção precisa de confiança |
| 3 | **Benefícios** (4–8) | benefício + característica; cada título se sustenta sozinho |
| 4 | o bloco 2 que não abriu a página | — |
| 5 | **Como funciona** (3–5 passos) | do contato ao resultado, sem esforço |
| 6 | **Objeções e garantias** | as objeções reais do time e os motivos de perda do Kommo |
| 7 | **Fechamento** | recapitulação, prova e formulário |

Detalhes e regras de texto em [docs/estrutura.md](docs/estrutura.md).

## O que o sistema garante

- **Revisão do texto:** termos e promessas proibidos pela marca, preço sem "a partir de" no imobiliário, promessa de valorização garantida, títulos genéricos ("Depoimentos", "Como funciona"), título longo demais para o celular, registro profissional (CRECI) no imobiliário.
- **Rastreamento** ([docs/contrato.md](docs/contrato.md)):
  - UTMs e identificadores de clique (`gclid`, `gbraid`, `wbraid`, `fbclid`…) guardados por 90 dias: um clique novo com campanha substitui o anterior, e uma visita sem campanha não apaga a mídia paga;
  - lead enviado ao webhook (n8n → Kommo) com esquema fixo e `event_id`;
  - conversão (`generate_lead` no GTM e `Lead` no pixel) **só depois** que o webhook confirma, com o mesmo `event_id` que o servidor manda ao Meta;
  - botão de WhatsApp com o código do criativo na mensagem;
  - WhatsApp validado como celular brasileiro e gravado em E.164 sem duplicar o 55;
  - pergunta de qualificação opcional, isca contra robô, modo de consentimento do Google e aviso de cookies.
- **Página leve:** sem framework, CSS embutido, imagens com tamanho declarado, celular primeiro, botão de WhatsApp fixo.

## Uso

```bash
pip install -e .

python -m trilha_lp validar exemplos/residencial-exemplo/pagina.yaml     # esquema + revisão do texto
python -m trilha_lp construir exemplos/residencial-exemplo/pagina.yaml --todas   # versões Meta e Google em dist/

python -m unittest discover -s tests -v
node --test tests/*.test.mjs
```

Sem `webhook_url`, a página roda em **modo teste**: o formulário funciona e dispara o evento com `entrega: modo_teste`, mas nenhum lead é enviado.

A pasta `dist/<id>/` é a página pronta: sobe para qualquer hospedagem de arquivos estáticos (gerenciador de arquivos da Hostinger, GitHub Pages, Netlify, Cloudflare Pages). Antes de ligar a campanha, o [checklist de publicação](docs/checklist-publicacao.md).

## Relação com o Trilha

O Trilha não constrói landing pages ([ADR-007 do Trilha](https://github.com/davi-barbosap/Trilha/blob/main/docs/decisoes/007-escopo-do-sistema.md)); este repositório é a ferramenta paralela que cumpre o contrato que ele espera ([ecossistema](https://github.com/davi-barbosap/Trilha/blob/main/docs/ecossistema.md) §3). O que liga os dois:
- a matéria-prima do texto vem da ficha da oferta (`ofertas/*.yaml`) e dos motivos de perda do Kommo (pacote de briefing do Trilha);
- o lead chega ao Kommo com os campos que o raio-x e a conversão real usam;
- o campo `pagina_id` permite ao raio-x comparar versões de página e origens de tráfego pela qualificação e pela venda.

## Estrutura

```
trilha_lp/           esquema, revisão do texto, montagem da página, CLI
trilha_lp/modelo/    estilo.css e rastreio.js (copiado para cada página)
exemplos/            página de exemplo (dados fictícios)
docs/                estrutura, contrato de rastreamento, checklist de publicação
tests/               testes (Python e JavaScript)
```
