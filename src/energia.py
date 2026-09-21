import csv
from datetime import datetime, timedelta
import gc
import json
import math
from pathlib import Path

from config import SEED, REPETICOES
import platform
import random
import statistics
from time import perf_counter
import tracemalloc

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .brute_force import forca_bruta
from .divide_conquer import dividir_conquistar, _resolver
from .estruturas import organizar_registros, consultar_picos, selecionar_intervalo


def gerar_registros(seed=SEED, horas=5000):
    if type(seed) is not int or type(horas) is not int or horas <= 0:
        raise ValueError("Seed deve ser inteira e horas deve ser um inteiro positivo.")
    rng = random.Random(seed)
    inicio = datetime(2026, 1, 1)
    regioes = [("Norte", 900, 3, 65), ("Nordeste", 1100, 5, 90),
               ("Sudeste", 1600, 4, 75), ("Sul", 1000, 2, 55)]
    registros = []
    for h in range(horas):
        data = inicio + timedelta(hours=h)
        ciclo = int(130 * math.sin(2 * math.pi * (data.hour - 7) / 24))
        renovavel = max(0, int(70 * math.sin(math.pi * (data.hour - 6) / 12)))
        acrescimo = 150 if 1000 <= h < 1250 else 0
        if 3200 <= h < 3500:
            acrescimo = 220
        for regiao, base, prioridade, custo in regioes:
            consumo = base - 80 + ciclo + acrescimo + rng.randint(-35, 35)
            registros.append({
                "timestamp": data.isoformat(timespec="minutes"),
                "regiao": regiao,
                "consumo": max(0, consumo),
                "capacidade_disponivel": base + renovavel,
                "prioridade": prioridade,
                "custo": custo,
            })
    return registros


def salvar_dados(registros, caminho):
    campos = ["timestamp", "regiao", "consumo", "capacidade_disponivel", "prioridade", "custo"]
    with Path(caminho).open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(registros)


def ler_dados(caminho):
    with Path(caminho).open(encoding="utf-8", newline="") as arquivo:
        registros = list(csv.DictReader(arquivo))
    for registro in registros:
        for campo in ("consumo", "capacidade_disponivel", "prioridade", "custo"):
            registro[campo] = int(registro[campo])
    return registros


def _medir_memoria(funcao, valores):
    gc.collect()
    tracemalloc.start()
    memoria_inicial = tracemalloc.get_traced_memory()[0]
    tracemalloc.reset_peak()
    try:
        funcao(valores)
        pico = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    return max(0, pico - memoria_inicial)


def medir_escalabilidade(valores, repeticoes=REPETICOES):
    if type(repeticoes) is not int or repeticoes < 1:
        raise ValueError("Informe pelo menos uma repetição.")
    tamanhos = [100, 250, 500, 1000, 2000, 5000]
    linhas = []
    for n in tamanhos:
        if n > len(valores):
            continue
        entrada = valores[:n]
        resultados = []
        for nome, funcao in (("Força bruta", forca_bruta), ("Dividir e conquistar", dividir_conquistar)):
            funcao(entrada)
            tempos = []
            for _ in range(repeticoes):
                inicio = perf_counter()
                resultado = funcao(entrada)
                tempos.append(perf_counter() - inicio)
            memoria = _medir_memoria(funcao, entrada)
            linhas.append({
                "n_horas": n,
                "registros_brutos": 4 * n,
                "algoritmo": nome,
                "repeticoes": repeticoes,
                "tempo_medio_s": statistics.mean(tempos),
                "desvio_padrao_s": statistics.stdev(tempos) if repeticoes > 1 else 0.0,
                "operacoes": resultado["operacoes"],
                "pico_memoria_bytes": memoria,
                "inicio": resultado["inicio"],
                "fim": resultado["fim"],
                "soma": resultado["soma"],
                "tempos_s": tempos,
            })
            resultados.append((resultado["soma"], resultado["inicio"], resultado["fim"]))
        if resultados[0] != resultados[1]:
            raise AssertionError(f"Os algoritmos discordaram para n={n}.")
    return linhas


def figura_serie(estruturas, resultado, caminho):
    datas = [datetime.fromisoformat(h) for h in estruturas["horarios"]]
    a = datas[resultado["inicio"]]
    b = datas[resultado["fim"]] + timedelta(hours=1)
    fig, eixos = plt.subplots(2, 1, figsize=(12, 7.2), sharex=True,
                             gridspec_kw={"height_ratios": [2, 1]})
    eixos[0].plot(datas, estruturas["consumos"], color="#155e75", lw=0.65, label="Consumo total")
    eixos[0].plot(datas, estruturas["capacidades"], color="#6b7280", lw=0.6, alpha=0.8,
                  label="Capacidade total")
    eixos[0].set_ylabel("Energia por hora (kWh)")
    eixos[0].legend(loc="upper left", ncol=2)
    eixos[1].plot(datas, estruturas["criticidades"], color="#7c3aed", lw=0.6)
    eixos[1].axhline(0, color="#64748b", lw=0.8)
    eixos[1].set_ylabel("Criticidade ponderada")
    for eixo in eixos:
        eixo.axvspan(a, b, color="#fb923c", alpha=0.25)
        eixo.grid(alpha=0.15)
    eixos[1].xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    eixos[1].set_xlabel("Tempo — ano de 2026; uma observação por hora, somando as 4 regiões")
    duracao = resultado["fim"] - resultado["inicio"] + 1
    fig.suptitle("Intervalo contínuo de maior criticidade acumulada", fontsize=16, fontweight="bold")
    eixos[0].set_title(f"Faixa laranja: {a:%d/%m %Hh} a {datas[resultado['fim']]:%d/%m %Hh} · "
                       f"{duracao} horas · soma {resultado['soma']:,}".replace(",", "."), fontsize=11)
    fig.tight_layout()
    fig.savefig(caminho, dpi=170, facecolor="white")
    plt.close(fig)


def figura_arvore(valores, horarios, caminho):
    fig, eixo = plt.subplots(figsize=(13, 6.5))
    eixo.set_xlim(0, 1)
    eixo.set_ylim(0, 1)
    eixo.axis("off")

    def desenhar(esquerda, direita, nivel, x, largura, pai=None):
        y = 0.84 - nivel * 0.29
        if pai:
            eixo.annotate("", xy=(x, y + 0.07), xytext=(pai[0], pai[1] - 0.08),
                          arrowprops={"arrowstyle": "->", "color": "#94a3b8", "lw": 1.5})
        melhor, _ = _resolver(valores, esquerda, direita)
        rotulo = (f"h{esquerda} a h{direita} | {direita - esquerda + 1} horas\n"
                  f"Melhor: h{melhor[1]}–h{melhor[2]}\nSoma = {melhor[0]:,}").replace(",", ".")
        eixo.text(x, y, rotulo, ha="center", va="center", fontsize=10,
                  bbox={"boxstyle": "round,pad=0.6", "facecolor": "#e0f2fe" if nivel == 0 else "#f1f5f9",
                        "edgecolor": "#0284c7"})
        if nivel < 2:
            meio = (esquerda + direita) // 2
            desenhar(esquerda, meio, nivel + 1, x - largura, largura / 2, (x, y))
            desenhar(meio + 1, direita, nivel + 1, x + largura, largura / 2, (x, y))

    desenhar(0, len(valores) - 1, 0, 0.5, 0.25)
    eixo.set_title("Dividir e conquistar — três níveis da entrada real", fontsize=16,
                   fontweight="bold", pad=20)
    eixo.text(0.5, 0.045,
              f"h0 = {horarios[0]} | h{len(valores)-1} = {horarios[-1]}\n"
              "Em cada nó: melhor da esquerda × melhor da direita × melhor intervalo que cruza o meio.",
              ha="center", va="center", fontsize=10, color="#475569")
    fig.tight_layout()
    fig.savefig(caminho, dpi=170, facecolor="white")
    plt.close(fig)


def figura_escalabilidade(linhas, caminho):
    fig, eixo = plt.subplots(figsize=(10.5, 6.5))
    for nome, cor in (("Força bruta", "#ea580c"), ("Dividir e conquistar", "#2563eb")):
        serie = [linha for linha in linhas if linha["algoritmo"] == nome]
        eixo.plot([l["n_horas"] for l in serie], [l["tempo_medio_s"] * 1000 for l in serie],
                   marker="o", color=cor, label=nome, lw=2)
    eixo.set_xscale("log")
    eixo.set_yscale("log")
    eixo.set_xticks([100, 250, 500, 1000, 2000, 5000])
    eixo.set_xticklabels(["100", "250", "500", "1.000", "2.000", "5.000"])
    eixo.set_xlabel("Tamanho da entrada n — horas agregadas (4n registros brutos)")
    eixo.set_ylabel("Tempo médio (ms) — escala logarítmica")
    eixo.set_title("Escalabilidade medida: força bruta × dividir e conquistar", fontsize=15, fontweight="bold")
    eixo.grid(which="both", alpha=0.15)
    eixo.legend()
    repeticoes = linhas[0]["repeticoes"]
    fig.text(0.5, 0.02, f"Média de {repeticoes} execuções por ponto; dados e gráficos fora do cronômetro. "
                        "Memória medida separadamente.", ha="center", fontsize=9, color="#475569")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(caminho, dpi=170, facecolor="white")
    plt.close(fig)


def _operacoes_dc(n):
    altura = (n - 1).bit_length()
    return n * (altura + 1) - 2 ** altura


def executar_questao2(raiz, seed=SEED, repeticoes=REPETICOES):
    raiz = Path(raiz)
    for pasta in ("data", "figures/questao2", "results"):
        (raiz / pasta).mkdir(parents=True, exist_ok=True)
    registros = gerar_registros(seed)
    salvar_dados(registros, raiz / "data/problema2.csv")
    estruturas = organizar_registros(registros)
    valores = estruturas["criticidades"]
    resultado_bf = forca_bruta(valores)
    resultado_dc = dividir_conquistar(valores)
    if any(resultado_bf[k] != resultado_dc[k] for k in ("inicio", "fim", "soma")):
        raise AssertionError("Os algoritmos deveriam encontrar o mesmo intervalo.")
    linhas = medir_escalabilidade(valores, repeticoes)
    campos = [k for k in linhas[0] if k != "tempos_s"]
    with (raiz / "results/escalabilidade.csv").open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)

    consultas = {
        "consumo_acumulado_por_regiao_kwh": {
            regiao: sum(r["consumo"] for r in estruturas["por_regiao"][regiao])
            for regiao in sorted(estruturas["regioes"])
        },
        "consumo_primeiro_horario_kwh": estruturas["consumos"][0],
        "registros_primeiro_horario": estruturas["por_horario"][estruturas["horarios"][0]],
        "cinco_maiores_picos": consultar_picos(estruturas),
        "tres_primeiras_horas_intervalo_critico": selecionar_intervalo(
            estruturas, resultado_dc["inicio"], min(resultado_dc["inicio"] + 2, resultado_dc["fim"]))
    }
    resultados = {
        "seed": seed,
        "registros_brutos": len(registros),
        "horas_agregadas": len(valores),
        "regioes": sorted(estruturas["regioes"]),
        "periodo": {"inicio": estruturas["horarios"][0], "fim": estruturas["horarios"][-1]},
        "formula": "soma_regioes((consumo - capacidade_disponivel) * prioridade * custo_centavos)",
        "horas_positivas": sum(v > 0 for v in valores),
        "horas_negativas": sum(v < 0 for v in valores),
        "horas_neutras": sum(v == 0 for v in valores),
        "forca_bruta": resultado_bf,
        "dividir_conquistar": resultado_dc,
        "intervalo": {
            "inicio": estruturas["horarios"][resultado_dc["inicio"]],
            "fim": estruturas["horarios"][resultado_dc["fim"]],
            "duracao_horas": resultado_dc["fim"] - resultado_dc["inicio"] + 1,
        },
        "consultas": consultas,
        "escalabilidade": linhas,
        "ambiente": {"python": platform.python_version(), "sistema": platform.system(),
                     "arquitetura": platform.machine(), "timer": "time.perf_counter",
                     "memoria": "pico adicional Python (bytes), tracemalloc; entrada excluída"},
        "projecao_registros": {
            "observacao": "Contagens teóricas, não execuções de um milhão de registros; quatro regiões fixas.",
            "1000_registros": {"n_horas": 250, "somas_bf": 250 * 251 // 2,
                               "somas_dc": _operacoes_dc(250)},
            "1000000_registros": {"n_horas": 250000, "somas_bf": 250000 * 250001 // 2,
                                  "somas_dc": _operacoes_dc(250000)},
        },
    }
    with (raiz / "results/questao2.json").open("w", encoding="utf-8") as arquivo:
        json.dump(resultados, arquivo, ensure_ascii=False, indent=2)
    figura_serie(estruturas, resultado_dc, raiz / "figures/questao2/01_serie_temporal.png")
    figura_arvore(valores, estruturas["horarios"], raiz / "figures/questao2/02_arvore_divisao.png")
    figura_escalabilidade(linhas, raiz / "figures/questao2/03_escalabilidade.png")
    return resultados
