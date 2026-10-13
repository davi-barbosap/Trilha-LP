"""CLI: validar · construir."""

from __future__ import annotations

import argparse
import sys

import yaml
from pydantic import ValidationError

from trilha_lp.construir import construir
from trilha_lp.esquema import carregar
from trilha_lp.revisao import revisar


def _carregar(caminho: str):
    try:
        return carregar(caminho)
    except ValidationError as e:
        print(f"ERRO — {caminho} não passou no esquema:", file=sys.stderr)
        for erro in e.errors(include_url=False):
            onde = ".".join(str(p) for p in erro["loc"]) or "(raiz)"
            print(f"  {onde}: {erro['msg']}", file=sys.stderr)
        return None
    except (OSError, yaml.YAMLError) as e:
        print(f"ERRO — {caminho}: {e}", file=sys.stderr)
        return None


ROTULO = {"bloqueia": "Bloqueia", "atencao": "Atenção", "sugestao": "Sugestão"}


def _avisos(lp) -> bool:
    """Mostra os avisos por gravidade; True se algum bloqueia."""
    avisos = revisar(lp)
    for aviso in avisos:
        print(f"{ROTULO[aviso.nivel]}: {aviso.texto}")
    if not avisos:
        print("Revisão: nenhum aviso")
    bloqueia = any(a.nivel == "bloqueia" for a in avisos)
    if bloqueia:
        print("✗ há aviso que bloqueia: a página não vai ao ar assim", file=sys.stderr)
    return bloqueia


def cmd_validar(args) -> int:
    lp = _carregar(args.pagina)
    if lp is None:
        return 1
    print(f"OK — '{lp.pagina.id}' ({lp.marca.nome}, origem {lp.pagina.origem})")
    return 1 if _avisos(lp) else 0


def cmd_construir(args) -> int:
    lp = _carregar(args.pagina)
    if lp is None:
        return 1
    origens = [args.origem] if args.origem else [lp.pagina.origem]
    if args.todas:
        origens = ["meta", "google"]
    for origem in origens:
        try:
            versao = lp if origem == lp.pagina.origem else lp.para_origem(origem)
        except ValidationError as e:
            print(f"ERRO — versão {origem}: {e.errors(include_url=False)[0]['msg']}", file=sys.stderr)
            return 1
        destino = construir(versao, args.saida)
        print(f"Página '{versao.pagina.id}' gerada em {destino}/index.html")
    return 1 if _avisos(lp) else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m trilha_lp")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("validar", help="confere o pagina.yaml e revisa o texto")
    s.add_argument("pagina")
    s.set_defaults(func=cmd_validar)
    s = sub.add_parser("construir", help="gera a página estática")
    s.add_argument("pagina")
    s.add_argument("--saida", default="dist")
    s.add_argument("--origem", choices=["meta", "google"], help="gera a versão para outra origem de tráfego")
    s.add_argument("--todas", action="store_true", help="gera as versões Meta e Google")
    s.set_defaults(func=cmd_construir)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
