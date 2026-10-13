# Checklist de publicação

Nada de campanha ligada antes de tudo marcado.

## Texto
- [ ] `python -m trilha_lp validar` sem erro; cada aviso lido e resolvido ou aceito de propósito
- [ ] Título diz o resultado, não quem é a empresa
- [ ] Provas verdadeiras e com fonte (CRM, construtora, cartório)
- [ ] Objeções conferidas com os motivos de perda recentes do Kommo
- [ ] CRECI, registro da incorporação e avisos legais no rodapé; política de privacidade do cliente no ar

## Rastreamento
- [ ] `gtm_id` e `webhook_url` preenchidos (sem eles a página está em modo teste)
- [ ] Abrir a página com `?utm_source=teste&utm_content=TESTE01&gclid=teste` e enviar um lead de teste
- [ ] O lead apareceu no Kommo, na etapa `lead`, com UTMs, `gclid`, `landing_page` e telefone em E.164
- [ ] No GTM (modo de visualização), `generate_lead` com `entrega: webhook_ok` e as tags do Google Ads e do Meta disparando
- [ ] No Gerenciador de Eventos do Meta, o `Lead` do navegador e o do servidor com o mesmo `event_id` (deduplicados)
- [ ] Botão de WhatsApp abre a conversa com o código do criativo na mensagem
- [ ] Lead de teste apagado ou marcado como teste no Kommo

## Página
- [ ] Testada no celular de verdade (não só no navegador reduzido)
- [ ] Imagens reais, comprimidas (WebP), com texto alternativo
- [ ] Velocidade medida no celular (PageSpeed Insights) e registrada
- [ ] Domínio com HTTPS

## Depois de ligar
- [ ] Na primeira semana, o raio-x do Trilha-ads mostra os leads da página com canal e `landing_page` preenchidos (sem "Não rastreado")
- [ ] Teste A/B decidido pela qualificação e pela visita por `pagina_id`, com amostra mínima
