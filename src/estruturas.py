from datetime import datetime, timedelta
import heapq


def validar_serie(valores):
    if not isinstance(valores, (list, tuple)) or len(valores) == 0:
        raise ValueError("A série deve ser uma lista ou tupla não vazia.")
    if any(type(valor) is not int for valor in valores):
        raise ValueError("A criticidade deve conter apenas números inteiros.")


def criticidade(registro):
    return (
        (registro["consumo"] - registro["capacidade_disponivel"])
        * registro["prioridade"]
        * registro["custo"]
    )


def organizar_registros(registros):
    if not isinstance(registros, list) or not registros:
        raise ValueError("Os registros devem formar uma lista não vazia.")
    por_regiao = {}
    por_horario = {}
    regioes = set()
    chaves = set()
    obrigatorios = {"timestamp", "regiao", "consumo", "capacidade_disponivel", "prioridade", "custo"}

    for registro in registros:
        if not isinstance(registro, dict) or not obrigatorios.issubset(registro):
            raise ValueError("Registro sem todos os campos obrigatórios.")
        horario = registro["timestamp"]
        try:
            data = datetime.fromisoformat(horario)
        except (TypeError, ValueError):
            raise ValueError("Timestamp inválido; use data e hora no formato ISO.") from None
        if data.tzinfo is not None or data.minute or data.second or data.microsecond:
            raise ValueError("Use horários inteiros, sem fuso, na mesma referência temporal.")
        horario = data.isoformat(timespec="minutes")
        regiao = registro["regiao"]
        if not isinstance(regiao, str) or not regiao.strip():
            raise ValueError("A região precisa ter um nome.")
        for campo in ("consumo", "capacidade_disponivel", "prioridade", "custo"):
            minimo = 1 if campo in ("prioridade", "custo") else 0
            if type(registro[campo]) is not int or registro[campo] < minimo:
                raise ValueError(f"Valor inválido em {campo}.")
        chave = (horario, regiao)
        if chave in chaves:
            raise ValueError("Medição duplicada para a mesma hora e região.")
        chaves.add(chave)
        regioes.add(regiao)
        por_regiao.setdefault(regiao, []).append(registro)
        por_horario.setdefault(horario, []).append(registro)

    horarios = sorted(por_horario)
    for anterior, atual in zip(horarios, horarios[1:]):
        if datetime.fromisoformat(atual) - datetime.fromisoformat(anterior) != timedelta(hours=1):
            raise ValueError("A série contém uma lacuna; as horas devem ser consecutivas.")
    if any({r["regiao"] for r in por_horario[h]} != regioes for h in horarios):
        raise ValueError("Todas as horas precisam conter as mesmas regiões.")

    consumos = []
    capacidades = []
    criticidades = []
    for horario in horarios:
        linhas = por_horario[horario]
        consumos.append(sum(r["consumo"] for r in linhas))
        capacidades.append(sum(r["capacidade_disponivel"] for r in linhas))
        criticidades.append(sum(criticidade(r) for r in linhas))

    picos = [(-consumo, horario) for consumo, horario in zip(consumos, horarios)]
    heapq.heapify(picos)
    return {
        "por_regiao": por_regiao,
        "por_horario": por_horario,
        "regioes": regioes,
        "chaves": chaves,
        "horarios": horarios,
        "consumos": consumos,
        "capacidades": capacidades,
        "criticidades": criticidades,
        "picos": picos,
    }


def consultar_picos(estruturas, quantidade=5):
    if type(quantidade) is not int or quantidade < 0:
        raise ValueError("A quantidade de picos deve ser um inteiro não negativo.")
    heap = estruturas["picos"].copy()
    resultado = []
    for _ in range(min(quantidade, len(heap))):
        consumo_negativo, horario = heapq.heappop(heap)
        resultado.append({"timestamp": horario, "consumo": -consumo_negativo})
    return resultado


def selecionar_intervalo(estruturas, inicio, fim):
    n = len(estruturas["horarios"])
    if type(inicio) is not int or type(fim) is not int or not 0 <= inicio <= fim < n:
        raise ValueError("Intervalo fora dos limites da série.")
    return [
        (estruturas["horarios"][i], estruturas["criticidades"][i])
        for i in range(inicio, fim + 1)
    ]
