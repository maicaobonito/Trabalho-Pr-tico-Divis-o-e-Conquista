#!/usr/bin/env python3
"""Etapa 3 — Análise das medições: resumos, ajustes, gráficos e tabelas.

Lê os CSVs brutos de resultados/ (gerados por experimentos/medir.py) e
produz:

    resultados/resumo_*.csv        média, mediana, desvio, mínimo por ponto
    resultados/figuras/*.svg|png   gráficos usados no relatório e no README
    relatorio/gerado/*.md          tabelas em Markdown para o relatório
    relatorio/gerado/numeros.json  números citados no texto do relatório

Uso (a partir da raiz do repositório):
    python3 experimentos/analisar.py
"""

import csv
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from algoritmos import par_mais_proximo as etapa2  # noqa: E402

RESULTADOS = RAIZ / "resultados"
FIGURAS = RESULTADOS / "figuras"
GERADO = RAIZ / "relatorio" / "gerado"

TAMANHOS = [100, 200, 400, 800, 1600, 3200, 6400]

# Paleta categórica (ordem fixa) e tinta de texto; marcadores distintos dão
# uma segunda codificação além da cor.
COR = {
    "forca-bruta": "#2a78d6",
    "dc": "#eb6834",
    "dc-linear": "#1baf7a",
    "kadane": "#eda100",
    "dc-limiar-2": "#1baf7a",
}
MARCADOR = {"forca-bruta": "o", "dc": "s", "dc-linear": "^", "kadane": "D",
            "dc-limiar-2": "^"}
ROTULO = {
    "forca-bruta": "Força bruta",
    "dc": "Divisão e conquista",
    "dc-linear": "D&C linear",
    "kadane": "Kadane",
    "dc-limiar-2": "D&C sem limiar (limiar 2)",
}
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
GRADE = "#e4e3df"

plt.rcParams.update({
    "font.size": 9,
    "axes.edgecolor": TINTA_2,
    "axes.labelcolor": TINTA,
    "axes.titlesize": 10,
    "axes.titleweight": "bold",
    "axes.titlecolor": TINTA,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRADE,
    "grid.linewidth": 0.6,
    "xtick.color": TINTA_2,
    "ytick.color": TINTA_2,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "lines.linewidth": 2,
    "lines.markersize": 5,
    "svg.fonttype": "none",
    "figure.dpi": 150,
})


# ---------------------------------------------------------------------------
# Leitura e resumo
# ---------------------------------------------------------------------------

def ler_csv(nome):
    with (RESULTADOS / nome).open(encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def resumir(linhas, chaves):
    """Agrupa por ``chaves`` e calcula estatísticas de ``tempo_s``."""
    grupos = defaultdict(list)
    for linha in linhas:
        grupos[tuple(linha[c] for c in chaves)].append(float(linha["tempo_s"]))
    resumo = {}
    for chave, tempos in grupos.items():
        resumo[chave] = {
            "media": statistics.mean(tempos),
            "mediana": statistics.median(tempos),
            "desvio": statistics.stdev(tempos) if len(tempos) > 1 else 0.0,
            "minimo": min(tempos),
            "repeticoes": len(tempos),
        }
    return resumo


def escrever_resumo(nome, chaves, resumo):
    with (RESULTADOS / nome).open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow([*chaves, "repeticoes", "media_s", "mediana_s", "desvio_s", "minimo_s"])
        for chave in sorted(resumo, key=lambda c: tuple(_ordem(v) for v in c)):
            r = resumo[chave]
            escritor.writerow([*chave, r["repeticoes"], f"{r['media']:.9f}",
                               f"{r['mediana']:.9f}", f"{r['desvio']:.9f}", f"{r['minimo']:.9f}"])


def _ordem(valor):
    try:
        return (0, float(valor), "")
    except ValueError:
        return (1, 0.0, valor)


def serie(resumo, algoritmo, estatistica="media"):
    """{n: valor} de um algoritmo num resumo com chaves (algoritmo, n)."""
    return {int(n): r[estatistica] for (alg, n), r in resumo.items() if alg == algoritmo}


# ---------------------------------------------------------------------------
# Ajustes
# ---------------------------------------------------------------------------

MODELOS = {
    "n²": lambda n: n * n,
    "n log n": lambda n: n * math.log2(n),
    "n": lambda n: n,
}


def inclinacao_loglog(pontos):
    """Inclinação da reta de mínimos quadrados em log T × log n."""
    xs = [math.log(n) for n in pontos]
    ys = [math.log(t) for t in pontos.values()]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    return (sum((x - mx) * (y - my) for x, y in zip(xs, ys))
            / sum((x - mx) ** 2 for x in xs))


def constante(pontos, modelo):
    """Constante c do modelo T(n) = c·f(n), por mínimos quadrados relativos.

    Minimiza o erro relativo (T - c f)/T, adequado para dados que variam
    várias ordens de grandeza: c = Σ(f/T) / Σ(f/T)².
    """
    f = MODELOS[modelo]
    razoes = [f(n) / t for n, t in pontos.items()]
    return sum(razoes) / sum(r * r for r in razoes)


def erro_relativo_maximo(pontos, modelo):
    c = constante(pontos, modelo)
    return max(abs(t - c * MODELOS[modelo](n)) / t for n, t in pontos.items())


def razoes_duplicacao(pontos):
    ns = sorted(pontos)
    return {n: pontos[n] / pontos[n // 2] for n in ns if n // 2 in pontos}


def cruzamento(bruta, dc):
    """Menor n medido a partir do qual a D&C é sempre mais rápida."""
    ns = sorted(set(bruta) & set(dc))
    resposta = None
    for n in reversed(ns):
        if dc[n] < bruta[n]:
            resposta = n
        else:
            break
    return resposta


# ---------------------------------------------------------------------------
# Modelo de custo do limiar
# ---------------------------------------------------------------------------

def contagens_recursao(n, limiar):
    """(pares nas folhas, pontos processados em nós internos, nº de folhas).

    Simula exatamente a forma da recursão de par_mais_proximo: um nó com
    m <= limiar pontos é folha e custa m(m-1)/2 comparações; um nó interno
    divide em m//2 e m - m//2 e faz trabalho linear em m (separar py, montar
    e percorrer a faixa).
    """
    pares = internos = folhas = 0
    pilha = [n]
    while pilha:
        m = pilha.pop()
        if m <= limiar:
            pares += m * (m - 1) // 2
            folhas += 1
        else:
            internos += m
            pilha.extend((m // 2, m - m // 2))
    return pares, internos, folhas


def minimos_quadrados(linhas_x, ys):
    """Resolve min ||X b - y|| pelas equações normais (poucas variáveis)."""
    k = len(linhas_x[0])
    ata = [[sum(x[i] * x[j] for x in linhas_x) for j in range(k)] for i in range(k)]
    aty = [sum(x[i] * y for x, y in zip(linhas_x, ys)) for i in range(k)]
    # Eliminação de Gauss com pivoteamento parcial.
    m = [linha + [v] for linha, v in zip(ata, aty)]
    for col in range(k):
        piv = max(range(col, k), key=lambda r: abs(m[r][col]))
        m[col], m[piv] = m[piv], m[col]
        for r in range(k):
            if r != col:
                fator = m[r][col] / m[col][col]
                m[r] = [a - fator * b for a, b in zip(m[r], m[col])]
    return [m[i][k] / m[i][i] for i in range(k)]


def ajustar_modelo_limiar(resumo_limiar):
    """Ajusta T(n, c) ≈ K_n + α·pares(c) + β·internos(c) às medições.

    K_n (um por n) absorve as ordenações iniciais, que não dependem do
    limiar; α é o custo de uma comparação da força bruta e β o custo, por
    ponto, de dividir e combinar. Dividir um subproblema de s pontos só
    compensa quando α s(s-1)/2 > 2·α (s/2)(s/2 - 1)/2 + β s, isto é, quando
    s > 4β/α: esse é o limiar previsto pelo modelo.
    """
    ns = sorted({int(n) for n, _ in resumo_limiar})
    linhas, ys = [], []
    for (n, c), r in resumo_limiar.items():
        pares, internos, _ = contagens_recursao(int(n), int(c))
        indicadores = [1.0 if int(n) == m else 0.0 for m in ns]
        linhas.append([*indicadores, pares, internos])
        ys.append(r["media"])
    coef = minimos_quadrados(linhas, ys)
    ks = dict(zip(ns, coef[:len(ns)]))
    alfa, beta = coef[-2], coef[-1]
    return {"K": ks, "alfa": alfa, "beta": beta, "limiar_previsto": 4 * beta / alfa}


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------

def salvar(figura, nome):
    FIGURAS.mkdir(parents=True, exist_ok=True)
    for extensao in ("svg", "png"):
        figura.savefig(FIGURAS / f"{nome}.{extensao}", bbox_inches="tight",
                       facecolor="white")
    plt.close(figura)


def eixo_tempo_loglog(ax, titulo):
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("n (escala log)")
    ax.set_ylabel("tempo médio (s, escala log)")
    ax.set_title(titulo, loc="left")


def plotar_tempos(ax, resumo, algoritmos):
    for alg in algoritmos:
        medias = serie(resumo, alg)
        desvios = serie(resumo, alg, "desvio")
        ns = sorted(medias)
        ax.errorbar(ns, [medias[n] for n in ns], yerr=[desvios[n] for n in ns],
                    color=COR[alg], marker=MARCADOR[alg], label=ROTULO[alg],
                    capsize=2, elinewidth=0.8)


def plotar_normalizado(ax, resumo, modelos, titulo):
    """T(n) / (c·f(n)): fica perto de 1 quando o modelo descreve os dados."""
    for alg, modelo in modelos.items():
        pontos = serie(resumo, alg)
        c = constante(pontos, modelo)
        ns = sorted(pontos)
        ax.plot(ns, [pontos[n] / (c * MODELOS[modelo](n)) for n in ns],
                color=COR[alg], marker=MARCADOR[alg],
                label=f"{ROTULO[alg]} ÷ c·{modelo}")
    ax.axhline(1.0, color=TINTA_2, linewidth=1, linestyle="--")
    ax.set_xscale("log", base=2)
    ax.set_ylim(0, 2)
    ax.set_xlabel("n (escala log)")
    ax.set_ylabel("tempo ÷ modelo ajustado")
    ax.set_title(titulo, loc="left")


def figura_etapa(resumo, algoritmos, modelos, nome, titulo):
    figura, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.9))
    plotar_tempos(ax1, resumo, algoritmos)
    eixo_tempo_loglog(ax1, f"(a) {titulo}: tempo × n")
    ax1.legend(loc="upper left")
    plotar_normalizado(ax2, resumo, modelos, "(b) tempo ÷ complexidade prevista")
    ax2.legend(loc="lower left", fontsize=7)
    figura.tight_layout()
    salvar(figura, nome)


def figura_pequenos(resumo_peq):
    figura, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 2.9))
    for ax, etapa, algoritmos, titulo in (
            (ax1, "1", ["forca-bruta", "dc", "dc-linear", "kadane"], "(a) Etapa 1, n pequeno"),
            (ax2, "2", ["forca-bruta", "dc", "dc-limiar-2"], "(b) Etapa 2, n pequeno")):
        for alg in algoritmos:
            pontos = {int(n): r["media"] for (e, a, n), r in resumo_peq.items()
                      if e == etapa and a == alg}
            ns = sorted(pontos)
            rotulo = ROTULO[alg]
            if etapa == "2" and alg == "dc":
                rotulo = f"D&C (limiar {etapa2.LIMIAR_PADRAO})"
            ax.plot(ns, [pontos[n] * 1e6 for n in ns], color=COR[alg],
                    marker=MARCADOR[alg], label=rotulo)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xlabel("n (escala log)")
        ax.set_ylabel("tempo médio (µs, escala log)")
        ax.set_title(titulo, loc="left")
        ax.legend(loc="upper left")
    figura.tight_layout()
    salvar(figura, "pequenos")


def figura_limiar(resumo_limiar, modelo):
    figura, ax = plt.subplots(figsize=(7.2, 2.6))
    ns = sorted({int(n) for n, _ in resumo_limiar})
    cores = ["#2a78d6", "#eb6834"]
    marcadores = ["o", "s"]
    for cor, marcador, n in zip(cores, marcadores, ns):
        pontos = {int(c): r for (m, c), r in resumo_limiar.items() if int(m) == n}
        cs = sorted(pontos)
        melhor = min(p["media"] for p in pontos.values())
        ax.errorbar(cs, [pontos[c]["media"] / melhor for c in cs],
                    yerr=[pontos[c]["desvio"] / melhor for c in cs],
                    color=cor, marker=marcador, capsize=2, elinewidth=0.8,
                    label=f"medido, n = {n}")
        previsto = [modelo["K"][n] + modelo["alfa"] * contagens_recursao(n, c)[0]
                    + modelo["beta"] * contagens_recursao(n, c)[1] for c in cs]
        ax.plot(cs, [p / melhor for p in previsto], color=cor, linewidth=1,
                linestyle=":", label=f"modelo ajustado, n = {n}")
    ax.axvline(etapa2.LIMIAR_PADRAO, color=TINTA_2, linewidth=1, linestyle="--")
    ax.annotate(f"limiar escolhido = {etapa2.LIMIAR_PADRAO}",
                xy=(etapa2.LIMIAR_PADRAO, 1.0), xytext=(4, -14), textcoords="offset points",
                color=TINTA, fontsize=8)
    ax.set_xscale("log", base=2)
    ax.set_xlabel("limiar c (escala log): subproblemas com até c pontos usam força bruta")
    ax.set_ylabel("tempo ÷ melhor tempo")
    ax.set_title("Etapa 2: efeito do limiar no tempo da divisão e conquista", loc="left")
    ax.legend(ncol=2, loc="upper center")
    figura.tight_layout()
    salvar(figura, "limiar")


def figura_faixa():
    """Ilustração do argumento dos 7 vizinhos (retângulo δ × 2δ)."""
    figura, ax = plt.subplots(figsize=(3.4, 2.1))
    d = 1.0
    for i in range(4):
        for j in range(2):
            ax.add_patch(Rectangle((-d + i * d / 2, j * d / 2), d / 2, d / 2,
                                   fill=False, edgecolor=TINTA_2, linewidth=0.8))
    ax.axvline(0, color=COR["dc"], linewidth=2)
    ax.plot([-0.12], [0.0], marker="o", color=COR["forca-bruta"], markersize=7)
    ax.annotate("p", (-0.12, 0.0), xytext=(-12, 4), textcoords="offset points", color=TINTA)
    exemplo = [(-0.9, 0.05), (-0.4, 0.45), (0.15, 0.2), (0.62, 0.08), (0.9, 0.85),
               (-0.65, 0.92), (0.3, 0.7)]
    ax.plot(*zip(*exemplo), linestyle="none", marker="o", color=COR["dc-linear"], markersize=5)
    ax.annotate("", xy=(-d, -0.12), xytext=(d, -0.12),
                arrowprops={"arrowstyle": "<->", "color": TINTA_2, "linewidth": 0.8})
    ax.text(0, -0.24, "2δ", ha="center", va="top", color=TINTA)
    ax.annotate("", xy=(1.1, 0), xytext=(1.1, d),
                arrowprops={"arrowstyle": "<->", "color": TINTA_2, "linewidth": 0.8})
    ax.text(1.16, d / 2, "δ", va="center", color=TINTA)
    ax.text(-0.98, 1.05, "esquerda", fontsize=8, color=TINTA_2)
    ax.text(0.5, 1.05, "direita", fontsize=8, color=TINTA_2)
    ax.text(0.03, 1.05, "linha", fontsize=8, color=COR["dc"])
    ax.set_xlim(-1.15, 1.35)
    ax.set_ylim(-0.42, 1.2)
    ax.set_aspect("equal")
    ax.axis("off")
    salvar(figura, "faixa")


# ---------------------------------------------------------------------------
# Tabelas e números para o relatório
# ---------------------------------------------------------------------------

def ms(segundos):
    """Formata em milissegundos com 3 algarismos significativos."""
    valor = segundos * 1e3
    if valor >= 100:
        return f"{valor:.0f}"
    if valor >= 10:
        return f"{valor:.1f}"
    if valor >= 1:
        return f"{valor:.2f}"
    return f"{valor:.3f}"


def virgula(texto):
    return texto.replace(".", ",")


def tabela_tempos(resumo, algoritmos, tamanhos):
    cabecalho = "| n | " + " | ".join(ROTULO[a] for a in algoritmos) + " |"
    separador = "|---:|" + "---:|" * len(algoritmos)
    linhas = [cabecalho, separador]
    for n in tamanhos:
        celulas = []
        for alg in algoritmos:
            r = resumo.get((alg, str(n)))
            if r is None:
                celulas.append("—")
                continue
            anterior = resumo.get((alg, str(n // 2)))
            texto = f"{ms(r['media'])} ± {ms(r['desvio'])}"
            if anterior:
                texto += f" (×{r['media'] / anterior['media']:.1f})"
            celulas.append(virgula(texto))
        linhas.append(f"| {n} | " + " | ".join(celulas) + " |")
    return "\n".join(linhas) + "\n"


def tabela_ajustes(ajustes):
    linhas = ["| Algoritmo | Complexidade | Inclinação log-log medida | "
              "Inclinação esperada | Maior desvio do modelo |",
              "|---|---|---:|---:|---:|"]
    for a in ajustes:
        linhas.append(virgula(
            f"| {a['nome']} | Θ({a['modelo']}) | {a['inclinacao']:.2f} | "
            f"{a['esperada']} | {100 * a['erro']:.0f}% |"))
    return "\n".join(linhas) + "\n"


def tabela_limiar(resumo_limiar, escolhido, selecao):
    ns = sorted({int(n) for n, _ in resumo_limiar})
    linhas = ["| Limiar c | " + " | ".join(f"n = {n}: média (ms)" for n in ns)
              + " | " + " | ".join(f"n = {n}: mediana (ms)" for n in ns) + " |",
              "|---:|" + "---:|" * (2 * len(ns))]
    for c in selecao:
        medias = [ms(resumo_limiar[(str(n), str(c))]["media"]) for n in ns]
        medianas = [ms(resumo_limiar[(str(n), str(c))]["mediana"]) for n in ns]
        rotulo = f"**{c}**" if c == escolhido else str(c)
        linhas.append(virgula(f"| {rotulo} | " + " | ".join(medias) + " | "
                              + " | ".join(medianas) + " |"))
    return "\n".join(linhas) + "\n"


def estatisticas_faixa():
    """Máximo de sucessores examinados na faixa em entradas aleatórias."""
    maior, total = 0, 0
    for semente in range(5):
        rng = random.Random(semente)
        pontos = [(rng.uniform(0, 1e6), rng.uniform(0, 1e6)) for _ in range(6400)]
        est = {}
        etapa2.divisao_conquista(pontos, limiar=2, vizinhos=None, estatisticas=est)
        maior = max(maior, est["max_sucessores"])
        total += est["comparacoes_faixa"]
    return maior, total / 5


# ---------------------------------------------------------------------------

def main():
    GERADO.mkdir(parents=True, exist_ok=True)
    numeros = {"limiar_padrao": etapa2.LIMIAR_PADRAO}
    maquina = (RESULTADOS / "maquina.txt").read_text(encoding="utf-8")
    numeros["maquina"] = maquina.strip().splitlines()

    # Etapa 1 ---------------------------------------------------------------
    r1 = resumir(ler_csv("etapa1_medicoes.csv"), ["algoritmo", "n"])
    escrever_resumo("resumo_etapa1.csv", ["algoritmo", "n"], r1)
    modelos1 = {"forca-bruta": "n²", "dc": "n log n", "dc-linear": "n", "kadane": "n"}
    figura_etapa(r1, ["forca-bruta", "dc", "dc-linear", "kadane"], modelos1,
                 "etapa1", "Etapa 1")
    extras1 = sorted({int(n) for (_, n) in r1} - set(TAMANHOS))
    (GERADO / "tabela_etapa1.md").write_text(
        tabela_tempos(r1, ["forca-bruta", "dc", "dc-linear", "kadane"], TAMANHOS + extras1),
        encoding="utf-8")

    # Etapa 2 ---------------------------------------------------------------
    r2 = resumir(ler_csv("etapa2_medicoes.csv"), ["algoritmo", "n"])
    escrever_resumo("resumo_etapa2.csv", ["algoritmo", "n"], r2)
    modelos2 = {"forca-bruta": "n²", "dc": "n log n"}
    figura_etapa(r2, ["forca-bruta", "dc"], modelos2, "etapa2", "Etapa 2")
    extras2 = sorted({int(n) for (_, n) in r2} - set(TAMANHOS))
    (GERADO / "tabela_etapa2.md").write_text(
        tabela_tempos(r2, ["forca-bruta", "dc"], TAMANHOS + extras2), encoding="utf-8")

    # Ajustes (inclinações e desvio máximo em relação ao modelo) -------------
    ajustes = []
    esperadas = {"n²": "2", "n log n": "≈ 1,1–1,2", "n": "1"}
    for etapa, resumo, modelos in ((1, r1, modelos1), (2, r2, modelos2)):
        for alg, modelo in modelos.items():
            pontos = serie(resumo, alg)
            chave = f"etapa{etapa}_{alg}"
            ajustes.append({
                "nome": f"Etapa {etapa}: {ROTULO[alg]}",
                "modelo": modelo,
                "inclinacao": inclinacao_loglog(pontos),
                "esperada": esperadas[modelo],
                "erro": erro_relativo_maximo(pontos, modelo),
            })
            numeros[f"{chave}_inclinacao"] = round(inclinacao_loglog(pontos), 2)
            numeros[f"{chave}_erro_pct"] = round(100 * erro_relativo_maximo(pontos, modelo))
            numeros[f"{chave}_ns"] = [min(pontos), max(pontos)]
            # Inclinação só no intervalo pedido no enunciado (100..6400).
            base = {n: t for n, t in pontos.items() if n in TAMANHOS}
            numeros[f"{chave}_inclinacao_base"] = round(inclinacao_loglog(base), 2)
            razoes = razoes_duplicacao(base)
            numeros[f"{chave}_razao_media"] = round(statistics.mean(razoes.values()), 2)
            numeros[f"{chave}_t6400_ms"] = round(pontos[6400] * 1e3, 1)
    (GERADO / "tabela_ajustes.md").write_text(tabela_ajustes(ajustes), encoding="utf-8")
    numeros["etapa1_speedup_6400"] = round(
        serie(r1, "forca-bruta")[6400] / serie(r1, "dc")[6400], 1)
    numeros["etapa2_speedup_6400"] = round(
        serie(r2, "forca-bruta")[6400] / serie(r2, "dc")[6400], 1)
    numeros["etapa1_dc_sobre_kadane_6400"] = round(
        serie(r1, "dc")[6400] / serie(r1, "kadane")[6400], 1)
    numeros["etapa1_linear_sobre_kadane_6400"] = round(
        serie(r1, "dc-linear")[6400] / serie(r1, "kadane")[6400], 1)
    # Razões T(2n)/T(n) previstas para n log n no intervalo do enunciado.
    numeros["razao_prevista_nlogn"] = round(statistics.mean(
        2 * math.log2(2 * n) / math.log2(n) for n in TAMANHOS[:-1]), 2)

    # Entradas pequenas -----------------------------------------------------
    rp = resumir(ler_csv("pequenos_medicoes.csv"), ["etapa", "algoritmo", "n"])
    escrever_resumo("resumo_pequenos.csv", ["etapa", "algoritmo", "n"], rp)
    figura_pequenos(rp)

    def pequenos(etapa, alg):
        return {int(n): r["media"] for (e, a, n), r in rp.items() if e == etapa and a == alg}

    numeros["cruzamento_etapa1_dc"] = cruzamento(pequenos("1", "forca-bruta"),
                                                 pequenos("1", "dc"))
    numeros["cruzamento_etapa1_kadane"] = cruzamento(pequenos("1", "forca-bruta"),
                                                     pequenos("1", "kadane"))
    numeros["cruzamento_etapa1_linear"] = cruzamento(pequenos("1", "forca-bruta"),
                                                     pequenos("1", "dc-linear"))
    numeros["cruzamento_etapa2_dc"] = cruzamento(pequenos("2", "forca-bruta"),
                                                 pequenos("2", "dc"))
    numeros["cruzamento_etapa2_dc2"] = cruzamento(pequenos("2", "forca-bruta"),
                                                  pequenos("2", "dc-limiar-2"))
    for etapa, alg in (("1", "forca-bruta"), ("1", "dc"), ("2", "forca-bruta"),
                       ("2", "dc"), ("2", "dc-limiar-2")):
        p = pequenos(etapa, alg)
        for n in (8, 16, 32, 64, 128):
            numeros[f"peq{etapa}_{alg}_{n}_us"] = round(p[n] * 1e6, 1)

    # Limiar ------------------------------------------------------------------
    rl = resumir(ler_csv("limiar_medicoes.csv"), ["n", "limiar"])
    escrever_resumo("resumo_limiar.csv", ["n", "limiar"], rl)
    modelo = ajustar_modelo_limiar(rl)
    figura_limiar(rl, modelo)
    ns_limiar = sorted({int(n) for n, _ in rl})
    limiares = sorted({int(c) for _, c in rl})
    # Tempo relativo ao melhor de cada n, combinado pela média geométrica.
    relativo = {}
    for c in limiares:
        razoes = []
        for n in ns_limiar:
            melhor = min(rl[(str(n), str(x))]["media"] for x in limiares)
            razoes.append(rl[(str(n), str(c))]["media"] / melhor)
        relativo[c] = math.exp(statistics.mean(math.log(r) for r in razoes))
    melhor_c = min(relativo, key=relativo.get)
    numeros["limiar_melhor_medido"] = melhor_c
    numeros["limiar_relativo"] = {str(c): round(v, 3) for c, v in relativo.items()}
    numeros["limiar_quase_otimos"] = [c for c, v in relativo.items() if v <= 1.05]
    numeros["limiar_previsto"] = round(modelo["limiar_previsto"], 1)
    numeros["limiar_alfa_ns"] = round(modelo["alfa"] * 1e9, 1)
    numeros["limiar_beta_ns"] = round(modelo["beta"] * 1e9, 1)
    numeros["limiar_ns"] = ns_limiar
    numeros["limiar_pior_2_pct"] = round(100 * (relativo[2] - 1))
    numeros["limiar_pior_128_pct"] = round(100 * (relativo[max(limiares)] - 1))
    numeros["limiar_padrao_pct"] = round(100 * (relativo[etapa2.LIMIAR_PADRAO] - 1), 1)
    selecao = [c for c in (2, 3, 4, 6, 8, 10, 12, 14, 16, 20, 24, 32, 48, 64, 128)
               if c in limiares]
    (GERADO / "tabela_limiar.md").write_text(
        tabela_limiar(rl, etapa2.LIMIAR_PADRAO, selecao), encoding="utf-8")
    # Custo por par da força bruta medido diretamente (n = 6400), p/ comparar com α.
    numeros["alfa_forca_bruta_ns"] = round(
        serie(r2, "forca-bruta")[6400] / (6400 * 6399 / 2) * 1e9, 1)

    # Limiares que produzem exatamente a mesma recursão que o escolhido.
    for n in ns_limiar:
        alvo = contagens_recursao(n, etapa2.LIMIAR_PADRAO)
        iguais = [c for c in range(2, 200) if contagens_recursao(n, c) == alvo]
        numeros[f"limiar_mesma_arvore_{n}"] = [min(iguais), max(iguais)]
        folhas = set()
        pilha = [n]
        while pilha:
            m = pilha.pop()
            if m <= etapa2.LIMIAR_PADRAO:
                folhas.add(m)
            else:
                pilha.extend((m // 2, m - m // 2))
        numeros[f"limiar_folhas_{n}"] = sorted(folhas)

    # Ruído: coeficiente de variação médio das medições principais.
    cvs = [r["desvio"] / r["media"] for resumo in (r1, r2) for r in resumo.values()]
    numeros["cv_medio_pct"] = round(100 * statistics.mean(cvs))
    numeros["cv_max_pct"] = round(100 * max(cvs))

    # Quantidade de casos nos arquivos de teste.
    sys.path.insert(0, str(RAIZ / "testes"))
    from leitor_casos import ler_casos
    numeros["casos_etapa1"] = len(ler_casos("casos_etapa1.txt"))
    numeros["casos_etapa2"] = len(ler_casos("casos_etapa2.txt"))

    # Faixa ---------------------------------------------------------------------
    figura_faixa()
    maior, comparacoes = estatisticas_faixa()
    numeros["faixa_max_sucessores"] = maior
    numeros["faixa_comparacoes_6400"] = round(comparacoes)

    (GERADO / "numeros.json").write_text(
        json.dumps(numeros, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(numeros, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
