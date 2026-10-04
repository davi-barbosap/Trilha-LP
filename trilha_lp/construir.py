"""Monta a landing page (HTML estático) a partir do `pagina.yaml`.

Sem framework e sem dependência no navegador: uma página leve, que abre rápido no
celular, com o rastreamento sob controle (`rastreio.js`).
"""

from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path
from urllib.parse import quote_plus

from trilha_lp.esquema import Imagem, Lp

MODELO = Path(__file__).parent / "modelo"


def _e(texto: str) -> str:
    return escape(texto, quote=True)


def _imagem(img: Imagem, classe: str, principal: bool = False) -> str:
    if not img.src:
        return f'<div class="{classe} reservado" role="img" aria-label="{_e(img.alt)}"></div>'
    carga = 'fetchpriority="high"' if principal else 'loading="lazy" decoding="async"'
    return (f'<img class="{classe}" src="{_e(img.src)}" alt="{_e(img.alt)}" '
            f'width="{img.largura}" height="{img.altura}" {carga}>')


def _cta(lp: Lp, texto: str, origem_cta: str) -> str:
    if lp.topo.cta.acao == "whatsapp":
        return (f'<a class="botao" href="https://wa.me/{lp.contato.whatsapp}" data-whatsapp '
                f'data-origem-cta="{origem_cta}" rel="noopener">{_e(texto)}</a>')
    return f'<a class="botao" href="#formulario" data-origem-cta="{origem_cta}">{_e(texto)}</a>'


def _lista(itens: list[str], classe: str) -> str:
    if not itens:
        return ""
    return f'<ul class="{classe}">' + "".join(f"<li>{_e(i)}</li>" for i in itens) + "</ul>"


def _topo(lp: Lp) -> str:
    t = lp.topo
    return f"""
<section class="topo" id="topo">
  <div class="topo-texto">
    <h1>{_e(t.titulo)}</h1>
    <p class="subtitulo">{_e(t.subtitulo)}</p>
    {_lista(t.provas, "provas")}
    {_cta(lp, t.cta.texto, "topo")}
    {_lista(t.reducao_medo, "reducao-medo")}
  </div>
  <div class="topo-imagem">{_imagem(t.imagem, "foto", principal=True)}</div>
</section>"""


def _dor(lp: Lp) -> str:
    d = lp.dor
    return f"""
<section class="dor">
  <h2>{_e(d.titulo)}</h2>
  <p>{_e(d.problema)}</p>
  <p>{_e(d.agravamento)}</p>
  <p class="solucao">{_e(d.solucao)}</p>
  {_cta(lp, lp.topo.cta.texto, "dor")}
</section>"""


def _prova(lp: Lp) -> str:
    p = lp.prova_social
    numeros = "".join(f'<li><strong>{_e(n.numero)}</strong><span>{_e(n.texto)}</span></li>' for n in p.numeros)
    depoimentos = "".join(
        f'<figure class="depoimento"><blockquote>{_e(d.texto)}</blockquote><figcaption>{_e(d.autor)}</figcaption></figure>'
        for d in p.depoimentos
    )
    return f"""
<section class="prova">
  <h2>{_e(p.titulo)}</h2>
  {f'<ul class="numeros">{numeros}</ul>' if numeros else ""}
  {f'<div class="depoimentos">{depoimentos}</div>' if depoimentos else ""}
</section>"""


def _beneficios(lp: Lp) -> str:
    itens = "".join(
        f'<article class="beneficio">{_imagem(b.imagem, "foto-beneficio") if b.imagem else ""}'
        f"<h3>{_e(b.titulo)}</h3><p>{_e(b.texto)}</p></article>"
        for b in lp.beneficios.itens
    )
    return f"""
<section class="beneficios">
  <h2>{_e(lp.beneficios.titulo)}</h2>
  <div class="grade">{itens}</div>
  {_cta(lp, lp.topo.cta.texto, "beneficios")}
</section>"""


def _como_funciona(lp: Lp) -> str:
    passos = "".join(f"<li><h3>{_e(p.titulo)}</h3><p>{_e(p.texto)}</p></li>" for p in lp.como_funciona.passos)
    return f"""
<section class="como-funciona">
  <h2>{_e(lp.como_funciona.titulo)}</h2>
  <ol class="passos">{passos}</ol>
</section>"""


def _objecoes(lp: Lp) -> str:
    o = lp.objecoes
    itens = "".join(f"<details><summary>{_e(p.pergunta)}</summary><p>{_e(p.resposta)}</p></details>" for p in o.itens)
    return f"""
<section class="objecoes">
  <h2>{_e(o.titulo)}</h2>
  {_lista(o.garantias, "garantias")}
  <div class="perguntas">{itens}</div>
</section>"""


def _fechamento(lp: Lp) -> str:
    f, form = lp.fechamento, lp.formulario
    email = ('<label>E-mail <span class="opcional">(opcional)</span>'
             '<input name="email" type="email" autocomplete="email" inputmode="email"></label>') if form.pedir_email else ""
    qualificacao = ""
    if form.qualificacao:
        opcoes = "".join(f'<option value="{_e(o)}">{_e(o)}</option>' for o in form.qualificacao.opcoes)
        qualificacao = (f'<label>{_e(form.qualificacao.rotulo)}<select name="qualificacao" required>'
                        f'<option value="" disabled selected>Selecione</option>{opcoes}</select></label>')
    return f"""
<section class="fechamento" id="formulario">
  <div class="fechamento-texto">
    <h2>{_e(f.titulo)}</h2>
    <p class="subtitulo">{_e(f.subtitulo)}</p>
    {_lista(f.lista, "lista-fechamento")}
    {_lista(f.provas, "provas")}
  </div>
  <form class="formulario" novalidate data-formulario>
    <label>Nome<input name="nome" autocomplete="name" required></label>
    <label>WhatsApp<input name="telefone" type="tel" autocomplete="tel" inputmode="tel" placeholder="(11) 91234-5678" required></label>
    {email}
    {qualificacao}
    <label class="isca" aria-hidden="true">Empresa<input name="empresa" tabindex="-1" autocomplete="off"></label>
    <button class="botao" type="submit">{_e(form.botao)}</button>
    <p class="consentimento">{_e(form.consentimento)} <a href="{_e(lp.marca.politica_privacidade_url)}" target="_blank" rel="noopener">Política de privacidade</a>.</p>
    <p class="erro" role="alert" hidden></p>
  </form>
  <div class="confirmacao" role="status" hidden>
    <p>{_e(form.confirmacao)}</p>
  </div>
</section>"""


def _rodape(lp: Lp) -> str:
    m = lp.marca
    linhas = [m.nome] + ([m.registro_profissional] if m.registro_profissional else []) + m.avisos_legais
    return (f'<footer class="rodape">{"".join(f"<p>{_e(l)}</p>" for l in linhas)}'
            f'<p><a href="{_e(m.politica_privacidade_url)}" target="_blank" rel="noopener">Política de privacidade</a></p></footer>')


def _gtm(gtm_id: str) -> tuple[str, str]:
    if not gtm_id:
        return "", ""
    cabeca = ("<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});"
              "var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;"
              f"j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','{gtm_id}');</script>")
    corpo = (f'<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={gtm_id}" height="0" width="0" '
             'style="display:none;visibility:hidden"></iframe></noscript>')
    return cabeca, corpo


def _estilo(lp: Lp) -> str:
    c, f = lp.marca.cores, lp.marca.fontes
    variaveis = (f":root{{--primaria:{c.primaria};--secundaria:{c.secundaria};--fundo:{c.fundo};--texto:{c.texto};"
                 f"--fonte-titulos:'{f.titulos}',system-ui,sans-serif;--fonte-texto:'{f.texto}',system-ui,sans-serif}}")
    return variaveis + (MODELO / "estilo.css").read_text(encoding="utf-8")


def html(lp: Lp) -> str:
    """A página completa. Ordem fixa: o segundo bloco depende da origem do tráfego."""
    segundo, outro = (_dor, _prova) if lp.pagina.origem == "meta" else (_prova, _dor)
    tem = {_dor: lp.dor is not None, _prova: lp.prova_social is not None}
    blocos = [_topo(lp), segundo(lp), _beneficios(lp)]
    if tem[outro]:
        blocos.append(outro(lp))
    blocos += [_como_funciona(lp), _objecoes(lp), _fechamento(lp)]
    config = {
        "pagina_id": lp.pagina.id, "cliente": lp.pagina.cliente, "oferta": lp.pagina.oferta, "origem": lp.pagina.origem,
        "webhook_url": lp.rastreio.webhook_url, "pagina_obrigado": lp.rastreio.pagina_obrigado,
        "whatsapp": lp.contato.whatsapp, "mensagem_whatsapp": lp.contato.mensagem_whatsapp,
    }
    config_json = json.dumps(config, ensure_ascii=False).replace("</", "<\\/")
    gtm_cabeca, gtm_corpo = _gtm(lp.rastreio.gtm_id)
    fontes = quote_plus(lp.marca.fontes.titulos) + ":wght@600;800&family=" + quote_plus(lp.marca.fontes.texto) + ":wght@400;600"
    logo = f'<img class="logo" src="{_e(lp.marca.logo)}" alt="{_e(lp.marca.nome)}" height="40">' if lp.marca.logo else f'<span class="logo-texto">{_e(lp.marca.nome)}</span>'
    whatsapp_fixo = (f'<a class="whatsapp-fixo" href="https://wa.me/{lp.contato.whatsapp}" data-whatsapp '
                     'data-origem-cta="botao_fixo" rel="noopener" aria-label="Conversar no WhatsApp">WhatsApp</a>')
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(lp.pagina.titulo_seo)}</title>
<meta name="description" content="{_e(lp.pagina.descricao_seo)}">
<meta property="og:title" content="{_e(lp.pagina.titulo_seo)}">
<meta property="og:description" content="{_e(lp.pagina.descricao_seo)}">
{f'<meta property="og:image" content="{_e(lp.topo.imagem.src)}">' if lp.topo.imagem.src else ""}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={fontes}&display=swap">
<style>{_estilo(lp)}</style>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}
gtag('consent','default',{{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied',wait_for_update:500}});
try{{if(localStorage.getItem('trilha_lp_consentimento')==='aceito')gtag('consent','update',{{ad_storage:'granted',ad_user_data:'granted',ad_personalization:'granted',analytics_storage:'granted'}});}}catch(e){{}}</script>
{gtm_cabeca}
<script type="application/json" id="lp-config">{config_json}</script>
<script src="rastreio.js" defer></script>
</head>
<body>
{gtm_corpo}
<header class="cabecalho">{logo}</header>
<main>{"".join(blocos)}
</main>
{_rodape(lp)}
{whatsapp_fixo}
<div class="consentimento-cookies" data-consentimento hidden>
  <p>Usamos cookies para medir os anúncios e melhorar o atendimento. <a href="{_e(lp.marca.politica_privacidade_url)}" target="_blank" rel="noopener">Saiba mais</a>.</p>
  <button type="button" data-consentimento-aceitar>Aceitar</button>
  <button type="button" class="secundario" data-consentimento-recusar>Recusar</button>
</div>
</body>
</html>
"""


def construir(lp: Lp, saida: str | Path) -> Path:
    destino = Path(saida) / lp.pagina.id
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "index.html").write_text(html(lp), encoding="utf-8")
    shutil.copyfile(MODELO / "rastreio.js", destino / "rastreio.js")
    return destino
