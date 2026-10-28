# Trabalho Prático: Divisão e Conquista

Dupla: **Michael David** e **Leonardo Sales**

Implementação, testes e análise experimental de dois problemas resolvidos por
divisão e conquista, cada um comparado com uma solução de força bruta:

| Etapa | Problema | Força bruta | Divisão e conquista | Extra |
|---|---|---|---|---|
| 1 | Subarranjo de soma máxima | Θ(n²) | Θ(n log n) | versões Θ(n): D&C com combinação O(1) e Kadane (questão desafio) |
| 2 | Par de pontos mais próximos | Θ(n²) | Θ(n log n) | limiar de força bruta escolhido experimentalmente (c = 16) |
| 3 | Análise experimental | — | — | CSVs brutos, tabelas, gráficos e relatório em PDF |

O relatório está em [`relatorio/relatorio.pdf`](relatorio/relatorio.pdf).

## Estrutura do repositório

```
algoritmos/
  subarranjo_maximo.py   Etapa 1: forca_bruta, divisao_conquista,
                         divisao_conquista_linear, kadane
  par_mais_proximo.py    Etapa 2: forca_bruta, divisao_conquista
  entrada.py             leitura da entrada padrão
etapa1.py                programa da Etapa 1 (lê stdin, escreve stdout)
etapa2.py                programa da Etapa 2
testes/
  casos_etapa1.txt       casos de teste da Etapa 1 (entrada, saída esperada, motivo)
  casos_etapa2.txt       casos de teste da Etapa 2
  test_etapa1.py         bateria de testes da Etapa 1
  test_etapa2.py         bateria de testes da Etapa 2
  leitor_casos.py        leitor do formato dos arquivos de casos
experimentos/
  medir.py               mede os tempos e grava os CSVs brutos
  analisar.py            resume, ajusta modelos, gera gráficos e tabelas
resultados/
  *_medicoes.csv         medições brutas (uma linha por execução)
  resumo_*.csv           média, mediana, desvio padrão e mínimo por tamanho
  maquina.txt            configuração da máquina usada
  figuras/               gráficos (SVG e PNG)
relatorio/
  relatorio.md           texto do relatório (com marcadores preenchidos a partir dos dados)
  relatorio.pdf          relatório final
  gerar_pdf.py           gera o PDF (pandoc + Chromium)
```

## Requisitos

- **Python 3.8 ou mais recente.** Os algoritmos, os programas e os testes usam só
  a biblioteca padrão.
- Para os gráficos: `matplotlib` (`pip install -r requirements.txt`).
- Só para regerar o PDF do relatório: `pandoc`, Node.js com o pacote `playwright`
  e o MathJax 3 (ver `relatorio/gerar_pdf.py`).

## Como executar

Todos os comandos são executados a partir da raiz do repositório.

### Etapa 1 — Subarranjo de soma máxima

Entrada: um inteiro `n` seguido de `n` inteiros (separados por espaços ou quebras
de linha). Saída: `soma inicio fim`, com índices **base 1**.

```bash
printf "16\n13 -3 -25 20 -3 -16 -23 18 20 -7 12 -5 -22 15 -4 7\n" | python3 etapa1.py
```

```
43 8 11
```

Opções:

- `--algoritmo {dc,forca-bruta,dc-linear,kadane}` (padrão `dc`);
- `--base {0,1}`: base dos índices impressos (padrão 1).

### Etapa 2 — Par de pontos mais próximos

Entrada: um inteiro `n` seguido de `n` pares `x y` (inteiros ou reais). Saída:
`distancia i j`, com `i < j` em base 1 e a distância com 6 casas decimais.

```bash
printf "6\n0 0\n0 100\n49 50\n51 50\n100 0\n100 100\n" | python3 etapa2.py --detalhado
```

```
2.000000 3 4
ponto 3: 49 50
ponto 4: 51 50
```

Opções:

- `--algoritmo {dc,forca-bruta}` (padrão `dc`);
- `--limiar C`: subproblemas com até `C` pontos usam força bruta (padrão 16, mínimo 2);
- `--base {0,1}` e `--detalhado` (imprime também as coordenadas).

### Regras comuns

- **Desempate.** Etapa 1: entre intervalos de mesma soma, vence o de menor início
  e, depois, o de menor fim. Etapa 2: entre pares de mesma distância, vence o de
  menor `(i, j)`. Todas as implementações seguem a mesma regra, então devolvem
  exatamente a mesma resposta.
- **Subarranjo não vazio.** Num vetor só de negativos a resposta é o maior elemento.
- **Entradas inválidas** (n ausente, n = 0 na Etapa 1, menos de 2 pontos na
  Etapa 2, valores faltando ou não numéricos) geram uma mensagem `erro: ...` na
  saída de erro e código de saída 1.

## Testes

```bash
python3 -m unittest discover -s testes -v
```

(`python3 -m pytest testes` também funciona, se o pytest estiver instalado.)

A bateria tem duas partes:

1. **Arquivos de casos** (`testes/casos_etapa1.txt`, `testes/casos_etapa2.txt`):
   cada caso traz a entrada, a saída esperada e o **motivo** de existir. Cobrem os
   casos de borda do enunciado (vetor de tamanho 1, só negativos, empates) e outros
   (n = 2, resposta cruzando o meio ou inteira em uma metade, valores grandes,
   pontos coincidentes, todos os pontos com o mesmo x ou o mesmo y, grades com
   muitos empates, coordenadas negativas, reais e grandes, formato livre da
   entrada). Cada caso é executado em todas as implementações e no programa de
   linha de comando, e as saídas esperadas são conferidas por um oráculo
   independente (definição do problema).
2. **Testes gerados**: milhares de entradas aleatórias pequenas (com valores em
   faixas estreitas para forçar empates) comparadas com o oráculo; todos os
   tamanhos de 1 a 70; entradas grandes; invariância a permutação e translação;
   verificação empírica de que nunca há mais de 7 sucessores a distância vertical
   δ na faixa (com um controle negativo mostrando que 1 vizinho não basta);
   rejeição de entradas inválidas.

O formato dos arquivos de casos é:

```
## nome_do_caso
motivo: o que o caso exercita
entrada:
3
-1 0 -2
saida:
0 2 2
```

## Experimentos (Etapa 3)

```bash
python3 experimentos/medir.py      # grava resultados/*_medicoes.csv e maquina.txt
python3 experimentos/analisar.py   # resumos, gráficos e tabelas do relatório
python3 relatorio/gerar_pdf.py     # (opcional) regera relatorio/relatorio.pdf
```

`medir.py` aceita a lista de experimentos (`etapa1`, `etapa2`, `limiar`,
`pequenos`, `localidade`) e `--repeticoes N` (mínimo 5). Os resultados
versionados foram obtidos com:

```bash
python3 experimentos/medir.py limiar --repeticoes 20
python3 experimentos/medir.py etapa1 etapa2 pequenos --repeticoes 15
python3 experimentos/medir.py localidade --repeticoes 10
```

A medição completa leva cerca de 10 minutos.

| Experimento | Tamanhos | O que mede |
|---|---|---|
| `etapa1` | 100 a 6400 (todas as versões) e até 204 800 (versões rápidas) | tempo × n da Etapa 1 |
| `etapa2` | 100 a 6400 (ambas) e até 204 800 (D&C) | tempo × n da Etapa 2 |
| `pequenos` | 2 a 512 | onde a força bruta vence |
| `limiar` | n = 6400 e 50 000, limiar de 2 a 128 | escolha do limiar da Etapa 2 |
| `localidade` | 3200 a 204 800 | D&C da Etapa 2 com os mesmos pontos em ordem aleatória e em ordem de x (efeito da memória) |

As medições foram feitas na máquina descrita em
[`resultados/maquina.txt`](resultados/maquina.txt) (máquina virtual em nuvem;
ver no relatório a discussão sobre o ruído das medições).
