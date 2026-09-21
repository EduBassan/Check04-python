def validar_capacidade(capacidade):
    if type(capacidade) is not int or capacidade < 0:
        raise ValueError("A capacidade deve ser um inteiro maior ou igual a zero.")


def validar_itens(regioes):
    identificadores = set()
    for regiao in regioes:
        if not isinstance(regiao, dict):
            raise ValueError("Cada região deve ser representada por um dict.")
        identificador = regiao.get("id")
        if not isinstance(identificador, str) or not identificador:
            raise ValueError("Cada região deve ter um id textual não vazio.")
        if identificador in identificadores:
            raise ValueError("Os ids das regiões não podem se repetir.")
        identificadores.add(identificador)
        if type(regiao.get("demanda")) is not int or regiao["demanda"] <= 0:
            raise ValueError("A demanda deve ser um inteiro positivo.")
        if type(regiao.get("beneficio")) is not int or regiao["beneficio"] < 0:
            raise ValueError("O benefício deve ser um inteiro não negativo.")


def mochila(regioes, capacidade):
    validar_capacidade(capacidade)
    validar_itens(regioes)
    quantidade = len(regioes)
    matriz = [[0] * (capacidade + 1) for _ in range(quantidade + 1)]
    for i in range(1, quantidade + 1):
        regiao = regioes[i - 1]
        demanda = regiao["demanda"]
        beneficio = regiao["beneficio"]
        for c in range(capacidade + 1):
            sem_regiao = matriz[i - 1][c]
            matriz[i][c] = sem_regiao
            if demanda <= c:
                com_regiao = beneficio + matriz[i - 1][c - demanda]
                if com_regiao > sem_regiao:
                    matriz[i][c] = com_regiao

    selecionados = []
    capacidade_restante = capacidade
    for i in range(quantidade, 0, -1):
        if matriz[i][capacidade_restante] != matriz[i - 1][capacidade_restante]:
            regiao = regioes[i - 1]
            selecionados.append(regiao["id"])
            capacidade_restante -= regiao["demanda"]
    selecionados.reverse()
    return {
        "selecionados": selecionados,
        "demanda_total": capacidade - capacidade_restante,
        "beneficio_total": matriz[quantidade][capacidade],
        "matriz": matriz,
    }
