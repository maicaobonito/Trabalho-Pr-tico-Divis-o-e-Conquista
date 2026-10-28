"""Etapa 2 — Par de pontos mais próximos.

As funções recebem uma sequência de pontos ``(x, y)`` com n >= 2 e devolvem
``(distancia, i, j)``, onde ``i < j`` são índices base 0 na sequência de
entrada.

Critério de desempate (igual nas duas versões): entre os pares com a mesma
distância mínima escolhe-se o de menor ``(i, j)`` em ordem lexicográfica.
Internamente as distâncias são comparadas ao quadrado, o que é exato para
coordenadas inteiras e evita a raiz quadrada no laço principal.

Implementações:
    forca_bruta         Θ(n²)        compara os n(n-1)/2 pares
    divisao_conquista   Θ(n log n)   ordenação inicial + T(n) = 2T(n/2) + Θ(n)
"""

from math import inf, sqrt

# Tamanho de subproblema a partir do qual a recursão para e usa força bruta.
# Valor escolhido experimentalmente (ver relatório, seção "Limiar").
LIMIAR_PADRAO = 12

# Quantidade máxima de sucessores (na ordem de y) comparados com cada ponto
# da faixa. O relatório demonstra por que 7 bastam.
VIZINHOS_NA_FAIXA = 7


def _validar(pontos):
    if len(pontos) < 2:
        raise ValueError("são necessários ao menos dois pontos")


# ---------------------------------------------------------------------------
# Força bruta — Θ(n²)
# ---------------------------------------------------------------------------

def forca_bruta(pontos):
    """Compara todos os n(n-1)/2 pares.

    Percorre os pares em ordem lexicográfica de (i, j) e só troca o melhor
    com distância estritamente menor; assim o par devolvido é o de menor
    (i, j) entre os de distância mínima.
    """
    _validar(pontos)
    xs = [p[0] for p in pontos]
    ys = [p[1] for p in pontos]
    n = len(pontos)
    melhor_d2, melhor_i, melhor_j = inf, -1, -1
    for i in range(n - 1):
        xi, yi = xs[i], ys[i]
        for j in range(i + 1, n):
            dx = xs[j] - xi
            dy = ys[j] - yi
            d2 = dx * dx + dy * dy
            if d2 < melhor_d2:
                melhor_d2, melhor_i, melhor_j = d2, i, j
    return (sqrt(melhor_d2), melhor_i, melhor_j)


# ---------------------------------------------------------------------------
# Divisão e conquista — Θ(n log n)
# ---------------------------------------------------------------------------

def _forca_bruta_ids(ids, xs, ys):
    """Caso base: força bruta sobre o subconjunto ``ids``.

    Devolve ``(d2, i, j)`` com i < j, ou ``(inf, -1, -1)`` se houver menos de
    dois pontos. Os candidatos são comparados como tuplas, o que aplica o
    desempate por (i, j) independentemente da ordem de visita.
    """
    melhor = (inf, -1, -1)
    m = len(ids)
    for a in range(m - 1):
        p = ids[a]
        xp, yp = xs[p], ys[p]
        for b in range(a + 1, m):
            q = ids[b]
            dx = xs[q] - xp
            dy = ys[q] - yp
            d2 = dx * dx + dy * dy
            if d2 <= melhor[0]:
                cand = (d2, p, q) if p < q else (d2, q, p)
                if cand < melhor:
                    melhor = cand
    return melhor


def _recursao(px, py, xs, ys, pos_x, limiar, vizinhos, est):
    """Resolve o subproblema formado pelos pontos de ``px``/``py``.

    px: índices ordenados por x (desempate y, índice);
    py: os mesmos índices ordenados por y (desempate x, índice);
    pos_x[k]: posição do ponto k na ordem global por x.
    """
    n = len(px)
    if est is not None:
        est["chamadas"] += 1
    if n <= limiar:
        return _forca_bruta_ids(px, xs, ys)

    # 1) Dividir: linha vertical na mediana de x. O ponto ``corte`` é o
    #    último da metade esquerda; a pertinência é decidida pela posição na
    #    ordem por x, o que funciona mesmo com muitos x repetidos.
    meio = n // 2
    corte = px[meio - 1]
    r = pos_x[corte]
    x_linha = xs[corte]
    esq_y = [k for k in py if pos_x[k] <= r]
    dir_y = [k for k in py if pos_x[k] > r]

    # 2) Conquistar: menor distância de cada lado (δ² = d2).
    melhor = min(
        _recursao(px[:meio], esq_y, xs, ys, pos_x, limiar, vizinhos, est),
        _recursao(px[meio:], dir_y, xs, ys, pos_x, limiar, vizinhos, est),
    )
    d2 = melhor[0]

    # 3) Combinar: faixa de largura 2δ em torno da linha, já ordenada por y.
    #    Cada ponto é comparado com os sucessores cuja diferença em y é <= δ;
    #    pelo argumento de empacotamento são no máximo 7.
    faixa = [k for k in py if (xs[k] - x_linha) ** 2 <= d2]
    m = len(faixa)
    for a in range(m - 1):
        p = faixa[a]
        xp, yp = xs[p], ys[p]
        limite = m if vizinhos is None else min(m, a + 1 + vizinhos)
        b = a + 1
        while b < limite:
            q = faixa[b]
            dy = ys[q] - yp
            if dy * dy > d2:
                break
            dx = xs[q] - xp
            dq = dx * dx + dy * dy
            if dq <= melhor[0]:
                cand = (dq, p, q) if p < q else (dq, q, p)
                if cand < melhor:
                    melhor = cand
            b += 1
        if est is not None:
            examinados = b - (a + 1)
            est["comparacoes_faixa"] += examinados
            if examinados > est["max_sucessores"]:
                est["max_sucessores"] = examinados
    return melhor


def divisao_conquista(pontos, limiar=LIMIAR_PADRAO, vizinhos=VIZINHOS_NA_FAIXA,
                      estatisticas=None):
    """Par mais próximo por divisão e conquista.

    Parâmetros:
        limiar: subproblemas com até ``limiar`` pontos são resolvidos por
            força bruta (mínimo 2).
        vizinhos: máximo de sucessores comparados na faixa (padrão 7);
            ``None`` remove o limite (usado nos testes para verificar que o
            limite de 7 nunca descarta um par necessário).
        estatisticas: dicionário opcional que recebe ``chamadas``,
            ``comparacoes_faixa`` e ``max_sucessores``.

    Custo: ordenações iniciais Θ(n log n) + T(n) = 2T(n/2) + Θ(n) = Θ(n log n).
    """
    _validar(pontos)
    if limiar < 2:
        raise ValueError("o limiar deve ser pelo menos 2")
    if estatisticas is not None:
        estatisticas.update(chamadas=0, comparacoes_faixa=0, max_sucessores=0)
    n = len(pontos)
    xs = [p[0] for p in pontos]
    ys = [p[1] for p in pontos]

    # Ordenação inicial com a função da biblioteca padrão (permitido no
    # enunciado). O índice no fim da chave torna as ordens totais.
    px = sorted(range(n), key=lambda k: (xs[k], ys[k], k))

    # Pontos coincidentes ficam adjacentes em px e dão distância 0, que não
    # pode ser superada. Tratá-los aqui garante δ > 0 na recursão, hipótese
    # do argumento dos 7 vizinhos. Dentro de um grupo de pontos iguais os
    # índices estão em ordem crescente, logo o primeiro par adjacente de cada
    # grupo é o menor (i, j) do grupo.
    par_zero = None
    for t in range(1, n):
        a, b = px[t - 1], px[t]
        if xs[a] == xs[b] and ys[a] == ys[b] and (par_zero is None or (a, b) < par_zero):
            par_zero = (a, b)
    if par_zero is not None:
        return (0.0, par_zero[0], par_zero[1])

    py = sorted(range(n), key=lambda k: (ys[k], xs[k], k))
    pos_x = [0] * n
    for posicao, k in enumerate(px):
        pos_x[k] = posicao

    d2, i, j = _recursao(px, py, xs, ys, pos_x, limiar, vizinhos, estatisticas)
    return (sqrt(d2), i, j)


ALGORITMOS = {
    "forca-bruta": forca_bruta,
    "dc": divisao_conquista,
}
