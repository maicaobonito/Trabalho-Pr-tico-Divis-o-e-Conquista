#!/usr/bin/env python3
"""Etapa 2 — Par de pontos mais próximos.

Entrada (stdin): um inteiro n seguido de n pares "x y" (inteiros ou reais).
Saída (stdout):  "distancia i j" com i < j (índices base 1 por padrão) e a
                 distância com 6 casas decimais.

Exemplos:
    python3 etapa2.py < testes/exemplo_etapa2.txt
    python3 etapa2.py --algoritmo forca-bruta --detalhado < entrada.txt
"""

import argparse
import sys

from algoritmos.entrada import EntradaInvalida, ler_pontos
from algoritmos.par_mais_proximo import ALGORITMOS, LIMIAR_PADRAO, divisao_conquista


def main(argv=None):
    parser = argparse.ArgumentParser(description="Par de pontos mais próximos.")
    parser.add_argument("--algoritmo", choices=sorted(ALGORITMOS), default="dc",
                        help="implementação a usar (padrão: dc, divisão e conquista)")
    parser.add_argument("--limiar", type=int, default=LIMIAR_PADRAO,
                        help=f"limiar da divisão e conquista (padrão: {LIMIAR_PADRAO})")
    parser.add_argument("--base", type=int, choices=(0, 1), default=1,
                        help="base dos índices impressos (padrão: 1)")
    parser.add_argument("--detalhado", action="store_true",
                        help="imprime também as coordenadas dos dois pontos")
    args = parser.parse_args(argv)
    if args.limiar < 2:
        parser.error("o limiar deve ser pelo menos 2")

    try:
        pontos = ler_pontos(sys.stdin.read())
        if len(pontos) < 2:
            raise EntradaInvalida("são necessários ao menos dois pontos")
    except EntradaInvalida as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1

    if args.algoritmo == "dc":
        distancia, i, j = divisao_conquista(pontos, limiar=args.limiar)
    else:
        distancia, i, j = ALGORITMOS[args.algoritmo](pontos)
    print(f"{distancia:.6f} {i + args.base} {j + args.base}")
    if args.detalhado:
        print(f"ponto {i + args.base}: {pontos[i][0]} {pontos[i][1]}")
        print(f"ponto {j + args.base}: {pontos[j][0]} {pontos[j][1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
