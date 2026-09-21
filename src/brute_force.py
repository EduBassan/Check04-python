from .estruturas import validar_serie

def forca_bruta(valores):
    validar_serie(valores)
    melhor_soma = valores[0]
    melhor_inicio = 0
    melhor_fim = 0
    n = len(valores)

    for inicio in range(n):
        soma = 0
        for fim in range(inicio, n):
            soma += valores[fim]
            if soma > melhor_soma:
                melhor_soma = soma
                melhor_inicio = inicio
                melhor_fim = fim

    return {
        "inicio": melhor_inicio,
        "fim": melhor_fim,
        "soma": melhor_soma,
        "operacoes": n * (n + 1) // 2,
    }
