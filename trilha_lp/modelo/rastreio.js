/* Rastreamento da landing page da Trilha.
 *
 * 1. Guarda de onde o visitante veio (UTMs e identificadores de clique) por 90 dias:
 *    um clique novo com campanha substitui o anterior; visita sem campanha não apaga a mídia paga.
 * 2. Envia o lead ao webhook (n8n → Kommo) com esquema fixo e um event_id.
 * 3. Só dispara a conversão (generate_lead / Lead) depois que o webhook confirma o recebimento,
 *    com o mesmo event_id que o servidor manda ao Meta, para deduplicar.
 * 4. Botão de WhatsApp leva o código do criativo na mensagem, para o lead não chegar sem atribuição.
 */
(function (raiz) {
  'use strict';

  var CHAVES = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term',
    'gclid', 'gbraid', 'wbraid', 'fbclid', 'ttclid', 'msclkid'];
  var ARMAZEM = 'trilha_lp_atribuicao';
  var VALIDADE_MS = 90 * 24 * 60 * 60 * 1000;
  var TEMPO_ENVIO_MS = 12000;

  function molde() {
    var a = {};
    CHAVES.forEach(function (k) { a[k] = ''; });
    a.referrer = ''; a.landing_page = ''; a.capturado_em = '';
    return a;
  }

  /* Decide a atribuição: clique com campanha vence; sem campanha, vale a guardada; sem nada, origem da visita. */
  function decidirAtribuicao(busca, salva, referrer, hostAtual, agora, caminho) {
    var p = new URLSearchParams(busca);
    var a = molde();
    a.landing_page = caminho;
    a.capturado_em = agora;
    if (CHAVES.some(function (k) { return p.get(k); })) {
      CHAVES.forEach(function (k) { a[k] = (p.get(k) || '').trim(); });
      a.referrer = referrer || '(direct)';
      return { atribuicao: a, gravar: true };
    }
    if (salva) return { atribuicao: salva, gravar: false };
    var externo = false;
    try { externo = !!referrer && new URL(referrer).host !== hostAtual; } catch (e) { externo = false; }
    a.utm_source = externo ? '(referral)' : '(direct)';
    a.utm_medium = externo ? 'referral' : '(none)';
    a.referrer = referrer || '(direct)';
    return { atribuicao: a, gravar: true };
  }

  /* Telefone em E.164, sem duplicar o 55. Devolve null se não for um número brasileiro. */
  function normalizarTelefone(texto) {
    var d = String(texto || '').replace(/\D/g, '').replace(/^0+/, '');
    if ((d.length === 12 || d.length === 13) && d.indexOf('55') === 0) return '+' + d;
    if (d.length === 10 || d.length === 11) return '+55' + d;
    return null;
  }

  /* Celular brasileiro: DDD válido + 9 dígitos começando com 9. */
  function celularBR(e164) {
    return !!e164 && /^\+55[1-9][1-9]9\d{8}$/.test(e164);
  }

  function novoEventId() {
    if (raiz.crypto && raiz.crypto.randomUUID) return raiz.crypto.randomUUID();
    return 'lp-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
  }

  /* Esquema fixo: todas as chaves sempre presentes (a automação aprende a estrutura pelo primeiro envio). */
  function montarPayload(cfg, atribuicao, campos, eventId, agora, pagina, userAgent) {
    var p = molde();
    Object.keys(p).forEach(function (k) { p[k] = atribuicao[k] || ''; });
    p.nome = campos.nome || '';
    p.telefone = campos.telefone || '';
    p.email = campos.email || '';
    p.qualificacao = campos.qualificacao || '';
    p.event_id = eventId;
    p.pagina_id = cfg.pagina_id;
    p.cliente = cfg.cliente;
    p.oferta = cfg.oferta;
    p.origem_trafego = cfg.origem;
    p.consentimento_contato = true;
    p.enviado_em = agora;
    p.pagina = pagina;
    p.user_agent = userAgent;
    return p;
  }

  function mensagemWhatsapp(cfg, atribuicao) {
    var codigo = atribuicao.utm_content || cfg.pagina_id;
    return cfg.mensagem_whatsapp + ' (cód. ' + codigo + ')';
  }

  var api = {
    CHAVES: CHAVES, decidirAtribuicao: decidirAtribuicao, normalizarTelefone: normalizarTelefone,
    celularBR: celularBR, montarPayload: montarPayload, mensagemWhatsapp: mensagemWhatsapp, novoEventId: novoEventId
  };
  if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }

  /* ---------- navegador ---------- */
  var doc = raiz.document;
  var cfg = JSON.parse(doc.getElementById('lp-config').textContent);
  raiz.dataLayer = raiz.dataLayer || [];

  function lerSalva() {
    try {
      var v = JSON.parse(raiz.localStorage.getItem(ARMAZEM) || 'null');
      if (v && Date.now() - v.t < VALIDADE_MS) return v.a;
    } catch (e) { /* armazenamento bloqueado: segue sem */ }
    return null;
  }
  function gravar(a) {
    try { raiz.localStorage.setItem(ARMAZEM, JSON.stringify({ t: Date.now(), a: a })); } catch (e) { /* idem */ }
  }

  var decisao = decidirAtribuicao(raiz.location.search, lerSalva(), doc.referrer, raiz.location.host,
    new Date().toISOString(), raiz.location.pathname + raiz.location.search);
  if (decisao.gravar) gravar(decisao.atribuicao);
  var atribuicao = decisao.atribuicao;
  raiz.dataLayer.push({ event: 'attribution_ready', atribuicao: atribuicao, pagina_id: cfg.pagina_id });

  /* WhatsApp com código do criativo */
  doc.querySelectorAll('[data-whatsapp]').forEach(function (el) {
    el.addEventListener('click', function () {
      el.href = 'https://wa.me/' + cfg.whatsapp + '?text=' + encodeURIComponent(mensagemWhatsapp(cfg, atribuicao));
      raiz.dataLayer.push({ event: 'whatsapp_click', origem_cta: el.getAttribute('data-origem-cta') || '', pagina_id: cfg.pagina_id });
    });
  });

  /* Consentimento (LGPD + modo de consentimento do Google) */
  var faixa = doc.querySelector('[data-consentimento]');
  var escolha = null;
  try { escolha = raiz.localStorage.getItem('trilha_lp_consentimento'); } catch (e) { escolha = null; }
  if (faixa && !escolha) faixa.hidden = false;
  function decidir(valor) {
    try { raiz.localStorage.setItem('trilha_lp_consentimento', valor); } catch (e) { /* idem */ }
    if (valor === 'aceito' && typeof raiz.gtag === 'function') {
      raiz.gtag('consent', 'update', { ad_storage: 'granted', ad_user_data: 'granted', ad_personalization: 'granted', analytics_storage: 'granted' });
    }
    if (faixa) faixa.hidden = true;
  }
  var aceitar = doc.querySelector('[data-consentimento-aceitar]');
  var recusar = doc.querySelector('[data-consentimento-recusar]');
  if (aceitar) aceitar.addEventListener('click', function () { decidir('aceito'); });
  if (recusar) recusar.addEventListener('click', function () { decidir('recusado'); });

  /* Formulário */
  var form = doc.querySelector('[data-formulario]');
  if (!form) return;
  var erro = form.querySelector('.erro');
  var confirmacao = doc.querySelector('.confirmacao');
  var iniciado = false;

  form.addEventListener('input', function () {
    if (iniciado) return;
    iniciado = true;
    raiz.dataLayer.push({ event: 'form_start', pagina_id: cfg.pagina_id });
  });

  function mostrarErro(texto, motivo) {
    erro.textContent = texto;
    erro.hidden = false;
    raiz.dataLayer.push({ event: 'form_error', motivo: motivo, pagina_id: cfg.pagina_id });
  }

  function concluir(payload, entrega) {
    raiz.dataLayer.push({
      event: 'generate_lead', event_id: payload.event_id, pagina_id: cfg.pagina_id, entrega: entrega,
      utm_source: payload.utm_source, utm_campaign: payload.utm_campaign, utm_content: payload.utm_content,
      enhanced_conversion_data: { email: payload.email, phone_number: payload.telefone }
    });
    if (typeof raiz.fbq === 'function') raiz.fbq('track', 'Lead', {}, { eventID: payload.event_id });
    if (cfg.pagina_obrigado) { raiz.location.href = cfg.pagina_obrigado; return; }
    form.hidden = true;
    confirmacao.hidden = false;
  }

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    erro.hidden = true;
    var dados = new FormData(form);
    if (dados.get('empresa')) { form.hidden = true; confirmacao.hidden = false; return; } /* robô */
    var nome = String(dados.get('nome') || '').trim();
    var telefone = normalizarTelefone(dados.get('telefone'));
    var email = String(dados.get('email') || '').trim();
    var qualificacao = String(dados.get('qualificacao') || '');
    if (nome.length < 2) return mostrarErro('Digite seu nome.', 'validacao_nome');
    if (!celularBR(telefone)) return mostrarErro('Digite um WhatsApp válido com DDD.', 'validacao_telefone');
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return mostrarErro('Confira o e-mail.', 'validacao_email');
    if (form.querySelector('[name="qualificacao"]') && !qualificacao) return mostrarErro('Escolha uma opção.', 'validacao_qualificacao');

    var payload = montarPayload(cfg, atribuicao, { nome: nome, telefone: telefone, email: email, qualificacao: qualificacao },
      novoEventId(), new Date().toISOString(), raiz.location.href, raiz.navigator.userAgent);

    if (!cfg.webhook_url) {
      raiz.console.warn('[trilha-lp] modo teste: lead não enviado', payload);
      return concluir(payload, 'modo_teste');
    }
    var botao = form.querySelector('button[type="submit"]');
    botao.disabled = true;
    var controle = new AbortController();
    var limite = raiz.setTimeout(function () { controle.abort(); }, TEMPO_ENVIO_MS);
    raiz.fetch(cfg.webhook_url, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      keepalive: true, signal: controle.signal
    }).then(function (r) {
      raiz.clearTimeout(limite);
      if (!r.ok) throw new Error('HTTP ' + r.status);
      concluir(payload, 'webhook_ok');
    }).catch(function (e) {
      raiz.clearTimeout(limite);
      botao.disabled = false;
      var link = 'https://wa.me/' + cfg.whatsapp + '?text=' + encodeURIComponent(mensagemWhatsapp(cfg, atribuicao));
      mostrarErro('Não conseguimos enviar agora. Fale com a gente pelo WhatsApp.', 'envio: ' + e.message);
      var a = doc.createElement('a');
      a.href = link; a.textContent = ' Abrir WhatsApp'; a.setAttribute('data-origem-cta', 'falha_formulario');
      erro.appendChild(a);
    });
  });
})(typeof window !== 'undefined' ? window : globalThis);
