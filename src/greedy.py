import heapq
import math

from src.dynamic_programming import validar_capacidade, validar_itens

def validar_grafo(grafo):
    if not isinstance(grafo, dict) or not grafo:
        raise ValueError("O grafo deve ser um dict não vazio.")
    for origem, vizinhos in grafo.items():
        if not isinstance(origem, str):
            raise ValueError("Os vértices devem ter ids textuais.")
        for destino, peso in vizinhos:
            if destino not in grafo:
                raise ValueError("Toda aresta deve apontar para um vértice existente.")
            if isinstance(peso, bool) or not isinstance(peso, (int, float)):
                raise ValueError("O peso da aresta deve ser numérico.")
            if not math.isfinite(peso) or peso < 0:
                raise ValueError("Dijkstra não aceita peso negativo ou não finito.")


def dijkstra(grafo, origem):
    validar_grafo(grafo)
    if origem not in grafo:
        raise ValueError("A origem não está no grafo.")
    distancias = {vertice: math.inf for vertice in grafo}
    anteriores = {vertice: None for vertice in grafo}
    distancias[origem] = 0.0
    fila = [(0.0, origem)]
    while fila:
        distancia_atual, atual = heapq.heappop(fila)
        if distancia_atual != distancias[atual]:
            continue
        for vizinho, peso in grafo[atual]:
            nova_distancia = distancia_atual + peso
            if nova_distancia < distancias[vizinho]:
                distancias[vizinho] = nova_distancia
                anteriores[vizinho] = atual
                heapq.heappush(fila, (nova_distancia, vizinho))
    return distancias, anteriores


def reconstruir_caminho(anteriores, origem, destino):
    if origem not in anteriores or destino not in anteriores:
        raise ValueError("Origem e destino precisam estar nos predecessores.")
    caminho = []
    visitados = set()
    atual = destino
    while atual is not None:
        if atual in visitados:
            raise ValueError("Predecessores inválidos: ciclo encontrado.")
        visitados.add(atual)
        caminho.append(atual)
        if atual == origem:
            return caminho[::-1]
        atual = anteriores.get(atual)
    return []


def pontuacao(regiao, distancia):
    return regiao["prioridade"] * regiao["beneficio"] / (
        regiao["demanda"] * (1 + distancia)
    )


def selecionar_guloso(regioes, grafo, capacidade, centro="CD", retornar=True):
    validar_capacidade(capacidade)
    validar_itens(regioes)
    validar_grafo(grafo)
    if centro not in grafo:
        raise ValueError("O centro de distribuição não está no grafo.")
    for regiao in regioes:
        if regiao["id"] not in grafo or regiao["id"] == centro:
            raise ValueError("Cada região deve ser um vértice diferente do centro.")
        if type(regiao.get("prioridade")) is not int or regiao["prioridade"] <= 0:
            raise ValueError("A prioridade deve ser um inteiro positivo.")

    pendentes = list(regioes)
    restante = capacidade
    atual = centro
    sequencia = []
    caminho_fisico = [centro]
    etapas = []
    beneficio = 0
    distancia_total = 0.0
    while pendentes:
        distancias, anteriores = dijkstra(grafo, atual)
        melhor = None
        melhor_chave = None
        for regiao in pendentes:
            distancia = distancias[regiao["id"]]
            if regiao["demanda"] > restante or not math.isfinite(distancia):
                continue
            chave = (-pontuacao(regiao, distancia), regiao["id"])
            if melhor_chave is None or chave < melhor_chave:
                melhor, melhor_chave = regiao, chave
        if melhor is None:
            break
        destino = melhor["id"]
        trecho = reconstruir_caminho(anteriores, atual, destino)
        caminho_fisico.extend(trecho[1:])
        etapas.append({
            "origem": atual, "destino": destino,
            "distancia_km": distancias[destino],
            "pontuacao": pontuacao(melhor, distancias[destino]),
            "trecho": trecho,
        })
        distancia_total += distancias[destino]
        sequencia.append(destino)
        restante -= melhor["demanda"]
        beneficio += melhor["beneficio"]
        pendentes.remove(melhor)
        atual = destino
    if retornar and atual != centro:
        distancias, anteriores = dijkstra(grafo, atual)
        if not math.isfinite(distancias[centro]):
            raise ValueError("Não há caminho para retornar ao centro.")
        trecho = reconstruir_caminho(anteriores, atual, centro)
        caminho_fisico.extend(trecho[1:])
        distancia_total += distancias[centro]
    return {
        "selecionados": sequencia,
        "demanda_total": capacidade - restante,
        "beneficio_total": beneficio,
        "caminho_fisico": caminho_fisico,
        "distancia_total_km": round(distancia_total, 6),
        "etapas": etapas,
    }
