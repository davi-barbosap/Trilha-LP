import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const r = require('../trilha_lp/modelo/rastreio.js');

const AGORA = '2026-10-04T12:00:00.000Z';

test('clique com campanha grava a atribuição', () => {
  const d = r.decidirAtribuicao('?utm_source=facebook&utm_content=VD01&fbclid=x', null, '', 'lp.com', AGORA, '/');
  assert.equal(d.gravar, true);
  assert.equal(d.atribuicao.utm_source, 'facebook');
  assert.equal(d.atribuicao.fbclid, 'x');
  assert.equal(d.atribuicao.gclid, '');
});

test('visita sem campanha não apaga a mídia paga guardada', () => {
  const salva = r.decidirAtribuicao('?gclid=g1', null, '', 'lp.com', AGORA, '/').atribuicao;
  const d = r.decidirAtribuicao('', salva, 'https://www.google.com/', 'lp.com', AGORA, '/');
  assert.equal(d.gravar, false);
  assert.equal(d.atribuicao.gclid, 'g1');
});

test('primeira visita sem campanha: outro site ou direto', () => {
  assert.equal(r.decidirAtribuicao('', null, 'https://blog.com/x', 'lp.com', AGORA, '/').atribuicao.utm_source, '(referral)');
  assert.equal(r.decidirAtribuicao('', null, '', 'lp.com', AGORA, '/').atribuicao.utm_source, '(direct)');
  assert.equal(r.decidirAtribuicao('', null, 'https://lp.com/a', 'lp.com', AGORA, '/').atribuicao.utm_source, '(direct)');
});

test('telefone em E.164 sem duplicar o 55', () => {
  assert.equal(r.normalizarTelefone('(11) 91234-5678'), '+5511912345678');
  assert.equal(r.normalizarTelefone('+55 11 91234-5678'), '+5511912345678');
  assert.equal(r.normalizarTelefone('5511912345678'), '+5511912345678');
  assert.equal(r.normalizarTelefone('011 91234-5678'), '+5511912345678');
  assert.equal(r.normalizarTelefone('1234'), null);
});

test('só celular brasileiro passa', () => {
  assert.equal(r.celularBR('+5511912345678'), true);
  assert.equal(r.celularBR('+551133334444'), false);
  assert.equal(r.celularBR('+5501912345678'), false);
});

test('payload tem esquema fixo e event_id', () => {
  const cfg = { pagina_id: 'p-meta', cliente: 'c', oferta: 'o', origem: 'meta' };
  const attr = r.decidirAtribuicao('?utm_source=facebook', null, '', 'lp.com', AGORA, '/').atribuicao;
  const p = r.montarPayload(cfg, attr, { nome: 'Ana', telefone: '+5511912345678' }, 'ev-1', AGORA, 'https://lp.com/', 'ua');
  for (const k of r.CHAVES) assert.ok(k in p, k);
  assert.equal(p.event_id, 'ev-1');
  assert.equal(p.email, '');
  assert.equal(p.pagina_id, 'p-meta');
});

test('WhatsApp leva o código do criativo', () => {
  const cfg = { pagina_id: 'p-meta', mensagem_whatsapp: 'Olá' };
  assert.equal(r.mensagemWhatsapp(cfg, { utm_content: 'VD01' }), 'Olá (cód. VD01)');
  assert.equal(r.mensagemWhatsapp(cfg, { utm_content: '' }), 'Olá (cód. p-meta)');
});
