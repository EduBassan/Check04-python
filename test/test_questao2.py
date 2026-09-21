import copy
import random
import tempfile
from pathlib import Path
import unittest

from config import SEED

from src.brute_force import forca_bruta
from src.divide_conquer import dividir_conquistar
from src.energia import gerar_registros, ler_dados, salvar_dados
from src.estruturas import organizar_registros, consultar_picos, selecionar_intervalo


def oraculo(valores):
    possibilidades = []
    for inicio in range(len(valores)):
        for fim in range(inicio, len(valores)):
            possibilidades.append((sum(valores[inicio:fim + 1]), inicio, fim))
    return sorted(possibilidades, key=lambda item: (-item[0], item[1], item[2]))[0]


class TesteIntervaloCritico(unittest.TestCase):
    def verificar(self, valores, esperado=None):
        if esperado is None:
            esperado = oraculo(valores)
        for algoritmo in (forca_bruta, dividir_conquistar):
            with self.subTest(algoritmo=algoritmo.__name__, valores=valores):
                resultado = algoritmo(valores)
                self.assertEqual((resultado["soma"], resultado["inicio"], resultado["fim"]), esperado)

    def test_exemplo_classico(self):
        self.verificar([-2, 1, -3, 4, -1, 2, 1, -5, 4], (6, 3, 6))

    def test_todos_negativos(self):
        self.verificar([-8, -3, -6, -3], (-3, 1, 1))

    def test_todos_zeros(self):
        self.verificar([0, 0, 0, 0], (0, 0, 0))

    def test_empates_de_inicio_e_fim(self):
        self.verificar([1, -1, 1], (1, 0, 0))
        self.verificar([0, 2, 0], (2, 0, 1))

    def test_um_elemento(self):
        for valor in (-10, 0, 10):
            self.verificar([valor], (valor, 0, 0))

    def test_intervalo_cruza_o_meio(self):
        self.verificar([-20, 4, 6, 8, -20], (18, 1, 3))

    def test_aleatorios_contra_oraculo_independente(self):
        rng = random.Random(123)
        for tamanho in range(1, 13):
            for _ in range(30):
                self.verificar([rng.randint(-8, 8) for _ in range(tamanho)])

    def test_contagem_de_somas(self):
        for n in (1, 2, 3, 7, 8, 15, 16, 100):
            self.assertEqual(forca_bruta([1] * n)["operacoes"], n * (n + 1) // 2)
            h = (n - 1).bit_length()
            self.assertEqual(dividir_conquistar([1] * n)["operacoes"], n * (h + 1) - 2 ** h)

    def test_entrada_invalida(self):
        for valores in ([], None, "123", [1, 2.5], [True], [float("nan")], [float("inf")]):
            for algoritmo in (forca_bruta, dividir_conquistar):
                with self.subTest(valores=valores, algoritmo=algoritmo.__name__):
                    with self.assertRaises(ValueError):
                        algoritmo(valores)


class TesteDadosEnergia(unittest.TestCase):
    def setUp(self):
        self.registros = gerar_registros(SEED, horas=3)

    def test_seed_reproduz_os_dados(self):
        self.assertEqual(self.registros, gerar_registros(SEED, horas=3))
        self.assertNotEqual(self.registros, gerar_registros(SEED + 1, horas=3))

    def test_arquivo_csv_preserva_registros(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "dados.csv"
            salvar_dados(self.registros, caminho)
            self.assertEqual(ler_dados(caminho), self.registros)

    def test_agrega_mesma_hora_sem_concatenar_regioes(self):
        estruturas = organizar_registros(list(reversed(self.registros)))
        self.assertEqual(len(estruturas["horarios"]), 3)
        self.assertEqual(len(estruturas["por_horario"]["2026-01-01T00:00"]), 4)
        esperado = sum((r["consumo"] - r["capacidade_disponivel"]) * r["prioridade"] * r["custo"]
                       for r in self.registros[:4])
        self.assertEqual(estruturas["criticidades"][0], esperado)

    def test_recusa_duplicatas(self):
        with self.assertRaises(ValueError):
            organizar_registros(self.registros + [self.registros[0]])

    def test_recusa_hora_ausente(self):
        with self.assertRaises(ValueError):
            organizar_registros(self.registros[:4] + self.registros[8:])

    def test_recusa_regiao_ausente_em_uma_hora(self):
        with self.assertRaises(ValueError):
            organizar_registros(self.registros[1:])

    def test_recusa_registro_invalido(self):
        for campo, valor in (("consumo", -1), ("prioridade", 0), ("custo", 0),
                             ("timestamp", "data"), ("regiao", ""), ("capacidade_disponivel", True)):
            invalido = copy.deepcopy(self.registros)
            invalido[0][campo] = valor
            with self.subTest(campo=campo):
                with self.assertRaises(ValueError):
                    organizar_registros(invalido)

    def test_picos_e_selecao_intervalo(self):
        estruturas = organizar_registros(self.registros)
        picos = consultar_picos(estruturas, 2)
        self.assertEqual([p["consumo"] for p in picos], sorted(estruturas["consumos"], reverse=True)[:2])
        self.assertEqual(len(estruturas["picos"]), 3)
        intervalo = selecionar_intervalo(estruturas, 1, 2)
        self.assertEqual(len(intervalo), 2)
        self.assertEqual(intervalo[0][0], "2026-01-01T01:00")
        with self.assertRaises(ValueError):
            selecionar_intervalo(estruturas, 2, 1)


if __name__ == "__main__":
    unittest.main()
