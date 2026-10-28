#!/usr/bin/env python3
"""Gera relatorio/relatorio.pdf a partir de relatorio/relatorio.md.

Passos:
  1. substitui os marcadores {{tabela:nome}}, {{num:chave}} e {{maquina}}
     pelo conteúdo de relatorio/gerado/ (produzido por experimentos/analisar.py);
  2. converte para HTML com o pandoc (fórmulas com MathJax);
  3. imprime o HTML em PDF com o Chromium do Playwright (imprimir_pdf.js).

Requisitos: pandoc, Node.js com o pacote ``playwright`` e o MathJax 3. O
MathJax é procurado em --mathjax, na variável MATHJAX e em
relatorio/node_modules (``npm install mathjax@3`` dentro de relatorio/);
se não for encontrado, é carregado da CDN jsDelivr.

Uso (a partir da raiz do repositório):
    python3 relatorio/gerar_pdf.py
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent
GERADO = PASTA / "gerado"
CDN_MATHJAX = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js"
LIMITE_PAGINAS = 8


def formatar(valor):
    if isinstance(valor, bool):
        return "sim" if valor else "não"
    if isinstance(valor, float):
        return f"{valor:g}".replace(".", ",")
    if isinstance(valor, list):
        itens = [formatar(v) for v in valor]
        return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]
    return str(valor)


def preencher(texto, numeros):
    def tabela(m):
        return (GERADO / f"tabela_{m.group(1)}.md").read_text(encoding="utf-8").strip()

    def numero(m):
        chave = m.group(1)
        if chave not in numeros:
            raise KeyError(f"número {chave!r} não existe em gerado/numeros.json")
        return formatar(numeros[chave])

    maquina = "\n".join(f"- {linha}" for linha in numeros["maquina"] if linha.strip())
    texto = texto.replace("{{maquina}}", maquina)
    texto = re.sub(r"\{\{tabela:([\w-]+)\}\}", tabela, texto)
    texto = re.sub(r"\{\{num:([\w-]+)\}\}", numero, texto)
    restantes = re.findall(r"\{\{[^}]*\}\}", texto)
    if restantes:
        raise ValueError(f"marcadores não substituídos: {restantes}")
    return texto


def localizar_mathjax(argumento):
    candidatos = [argumento, os.environ.get("MATHJAX"),
                  PASTA / "node_modules" / "mathjax" / "es5" / "tex-svg.js"]
    for candidato in candidatos:
        if candidato and Path(candidato).is_file():
            return Path(candidato).resolve().as_uri()
    print("MathJax local não encontrado; usando a CDN.", file=sys.stderr)
    return CDN_MATHJAX


def ambiente_node():
    ambiente = dict(os.environ)
    try:
        raiz_global = subprocess.run(["npm", "root", "-g"], capture_output=True,
                                     text=True, check=True).stdout.strip()
        ambiente["NODE_PATH"] = os.pathsep.join(
            p for p in (ambiente.get("NODE_PATH"), raiz_global) if p)
    except (OSError, subprocess.CalledProcessError):
        pass
    return ambiente


def contar_paginas(pdf):
    try:
        saida = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        return int(re.search(r"Pages:\s+(\d+)", saida).group(1))
    except (OSError, AttributeError):
        return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def main():
    parser = argparse.ArgumentParser(description="Gera o PDF do relatório.")
    parser.add_argument("--mathjax", help="caminho do tex-svg.js do MathJax 3")
    args = parser.parse_args()

    numeros = json.loads((GERADO / "numeros.json").read_text(encoding="utf-8"))
    markdown = preencher((PASTA / "relatorio.md").read_text(encoding="utf-8"), numeros)

    html = PASTA / "relatorio.html"
    subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html5", "-s", "--number-sections",
         f"--mathjax={localizar_mathjax(args.mathjax)}",
         "--css", "estilo.css", "--metadata", "lang=pt-BR", "-o", str(html)],
        input=markdown, text=True, check=True, cwd=PASTA)

    pdf = PASTA / "relatorio.pdf"
    subprocess.run(["node", str(PASTA / "imprimir_pdf.js"), str(html), str(pdf)],
                   check=True, env=ambiente_node())
    paginas = contar_paginas(pdf)
    print(f"{pdf.relative_to(PASTA.parent)}: {paginas} páginas")
    if paginas > LIMITE_PAGINAS:
        print(f"ATENÇÃO: o enunciado limita o relatório a {LIMITE_PAGINAS} páginas.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
