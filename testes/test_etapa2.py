"""Testes da Etapa 2 — Par de Pontos Mais Próximos.

Executar a partir da raiz do repositório:
    python3 -m unittest discover -s testes -v
"""

import math
import random
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "testes"))

from algoritmos.entrada import ler_pontos  # noqa: E402
from algoritmos.par_mais_proximo import (  # noqa: E402
    LIMIAR_PADRAO, VIZINHOS_NA_FAIXA, divisao_conquista, forca_bruta)
from leitor_casos import ler_casos  # noqa: E402

CASOS = ler_casos("casos_etapa2.txt")
LIMIARES = sorted({2, 3, 4, LIMIAR_PADRAO})


def formatar(resultado):
    distancia, i, j = resultado
    return f"{distancia:.6f} {i + 1} {j + 1}"


def oraculo(pontos):
    """Resposta por definição: menor (distância², i, j) entre todos os pares."""
    def d2(p, q):
        return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2
    n = len(pontos)
    melhor = min((d2(pontos[i], pontos[j]), i, j)
                 for i in range(n) for j in range(i + 1, n))
    return (math.sqrt(melhor[0]), melhor[1], melhor[2])


def executar_programa(entrada, *argumentos):
    return subprocess.run(
        [sys.executable, str(RAIZ / "etapa2.py"), *argumentos],
        input=entrada, capture_output=True, text=True, cwd=RAIZ, timeout=60)


def todas_as_versoes(pontos):
    """Resultados de todas as variações testadas, rotulados."""
    yield "forca-bruta", forca_bruta(pontos)
    for limiar in LIMIARES:
        yield f"dc(limiar={limiar})", divisao_conquista(pontos, limiar=limiar)
        yield (f"dc(limiar={limiar}, sem limite de vizinhos)",
               divisao_conquista(pontos, limiar=limiar, vizinhos=None))


class TestCasosDoArquivo(unittest.TestCase):
    """Cada caso de testes/casos_etapa2.txt em todas as versões."""

    def test_arquivo_tem_casos_documentados(self):
        self.assertGreaterEqual(len(CASOS), 20)
        for caso in CASOS:
            with self.subTest(caso=caso.nome):
                self.assertTrue(caso.motivo, "todo caso deve justificar sua existência")

    def test_todas_as_versoes(self):
        for caso in CASOS:
            pontos = ler_pontos(caso.entrada)
            for nome, resultado in todas_as_versoes(pontos):
                with self.subTest(caso=caso.nome, versao=nome):
                    self.assertEqual(formatar(resultado), caso.saida)

    def test_programa_linha_de_comando(self):
        for caso in CASOS:
            for algoritmo in ("dc", "forca-bruta"):
                with self.subTest(caso=caso.nome, algoritmo=algoritmo):
                    resultado = executar_programa(caso.entrada, "--algoritmo", algoritmo)
                    self.assertEqual(resultado.returncode, 0, resultado.stderr)
                    self.assertEqual(resultado.stdout.strip(), caso.saida)

    def test_oraculo_confirma_saidas_esperadas(self):
        for caso in CASOS:
            with self.subTest(caso=caso.nome):
                self.assertEqual(formatar(oraculo(ler_pontos(caso.entrada))), caso.saida)


class TestBordas(unittest.TestCase):

    def setUp(self):
        self.rng = random.Random(2026)

    def test_dois_pontos(self):
        for _ in range(200):
            p = (self.rng.randint(-50, 50), self.rng.randint(-50, 50))
            q = (self.rng.randint(-50, 50), self.rng.randint(-50, 50))
            esperado = (math.dist(p, q), 0, 1)
            for nome, resultado in todas_as_versoes([p, q]):
                with self.subTest(p=p, q=q, versao=nome):
                    self.assertEqual(resultado, esperado)

    def test_pontos_coincidentes(self):
        # Vários pontos repetidos: distância 0 e menor (i, j) entre os repetidos.
        for _ in range(500):
            n = self.rng.randint(2, 30)
            pontos = [(self.rng.randint(0, 3), self.rng.randint(0, 3)) for _ in range(n)]
            esperado = oraculo(pontos)
            for nome, resultado in todas_as_versoes(pontos):
                with self.subTest(pontos=pontos, versao=nome):
                    self.assertEqual(resultado, esperado)

    def test_todos_os_pontos_iguais(self):
        for n in (2, 3, 10, 50):
            for nome, resultado in todas_as_versoes([(5, -5)] * n):
                with self.subTest(n=n, versao=nome):
                    self.assertEqual(resultado, (0.0, 0, 1))

    def test_mesmo_x_e_mesmo_y(self):
        # Retas verticais/horizontais: a mediana de x não separa os pontos.
        for _ in range(200):
            n = self.rng.randint(2, 60)
            valores = self.rng.sample(range(-1000, 1000), n)
            for pontos in ([(7, v) for v in valores], [(v, 7) for v in valores]):
                esperado = oraculo(pontos)
                for nome, resultado in todas_as_versoes(pontos):
                    with self.subTest(versao=nome):
                        self.assertEqual(resultado, esperado)

    def test_grades_com_muitos_empates(self):
        # Grade k x k embaralhada: muitos pares a distância 1 e faixa densa.
        for k in range(2, 16):
            pontos = [(x, y) for x in range(k) for y in range(k)]
            self.rng.shuffle(pontos)
            esperado = oraculo(pontos)
            for nome, resultado in todas_as_versoes(pontos):
                with self.subTest(k=k, versao=nome):
                    self.assertEqual(resultado, esperado)

    def test_menos_de_dois_pontos_e_rejeitado(self):
        for pontos in ([], [(1, 2)]):
            with self.assertRaises(ValueError):
                forca_bruta(pontos)
            with self.assertRaises(ValueError):
                divisao_conquista(pontos)

    def test_limiar_invalido_e_rejeitado(self):
        with self.assertRaises(ValueError):
            divisao_conquista([(0, 0), (1, 1), (2, 2)], limiar=1)


class TestFaixaSeteVizinhos(unittest.TestCase):
    """Verificação empírica do argumento dos 7 vizinhos na faixa."""

    def configuracoes(self):
        rng = random.Random(7)
        for _ in range(300):
            n = rng.randint(2, 300)
            yield [(rng.uniform(0, 1000), rng.uniform(0, 1000)) for _ in range(n)]
        for k in range(2, 25):
            grade = [(x, y) for x in range(k) for y in range(k)]
            rng.shuffle(grade)
            yield grade
        for k in range(2, 60):
            # Duas colunas de pontos encostadas na linha divisória.
            yield [(x, y) for x in (0, 1) for y in range(k)]
        for n in (8, 16, 64, 256):
            # Pontos equidistantes num círculo (todos os pares vizinhos empatam).
            yield [(round(1000 * math.cos(2 * math.pi * t / n), 9),
                    round(1000 * math.sin(2 * math.pi * t / n), 9)) for t in range(n)]
        for n in (2, 9, 40, 100):
            # Pontos repetidos (δ = 0): o limite só vale porque eles são
            # tratados antes da recursão.
            yield [(3, 3)] * n
            yield [(rng.randint(0, 2), rng.randint(0, 2)) for _ in range(n)]

    def test_nunca_ha_mais_de_7_sucessores_a_distancia_vertical_delta(self):
        maior = 0
        for pontos in self.configuracoes():
            for limiar in (2, 3, LIMIAR_PADRAO):
                est = {}
                sem_limite = divisao_conquista(pontos, limiar=limiar, vizinhos=None,
                                               estatisticas=est)
                maior = max(maior, est["max_sucessores"])
                self.assertLessEqual(est["max_sucessores"], VIZINHOS_NA_FAIXA)
                self.assertEqual(divisao_conquista(pontos, limiar=limiar), sem_limite)
        self.assertGreater(maior, 0)

    def test_limitar_a_um_vizinho_perde_respostas(self):
        # Controle negativo: com 1 vizinho a resposta fica errada em algum
        # caso, mostrando que o teste acima é capaz de detectar o limite.
        erros = 0
        rng = random.Random(11)
        for _ in range(300):
            pontos = [(rng.randint(0, 40), rng.randint(0, 40)) for _ in range(40)]
            if divisao_conquista(pontos, limiar=2, vizinhos=1) != forca_bruta(pontos):
                erros += 1
        self.assertGreater(erros, 0)


class TestPropriedades(unittest.TestCase):

    def setUp(self):
        self.rng = random.Random(42)

    def test_aleatorio_inteiros_pequenos(self):
        # Coordenadas num intervalo pequeno forçam empates e repetições.
        for _ in range(1500):
            n = self.rng.randint(2, 40)
            r = self.rng.choice((2, 5, 20, 1000))
            pontos = [(self.rng.randint(-r, r), self.rng.randint(-r, r)) for _ in range(n)]
            esperado = oraculo(pontos)
            for nome, resultado in todas_as_versoes(pontos):
                with self.subTest(pontos=pontos, versao=nome):
                    self.assertEqual(resultado, esperado)

    def test_aleatorio_reais(self):
        for _ in range(500):
            n = self.rng.randint(2, 80)
            pontos = [(self.rng.uniform(-1, 1), self.rng.uniform(-1, 1)) for _ in range(n)]
            esperado = forca_bruta(pontos)
            for nome, resultado in todas_as_versoes(pontos):
                with self.subTest(versao=nome):
                    self.assertEqual(resultado, esperado)

    def test_par_devolvido_e_valido(self):
        for _ in range(300):
            n = self.rng.randint(2, 200)
            pontos = [(self.rng.randint(-10**6, 10**6), self.rng.randint(-10**6, 10**6))
                      for _ in range(n)]
            distancia, i, j = divisao_conquista(pontos)
            self.assertTrue(0 <= i < j < n)
            self.assertAlmostEqual(distancia, math.dist(pontos[i], pontos[j]))

    def test_distancia_invariante_a_permutacao_e_translacao(self):
        for _ in range(200):
            n = self.rng.randint(2, 100)
            pontos = [(self.rng.randint(-500, 500), self.rng.randint(-500, 500))
                      for _ in range(n)]
            base = divisao_conquista(pontos)[0]
            embaralhados = list(pontos)
            self.rng.shuffle(embaralhados)
            dx, dy = self.rng.randint(-10**6, 10**6), self.rng.randint(-10**6, 10**6)
            transladados = [(x + dx, y + dy) for x, y in pontos]
            self.assertEqual(divisao_conquista(embaralhados)[0], base)
            self.assertEqual(divisao_conquista(transladados)[0], base)

    def test_entradas_medias_contra_forca_bruta(self):
        for n in (500, 1000, 2000):
            pontos = [(self.rng.uniform(0, 10**4), self.rng.uniform(0, 10**4))
                      for _ in range(n)]
            esperado = forca_bruta(pontos)
            for limiar in LIMIARES:
                with self.subTest(n=n, limiar=limiar):
                    self.assertEqual(divisao_conquista(pontos, limiar=limiar), esperado)

    def test_entrada_nao_e_modificada(self):
        pontos = [(self.rng.randint(0, 9), self.rng.randint(0, 9)) for _ in range(30)]
        copia = list(pontos)
        forca_bruta(pontos)
        divisao_conquista(pontos)
        self.assertEqual(pontos, copia)


class TestProgramaLinhaDeComando(unittest.TestCase):

    def test_saida_detalhada(self):
        resultado = executar_programa("3\n0 0\n10 10\n1 1\n", "--detalhado")
        self.assertEqual(resultado.stdout.splitlines(),
                         ["1.414214 1 3", "ponto 1: 0 0", "ponto 3: 1 1"])

    def test_indices_base_zero_e_limiar(self):
        resultado = executar_programa("3\n0 0\n10 10\n1 1\n", "--base", "0", "--limiar", "2")
        self.assertEqual(resultado.stdout.strip(), "1.414214 0 2")

    def test_entradas_invalidas(self):
        invalidas = {
            "vazia": "",
            "n_zero": "0\n",
            "um_ponto": "1\n3 4\n",
            "falta_coordenada": "2\n0 0\n1\n",
            "coordenada_nao_numerica": "2\n0 0\n1 y\n",
        }
        for nome, entrada in invalidas.items():
            with self.subTest(caso=nome):
                resultado = executar_programa(entrada)
                self.assertEqual(resultado.returncode, 1)
                self.assertIn("erro:", resultado.stderr)
                self.assertEqual(resultado.stdout, "")


if __name__ == "__main__":
    unittest.main()
