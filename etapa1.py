#!/usr/bin/env python3
"""Etapa 1 — Subarranjo de soma máxima.

Entrada (stdin): um inteiro n seguido de n inteiros.
Saída (stdout):  "soma inicio fim" (índices base 1 por padrão).

Exemplos:
    python3 etapa1.py < testes/exemplo_etapa1.txt
    python3 etapa1.py --algoritmo forca-bruta --base 0 < entrada.txt
"""

import argparse
import sys

from algoritmos.entrada import EntradaInvalida, ler_vetor
from algoritmos.subarranjo_maximo import ALGORITMOS


def main(argv=None):
    parser = argparse.ArgumentParser(description="Subarranjo de soma máxima.")
    parser.add_argument("--algoritmo", choices=sorted(ALGORITMOS), default="dc",
                        help="implementação a usar (padrão: dc, divisão e conquista)")
    parser.add_argument("--base", type=int, choices=(0, 1), default=1,
                        help="base dos índices impressos (padrão: 1)")
    args = parser.parse_args(argv)

    try:
        vetor = ler_vetor(sys.stdin.read())
        if not vetor:
            raise EntradaInvalida("n deve ser pelo menos 1")
    except EntradaInvalida as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1

    soma, inicio, fim = ALGORITMOS[args.algoritmo](vetor)
    print(soma, inicio + args.base, fim + args.base)
    return 0


if __name__ == "__main__":
    sys.exit(main())
