"""Esquema validado de `pagina.yaml`: o esqueleto da landing page da Trilha.

A ordem dos blocos é fixa e cada bloco tem uma função. O que muda por página é o texto,
a marca e a origem do tráfego (Meta abre com a dor; Google abre com a prova social).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Origem = Literal["meta", "google"]
Cor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Imagem(_Base):
    src: str = ""  # vazio = espaço reservado até a foto real chegar
    alt: str
    largura: int = 1200
    altura: int = 900


class Cores(_Base):
    primaria: Cor
    secundaria: Cor
    fundo: Cor = "#FFFFFF"
    texto: Cor = "#1A1A1A"


class Fontes(_Base):
    titulos: str = "Montserrat"
    texto: str = "Inter"


class Marca(_Base):
    nome: str
    cores: Cores
    fontes: Fontes = Field(default_factory=Fontes)
    logo: str = ""
    registro_profissional: str = ""  # CRECI, CRM, CRO… obrigatório onde a profissão exige
    avisos_legais: list[str] = Field(default_factory=list)
    politica_privacidade_url: str
    termos_proibidos: list[str] = Field(default_factory=list)
    promessas_proibidas: list[str] = Field(default_factory=list)


class Rastreio(_Base):
    gtm_id: str = ""  # GTM-XXXXXXX; tags do Google e do Meta ficam no GTM
    webhook_url: str = ""  # vazio = modo teste (nenhum lead é enviado)
    pagina_obrigado: str = ""  # URL para redirecionar depois do envio confirmado

    @field_validator("gtm_id")
    @classmethod
    def _gtm(cls, v: str) -> str:
        if v and not re.fullmatch(r"GTM-[A-Z0-9]+", v):
            raise ValueError("gtm_id no formato GTM-XXXXXXX")
        return v

    @field_validator("webhook_url", "pagina_obrigado")
    @classmethod
    def _https(cls, v: str) -> str:
        if v and not v.startswith("https://"):
            raise ValueError("precisa começar com https://")
        return v


class Contato(_Base):
    whatsapp: Annotated[str, Field(pattern=r"^55\d{10,11}$")]  # 55 + DDD + número, só dígitos
    mensagem_whatsapp: str


class Cta(_Base):
    texto: str
    acao: Literal["whatsapp", "formulario"] = "formulario"


class Topo(_Base):
    titulo: str  # resultado + prazo (se houver) + ganho emocional
    subtitulo: str  # dor + como a oferta resolve (3 a 4 benefícios)
    provas: Annotated[list[str], Field(min_length=1, max_length=2)]
    cta: Cta
    reducao_medo: list[str] = Field(default_factory=list, max_length=3)
    imagem: Imagem


class Dor(_Base):
    """Segundo bloco no tráfego frio (Meta): problema → agravamento → solução."""

    titulo: str
    problema: str
    agravamento: str
    solucao: str


class Numero(_Base):
    numero: str
    texto: str


class Depoimento(_Base):
    texto: str
    autor: str


class ProvaSocial(_Base):
    """Segundo bloco no tráfego com intenção (Google). O título diz o benefício, não "depoimentos"."""

    titulo: str
    numeros: list[Numero] = Field(default_factory=list)
    depoimentos: list[Depoimento] = Field(default_factory=list)

    @model_validator(mode="after")
    def _algo(self) -> ProvaSocial:
        if not self.numeros and not self.depoimentos:
            raise ValueError("prova social precisa de números ou depoimentos")
        return self


class Beneficio(_Base):
    titulo: str  # benefício + característica; precisa se sustentar sozinho
    texto: str
    imagem: Imagem | None = None


class Beneficios(_Base):
    titulo: str
    itens: Annotated[list[Beneficio], Field(min_length=4, max_length=8)]


class Passo(_Base):
    titulo: str
    texto: str


class ComoFunciona(_Base):
    titulo: str
    passos: Annotated[list[Passo], Field(min_length=3, max_length=5)]


class Pergunta(_Base):
    pergunta: str
    resposta: str


class Objecoes(_Base):
    titulo: str = "Perguntas frequentes"
    itens: Annotated[list[Pergunta], Field(min_length=3)]
    garantias: list[str] = Field(default_factory=list)


class Fechamento(_Base):
    titulo: str
    subtitulo: str
    lista: Annotated[list[str], Field(min_length=3, max_length=4)]
    provas: list[str] = Field(default_factory=list, max_length=2)


class Qualificacao(_Base):
    """Uma pergunta que qualifica: perde um pouco de volume, ganha muito em qualidade."""

    rotulo: str
    opcoes: Annotated[list[str], Field(min_length=2)]


class Formulario(_Base):
    pedir_email: bool = False
    qualificacao: Qualificacao | None = None
    botao: str
    consentimento: str
    confirmacao: str


class Pagina(_Base):
    id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")]
    cliente: str
    oferta: str
    segmento: str
    origem: Origem
    titulo_seo: str
    descricao_seo: str


class Lp(_Base):
    pagina: Pagina
    marca: Marca
    rastreio: Rastreio = Field(default_factory=Rastreio)
    contato: Contato
    topo: Topo
    dor: Dor | None = None
    prova_social: ProvaSocial | None = None
    beneficios: Beneficios
    como_funciona: ComoFunciona
    objecoes: Objecoes
    fechamento: Fechamento
    formulario: Formulario

    @model_validator(mode="after")
    def _segundo_bloco(self) -> Lp:
        if self.pagina.origem == "meta" and self.dor is None:
            raise ValueError("origem meta (tráfego frio) exige o bloco dor")
        if self.pagina.origem == "google" and self.prova_social is None:
            raise ValueError("origem google (tráfego com intenção) exige o bloco prova_social")
        if self.pagina.segmento == "imobiliario" and not self.marca.registro_profissional:
            raise ValueError("segmento imobiliario exige marca.registro_profissional (CRECI)")
        return self

    def para_origem(self, origem: Origem) -> Lp:
        """A mesma página para outra origem de tráfego (o id ganha o sufixo da origem)."""
        dados = self.model_dump()
        base = re.sub(r"-(meta|google)$", "", self.pagina.id)
        dados["pagina"].update(origem=origem, id=f"{base}-{origem}")
        return Lp.model_validate(dados)


def carregar(caminho: str | Path) -> Lp:
    with open(caminho, encoding="utf-8") as f:
        return Lp.model_validate(yaml.safe_load(f))
