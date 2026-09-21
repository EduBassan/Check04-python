# Análise de complexidade

## Parâmetros

- `V`: número de vértices, incluindo o centro de distribuição.
- `E`: número de arestas. Uma rua de mão dupla gera duas entradas na lista de adjacência, o que não muda a ordem de complexidade.
- `N`: número de regiões candidatas alcançáveis.
- `C`: capacidade inteira do veículo, em kits.
- `M`: número de registros brutos de energia.
- `H`: número de horários distintos após a agregação.
- `n`: quantidade de horários usada em cada experimento; `n <= H`.
- `k`: quantidade de picos consultados.

Os limites abaixo usam o modelo usual de custo constante para operações com números de tamanho limitado. Não incluem gravação de arquivos ou desenho das figuras no tempo dos algoritmos.

## Questão 1

### Representação do grafo

A lista de adjacência ocupa `O(V + E)`: há uma entrada para cada vértice e uma para cada direção de rua existente. A leitura das conexões e a retirada das vias bloqueadas também custam `O(V + E)`. O conjunto de candidatos é obtido a partir das distâncias do centro; regiões com distância infinita ficam fora dos dois métodos.

### Dijkstra

As arestas dos vértices processados são examinadas para tentar melhorar distâncias. Cada melhora pode inserir uma entrada no heap, e inserções e retiradas custam tempo logarítmico. Como esta implementação mantém entradas antigas até descartá-las, o heap pode guardar `O(E)` entradas.

O limite geral é `O(V + E log(E + 1))`. No grafo simples usado no projeto, `E = O(V²)`, então usamos a forma habitual `O((V + E) log V)`. A validação do grafo é linear e não aumenta esse limite. O espaço auxiliar é `O(V + E)`: distâncias, predecessores e heap.

Reconstruir um trecho segue os predecessores e visita no máximo `V` vértices: `O(V)` de tempo e espaço para a lista retornada.

### Escolha gulosa

Em cada rodada, calculamos as distâncias a partir da posição atual e examinamos as regiões pendentes que ainda cabem. Há no máximo `N` escolhas, uma possível rodada sem escolha e uma busca adicional para o retorno ao centro.

As buscas de caminhos custam, no total, `O(N(V + E) log V)`. As varreduras e remoções na lista de pendentes somam `O(N²)`. Assim, para `N >= 1`:

`T(N,V,E) = O(N(V + E) log V + N²)`.

O trabalho temporário usa `O(V + E + N)`. A função também guarda a sequência, cada trecho percorrido e o caminho completo. Até `N + 1` trechos podem ter `O(V)` vértices cada. Incluindo essa saída, o espaço é `O(V + E + NV)`.

### Programação dinâmica

A tabela tem `(N + 1)` linhas e `(C + 1)` colunas. Cada célula compara no máximo duas possibilidades, em tempo constante. Por isso, o preenchimento custa `O((N + 1)(C + 1))`, normalmente escrito `O(NC)` quando ambos são positivos.

A reconstrução percorre as `N` linhas de trás para frente, adicionando `O(N)` de tempo e até `O(N)` para os ids escolhidos. A matriz inteira é mantida e retornada para visualização e reconstrução, portanto:

`T(N,C) = O((N + 1)(C + 1))` e `S(N,C) = O((N + 1)(C + 1))`.

O algoritmo é **pseudopolinomial**: depende do valor de `C`, e não apenas da quantidade de bits necessária para escrever a capacidade. Uma capacidade muito grande pode inviabilizar a tabela.

Uma tabela com uma linha reduziria o espaço para `O(C)` se só precisássemos do valor ótimo. Escolhemos guardar todas as linhas porque o exercício também exige mostrar a evolução e reconstruir os atendimentos.

### Fluxo completo

Filtrar candidatos exige uma busca a partir do centro. A DP depois otimiza somente o benefício sob capacidade. A ordem de visita aos pontos que ela selecionou é produzida separadamente por uma heurística com Dijkstra.

Portanto, não se deve atribuir o custo da rota à recorrência da mochila, nem dizer que `O(NC)` representa todo o fluxo. Incluindo filtragem, seleção e roteamento, o limite é a soma dessas etapas. Também não se deve afirmar que a DP encontra a menor rota: ela resolve exatamente o modelo da mochila adotado.

## Questão 2

### Organização dos registros

Percorrer os `M` registros constrói dicionários por região e horário e conjuntos de chaves. Inserções e consultas nesses dicionários e conjuntos têm custo médio `O(1)`. A ordenação dos `H` horários custa `O(H log H)`.

A validação da cobertura regional, a agregação dos dados e a montagem das séries percorrem os registros e horários. O heap dos picos é construído por `heapify`, com custo linear em `H`. Assim, a preparação custa `O(M + H log H)` em tempo e `O(M + H)` em espaço.

A consulta de um dicionário encontra uma região ou hora em `O(1)` médio. Percorrer os registros encontrados ainda depende da quantidade de resultados. Selecionar um intervalo de `L` horas produz uma lista em `O(L)` de tempo e espaço.

`consultar_picos` copia o heap para preservar o original. Por isso, a consulta custa `O(H + k log H)` em tempo e `O(H + k)` em espaço. Não seria correto ignorar o custo da cópia.

### Força bruta

Para o primeiro início, testamos `n` finais; para o seguinte, `n - 1`; e assim por diante:

`n + (n - 1) + ... + 1 = n(n + 1)/2`.

Essa é também a contagem exata das somas incrementais registradas. Cada avanço do final adiciona um elemento à soma atual. Não recalculamos o intervalo inteiro. Portanto, `T(n) = O(n²)`.

Guardamos somente índices, soma atual e melhor resposta: `S(n) = O(1)` auxiliar. A série de entrada já existe; incluindo sua armazenagem, o espaço é `O(n)`.

### Dividir e conquistar

O caso-base tem um único elemento e custa `O(1)`. Nas demais chamadas, dividimos o intervalo ao meio, resolvemos as duas metades e procuramos o melhor intervalo que cruza o meio.

O cruzamento varre o lado esquerdo de trás para frente e o direito de frente para trás. As duas varreduras, juntas, visitam todos os elementos daquele subproblema. A combinação das três respostas custa tempo constante.

`T(n) = T(floor(n/2)) + T(ceil(n/2)) + O(n) = O(n log n)`.

Há aproximadamente `log2(n)` níveis, e em cada nível o total de elementos percorridos é `O(n)`. A contagem registrada soma somente as adições das duas varreduras; não pretende contar todas as instruções do processador. Para uma potência de dois, essa contagem é exatamente `n log2(n)`.

Passamos a mesma lista e os índices de suas extremidades. Não fazemos cópias das metades e não guardamos a árvore inteira dentro do algoritmo. A profundidade da recursão é `O(log n)` e cada chamada mantém poucas variáveis e tuplas pequenas. Logo, `S(n) = O(log n)` auxiliar; incluindo a entrada, `O(n)`.

A figura da árvore é gerada separadamente. Ela não faz parte da medição do núcleo do algoritmo.

## Crescimento de 1.000 para 1.000.000 de registros

Neste projeto, cada hora contém quatro registros, um por região. Portanto, 1.000 registros completos correspondem a `n = 250` horas, enquanto 1.000.000 correspondem a `n = 250.000` horas.

A força bruta passaria de **31.375** para **31.250.125.000** intervalos. Dividir e conquistar cresce na ordem de `n log2(n)`: cerca de 2 mil contra 4,48 milhões de passos nessa aproximação. Aumentar a entrada mil vezes multiplica o trabalho quadrático por aproximadamente um milhão; o outro cresce por cerca de 2.250 vezes nessa faixa.

Se cada registro já representasse uma hora agregada, para `n = 1.000.000` a força bruta examinaria **500.000.500.000** intervalos e a escala de dividir e conquistar seria de aproximadamente **19,9 milhões**. Estes são cálculos teóricos, não tempos medidos.

Entre os algoritmos implementados, dividir e conquistar continua sendo a escolha mais viável pelo crescimento muito menor e pela pilha pequena. A leitura e os índices de um milhão de registros ainda exigiriam memória proporcional aos dados. A possibilidade prática de executar depende da máquina e da representação usada; não foi realizado um experimento de um milhão de registros.
