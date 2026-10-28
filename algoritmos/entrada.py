"""Leitura das entradas no formato do enunciado (texto livre separado por espaços)."""


class EntradaInvalida(ValueError):
    pass


def _numero(token):
    """Converte um token em int quando possível; caso contrário, em float."""
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            raise EntradaInvalida(f"valor não numérico: {token!r}") from None


def _ler_n(tokens):
    if not tokens:
        raise EntradaInvalida("entrada vazia: esperado o inteiro n")
    try:
        n = int(tokens[0])
    except ValueError:
        raise EntradaInvalida(f"n deve ser inteiro, recebido {tokens[0]!r}") from None
    if n < 0:
        raise EntradaInvalida("n não pode ser negativo")
    return n


def ler_vetor(texto):
    """Etapa 1: ``n`` seguido de ``n`` inteiros (em qualquer quebra de linha)."""
    tokens = texto.split()
    n = _ler_n(tokens)
    valores = tokens[1:]
    if len(valores) < n:
        raise EntradaInvalida(f"esperados {n} inteiros, encontrados {len(valores)}")
    vetor = []
    for token in valores[:n]:
        try:
            vetor.append(int(token))
        except ValueError:
            raise EntradaInvalida(f"valor não inteiro: {token!r}") from None
    return vetor


def ler_pontos(texto):
    """Etapa 2: ``n`` seguido de ``n`` pares ``x y`` (inteiros ou reais)."""
    tokens = texto.split()
    n = _ler_n(tokens)
    valores = tokens[1:]
    if len(valores) < 2 * n:
        raise EntradaInvalida(
            f"esperadas {2 * n} coordenadas ({n} pontos), encontradas {len(valores)}")
    coords = [_numero(t) for t in valores[:2 * n]]
    return [(coords[2 * k], coords[2 * k + 1]) for k in range(n)]
