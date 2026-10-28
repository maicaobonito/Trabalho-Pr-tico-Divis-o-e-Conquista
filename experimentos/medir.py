#!/usr/bin/env python3
"""Etapa 3 — Medição dos tempos de execução.

Gera os CSVs com as medições brutas em resultados/:

    etapa1_medicoes.csv    subarranjo máximo, n = 100 ... 6400 (e maiores
                           para as versões rápidas)
    etapa2_medicoes.csv    par mais próximo, n = 100 ... 6400 (e maiores
                           para a divisão e conquista)
    limiar_medicoes.csv    divisão e conquista da Etapa 2 variando o limiar
    pequenos_medicoes.csv  entradas pequenas (2 a 512) para achar o ponto em
                           que a divisão e conquista passa a vencer
    maquina.txt            configuração da máquina

Uso (a partir da raiz do repositório):
    python3 experimentos/medir.py                 # tudo, 10 repetições
    python3 experimentos/medir.py etapa2 limiar   # só alguns experimentos
    python3 experimentos/medir.py --rapido        # teste rápido do script

Metodologia: cada repetição usa uma entrada aleatória nova (semente
registrada no CSV) e todos os algoritmos medem a mesma entrada, em ordem
sorteada. O coletor de lixo fica desligado durante a medição. O tempo é
medido com time.perf_counter_ns e inclui todo o trabalho do algoritmo (na
Etapa 2, inclusive as ordenações iniciais), mas não a geração da entrada.
"""

import argparse
import csv
import gc
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from algoritmos import par_mais_proximo as etapa2  # noqa: E402
from algoritmos import subarranjo_maximo as etapa1  # noqa: E402

RESULTADOS = RAIZ / "resultados"

TAMANHOS = [100, 200, 400, 800, 1600, 3200, 6400]
TAMANHOS_EXTRAS = [12800, 25600, 51200, 102400, 204800]
LIMIARES = [2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 20, 24, 28, 32, 40, 48, 64, 96, 128]
TAMANHOS_LIMIAR = [6400, 50000]
TAMANHOS_PEQUENOS = [2, 3, 4, 6, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512]

ALGORITMOS_1 = {
    "forca-bruta": etapa1.forca_bruta,
    "dc": etapa1.divisao_conquista,
    "dc-linear": etapa1.divisao_conquista_linear,
    "kadane": etapa1.kadane,
}
ALGORITMOS_2 = {
    "forca-bruta": etapa2.forca_bruta,
    "dc": etapa2.divisao_conquista,
}
# Nas entradas pequenas também medimos a D&C "pura" (limiar 2) da Etapa 2.
ALGORITMOS_2_PEQUENOS = dict(ALGORITMOS_2, **{
    "dc-limiar-2": lambda pontos: etapa2.divisao_conquista(pontos, limiar=2)})


def vetor_aleatorio(n, semente):
    rng = random.Random(semente)
    return [rng.randint(-100, 100) for _ in range(n)]


def pontos_aleatorios(n, semente):
    rng = random.Random(semente)
    return [(rng.uniform(0, 1e6), rng.uniform(0, 1e6)) for _ in range(n)]


def cronometrar(funcao, entrada, chamadas=1):
    """Tempo médio por chamada, em segundos, com o coletor de lixo desligado."""
    gc_ativo = gc.isenabled()
    gc.disable()
    try:
        inicio = time.perf_counter_ns()
        for _ in range(chamadas):
            funcao(entrada)
        fim = time.perf_counter_ns()
    finally:
        if gc_ativo:
            gc.enable()
    return (fim - inicio) / chamadas / 1e9


def escrever_csv(nome, cabecalho, linhas):
    caminho = RESULTADOS / nome
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)
    print(f"  -> {caminho.relative_to(RAIZ)} ({len(linhas)} linhas)", flush=True)


def medir_tamanhos(algoritmos, gerador, tamanhos, extras, rapidos, repeticoes, semente_base):
    """Mede todos os algoritmos em ``tamanhos`` e só os ``rapidos`` em ``extras``."""
    linhas = []
    sorteio = random.Random(semente_base)
    for n in tamanhos + extras:
        nomes = list(algoritmos) if n in tamanhos else list(rapidos)
        for rep in range(repeticoes):
            semente = semente_base + 1000 * n + rep
            entrada = gerador(n, semente)
            sorteio.shuffle(nomes)
            for nome in nomes:
                t = cronometrar(algoritmos[nome], entrada)
                linhas.append([nome, n, rep + 1, semente, f"{t:.9f}"])
        print(f"  n = {n:>6}: {', '.join(sorted(nomes))}", flush=True)
    return linhas


def experimento_etapa1(repeticoes, rapido):
    print("Etapa 1 — subarranjo de soma máxima", flush=True)
    tamanhos = TAMANHOS[:3] if rapido else TAMANHOS
    extras = [] if rapido else TAMANHOS_EXTRAS
    linhas = medir_tamanhos(ALGORITMOS_1, vetor_aleatorio, tamanhos, extras,
                            ["dc", "dc-linear", "kadane"], repeticoes, 10_000)
    escrever_csv("etapa1_medicoes.csv",
                 ["algoritmo", "n", "repeticao", "semente", "tempo_s"], linhas)


def experimento_etapa2(repeticoes, rapido):
    print("Etapa 2 — par de pontos mais próximos", flush=True)
    tamanhos = TAMANHOS[:3] if rapido else TAMANHOS
    extras = [] if rapido else TAMANHOS_EXTRAS
    linhas = medir_tamanhos(ALGORITMOS_2, pontos_aleatorios, tamanhos, extras,
                            ["dc"], repeticoes, 20_000)
    escrever_csv("etapa2_medicoes.csv",
                 ["algoritmo", "n", "repeticao", "semente", "tempo_s"], linhas)


def experimento_limiar(repeticoes, rapido):
    print(f"Etapa 2 — escolha do limiar (padrão atual: {etapa2.LIMIAR_PADRAO})", flush=True)
    limiares = LIMIARES[:4] if rapido else LIMIARES
    tamanhos = [1000] if rapido else TAMANHOS_LIMIAR
    linhas = []
    sorteio = random.Random(30_000)
    for n in tamanhos:
        for rep in range(repeticoes):
            semente = 30_000 + 1000 * n + rep
            pontos = pontos_aleatorios(n, semente)
            ordem = list(limiares)
            sorteio.shuffle(ordem)
            for limiar in ordem:
                t = cronometrar(lambda p: etapa2.divisao_conquista(p, limiar=limiar), pontos)
                linhas.append([n, limiar, rep + 1, semente, f"{t:.9f}"])
        print(f"  n = {n}", flush=True)
    escrever_csv("limiar_medicoes.csv",
                 ["n", "limiar", "repeticao", "semente", "tempo_s"], linhas)


def calibrar_chamadas(funcao, entrada, alvo_s=0.02):
    """Quantas chamadas seguidas são necessárias para somar ~alvo_s segundos."""
    chamadas = 1
    while True:
        t = cronometrar(funcao, entrada, chamadas) * chamadas
        if t >= alvo_s or chamadas >= 1 << 20:
            return chamadas
        chamadas *= 2


def experimento_pequenos(repeticoes, rapido):
    print("Entradas pequenas — onde a força bruta vence", flush=True)
    tamanhos = TAMANHOS_PEQUENOS[:5] if rapido else TAMANHOS_PEQUENOS
    linhas = []
    for etapa, algoritmos, gerador in (
            (1, ALGORITMOS_1, vetor_aleatorio),
            (2, ALGORITMOS_2_PEQUENOS, pontos_aleatorios)):
        for n in tamanhos:
            for nome, funcao in algoritmos.items():
                chamadas = calibrar_chamadas(funcao, gerador(n, 1))
                for rep in range(repeticoes):
                    semente = 40_000 + 1000 * n + rep
                    t = cronometrar(funcao, gerador(n, semente), chamadas)
                    linhas.append([etapa, nome, n, rep + 1, semente, chamadas, f"{t:.12f}"])
        print(f"  etapa {etapa} concluída", flush=True)
    escrever_csv("pequenos_medicoes.csv",
                 ["etapa", "algoritmo", "n", "repeticao", "semente", "chamadas", "tempo_s"],
                 linhas)


def _comando(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def registrar_maquina():
    cpu = "desconhecido"
    for linha in _comando("lscpu").splitlines():
        if linha.startswith("Model name:"):
            cpu = linha.split(":", 1)[1].strip()
    if cpu == "desconhecido":
        cpu = platform.processor() or cpu
    memoria = "desconhecida"
    try:
        for linha in Path("/proc/meminfo").read_text().splitlines():
            if linha.startswith("MemTotal:"):
                memoria = f"{int(linha.split()[1]) / 1024 / 1024:.1f} GiB"
    except OSError:
        pass
    sistema = platform.platform()
    try:
        for linha in Path("/etc/os-release").read_text().splitlines():
            if linha.startswith("PRETTY_NAME="):
                sistema = f"{linha.split('=', 1)[1].strip(chr(34))} ({platform.platform()})"
    except OSError:
        pass
    virtualizacao = ""
    for linha in _comando("lscpu").splitlines():
        if linha.startswith("Hypervisor vendor:"):
            virtualizacao = linha.split(":", 1)[1].strip()
    texto = "\n".join([
        f"Data das medições: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}",
        f"Processador: {cpu}",
        f"Núcleos lógicos: {os.cpu_count()} (as medições usam um único núcleo)",
        f"Memória: {memoria}",
        f"Sistema: {sistema}",
        f"Virtualização: {virtualizacao or 'não detectada'}",
        f"Python: {platform.python_implementation()} {platform.python_version()}",
        "",
    ])
    (RESULTADOS / "maquina.txt").write_text(texto, encoding="utf-8")
    print(texto)


EXPERIMENTOS = {
    "etapa1": experimento_etapa1,
    "etapa2": experimento_etapa2,
    "limiar": experimento_limiar,
    "pequenos": experimento_pequenos,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("experimentos", nargs="*", choices=[[], *EXPERIMENTOS],
                        help="experimentos a executar (padrão: todos)")
    parser.add_argument("--repeticoes", type=int, default=10,
                        help="execuções por tamanho (mínimo 5; padrão 10)")
    parser.add_argument("--rapido", action="store_true",
                        help="poucos tamanhos, só para testar o script")
    args = parser.parse_args()
    if args.repeticoes < 5 and not args.rapido:
        parser.error("o enunciado pede média de pelo menos 5 execuções")

    RESULTADOS.mkdir(exist_ok=True)
    registrar_maquina()
    for nome in args.experimentos or EXPERIMENTOS:
        inicio = time.perf_counter()
        EXPERIMENTOS[nome](args.repeticoes, args.rapido)
        print(f"  ({time.perf_counter() - inicio:.0f} s)\n", flush=True)


if __name__ == "__main__":
    main()
