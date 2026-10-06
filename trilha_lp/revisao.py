"""Revisão do texto antes de publicar: regras da Trilha que o esquema não pega.

As regras de texto seguem o padrão de texto da Trilha (o arquivo canônico mora no Trilha-copy; aqui fica a cópia dos
vocabulários em regras/padrao-vocabularios.yaml). Três gravidades, como nas outras ferramentas:

    bloqueia   não vai ao ar assim: termo ou promessa proibidos, garantia de resultado, preço onde o segmento não mostra
    atencao    vai custar caro: título genérico, título longo, preço fora da forma, rastreamento ou imagem faltando
    sugestao   melhora a página: botão genérico, pergunta de qualificação

Quem decide é o assessor. Nada aqui reescreve o texto. O texto inteiro também passa pelo padrão completo no
Trilha-copy, com o contrato do cliente: python -m trilha_copy revisar-pagina <pagina.yaml>.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from trilha_lp import padrao
from trilha_lp.esquema import Lp

Nivel = Literal["bloqueia", "atencao", "sugestao"]
NIVEIS: tuple[Nivel, ...] = ("bloqueia", "atencao", "sugestao")


@dataclass(frozen=True)
class Aviso:
    nivel: Nivel
    texto: str

    def __str__(self) -> str:
        return self.texto


def _sem_pontuacao(texto: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", padrao.normalizar(texto)).split())


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


def _frases(texto: str) -> list[str]:
    return [f for f in re.split(r"(?<=[.!?…])\s+|\n+", texto) if f.strip()]


def _precos(frase: str) -> list[int]:
    """Posições de valores em reais que são preço ("por", "a partir de", "10x"… por perto), não número de prova."""
    janela = padrao.carregar()["janela_preco_palavras"]
    contexto = [i for i, _ in padrao.posicoes(padrao.carregar()["vocabularios"]["preco_contexto"], frase)]
    return [i for i, _ in padrao.posicoes(padrao.carregar()["vocabularios"]["preco_valor"], frase)
            if any(abs(i - j) <= janela for j in contexto)]


def revisar(lp: Lp) -> list[Aviso]:
    avisos: list[Aviso] = []
    textos = _textos(lp)
    segmento = lp.pagina.segmento
    proibidos = [(t, "termo proibido pela marca") for t in lp.marca.termos_proibidos]
    proibidos += [(t, "promessa proibida") for t in lp.marca.promessas_proibidas]
    proibidos += [(t, "proibido no segmento") for t in padrao.carregar()["vocabularios"].get(f"promessa_proibida_{segmento}", [])]
    regra_preco = padrao.carregar()["preco_padrao_por_segmento"].get(segmento, {}).get("landing", "")
    for onde, texto in textos:
        for termo, motivo in proibidos:
            if termo and padrao.contem_termo(texto, termo):
                avisos.append(Aviso("bloqueia", f"{onde}: {motivo} — \"{termo}\""))
        for frase in _frases(texto):
            if padrao.garante_resultado(frase):
                avisos.append(Aviso("bloqueia", f"{onde}: garante um resultado que não depende só da empresa (\"{frase[:60]}\"): "
                                                "mostre o que já aconteceu, com prova, ou garanta o que a empresa controla"))
            precos = _precos(frase)
            if precos and regra_preco == "nunca":
                avisos.append(Aviso("bloqueia", f"{onde}: mostra preço, mas no segmento {segmento} a página não mostra"))
            elif precos and regra_preco == "a_partir_de":
                formas = [i for i, _ in padrao.posicoes(padrao.carregar()["vocabularios"]["forma_a_partir_de"], frase)]
                if not all(any(0 <= i - j <= 4 for j in formas) for i in precos):
                    avisos.append(Aviso("atencao", f"{onde}: preço sem \"a partir de\" (no segmento {segmento} a página mostra só o "
                                                   "valor de entrada, amarrado à visita ou à simulação)"))
    genericos = {_sem_pontuacao(t) for t in padrao.carregar()["vocabularios"]["titulo_generico"]}
    for onde, titulo in [("prova_social.titulo", lp.prova_social.titulo if lp.prova_social else ""),
                         ("beneficios.titulo", lp.beneficios.titulo), ("como_funciona.titulo", lp.como_funciona.titulo),
                         ("objecoes.titulo", lp.objecoes.titulo), ("fechamento.titulo", lp.fechamento.titulo)]:
        if titulo and _sem_pontuacao(titulo) in genericos:
            avisos.append(Aviso("atencao", f"{onde}: título genérico (\"{titulo}\"); o título do bloco diz o benefício, porque "
                                           "muita gente só lê os títulos"))
    ctas = {_sem_pontuacao(t) for t in padrao.carregar()["vocabularios"]["cta_generico"]}
    for onde, botao in (("topo.cta", lp.topo.cta.texto), ("formulario.botao", lp.formulario.botao)):
        if _sem_pontuacao(botao) in ctas:
            avisos.append(Aviso("sugestao", f"{onde}: botão genérico (\"{botao}\"): diga o que a pessoa recebe ao clicar"))
    limites = padrao.carregar()["pagina"]
    if len(lp.topo.titulo) > limites["topo_titulo_maximo"]:
        avisos.append(Aviso("atencao", f"topo.titulo com {len(lp.topo.titulo)} caracteres: no celular passa de 3 linhas e "
                                       "empurra o botão para baixo"))
    if len(lp.pagina.descricao_seo) > limites["descricao_seo_maximo"]:
        avisos.append(Aviso("atencao", f"pagina.descricao_seo com {len(lp.pagina.descricao_seo)} caracteres: o Google corta "
                                       "no resultado da busca"))
    # Estrutura e rastreamento: regras da LP, não do padrão de texto.
    if not lp.topo.imagem.src:
        avisos.append(Aviso("atencao", "topo.imagem sem arquivo: a página sai com um espaço reservado"))
    if not lp.rastreio.webhook_url:
        avisos.append(Aviso("atencao", "rastreio.webhook_url vazio: modo teste, nenhum lead chega ao Kommo"))
    if not lp.rastreio.gtm_id:
        avisos.append(Aviso("atencao", "rastreio.gtm_id vazio: sem tag do Google e do Meta, o freio de emergência e a "
                                       "otimização ficam cegos"))
    if lp.formulario.qualificacao is None:
        avisos.append(Aviso("sugestao", "formulario sem pergunta de qualificação: mais volume, lead menos filtrado"))
    if lp.dor and lp.prova_social is None:
        avisos.append(Aviso("atencao", "sem bloco prova_social: a página não tem prova além do topo"))
    vistos, unicos = set(), []
    for a in avisos:
        if a.texto not in vistos:
            vistos.add(a.texto)
            unicos.append(a)
    return sorted(unicos, key=lambda a: NIVEIS.index(a.nivel))
