from .estruturas import validar_serie


def escolher_melhor(a, b):
    if a[0] != b[0]:
        return a if a[0] > b[0] else b
    if a[1] != b[1]:
        return a if a[1] < b[1] else b
    return a if a[2] <= b[2] else b


def _resolver(valores, esquerda, direita):
    if esquerda == direita:
        return (valores[esquerda], esquerda, direita), 0

    meio = (esquerda + direita) // 2
    melhor_esquerda, op_esquerda = _resolver(valores, esquerda, meio)
    melhor_direita, op_direita = _resolver(valores, meio + 1, direita)

    soma = 0
    soma_esquerda = None
    inicio_cruzado = meio
    for i in range(meio, esquerda - 1, -1):
        soma += valores[i]
        if soma_esquerda is None or soma >= soma_esquerda:
            soma_esquerda = soma
            inicio_cruzado = i

    soma = 0
    soma_direita = None
    fim_cruzado = meio + 1
    for j in range(meio + 1, direita + 1):
        soma += valores[j]
        if soma_direita is None or soma > soma_direita:
            soma_direita = soma
            fim_cruzado = j

    cruzado = (soma_esquerda + soma_direita, inicio_cruzado, fim_cruzado)
    melhor = escolher_melhor(escolher_melhor(melhor_esquerda, melhor_direita), cruzado)
    operacoes = op_esquerda + op_direita + (direita - esquerda + 1)
    return melhor, operacoes


def dividir_conquistar(valores):
    validar_serie(valores)
    melhor, operacoes = _resolver(valores, 0, len(valores) - 1)
    return {
        "inicio": melhor[1],
        "fim": melhor[2],
        "soma": melhor[0],
        "operacoes": operacoes,
    }
