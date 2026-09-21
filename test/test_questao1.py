import math
import random
import unittest

from config import SEED

from src.dynamic_programming import mochila
from src.greedy import dijkstra, reconstruir_caminho, selecionar_guloso
from src.logistica import construir_grafo, gerar_dados


def otimo_por_enumeracao(regioes, capacidade):
    maior_beneficio = 0
    for mascara in range(1 << len(regioes)):
        demanda = 0
        beneficio = 0
        for i, regiao in enumerate(regioes):
            if mascara & (1 << i):
                demanda += regiao["demanda"]
                beneficio += regiao["beneficio"]
        if demanda <= capacidade:
            maior_beneficio = max(maior_beneficio, beneficio)
    return maior_beneficio


class TestQuestao1(unittest.TestCase):
    def setUp(self):
        self.regioes = [
            {"id": "A", "demanda": 4, "beneficio": 7, "prioridade": 1},
            {"id": "B", "demanda": 3, "beneficio": 5, "prioridade": 1},
            {"id": "C", "demanda": 3, "beneficio": 5, "prioridade": 1},
        ]
        ids = ["CD", "A", "B", "C"]
        self.grafo = {origem: [(destino, 1) for destino in ids if destino != origem]
                      for origem in ids}

    def test_guloso_otimo(self):
        guloso = selecionar_guloso(self.regioes, self.grafo, 4)
        dp = mochila(self.regioes, 4)
        self.assertEqual(guloso["beneficio_total"], 7)
        self.assertEqual(guloso["beneficio_total"], otimo_por_enumeracao(self.regioes, 4))
        self.assertEqual(dp["beneficio_total"], 7)

    def test_contraexemplo_provado_por_enumeracao(self):
        guloso = selecionar_guloso(self.regioes, self.grafo, 6)
        dp = mochila(self.regioes, 6)
        self.assertEqual(guloso["selecionados"], ["A"])
        self.assertEqual(guloso["beneficio_total"], 7)
        self.assertEqual(set(dp["selecionados"]), {"B", "C"})
        self.assertEqual(dp["beneficio_total"], 10)
        self.assertEqual(dp["beneficio_total"], otimo_por_enumeracao(self.regioes, 6))

    def test_dp_contra_forca_bruta_em_instancias_pequenas(self):
        sorteio = random.Random(SEED)
        for numero_caso in range(40):
            regioes = [{"id": f"R{i}", "demanda": sorteio.randint(1, 8),
                        "beneficio": sorteio.randint(0, 20)}
                       for i in range(sorteio.randint(0, 8))]
            capacidade = sorteio.randint(0, 20)
            with self.subTest(caso=numero_caso):
                dp = mochila(regioes, capacidade)
                self.assertEqual(dp["beneficio_total"], otimo_por_enumeracao(regioes, capacidade))
                escolhidos = [r for r in regioes if r["id"] in dp["selecionados"]]
                self.assertEqual(dp["demanda_total"], sum(r["demanda"] for r in escolhidos))
                self.assertEqual(dp["beneficio_total"], sum(r["beneficio"] for r in escolhidos))
                self.assertLessEqual(dp["demanda_total"], capacidade)
                self.assertEqual(len(dp["selecionados"]), len(set(dp["selecionados"])))

    def test_capacidade_zero_e_lista_vazia(self):
        self.assertEqual(mochila(self.regioes, 0)["selecionados"], [])
        self.assertEqual(mochila([], 6)["beneficio_total"], 0)
        guloso = selecionar_guloso(self.regioes, self.grafo, 0)
        self.assertEqual(guloso["selecionados"], [])
        self.assertEqual(guloso["caminho_fisico"], ["CD"])
        self.assertEqual(selecionar_guloso([], self.grafo, 6)["beneficio_total"], 0)

    def test_demanda_maior_que_capacidade_e_capacidade_total(self):
        self.assertEqual(mochila(self.regioes, 2)["beneficio_total"], 0)
        self.assertEqual(mochila(self.regioes, 10)["beneficio_total"], 17)
        self.assertEqual(selecionar_guloso(self.regioes, self.grafo, 10)["beneficio_total"], 17)

    def test_dijkstra_reconstroi_menor_caminho(self):
        grafo = {"CD": [("A", 9), ("B", 2)], "A": [("CD", 9), ("B", 1)],
                 "B": [("CD", 2), ("A", 1)], "X": []}
        distancias, anteriores = dijkstra(grafo, "CD")
        self.assertEqual(distancias["A"], 3)
        self.assertEqual(reconstruir_caminho(anteriores, "CD", "A"), ["CD", "B", "A"])
        self.assertEqual(distancias["X"], math.inf)
        self.assertEqual(reconstruir_caminho(anteriores, "CD", "X"), [])
        self.assertEqual(reconstruir_caminho(anteriores, "CD", "CD"), ["CD"])

    def test_inacessivel_nao_e_escolhido(self):
        grafo = {"CD": [("A", 1)], "A": [("CD", 1)], "B": [], "C": []}
        resultado = selecionar_guloso(self.regioes, grafo, 100)
        self.assertEqual(resultado["selecionados"], ["A"])

    def test_transito_nao_e_entrega(self):
        regioes = [{"id": "A", "demanda": 1, "beneficio": 10, "prioridade": 1},
                   {"id": "B", "demanda": 4, "beneficio": 2, "prioridade": 1}]
        grafo = {"CD": [("B", 1)], "B": [("CD", 1), ("A", 1)], "A": [("B", 1)]}
        resultado = selecionar_guloso(regioes, grafo, 1)
        self.assertEqual(resultado["selecionados"], ["A"])
        self.assertEqual(resultado["caminho_fisico"], ["CD", "B", "A", "B", "CD"])
        self.assertEqual(resultado["distancia_total_km"], 4)

    def test_validacao_de_capacidade(self):
        for capacidade in (-1, 1.5, True, "6"):
            with self.subTest(capacidade=capacidade):
                with self.assertRaises(ValueError):
                    mochila(self.regioes, capacidade)
                with self.assertRaises(ValueError):
                    selecionar_guloso(self.regioes, self.grafo, capacidade)

    def test_validacao_de_regioes(self):
        for campo, valor in [("demanda", 0), ("demanda", -1), ("demanda", 1.5),
                             ("beneficio", -1), ("beneficio", math.inf), ("id", "")]:
            regioes = [dict(self.regioes[0], **{campo: valor})]
            with self.subTest(campo=campo, valor=valor):
                with self.assertRaises(ValueError):
                    mochila(regioes, 6)
        with self.assertRaises(ValueError):
            mochila([self.regioes[0], self.regioes[0]], 10)
        with self.assertRaises(ValueError):
            selecionar_guloso([dict(self.regioes[0], prioridade=0)], self.grafo, 6)

    def test_validacao_de_pesos_e_origem(self):
        for peso in (-1, math.inf, math.nan, "2", True):
            with self.subTest(peso=peso):
                with self.assertRaises(ValueError):
                    dijkstra({"CD": [("A", peso)], "A": []}, "CD")
        with self.assertRaises(ValueError):
            dijkstra(self.grafo, "inexistente")
        with self.assertRaises(ValueError):
            dijkstra({"CD": [("A", 2)]}, "CD")

    def test_dados_reproduziveis_e_bloqueios(self):
        pontos, conexoes = gerar_dados(SEED)
        self.assertEqual((pontos, conexoes), gerar_dados(SEED))
        self.assertNotEqual(pontos, gerar_dados(SEED + 1)[0])
        self.assertEqual(len(pontos), 21)
        self.assertGreaterEqual(len(conexoes), 35)
        self.assertLess(len(conexoes), 21 * 20 // 2)
        grafo = construir_grafo(pontos, conexoes)
        self.assertEqual(grafo["P20"], [])
        distancias, _ = dijkstra(grafo, "CD")
        self.assertEqual(sum(math.isfinite(d) for d in distancias.values()), 20)
        for conexao in conexoes:
            if conexao["bloqueada"]:
                self.assertNotIn((conexao["destino"], conexao["distancia_km"]),
                                 grafo[conexao["origem"]])

    def test_rota_principal_so_usa_arestas_disponiveis(self):
        pontos, conexoes = gerar_dados(SEED)
        grafo = construir_grafo(pontos, conexoes)
        regioes = [p for p in pontos if p["tipo"] == "regiao"]
        resultado = selecionar_guloso(regioes, grafo, 80)
        distancia = 0
        for origem, destino in zip(resultado["caminho_fisico"], resultado["caminho_fisico"][1:]):
            vizinhos = dict(grafo[origem])
            self.assertIn(destino, vizinhos)
            distancia += vizinhos[destino]
        self.assertAlmostEqual(distancia, resultado["distancia_total_km"])
        self.assertNotIn("P20", resultado["selecionados"])
        self.assertLessEqual(resultado["demanda_total"], 80)


if __name__ == "__main__":
    unittest.main()
