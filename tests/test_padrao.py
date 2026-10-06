"""A cópia dos vocabulários do padrão de texto bate com o Trilha-copy, onde mora o arquivo canônico.

A CI clona o Trilha-copy (é público) e compara lista a lista:

    PYTHONPATH=../Trilha-copy python -m unittest tests.test_padrao -v
"""

import unittest

from trilha_lp import padrao

try:
    from trilha_copy import padrao as canonico
    TEM_PADRAO = True
except ImportError:  # Trilha-copy ausente, ou anterior à 0.2.0 (sem o padrão de texto)
    TEM_PADRAO = False


@unittest.skipUnless(TEM_PADRAO, "Trilha-copy com o padrão de texto (0.2.0+) não instalado")
class TestCopiaEmDia(unittest.TestCase):
    def test_vocabularios_e_parametros_iguais(self):
        """Se falhar: copie de trilha_copy/regras/padrao.yaml para trilha_lp/regras/padrao-vocabularios.yaml."""
        c = canonico.carregar()
        nosso = padrao.carregar()
        for nome, itens in nosso["vocabularios"].items():
            self.assertEqual(itens, c.vocabularios[nome], nome)
        for chave in ("janela_garantia_palavras", "janela_preco_palavras", "preco_padrao_por_segmento", "pagina"):
            self.assertEqual(nosso[chave], c.parametros[chave], chave)

    def test_casa_igual_ao_trilha_copy(self):
        for nome, texto in [("cta_generico", "Clique aqui e envie"), ("preco_valor", "por R$ 450"),
                            ("garantia_de_resultado", "Valorização garantida"), ("forma_parcela", "em 10x de R$ 90")]:
            self.assertEqual(padrao.achar(nome, texto), canonico.achar(nome, texto), nome)


if __name__ == "__main__":
    unittest.main()
