import argparse
from pathlib import Path

from config import REPETICOES, SEED

def main():
    parser = argparse.ArgumentParser(description="Checkpoint 4 - Algoritmos")
    parser.add_argument("--questao", choices=["1", "2", "todas"], default="todas")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--repeticoes", type=int, default=REPETICOES)
    argumentos = parser.parse_args()
    if argumentos.repeticoes < 1:
        parser.error("O número de repetições precisa ser pelo menos 1.")

    raiz = Path(__file__).resolve().parent
    if argumentos.questao in ("1", "todas"):
        from src.logistica import executar_questao1
        executar_questao1(raiz, seed=argumentos.seed)
        print("Questão 1 concluída. Veja results/questao1.json e figures/questao1/.")
    if argumentos.questao in ("2", "todas"):
        from src.energia import executar_questao2
        executar_questao2(raiz, seed=argumentos.seed,
                         repeticoes=argumentos.repeticoes)
        print("Questão 2 concluída. Veja results/questao2.json e figures/questao2/.")
    print("Seed utilizada:", argumentos.seed)


if __name__ == "__main__":
    main()
