"""Etapa 1 — Subarranjo de soma máxima.

Todas as funções recebem uma sequência NÃO vazia de inteiros ``a`` e devolvem
uma tupla ``(soma, inicio, fim)``, com índices base 0 e intervalo fechado
``a[inicio..fim]``. O subarranjo nunca é vazio: num vetor só de negativos a
resposta é o maior elemento.

Critério de desempate (o mesmo nas quatro implementações): entre os intervalos
de soma máxima escolhe-se o de menor ``inicio``; persistindo o empate, o de
menor ``fim`` (o mais curto). Com um critério único, todas as versões devolvem
exatamente a mesma resposta e podem ser comparadas entre si nos testes.

Implementações:
    forca_bruta                 Θ(n²)        testa todos os intervalos
    divisao_conquista           Θ(n log n)   T(n) = 2T(n/2) + Θ(n)
    divisao_conquista_linear    Θ(n)         T(n) = 2T(n/2) + Θ(1)
    kadane                      Θ(n)         varredura única
"""

NEG_INF = float("-inf")


def _validar(a):
    if len(a) == 0:
        raise ValueError("o vetor deve ter ao menos um elemento")


def _melhor(x, y):
    """Devolve o melhor entre dois candidatos ``(soma, inicio, fim)``.

    Maior soma vence; em empate vence o menor ``(inicio, fim)``.
    """
    if x[0] != y[0]:
        return x if x[0] > y[0] else y
    return x if (x[1], x[2]) <= (y[1], y[2]) else y


# ---------------------------------------------------------------------------
# Força bruta — Θ(n²)
# ---------------------------------------------------------------------------

def forca_bruta(a):
    """Testa todos os n(n+1)/2 intervalos [i..j].

    A soma de [i..j] é obtida de [i..j-1] somando a[j], então cada intervalo
    custa O(1) e o total é Θ(n²). Como i e j crescem e a troca só ocorre com
    soma estritamente maior, o primeiro intervalo encontrado com a soma máxima
    já é o de menor (inicio, fim).
    """
    _validar(a)
    n = len(a)
    melhor_soma, melhor_i, melhor_j = a[0], 0, 0
    for i in range(n):
        soma = 0
        for j in range(i, n):
            soma += a[j]
            if soma > melhor_soma:
                melhor_soma, melhor_i, melhor_j = soma, i, j
    return (melhor_soma, melhor_i, melhor_j)


# ---------------------------------------------------------------------------
# Divisão e conquista — Θ(n log n)
# ---------------------------------------------------------------------------

def _melhor_cruzando(a, lo, meio, hi):
    """Melhor subarranjo que contém a[meio] e a[meio + 1], em Θ(hi - lo).

    É a junção do melhor sufixo de a[lo..meio] com o melhor prefixo de
    a[meio+1..hi]; as duas partes são independentes. Para o desempate:
      - no lado esquerdo, varrendo de meio para lo, ``>=`` fica com o menor
        início entre os sufixos de soma máxima;
      - no lado direito, varrendo de meio+1 para hi, ``>`` fica com o menor
        fim entre os prefixos de soma máxima.
    """
    soma = 0
    melhor_esq, inicio = NEG_INF, meio
    for i in range(meio, lo - 1, -1):
        soma += a[i]
        if soma >= melhor_esq:
            melhor_esq, inicio = soma, i

    soma = 0
    melhor_dir, fim = NEG_INF, meio + 1
    for j in range(meio + 1, hi + 1):
        soma += a[j]
        if soma > melhor_dir:
            melhor_dir, fim = soma, j

    return (melhor_esq + melhor_dir, inicio, fim)


def _dc(a, lo, hi):
    if lo == hi:
        return (a[lo], lo, lo)
    meio = (lo + hi) // 2
    esquerda = _dc(a, lo, meio)
    direita = _dc(a, meio + 1, hi)
    cruzando = _melhor_cruzando(a, lo, meio, hi)
    return _melhor(_melhor(esquerda, cruzando), direita)


def divisao_conquista(a):
    """Divide ao meio, resolve cada metade e combina com o melhor cruzamento.

    Recorrência: T(1) = Θ(1), T(n) = 2T(n/2) + Θ(n)  =>  Θ(n log n).

    Todo intervalo ótimo está inteiro na esquerda, inteiro na direita ou cruza
    o meio; cada parte devolve o menor (inicio, fim) da sua categoria, logo o
    melhor dos três respeita o critério de desempate global.
    """
    _validar(a)
    return _dc(a, 0, len(a) - 1)


# ---------------------------------------------------------------------------
# Versão O(n) (questão desafio): divisão e conquista com combinação O(1)
# ---------------------------------------------------------------------------

def _dc_linear(a, lo, hi):
    """Devolve (total, prefixo, fim_prefixo, sufixo, ini_sufixo, melhor).

    prefixo: maior soma de a[lo..k] (menor k em empate);
    sufixo:  maior soma de a[k..hi] (menor k em empate);
    melhor:  (soma, inicio, fim) do melhor subarranjo de a[lo..hi].
    """
    if lo == hi:
        v = a[lo]
        return (v, v, lo, v, lo, (v, lo, lo))
    meio = (lo + hi) // 2
    tot_e, pre_e, fpre_e, suf_e, isuf_e, mel_e = _dc_linear(a, lo, meio)
    tot_d, pre_d, fpre_d, suf_d, isuf_d, mel_d = _dc_linear(a, meio + 1, hi)

    total = tot_e + tot_d

    # Prefixo: ou fica na esquerda, ou cobre a esquerda inteira e entra na
    # direita. Em empate a primeira opção termina antes (menor fim).
    if pre_e >= tot_e + pre_d:
        prefixo, fim_prefixo = pre_e, fpre_e
    else:
        prefixo, fim_prefixo = tot_e + pre_d, fpre_d

    # Sufixo: ou fica na direita, ou cobre a direita inteira e entra na
    # esquerda. Em empate a segunda opção começa antes (menor início).
    if suf_e + tot_d >= suf_d:
        sufixo, ini_sufixo = suf_e + tot_d, isuf_e
    else:
        sufixo, ini_sufixo = suf_d, isuf_d

    cruzando = (suf_e + pre_d, isuf_e, fpre_d)
    melhor = _melhor(_melhor(mel_e, cruzando), mel_d)
    return (total, prefixo, fim_prefixo, sufixo, ini_sufixo, melhor)


def divisao_conquista_linear(a):
    """Divisão e conquista em Θ(n).

    Cada chamada devolve, além da resposta, o total, o melhor prefixo e o
    melhor sufixo do trecho. O cruzamento passa a ser sufixo(esq) +
    prefixo(dir), obtido em O(1), e a recorrência vira
    T(n) = 2T(n/2) + Θ(1)  =>  Θ(n).
    """
    _validar(a)
    return _dc_linear(a, 0, len(a) - 1)[5]


# ---------------------------------------------------------------------------
# Kadane — Θ(n)
# ---------------------------------------------------------------------------

def kadane(a):
    """Varredura única mantendo a melhor soma que termina na posição atual.

    O trecho corrente só é descartado quando sua soma fica negativa; com soma
    zero ele é mantido, o que preserva o menor início. Atualizar o melhor só
    com soma estritamente maior preserva o menor fim; juntas, as duas regras
    reproduzem o desempate das demais versões.
    """
    _validar(a)
    atual, inicio_atual = a[0], 0
    melhor_soma, melhor_i, melhor_j = a[0], 0, 0
    for j in range(1, len(a)):
        if atual < 0:
            atual, inicio_atual = a[j], j
        else:
            atual += a[j]
        if atual > melhor_soma:
            melhor_soma, melhor_i, melhor_j = atual, inicio_atual, j
    return (melhor_soma, melhor_i, melhor_j)


ALGORITMOS = {
    "forca-bruta": forca_bruta,
    "dc": divisao_conquista,
    "dc-linear": divisao_conquista_linear,
    "kadane": kadane,
}
