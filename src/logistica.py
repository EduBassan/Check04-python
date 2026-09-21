import csv
import json
import math
import random
import time
from pathlib import Path

from config import SEED

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from src.dynamic_programming import mochila, validar_capacidade
from src.greedy import dijkstra, selecionar_guloso


CAPACIDADE_PADRAO = 80


def gerar_dados(seed=SEED):
    if type(seed) is not int:
        raise ValueError("A seed deve ser inteira.")
    sorteio = random.Random(seed)
    pontos = [{"id": "CD", "tipo": "centro", "x": 0.0, "y": 1.5,
               "pessoas": 0, "prioridade": 0, "demanda": 0, "beneficio": 0}]
    for linha in range(4):
        for coluna in range(1, 6):
            pessoas = sorteio.randint(35, 250)
            prioridade = sorteio.randint(1, 5)
            pontos.append({
                "id": f"P{linha * 5 + coluna:02d}", "tipo": "regiao",
                "x": coluna + round(sorteio.uniform(-0.08, 0.08), 2),
                "y": linha + round(sorteio.uniform(-0.08, 0.08), 2),
                "pessoas": pessoas, "prioridade": prioridade,
                "demanda": sorteio.randint(5, 16),
                "beneficio": pessoas + 25 * prioridade,
            })
    pares = set()
    for linha in range(4):
        for coluna in range(1, 6):
            indice = linha * 5 + coluna
            if coluna < 5:
                pares.add((f"P{indice:02d}", f"P{indice + 1:02d}"))
            if linha < 3:
                pares.add((f"P{indice:02d}", f"P{indice + 5:02d}"))
    for indice in (1, 6, 11, 16):
        pares.add(("CD", f"P{indice:02d}"))
    for indice in (1, 3, 4, 6, 8, 9, 11, 13, 14):
        pares.add((f"P{indice:02d}", f"P{indice + 6:02d}"))
    por_id = {ponto["id"]: ponto for ponto in pontos}
    conexoes = []
    for origem, destino in sorted(pares):
        a, b = por_id[origem], por_id[destino]
        distancia = math.hypot(a["x"] - b["x"], a["y"] - b["y"])
        peso = round(distancia * sorteio.uniform(1.0, 1.6), 1)
        bloqueada = "P20" in (origem, destino) or (origem, destino) in {
            ("P07", "P08"), ("P12", "P17")
        }
        conexoes.append({"origem": origem, "destino": destino,
                         "distancia_km": peso, "bloqueada": bloqueada})
    return pontos, conexoes


def construir_grafo(pontos, conexoes):
    grafo = {ponto["id"]: [] for ponto in pontos}
    if len(grafo) != len(pontos):
        raise ValueError("Existem ids de pontos repetidos.")
    existentes = set()
    for conexao in conexoes:
        origem, destino = conexao["origem"], conexao["destino"]
        peso = conexao["distancia_km"]
        if origem not in grafo or destino not in grafo or origem == destino:
            raise ValueError("Conexão inválida: confira os vértices.")
        if isinstance(peso, bool) or not isinstance(peso, (int, float)):
            raise ValueError("A distância deve ser numérica.")
        if not math.isfinite(peso) or peso < 0:
            raise ValueError("A distância deve ser finita e não negativa.")
        if type(conexao["bloqueada"]) is not bool:
            raise ValueError("O campo bloqueada deve ser booleano.")
        chave = tuple(sorted((origem, destino)))
        if chave in existentes:
            raise ValueError("Uma conexão não pode aparecer duas vezes.")
        existentes.add(chave)
        if not conexao["bloqueada"]:
            grafo[origem].append((destino, peso))
            grafo[destino].append((origem, peso))
    return grafo


def salvar_csv(caminho, linhas):
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({chave: int(valor) if type(valor) is bool else valor
                               for chave, valor in linha.items()})


def casos_pequenos():
    regioes = [
        {"id": "A", "demanda": 4, "beneficio": 7, "prioridade": 1},
        {"id": "B", "demanda": 3, "beneficio": 5, "prioridade": 1},
        {"id": "C", "demanda": 3, "beneficio": 5, "prioridade": 1},
    ]
    grafo = {identificador: [] for identificador in ["CD", "A", "B", "C"]}
    ids = list(grafo)
    for i, origem in enumerate(ids):
        for destino in ids[i + 1:]:
            grafo[origem].append((destino, 1))
            grafo[destino].append((origem, 1))
    resultados = []
    for capacidade in (4, 6):
        guloso = selecionar_guloso(regioes, grafo, capacidade)
        dinamico = mochila(regioes, capacidade)
        resultados.append({
            "capacidade": capacidade, "regioes": regioes,
            "todas_distancias_km": 1,
            "guloso": guloso,
            "dp": {chave: valor for chave, valor in dinamico.items() if chave != "matriz"},
        })
    return resultados


def desenhar_rede(eixo, pontos, conexoes, atendidos=None, caminho=None, pesos=False):
    por_id = {ponto["id"]: ponto for ponto in pontos}
    atendidos = set(atendidos or [])
    for conexao in conexoes:
        origem, destino = por_id[conexao["origem"]], por_id[conexao["destino"]]
        bloqueada = conexao["bloqueada"]
        eixo.plot([origem["x"], destino["x"]], [origem["y"], destino["y"]],
                  color="#cc4250" if bloqueada else "#bac3cd",
                  linestyle="--" if bloqueada else "-", linewidth=1.2, zorder=1)
        if pesos:
            eixo.text((origem["x"] + destino["x"]) / 2,
                      (origem["y"] + destino["y"]) / 2,
                      f'{conexao["distancia_km"]:.1f}', fontsize=8, ha="center",
                      color="#b12636" if bloqueada else "#32445a",
                      bbox={"facecolor": "white", "alpha": .8, "edgecolor": "none", "pad": .4})
    for origem, destino in zip(caminho or [], (caminho or [])[1:]):
        a, b = por_id[origem], por_id[destino]
        eixo.annotate("", (b["x"], b["y"]), (a["x"], a["y"]),
                      arrowprops={"arrowstyle": "->", "color": "#3667c8", "lw": 1.7,
                                  "shrinkA": 13, "shrinkB": 13}, zorder=2)
    for ponto in pontos:
        centro = ponto["id"] == "CD"
        cor = "#6954c8" if centro else "#35a16b" if ponto["id"] in atendidos else "#e2e7ed"
        eixo.scatter(ponto["x"], ponto["y"], s=560 if centro else 380,
                     marker="*" if centro else "o", c=cor, edgecolor="#3f4e60", zorder=3)
        eixo.text(ponto["x"], ponto["y"] - .20, ponto["id"], ha="center",
                  fontsize=9, fontweight="bold", color="#152b44", zorder=4)
    eixo.set(xlim=(-.5, 5.5), ylim=(-.55, 3.55))
    eixo.set_aspect("equal")
    eixo.axis("off")


def gerar_figuras(pasta, pontos, conexoes, candidatos, guloso, dp, rota_dp, capacidade):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, eixo = plt.subplots(figsize=(12, 8))
    desenhar_rede(eixo, pontos, conexoes, pesos=True)
    eixo.set_title(f"Rede de emergência: {len(pontos)} vértices e {len(conexoes)} conexões", fontsize=17, pad=20)
    legenda = [
        Line2D([0], [0], color="#bac3cd", label="Via disponível; rótulo = km"),
        Line2D([0], [0], color="#cc4250", linestyle="--", label="Via bloqueada"),
        Line2D([0], [0], marker="*", color="white", markerfacecolor="#6954c8", markersize=15,
               label="CD: centro de distribuição"),
    ]
    eixo.legend(handles=legenda, loc="lower center", bbox_to_anchor=(.5, -0.1), ncol=3)
    fig.text(.5, .055, "P20 permanece sem acesso: todas as vias incidentes estão bloqueadas.\n"
             "Posições são esquemáticas; o trajeto usa os pesos das vias disponíveis.",
             ha="center", fontsize=10)
    fig.subplots_adjust(bottom=.18, top=.89)
    fig.savefig(pasta / "01_grafo.png", dpi=170, bbox_inches="tight")
    plt.close(fig)

    fig, eixos = plt.subplots(1, 2, figsize=(16, 7))
    for eixo, nome, resultado, rota in [
        (eixos[0], "Guloso", guloso, guloso), (eixos[1], "Mochila por DP", dp, rota_dp)
    ]:
        desenhar_rede(eixo, pontos, conexoes, resultado["selecionados"], rota["caminho_fisico"])
        eixo.set_title(f'{nome}: benefício {resultado["beneficio_total"]}\n'
                       f'{resultado["demanda_total"]}/{capacidade} kits | '
                       f'{rota["distancia_total_km"]:.1f} km com retorno', fontsize=13)
        sequencia = " → ".join(rota["selecionados"])
        partes = [sequencia[i:i + 54] for i in range(0, len(sequencia), 54)]
        eixo.text(.5, -.08, "Entregas: " + "\n".join(partes), transform=eixo.transAxes,
                  ha="center", va="top", fontsize=9)
    fig.suptitle("Mesmos candidatos, mesma capacidade; seleção e percurso", fontsize=17)
    fig.text(.5, .035, "Verde = atendido; cinza = não atendido; azul = trajeto pelas vias.\n"
             "Passar por uma região não significa entregar. A sequência da seleção DP usa a mesma heurística, sem garantia de rota ótima.",
             ha="center", fontsize=10)
    fig.subplots_adjust(bottom=.24, top=.86, wspace=.06)
    fig.savefig(pasta / "02_solucoes.png", dpi=170, bbox_inches="tight")
    plt.close(fig)

    fig, eixos = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={"width_ratios": [1.2, 1]})
    mapa = eixos[0].imshow(dp["matriz"], origin="lower", aspect="auto", cmap="viridis")
    fig.colorbar(mapa, ax=eixos[0], label="Maior benefício acumulado", fraction=.04, pad=.03)
    eixos[0].set(xlabel="Capacidade disponível c (kits)", ylabel="Quantidade de regiões consideradas i",
                 title="DP[i][c] e reconstrução da solução")
    eixos[0].set_yticks(range(0, len(candidatos) + 1, 2))
    c = capacidade
    xs, ys = [c], [len(candidatos)]
    for i in range(len(candidatos), 0, -1):
        if dp["matriz"][i][c] != dp["matriz"][i - 1][c]:
            c -= candidatos[i - 1]["demanda"]
        xs.append(c)
        ys.append(i - 1)
    eixos[0].plot(xs, ys, "w.-", markersize=4, linewidth=1, label="Caminho da reconstrução")
    eixos[0].legend(loc="upper left", fontsize=8)
    eixos[1].step(range(capacidade + 1), dp["matriz"][-1], where="post",
                  color="#3667c8", linewidth=2, label="Benefício ótimo por capacidade")
    eixos[1].scatter([capacidade], [guloso["beneficio_total"]], marker="x", s=100,
                     color="#cc4250", label=f"Guloso em C={capacidade}", zorder=4)
    eixos[1].set(xlabel="Capacidade disponível (kits)", ylabel="Benefício total",
                 title="Última linha da matriz DP")
    eixos[1].grid(alpha=.2)
    eixos[1].legend(loc="upper left", fontsize=9)
    fig.suptitle("Evolução da mochila 0/1: combinar pode superar a decisão local", fontsize=16)
    fig.text(.5, .03, "Base: zero regiões ou zero kits → benefício 0. Cada linha decide incluir ou excluir uma região.\n"
             "A linha branca volta do estado final até a base; deslocamentos para a esquerda indicam regiões incluídas.",
             ha="center", fontsize=10)
    fig.subplots_adjust(bottom=.2, top=.85, wspace=.3)
    fig.savefig(pasta / "03_programacao_dinamica.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def executar_questao1(raiz, seed=SEED, capacidade=CAPACIDADE_PADRAO):
    raiz = Path(raiz)
    validar_capacidade(capacidade)
    for subpasta in ("data", "results", "figures/questao1"):
        (raiz / subpasta).mkdir(parents=True, exist_ok=True)
    pontos, conexoes = gerar_dados(seed)
    salvar_csv(raiz / "data/problema1.csv", pontos)
    salvar_csv(raiz / "data/conexoes.csv", conexoes)
    grafo = construir_grafo(pontos, conexoes)
    distancias, _ = dijkstra(grafo, "CD")
    candidatos = [ponto for ponto in pontos if ponto["tipo"] == "regiao"
                  and math.isfinite(distancias[ponto["id"]])]
    inicio = time.perf_counter()
    guloso = selecionar_guloso(candidatos, grafo, capacidade)
    tempo_guloso = time.perf_counter() - inicio
    inicio = time.perf_counter()
    dp = mochila(candidatos, capacidade)
    tempo_dp = time.perf_counter() - inicio
    selecionados = set(dp["selecionados"])
    regioes_dp = [regiao for regiao in candidatos if regiao["id"] in selecionados]
    rota_dp = selecionar_guloso(regioes_dp, grafo, capacidade)
    dados = {
        "seed": seed, "capacidade": capacidade,
        "formula_gulosa": "prioridade * beneficio / (demanda * (1 + distancia_km))",
        "modelo": "Demanda inteira em kits equivalentes; atendimento integral; mochila 0/1; uma carga, sem reposição; distância não limita a seleção.",
        "beneficio_sintetico": "pessoas + 25 * prioridade (pontos de utilidade, não pessoas atendidas)",
        "numero_vertices": len(pontos), "numero_conexoes": len(conexoes),
        "vias_bloqueadas": sum(c["bloqueada"] for c in conexoes),
        "numero_candidatos": len(candidatos),
        "regioes": pontos, "candidatos": [p["id"] for p in candidatos],
        "inacessiveis": [p["id"] for p in pontos if not math.isfinite(distancias[p["id"]])],
        "distancias_do_centro_km": {chave: valor if math.isfinite(valor) else None
                                     for chave, valor in distancias.items()},
        "guloso": guloso,
        "dp": {chave: valor for chave, valor in dp.items() if chave != "matriz"},
        "rota_dp": rota_dp,
        "diferenca_beneficio": dp["beneficio_total"] - guloso["beneficio_total"],
        "tempos_segundos_uma_execucao": {"guloso_com_rota": tempo_guloso,
                                         "mochila_dp_sem_rota": tempo_dp},
        "escopo_tempos": "Tempos ilustrativos de uma execução. Guloso inclui Dijkstra e percurso; DP mede somente seleção. Não são comparação isolada entre seletores.",
        "celulas_dp": (len(candidatos) + 1) * (capacidade + 1),
        "casos_controlados": casos_pequenos(),
    }
    gerar_figuras(raiz / "figures/questao1", pontos, conexoes, candidatos,
                  guloso, dp, rota_dp, capacidade)
    with (raiz / "results/questao1.json").open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2, allow_nan=False)
        arquivo.write("\n")
    return dados
