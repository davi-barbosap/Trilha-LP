"""Revisão do texto antes de publicar: regras da Trilha que o esquema não pega.

Devolve avisos; quem decide é o assessor. Nada aqui reescreve o texto.
"""

from __future__ import annotations

import re
import unicodedata

from trilha_lp.esquema import Lp

TITULOS_GENERICOS = {
    "depoimentos", "nossos depoimentos", "o que dizem nossos clientes", "o que nossos clientes dizem",
    "pessoas reais resultados reais", "resultados reais", "como funciona", "nossos diferenciais",
    "diferenciais", "beneficios", "sobre nos", "quem somos",
}
LIMITE_TITULO = 90


def _sem_acento(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def _textos(lp: Lp) -> list[tuple[str, str]]:
    """(onde, texto) de tudo que o visitante lê."""
    saida = [("topo.titulo", lp.topo.titulo), ("topo.subtitulo", lp.topo.subtitulo), ("topo.cta", lp.topo.cta.texto)]
    saida += [(f"topo.provas[{i}]", t) for i, t in enumerate(lp.topo.provas)]
    saida += [(f"topo.reducao_medo[{i}]", t) for i, t in enumerate(lp.topo.reducao_medo)]
    if lp.dor:
        saida += [(f"dor.{c}", getattr(lp.dor, c)) for c in ("titulo", "problema", "agravamento", "solucao")]
    if lp.prova_social:
        saida.append(("prova_social.titulo", lp.prova_social.titulo))
        saida += [(f"prova_social.depoimentos[{i}]", d.texto) for i, d in enumerate(lp.prova_social.depoimentos)]
        saida += [(f"prova_social.numeros[{i}]", f"{n.numero} {n.texto}") for i, n in enumerate(lp.prova_social.numeros)]
    saida.append(("beneficios.titulo", lp.beneficios.titulo))
    for i, b in enumerate(lp.beneficios.itens):
        saida += [(f"beneficios.itens[{i}].titulo", b.titulo), (f"beneficios.itens[{i}].texto", b.texto)]
    saida.append(("como_funciona.titulo", lp.como_funciona.titulo))
    saida += [(f"como_funciona.passos[{i}]", f"{p.titulo} {p.texto}") for i, p in enumerate(lp.como_funciona.passos)]
    saida += [(f"objecoes.itens[{i}]", f"{p.pergunta} {p.resposta}") for i, p in enumerate(lp.objecoes.itens)]
    saida += [(f"objecoes.garantias[{i}]", t) for i, t in enumerate(lp.objecoes.garantias)]
    saida += [("fechamento.titulo", lp.fechamento.titulo), ("fechamento.subtitulo", lp.fechamento.subtitulo)]
    saida += [(f"fechamento.lista[{i}]", t) for i, t in enumerate(lp.fechamento.lista)]
    saida += [("formulario.botao", lp.formulario.botao), ("contato.mensagem_whatsapp", lp.contato.mensagem_whatsapp)]
    return saida


def revisar(lp: Lp) -> list[str]:
    avisos = []
    textos = _textos(lp)
    proibidos = [(t, "termo proibido pela marca") for t in lp.marca.termos_proibidos]
    proibidos += [(t, "promessa proibida") for t in lp.marca.promessas_proibidas]
    for onde, texto in textos:
        normal = _sem_acento(texto)
        for termo, motivo in proibidos:
            if _sem_acento(termo) in normal:
                avisos.append(f"{onde}: {motivo} — \"{termo}\"")
        if lp.pagina.segmento == "imobiliario" and re.search(r"r\$\s*\d", normal) and "a partir de" not in normal:
            avisos.append(f"{onde}: preço sem \"a partir de\" (no imobiliário a landing mostra só o valor de entrada, amarrado à visita)")
        if lp.pagina.segmento == "imobiliario" and re.search(r"valoriza\w*\s+garantid|garant\w*\s+(de\s+)?valoriza", normal):
            avisos.append(f"{onde}: promessa de valorização garantida")
    for onde, titulo in [("prova_social.titulo", lp.prova_social.titulo if lp.prova_social else ""),
                         ("beneficios.titulo", lp.beneficios.titulo), ("como_funciona.titulo", lp.como_funciona.titulo)]:
        if re.sub(r"[^a-z ]", "", _sem_acento(titulo)).strip() in TITULOS_GENERICOS:
            avisos.append(f"{onde}: título genérico (\"{titulo}\"); o título do bloco diz o benefício, porque muita gente só lê os títulos")
    if len(lp.topo.titulo) > LIMITE_TITULO:
        avisos.append(f"topo.titulo com {len(lp.topo.titulo)} caracteres: no celular passa de 3 linhas e empurra o botão para baixo")
    if not lp.topo.imagem.src:
        avisos.append("topo.imagem sem arquivo: a página sai com um espaço reservado")
    if not lp.rastreio.webhook_url:
        avisos.append("rastreio.webhook_url vazio: modo teste, nenhum lead chega ao Kommo")
    if not lp.rastreio.gtm_id:
        avisos.append("rastreio.gtm_id vazio: sem tag do Google e do Meta, o freio de emergência e a otimização ficam cegos")
    if lp.formulario.qualificacao is None:
        avisos.append("formulario sem pergunta de qualificação: mais volume, lead menos filtrado")
    if lp.dor and lp.prova_social is None:
        avisos.append("sem bloco prova_social: a página não tem prova além do topo")
    return avisos
