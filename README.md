# Checkpoint 4 - Algoritmos e Estruturas de Dados

**Curso:** Engenharia de Software - 2º ano  
**Disciplina:** Dynamic Programming - FIAP  
**Turma:** W  
**Data do enunciado:** 21/09/2026

## Integrantes e identificação

| Nome completo | RA       |
| ------------- | -------- |
| Eduardo       | RM561474 |
| João Abe      | RM561446 |

**Número do grupo: 4.** A seed utilizada é **4**, definida em `config.py`, igual ao número do grupo.

## 1. Problemas e modelos adotados

### Questão 1 - Logística de emergência

Representamos as ruas por um grafo ponderado e não direcionado. Há **20 regiões e um centro**, **44 conexões**, das quais **5 estão bloqueadas**. As 39 vias disponíveis entram na lista de adjacência. O grafo é esparso, sem todas as ligações possíveis. P20 fica inacessível e é excluído igualmente dos dois métodos, deixando **19 candidatos**.

Cada região possui pessoas afetadas, prioridade de 1 a 5, demanda inteira e benefício. Um kit representa uma unidade equivalente de carga com uma composição fixa de suprimentos. O benefício sintético é `pessoas + 25 * prioridade`, em pontos de utilidade. Benefício não representa diretamente quantidade de pessoas atendidas. A demanda varia de 5 a 16 kits. A capacidade padrão é **80 kits**.

Há uma única carga e atendimento integral: ou a região recebe toda a demanda, ou não é atendida. Não há recarga durante a rota. A distância influencia a ordem gulosa, mas não é uma restrição da mochila. Assim, o ótimo calculado pela DP é o **maior benefício sob capacidade entre os locais alcançáveis**, sem garantir a menor rota.

As distâncias em quilômetros são geradas a partir das posições dos pontos, com um fator de percurso sorteado. As posições servem para desenhar a rede; os caminhos usam os pesos das ruas disponíveis. O retorno ao centro está incluído nos percursos.

### Questão 2 - Consumo de energia

Geramos **20.000 registros**, correspondentes a **quatro regiões por hora durante 5.000 horas**, a partir de 01/01/2026. Todos os registros têm timestamp, região, consumo em kWh, capacidade disponível em kWh, prioridade e custo em centavos/kWh.

O consumo combina uma base regional, uma oscilação diária senoidal, ruído inteiro entre -35 e 35 e dois períodos de pressão adicional: horas 1.000 a 1.249 e 3.200 a 3.499. A capacidade tem um acréscimo diurno que representa geração renovável de forma simplificada. Os dados são sintéticos e não representam medições do sistema elétrico brasileiro.

Definimos, para cada registro:

```text
criticidade = (consumo - capacidade_disponivel) * prioridade * custo
```

Somamos a criticidade das quatro regiões de cada timestamp antes da busca. Excesso gera pontuação positiva; sobra gera pontuação negativa. Isso permite localizar um período de pressão acumulada sem tornar a série inteira automaticamente a resposta. A pontuação é didática, não uma tarifa ou métrica oficial.

O intervalo é contínuo e não vazio. Índices começam em zero e as duas pontas são inclusivas. Os dois algoritmos usam o mesmo desempate: maior soma, depois menor início e menor fim. Não permitimos horas ausentes, duplicatas ou cobertura regional incompleta.

## 2. Estruturas de dados e suas vantagens

| Estrutura | Uso concreto                                                          | Por que ajuda                                                                                       |
| --------- | --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `dict`    | Grafo por id; distâncias; índices por região e horário                | Consultar uma chave custa O(1) em média; evita procurar sempre em todos os registros.               |
| `list`    | Vizinhos, candidatos, série ordenada e linhas da DP                   | Acesso por índice O(1) e varredura sequencial; representa naturalmente a ordem temporal e a tabela. |
| `tuple`   | Aresta `(vizinho, peso)`, entrada do heap e chave `(horário, região)` | Agrupa campos relacionados; a chave imutável pode ser armazenada em um conjunto.                    |
| `set`     | Detecção de ids e medições duplicados; conjunto de regiões            | Verificação de existência em O(1) médio, sem varrer a lista toda.                                   |
| `heapq`   | Próximo vértice do Dijkstra e consulta dos maiores picos              | Retira o menor elemento em O(log n); os consumos são negados para obter os maiores picos.           |

O índice de picos é copiado para preservar o original. Por isso, consultar `k` picos custa `O(H + k log H)`, incluindo a cópia, para `H` horários. As consultas por região, por horário, por pico e por intervalo são calculadas na execução e salvas em `results/questao2.json`. O notebook 2 também imprime exemplos por região e de picos.

## 3. Algoritmos da questão 1

### Dijkstra e escolha gulosa

Dijkstra foi implementado manualmente com uma fila de prioridade. Começa com distância zero para a origem e infinita para os demais vértices. Ao retirar um vértice do heap, tenta melhorar as distâncias dos vizinhos. O dicionário de predecessores permite reconstruir cada trecho. Vias bloqueadas não entram no grafo percorrido.

A cada parada, o guloso recalcula a seguinte pontuação para os locais acessíveis que ainda cabem na carga:

```text
escore = prioridade * beneficio / (demanda * (1 + distancia_km))
```

O numerador favorece urgência e ganho. O denominador penaliza uso de carga e deslocamento. O `1` é uma referência de 1 km que evita divisão por zero. A maior pontuação é localmente vantajosa segundo essa regra, mas ela não compara combinações futuras. Empates são resolvidos pelo menor id.

### Programação dinâmica: mochila 0/1

1. **Estado:** `DP[i][c]` é o maior benefício usando as primeiras `i` regiões e até `c` kits.
2. **Decisão:** atender ou não atender a região atual.
3. **Caso-base:** `DP[0][c] = 0` e `DP[i][0] = 0`, pois as demandas são positivas.
4. **Recorrência:** se a região não cabe, copiamos a linha anterior; se cabe, comparamos as duas alternativas abaixo.
5. **Reconstrução:** partimos de `DP[N][C]` e voltamos pelas linhas. Se o valor difere da linha anterior, a região foi incluída, e descontamos sua demanda. Em empate, mantemos a solução anterior.

```text
Se demanda_i > c:
    DP[i][c] = DP[i-1][c]
Senão:
    DP[i][c] = max(DP[i-1][c], beneficio_i + DP[i-1][c-demanda_i])
```

Consultar a linha anterior impede que a mesma região seja escolhida mais de uma vez. Depois da seleção ótima, a mesma heurística gulosa organiza as paradas apenas entre os locais escolhidos. Como a soma das demandas deles cabe na capacidade, todos são atendidos.

### Contraexemplo e caso ótimo

| Região | Demanda | Benefício | Prioridade | Distância inicial | Escore   |
| ------ | ------- | --------- | ---------- | ----------------- | -------- |
| A      | 4       | 7         | 1          | 1 km              | 0,875    |
| B      | 3       | 5         | 1          | 1 km              | 0,833... |
| C      | 3       | 5         | 1          | 1 km              | 0,833... |

Todas as distâncias no exemplo pequeno são 1 km. **Com capacidade 4**, A é a melhor opção: guloso e DP valem 7. **Com capacidade 6**, o guloso escolhe A e sobram 2 kits; B e C não cabem. A DP escolhe B+C, usa 6 kits e vale 10. Enumerar os oito subconjuntos comprova o ótimo desse contraexemplo.

## 4. Algoritmos da questão 2

**Força bruta:** um laço escolhe o início e outro avança o fim. A cada avanço, adicionamos um valor à soma atual. Examinamos todos os `n(n+1)/2` intervalos, sem recalcular uma soma desde o começo.

**Dividir e conquistar:** o caso-base contém um elemento. Dividimos o problema pelo índice do meio, resolvemos a metade esquerda e a direita, calculamos o melhor intervalo que cruza o meio e escolhemos a melhor das três respostas.

Para o cruzamento, buscamos o melhor sufixo que termina no meio e o melhor prefixo que começa depois dele. Qualquer intervalo que atravessa a divisão contém esses dois tipos de trecho. Passamos índices, sem copiar as metades da lista.

Exemplo: em `[4, -6, 3, 5, -2]`, o melhor intervalo é `[3, 5]`, índices 2 a 3, soma 8. Para uma série toda negativa, escolhemos o maior elemento, pois intervalo vazio não é permitido.

## 5. Como executar

Use Python 3.10 ou superior. A execução entregue foi feita com Python 3.12.14 e Matplotlib 3.10.8. No terminal, entre na pasta `checkpoint4` e execute:

```bash
python -m venv .venv
```

Ative o ambiente no Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Ou no Linux/macOS:

```bash
source .venv/bin/activate
```

Depois instale e execute:

```bash
python -m pip install -r requirements.txt
python main.py
python -m unittest discover -s tests -v
python -m notebook
```

Abra `notebooks/questao1.ipynb` e `notebooks/questao2.ipynb` e execute as células de cima para baixo. Eles recriam dados, resultados e figuras e já contêm saídas da execução entregue. A medição de memória é separada da de tempo e pode levar mais alguns segundos.

Para rodar uma questão ou usar outra seed:

```bash
python main.py --questao 1 --seed 4
python main.py --questao 2 --seed 4 --repeticoes 3
```

Também é possível alterar `SEED` e `REPETICOES` em `config.py`. Para mudar a capacidade da questão 1, altere `CAPACIDADE_PADRAO` em `src/logistica.py` ou o argumento `capacidade` no notebook 1. A mesma seed reproduz os dados e respostas; os tempos podem variar.

Os comandos recriam os CSVs a partir da seed. Para experimentar uma alteração manual, modifique os objetos retornados pelos geradores no notebook antes de chamar os algoritmos. O notebook pode também usar `ler_dados` para carregar o CSV de energia editado. Alterações de entrada exigem atualização dos resultados citados neste README e nos notebooks.

## 6. Resultados obtidos com seed 4

### Logística

| Método                | Benefício | Kits usados / capacidade | Regiões atendidas | Percurso com retorno |
| --------------------- | --------- | ------------------------ | ----------------- | -------------------- |
| Guloso                | 2.487     | 80 / 80                  | 10                | 28,5 km              |
| DP + ordem heurística | 2.569     | 80 / 80                  | 10                | 31,8 km              |

A DP ganhou **82 pontos de benefício, aproximadamente 3,30%**. Ela escolheu P01, P03, P04, P05, P07, P09, P10, P11, P15 e P19. O percurso ficou maior porque distância não faz parte do objetivo da mochila. Isso mostra uma limitação do modelo, não um erro do resultado ótimo.

As sequências de entrega e todos os vértices percorridos estão no JSON. Passar por uma região durante um trecho não significa que houve uma entrega nela. A comparação exigida entre métodos é de benefício sob a mesma capacidade. Os tempos ilustrativos de Q1 têm escopos diferentes, descritos no JSON, e não sustentam uma conclusão de velocidade entre os seletores.

### Energia e escalabilidade

Ambos encontraram os índices **3.200 a 3.499**, de **14/05/2026 às 08h a 26/05/2026 às 19h**, com **300 horas** e soma **38.328.640**.

| n, em horas | Registros brutos | Força bruta (ms) | Dividir e conquistar (ms) | Somas BF   | Somas DC |
| ----------- | ---------------- | ---------------- | ------------------------- | ---------- | -------- |
| 100         | 400              | 0,153            | 0,070                     | 5.050      | 672      |
| 250         | 1.000            | 0,995            | 0,190                     | 31.375     | 1.994    |
| 500         | 2.000            | 4,806            | 0,424                     | 125.250    | 4.488    |
| 1.000       | 4.000            | 19,040           | 0,999                     | 500.500    | 9.976    |
| 2.000       | 8.000            | 71,546           | 2,011                     | 2.001.000  | 21.952   |
| 5.000       | 20.000           | 454,590          | 6,490                     | 12.502.500 | 61.808   |

São médias de **três execuções após aquecimento**, em Linux x86_64. Leitura, geração e figuras ficam fora do cronômetro. Os tempos individuais, desvios e picos de memória estão nos arquivos de resultados. As operações contam as somas incrementais dos intervalos na força bruta e as somas nas varreduras do cruzamento em DC; não são uma contagem de todas as instruções.

Em 5.000 horas, dividir e conquistar foi aproximadamente **70,0 vezes mais rápido nesta medição**. O pico extra rastreado pelo `tracemalloc` foi de **492 bytes** na força bruta e **2.960 bytes** em DC. A entrada já existia antes do rastreio: esses números não representam toda a memória do processo, nem os dados e gráficos.

De 1.000 para 2.000 horas, a força bruta passou de 19,04 para 71,55 ms; as somas passaram de 500.500 para 2.001.000, aproximadamente quatro vezes mais, como previsto por O(n²). DC passou de 1,00 para 2,01 ms, com crescimento de 9.976 para 21.952 somas. A tendência é compatível com O(n log n). Resultados pequenos sofrem mais influência do custo fixo e das oscilações da máquina.

## 7. Figuras

| Arquivo                                        | O que explica                                                    |
| ---------------------------------------------- | ---------------------------------------------------------------- |
| `figures/questao1/01_grafo.png`                | Centro, regiões, pesos e vias bloqueadas.                        |
| `figures/questao1/02_solucoes.png`             | Atendidos, não atendidos e percurso dos dois métodos.            |
| `figures/questao1/03_programacao_dinamica.png` | Tabela, reconstrução e evolução do benefício por capacidade.     |
| `figures/questao2/01_serie_temporal.png`       | Consumo, capacidade e criticidade, com o intervalo em destaque.  |
| `figures/questao2/02_arvore_divisao.png`       | Três níveis da divisão dos 5.000 horários realmente processados. |
| `figures/questao2/03_escalabilidade.png`       | Crescimento dos tempos dos dois algoritmos.                      |

## 8. Complexidade e crescimento dos dados

| Parte                         | Tempo                | Espaço auxiliar ou saída                |
| ----------------------------- | -------------------- | --------------------------------------- |
| Grafo por adjacência          | O(V+E) para montar   | O(V+E)                                  |
| Dijkstra, neste grafo simples | O((V+E) log V)       | O(V+E) com heap de entradas antigas     |
| Guloso, com caminhos          | O(N(V+E) log V + N²) | O(V+E+NV), incluindo trechos retornados |
| Mochila DP                    | O(NC)                | O(NC) para matriz e reconstrução        |
| Força bruta                   | O(n²)                | O(1), sem contar entrada                |
| Dividir e conquistar          | O(n log n)           | O(log n), sem contar entrada            |

`V` é o número de vértices, `E` o de arestas, `N` o de regiões candidatas, `C` a capacidade e `n` a quantidade de horas. A matriz DP mantém `(N+1)(C+1)` células, sendo 1.620 nesta execução. Seu custo é pseudopolinomial: uma capacidade numericamente enorme exige uma tabela enorme.

A força bruta tem dois laços, totalizando `n(n+1)/2` intervalos. Em DC, `T(n)=2T(n/2)+O(n)`: há O(log n) níveis e O(n) de trabalho total por nível. Como as chamadas passam índices, a pilha ocupa O(log n).

**De 1.000 para 1.000.000 de registros:** com quatro regiões, passamos de 250 para 250.000 horas. A força bruta passa de 31.375 para **31.250.125.000 intervalos**. A escala de DC é de aproximadamente **4,48 milhões** em `n log2(n)` no tamanho maior. Entre as duas soluções, DC permanece a mais viável, preservando o resultado exato com crescimento muito menor. Essa é uma projeção teórica, não uma medição com um milhão de registros. O armazenamento dos dados ainda cresce linearmente.

As demonstrações completas, incluindo preparação e consultas, estão em [docs/analise_complexidade.md](docs/analise_complexidade.md).

## 9. Testes, organização e limitações

**30 testes passaram** com `unittest`. Eles verificam caminhos e bloqueios, capacidade zero, entradas inválidas, reconstrução, contraexemplo, agregação temporal, duplicatas, lacunas, todos os valores negativos, zeros e empates. A mochila é comparada com enumeração exaustiva em 40 instâncias pequenas. Os algoritmos de energia são comparados com um oráculo independente em 360 séries aleatórias pequenas.

As oito células Python dos dois notebooks foram executadas sequencialmente, com as saídas salvas. O formato é Jupyter; a interface gráfica do Jupyter não foi usada nesta validação. A execução pelo terminal e as mesmas funções usadas pelos notebooks foram verificadas.

O código usa funções pequenas e estruturas básicas. Não foram criadas classes sem necessidade. O núcleo dos algoritmos foi implementado em Python; `matplotlib` apenas desenha, `csv` lê/grava arquivos e `unittest` verifica respostas. Não usamos bibliotecas prontas de otimização ou caminhos mínimos.

Os principais diretórios são `src/` para código, `data/` para entradas, `results/` para medições, `figures/` para imagens, `notebooks/` para execução comentada, `tests/` para testes e `docs/` para explicações.

Limitações: kits são padronizados, não há múltiplos veículos nem estoque separado por produto, distâncias não limitam a mochila e não otimizamos a rota completa. A prioridade influencia também o benefício sintético, mas não é uma exigência de atendimento obrigatório. Em energia, agregamos regiões e permitimos que a sobra de uma compense parte da pressão de outra na pontuação; não modelamos restrições de transmissão. Não há previsão de demanda, apenas análise dos dados existentes.

## Pergunta final obrigatória

**Qual foi a decisão algorítmica mais importante, e qual alternativa foi descartada?**

A decisão mais importante foi usar programação dinâmica para selecionar os atendimentos dentro da capacidade do veículo. Consideramos usar apenas a regra gulosa para essa seleção, mas ela decide uma região por vez e pode perder combinações melhores.

Na nossa execução com capacidade de 80 kits, o guloso alcançou 2.487 pontos de benefício, enquanto a DP alcançou 2.569: um ganho de 82 pontos. No contraexemplo de capacidade 6, o guloso escolheu A e obteve 7, mas B+C cabia e valia 10. Esses resultados mostram por que a escolha local não basta para garantir o maior benefício.

A DP exige tempo e memória O(NC). Para 19 candidatos e capacidade 80, a tabela tem 1.620 células, um tamanho pequeno para este projeto. Guardamos a tabela completa para reconstruir os atendimentos e explicar a evolução da solução. Uma tabela de uma linha usaria menos memória, mas exigiria outro cuidado para reconstruir as escolhas.

Mantivemos a heurística gulosa para organizar as paradas depois da seleção. Essa decisão separa os objetivos: a DP garante o melhor benefício no modelo adotado, enquanto a rota continua sendo aproximada. O percurso de 31,8 km da solução da DP, contra 28,5 km do guloso, também mostra que maximizar benefício não equivale a minimizar distância.
