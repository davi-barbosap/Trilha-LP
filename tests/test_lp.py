import copy
import tempfile
import unittest
from pathlib import Path

import yaml
from pydantic import ValidationError

from trilha_lp.construir import construir, html
from trilha_lp.esquema import Lp, carregar
from trilha_lp.revisao import revisar

EXEMPLO = Path(__file__).parents[1] / "exemplos" / "residencial-exemplo" / "pagina.yaml"


def dados():
    return yaml.safe_load(EXEMPLO.read_text(encoding="utf-8"))


class TestEsquema(unittest.TestCase):
    def test_exemplo_valido(self):
        self.assertEqual(carregar(EXEMPLO).pagina.origem, "meta")

    def test_meta_exige_dor_e_google_exige_prova(self):
        d = dados(); d.pop("dor")
        with self.assertRaises(ValidationError):
            Lp.model_validate(d)
        d = dados(); d.pop("prova_social"); d["pagina"]["origem"] = "google"
        with self.assertRaises(ValidationError):
            Lp.model_validate(d)

    def test_beneficios_entre_4_e_8_e_ate_2_provas_no_topo(self):
        d = dados(); d["beneficios"]["itens"] = d["beneficios"]["itens"][:3]
        with self.assertRaises(ValidationError):
            Lp.model_validate(d)
        d = dados(); d["topo"]["provas"] = ["a", "b", "c"]
        with self.assertRaises(ValidationError):
            Lp.model_validate(d)

    def test_imobiliario_exige_creci_e_webhook_exige_https(self):
        d = dados(); d["marca"]["registro_profissional"] = ""
        with self.assertRaises(ValidationError):
            Lp.model_validate(d)
        d = dados(); d["rastreio"]["webhook_url"] = "http://n8n.exemplo.com/webhook/lp"
        with self.assertRaises(ValidationError):
            Lp.model_validate(d)

    def test_versao_para_outra_origem(self):
        g = carregar(EXEMPLO).para_origem("google")
        self.assertEqual((g.pagina.id, g.pagina.origem), ("residencial-exemplo-google", "google"))


class TestRevisao(unittest.TestCase):
    def textos(self, d, nivel=None):
        return " | ".join(a.texto for a in revisar(Lp.model_validate(d)) if nivel is None or a.nivel == nivel)

    def test_pega_termo_proibido_preco_solto_e_titulo_generico(self):
        d = dados()
        d["topo"]["subtitulo"] = "Oportunidade única: apartamento por R$ 540.000"
        d["prova_social"]["titulo"] = "Depoimentos"
        self.assertIn("oportunidade única", self.textos(d, "bloqueia"))
        self.assertIn("preço sem \"a partir de\"", self.textos(d, "atencao"))
        self.assertIn("título genérico", self.textos(d, "atencao"))

    def test_a_partir_de_e_aceito(self):
        avisos = revisar(carregar(EXEMPLO))
        self.assertFalse(any("preço sem" in a.texto for a in avisos))
        self.assertFalse(any(a.nivel == "bloqueia" for a in avisos))

    def test_numero_de_prova_em_reais_nao_e_preco(self):
        d = dados()
        d["topo"]["subtitulo"] = "R$ 80 milhões em obras entregues no prazo desde 2010"
        self.assertNotIn("preço sem", self.textos(d))

    def test_termo_inteiro_e_garantia_em_qualquer_segmento(self):
        d = dados()
        d["marca"]["termos_proibidos"] = ["corra"]
        d["topo"]["subtitulo"] = "Caso ocorra um atraso, avisamos na hora"
        self.assertNotIn("corra", self.textos(d))
        d["topo"]["subtitulo"] = "Valorização garantida em 2 anos"
        self.assertIn("garante um resultado", self.textos(d, "bloqueia"))

    def test_lista_do_segmento_e_botao_generico(self):
        d = dados()
        d["topo"]["subtitulo"] = "Aprovação garantida, sem consulta ao SPC"
        d["formulario"]["botao"] = "Enviar"
        self.assertIn("proibido no segmento", self.textos(d, "bloqueia"))
        self.assertIn("botão genérico", self.textos(d, "sugestao"))

    def test_validar_sai_com_erro_quando_bloqueia(self):
        import tempfile
        from trilha_lp.__main__ import main
        d = dados()
        d["topo"]["subtitulo"] = "Oportunidade única: apartamento a partir de R$ 540.000"
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "pagina.yaml"
            caminho.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")
            self.assertEqual(main(["validar", str(caminho)]), 1)
        self.assertEqual(main(["validar", str(EXEMPLO)]), 0)


class TestPagina(unittest.TestCase):
    def test_ordem_dos_blocos_depende_da_origem(self):
        lp = carregar(EXEMPLO)
        meta, google = html(lp), html(lp.para_origem("google"))
        self.assertLess(meta.index('class="dor"'), meta.index('class="prova"'))
        self.assertLess(google.index('class="prova"'), google.index('class="dor"'))

    def test_texto_escapado_e_config_sem_quebrar_script(self):
        d = dados()
        d["topo"]["titulo"] = "<script>alert(1)</script>"
        d["contato"]["mensagem_whatsapp"] = "oi </script><b>"
        pagina = html(Lp.model_validate(d))
        self.assertNotIn("<script>alert(1)", pagina)
        self.assertNotIn("oi </script>", pagina)

    def test_gtm_consentimento_e_registro_profissional(self):
        d = dados(); d["rastreio"]["gtm_id"] = "GTM-ABC1234"
        pagina = html(Lp.model_validate(d))
        self.assertIn("GTM-ABC1234", pagina)
        self.assertLess(pagina.index("gtag('consent','default'"), pagina.index("googletagmanager.com/gtm.js"))
        self.assertIn("CRECI 00000-J", pagina)

    def test_construir_gera_pagina_e_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            destino = construir(carregar(EXEMPLO), tmp)
            self.assertTrue((destino / "index.html").is_file())
            self.assertTrue((destino / "rastreio.js").is_file())


if __name__ == "__main__":
    unittest.main()
