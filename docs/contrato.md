# Contrato de rastreamento: página → n8n → Kommo → Trilha-ads

## Atribuição guardada no navegador

| Situação | O que acontece |
|---|---|
| URL com qualquer UTM ou identificador de clique | grava tudo (o clique novo vence), por 90 dias |
| URL sem campanha e atribuição guardada | mantém a guardada (a navegação orgânica não apaga a mídia paga) |
| primeira visita sem campanha | `utm_source` = `(referral)` se veio de outro site, `(direct)` se não |

Chave `trilha_lp_atribuicao` no `localStorage`. Se o armazenamento estiver bloqueado, a página segue com a atribuição só da visita atual.

## Payload enviado ao webhook (POST JSON, esquema fixo)

Todas as chaves vão sempre, vazias quando não houver.

| Chave | Conteúdo |
|---|---|
| `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term` | da atribuição |
| `gclid`, `gbraid`, `wbraid`, `fbclid`, `ttclid`, `msclkid` | identificadores de clique |
| `referrer`, `landing_page`, `capturado_em` | de onde veio, onde entrou, hora do clique |
| `nome`, `telefone` (E.164), `email`, `qualificacao` | formulário |
| `event_id` | gerado na página; o mesmo vai no evento do navegador e deve ir na API de Conversões |
| `pagina_id`, `cliente`, `oferta`, `origem_trafego` | identificação da página e da versão |
| `consentimento_contato`, `enviado_em`, `pagina`, `user_agent` | registro do envio |

O webhook responde 2xx só depois de gravar. Sem 2xx, a página mostra o erro e oferece o WhatsApp; nenhuma conversão é disparada.

## O que o n8n grava no Kommo

Campos padrão do Trilha-ads, criados em toda conta pelo `python -m trilha kommo preparar` ([Kommo](https://github.com/davi-barbosap/Trilha-ads/blob/main/docs/integracoes/kommo.md) §4). `landing_page` e `event_id_lead` ainda não são lidos pelo raio-x nem pelo W01.

**Pendente — bloqueia página em campanha:** o fluxo que recebe este POST e grava lead e contato no Kommo (W15 no [roadmap do Trilha-ads](https://github.com/davi-barbosap/Trilha-ads/blob/main/docs/roadmap.md)) ainda não existe. Como o payload traz dados pessoais, a gravação passa pela trilha-api ([ADR-002](https://github.com/davi-barbosap/Trilha-ads/blob/main/docs/decisoes/002-n8n-orquestrador.md)), não por nós do n8n.

| Payload | Kommo |
|---|---|
| `nome`, `telefone`, `email` | contato (telefone em E.164 é a chave da pessoa no raio-x) |
| `gclid`, `gbraid`, `wbraid`, `fbclid`, `ttclid` | campos de mesmo nome no lead |
| `utm_*` | campos de mesmo nome no lead |
| `utm_source` normalizado | campo `origem` |
| `pagina_id` | campo `landing_page` (novo; para o raio-x do Trilha-ads comparar versões de página) |
| `qualificacao` | campo do cliente (ex.: "Finalidade") |
| `event_id` | campo `event_id_lead` (novo; o W01 do Trilha-ads passa a usá-lo no `Lead` enviado ao Meta, para deduplicar com o do navegador) |

O lead entra na etapa `lead` do funil cadastrado no `perfil.yaml` do cliente no Trilha-ads.

## Eventos no dataLayer (GTM)

| Evento | Quando | Dados |
|---|---|---|
| `attribution_ready` | ao abrir | `atribuicao`, `pagina_id` |
| `whatsapp_click` | clique em qualquer WhatsApp | `origem_cta` (`topo`, `botao_fixo`, `falha_formulario`…) |
| `form_start` | primeira digitação | `pagina_id` |
| `form_error` | validação ou envio | `motivo` |
| `generate_lead` | **só após o webhook confirmar** (ou `modo_teste`) | `event_id`, `entrega`, UTMs, `enhanced_conversion_data` (e-mail e telefone para conversões otimizadas) |

Se o pixel do Meta estiver na página, `fbq('track', 'Lead', {}, {eventID})` sai junto com o mesmo `event_id`. No GTM, a tag de conversão do Google Ads e a do Meta disparam em `generate_lead` com `entrega` = `webhook_ok`.

## Consentimento

Modo de consentimento do Google com tudo negado por padrão; o aviso de cookies grava a escolha e libera os armazenamentos ao aceitar. O formulário traz o texto de consentimento de contato e o link da política de privacidade do cliente.
