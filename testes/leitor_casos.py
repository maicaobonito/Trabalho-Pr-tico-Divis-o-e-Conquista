"""Leitura dos arquivos de casos de teste (testes/casos_etapa*.txt)."""

from dataclasses import dataclass
from pathlib import Path

PASTA = Path(__file__).resolve().parent


@dataclass
class Caso:
    nome: str
    motivo: str
    entrada: str
    saida: str


def ler_casos(nome_arquivo):
    """Devolve a lista de casos do arquivo, na ordem em que aparecem."""
    casos = []
    atual = None
    secao = None
    linhas = {"entrada": [], "saida": []}

    def fechar():
        if atual is None:
            return
        if not linhas["entrada"] or not linhas["saida"]:
            raise ValueError(f"caso {atual['nome']!r} sem entrada ou saída")
        casos.append(Caso(
            nome=atual["nome"],
            motivo=atual["motivo"],
            entrada="\n".join(linhas["entrada"]).strip() + "\n",
            saida="\n".join(linhas["saida"]).strip(),
        ))

    for linha in (PASTA / nome_arquivo).read_text(encoding="utf-8").splitlines():
        if linha.startswith("## "):
            fechar()
            atual = {"nome": linha[3:].strip(), "motivo": ""}
            linhas = {"entrada": [], "saida": []}
            secao = None
        elif linha.startswith("#"):
            continue
        elif atual is None:
            continue
        elif linha.startswith("motivo:"):
            atual["motivo"] = linha[len("motivo:"):].strip()
        elif linha.strip() in ("entrada:", "saida:"):
            secao = linha.strip()[:-1]
        elif secao is not None:
            linhas[secao].append(linha)
    fechar()

    nomes = [c.nome for c in casos]
    if len(nomes) != len(set(nomes)):
        raise ValueError(f"nomes de casos repetidos em {nome_arquivo}")
    return casos
