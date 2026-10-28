"""Testes da Etapa 1 — Subarranjo de Soma Máxima.

Executar a partir da raiz do repositório:
    python3 -m unittest discover -s testes -v
"""

import random
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "testes"))

from algoritmos.entrada import ler_vetor  # noqa: E402
from algoritmos.subarranjo_maximo import (  # noqa: E402
    ALGORITMOS, divisao_conquista, divisao_conquista_linear, forca_bruta, kadane)
from leitor_casos import ler_casos  # noqa: E402

CASOS = ler_casos("casos_etapa1.txt")
RAPIDOS = {nome: f for nome, f in ALGORITMOS.items() if nome != "forca-bruta"}


def oraculo(a):
    """Resposta por definição, independente das implementações testadas.

    Usa somas de prefixo para calcular a soma de cada intervalo e escolhe
    explicitamente a maior soma e, em empate, o menor (inicio, fim).
    """
    prefixo = [0]
    for v in a:
        prefixo.append(prefixo[-1] + v)
    candidatos = ((prefixo[j + 1] - prefixo[i], i, j)
                  for i in range(len(a)) for j in range(i, len(a)))
    soma, menos_i, menos_j = max((s, -i, -j) for s, i, j in candidatos)
    return (soma, -menos_i, -menos_j)


def executar_programa(entrada, *argumentos):
    return subprocess.run(
        [sys.executable, str(RAIZ / "etapa1.py"), *argumentos],
        input=entrada, capture_output=True, text=True, cwd=RAIZ, timeout=60)


class TestCasosDoArquivo(unittest.TestCase):
    """Cada caso de testes/casos_etapa1.txt em todas as implementações."""

    def test_arquivo_tem_casos_documentados(self):
        self.assertGreaterEqual(len(CASOS), 20)
        for caso in CASOS:
            with self.subTest(caso=caso.nome):
                self.assertTrue(caso.motivo, "todo caso deve justificar sua existência")

    def test_todas_as_implementacoes(self):
        for caso in CASOS:
            vetor = ler_vetor(caso.entrada)
            for nome, algoritmo in ALGORITMOS.items():
                with self.subTest(caso=caso.nome, algoritmo=nome):
                    soma, i, j = algoritmo(vetor)
                    self.assertEqual(f"{soma} {i + 1} {j + 1}", caso.saida)

    def test_programa_linha_de_comando(self):
        for caso in CASOS:
            with self.subTest(caso=caso.nome):
                resultado = executar_programa(caso.entrada)
                self.assertEqual(resultado.returncode, 0, resultado.stderr)
                self.assertEqual(resultado.stdout.strip(), caso.saida)

    def test_oraculo_confirma_saidas_esperadas(self):
        # Garante que as saídas escritas à mão no arquivo estão corretas.
        for caso in CASOS:
            with self.subTest(caso=caso.nome):
                soma, i, j = oraculo(ler_vetor(caso.entrada))
                self.assertEqual(f"{soma} {i + 1} {j + 1}", caso.saida)


class TestBordas(unittest.TestCase):
    """Casos de borda exigidos no enunciado, gerados em grande quantidade."""

    def setUp(self):
        self.rng = random.Random(2026)

    def test_vetor_de_tamanho_1(self):
        for v in [-10**12, -5, -1, 0, 1, 7, 10**12]:
            for nome, algoritmo in ALGORITMOS.items():
                with self.subTest(valor=v, algoritmo=nome):
                    self.assertEqual(algoritmo([v]), (v, 0, 0))

    def test_apenas_negativos(self):
        # Resposta: o maior elemento, na sua primeira ocorrência.
        for _ in range(500):
            n = self.rng.randint(1, 40)
            a = [self.rng.randint(-20, -1) for _ in range(n)]
            k = a.index(max(a))
            for nome, algoritmo in ALGORITMOS.items():
                with self.subTest(a=a, algoritmo=nome):
                    self.assertEqual(algoritmo(a), (max(a), k, k))

    def test_empates_com_valores_pequenos(self):
        # Valores em [-2, 2] geram muitos intervalos com a mesma soma.
        for _ in range(3000):
            n = self.rng.randint(1, 25)
            a = [self.rng.randint(-2, 2) for _ in range(n)]
            esperado = oraculo(a)
            for nome, algoritmo in ALGORITMOS.items():
                with self.subTest(a=a, algoritmo=nome):
                    self.assertEqual(algoritmo(a), esperado)

    def test_todos_iguais(self):
        for v in (-3, 0, 4):
            for n in (1, 2, 3, 8, 17):
                a = [v] * n
                esperado = (v * n, 0, n - 1) if v > 0 else (v, 0, 0)
                for nome, algoritmo in ALGORITMOS.items():
                    with self.subTest(v=v, n=n, algoritmo=nome):
                        self.assertEqual(algoritmo(a), esperado)

    def test_apenas_positivos_devolve_vetor_inteiro(self):
        for n in range(1, 40):
            a = [self.rng.randint(1, 9) for _ in range(n)]
            for nome, algoritmo in ALGORITMOS.items():
                with self.subTest(n=n, algoritmo=nome):
                    self.assertEqual(algoritmo(a), (sum(a), 0, n - 1))

    def test_vetor_vazio_e_rejeitado(self):
        for nome, algoritmo in ALGORITMOS.items():
            with self.subTest(algoritmo=nome):
                with self.assertRaises(ValueError):
                    algoritmo([])


class TestPropriedades(unittest.TestCase):
    """Comparação entre implementações em entradas aleatórias."""

    def setUp(self):
        self.rng = random.Random(42)

    def test_todos_os_tamanhos_de_1_a_70(self):
        # Cobre n par, ímpar e potências de 2 (formas diferentes da recursão).
        for n in range(1, 71):
            for _ in range(10):
                a = [self.rng.randint(-50, 50) for _ in range(n)]
                esperado = oraculo(a)
                for nome, algoritmo in ALGORITMOS.items():
                    with self.subTest(n=n, algoritmo=nome):
                        self.assertEqual(algoritmo(a), esperado)

    def test_soma_devolvida_corresponde_aos_indices(self):
        for _ in range(500):
            n = self.rng.randint(1, 200)
            a = [self.rng.randint(-1000, 1000) for _ in range(n)]
            for nome, algoritmo in ALGORITMOS.items():
                soma, i, j = algoritmo(a)
                with self.subTest(algoritmo=nome):
                    self.assertTrue(0 <= i <= j < n)
                    self.assertEqual(soma, sum(a[i:j + 1]))

    def test_forca_bruta_e_rapidos_concordam_em_vetores_medios(self):
        for _ in range(30):
            n = self.rng.randint(200, 600)
            a = [self.rng.randint(-100, 100) for _ in range(n)]
            esperado = forca_bruta(a)
            for nome, algoritmo in RAPIDOS.items():
                with self.subTest(n=n, algoritmo=nome):
                    self.assertEqual(algoritmo(a), esperado)

    def test_vetor_grande(self):
        # n = 2^16 + 3: recursão profunda e tamanho não potência de 2.
        a = [self.rng.randint(-10**6, 10**6) for _ in range(2**16 + 3)]
        esperado = kadane(a)
        self.assertEqual(divisao_conquista(a), esperado)
        self.assertEqual(divisao_conquista_linear(a), esperado)

    def test_entrada_nao_e_modificada(self):
        a = [self.rng.randint(-9, 9) for _ in range(50)]
        copia = list(a)
        for algoritmo in ALGORITMOS.values():
            algoritmo(a)
        self.assertEqual(a, copia)


class TestProgramaLinhaDeComando(unittest.TestCase):

    def test_todos_os_algoritmos_pelo_programa(self):
        entrada = "9\n-2 1 -3 4 -1 2 1 -5 4\n"
        for nome in ALGORITMOS:
            with self.subTest(algoritmo=nome):
                resultado = executar_programa(entrada, "--algoritmo", nome)
                self.assertEqual(resultado.stdout.strip(), "6 4 7")

    def test_indices_base_zero(self):
        resultado = executar_programa("3\n-1 5 -1\n", "--base", "0")
        self.assertEqual(resultado.stdout.strip(), "5 1 1")

    def test_entradas_invalidas(self):
        invalidas = {
            "vazia": "",
            "n_zero": "0\n",
            "n_negativo": "-3\n1 2 3\n",
            "faltam_valores": "4\n1 2 3\n",
            "valor_nao_inteiro": "3\n1 x 3\n",
            "valor_real": "2\n1.5 2\n",
            "n_nao_inteiro": "abc\n1 2\n",
        }
        for nome, entrada in invalidas.items():
            with self.subTest(caso=nome):
                resultado = executar_programa(entrada)
                self.assertEqual(resultado.returncode, 1)
                self.assertIn("erro:", resultado.stderr)
                self.assertEqual(resultado.stdout, "")


if __name__ == "__main__":
    unittest.main()
