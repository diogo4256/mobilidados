# Estudo de viabilidade e análise custo-benefício: Rua Ricardo Jorge

Gerado por `mobilidados run` a partir das tabelas em `tables/` e da configuração do caso (`[appraisal]`). Cada valor diz de onde vem e com que grau: **M** medido · **D** documento oficial · **I** inferido · **P** pressuposto · **NE** não encontrado. Método em docs/appraisal.md.

## Resumo

- Nos troços com estacionamento dos dois lados (117,5 m), a largura livre mediana é de 4,90 m; dois autocarros lado a lado precisam de pelo menos 5,00 m só com a carroçaria (5,80 m com espelhos).
- Nos dias úteis, às 17h–19h, a diferença entre o tempo dos autocarros no troço entre paragens e o que os troços vizinhos explicariam foi de +49% (intervalo de 90%: +34% a +65%), cerca de 14 s por passagem (6 a 24 s), segundo posições GPS arquivadas por terceiros (por ano: 2025: +60%; 2026: +4%, não confirmado: o intervalo inclui 0, com muito menos registos).
- Contando só o tempo dos autocarros na ponta da tarde, nenhuma opção de retirar estacionamento compensa os lugares que retira: a de menor perda é a H (VAL de −9 300 €, benefício/custo 0,60, probabilidade de VAL > 0 de 5%).
- Para a opção H compensar, seria preciso, por exemplo, um excesso de 24,1 s por passagem (medido: 14,5 s, até 23,9 s); ou que um lugar valesse no máximo 200 € por ano a quem o perde (central: 560 €).
- A alternativa P (prioridade nos estreitamentos com os sinais B5 e B6, sem retirar estacionamento) custa cerca de 1 800 € e paga-se com 0,9 s poupados por passagem na ponta: é a medida que menos arrisca, e pode experimentar-se primeiro.
- O que mais mudaria estas conclusões: os dados de localização da própria Carris (o atraso atual, que o arquivo de 2026 já não mostra), a ocupação dos lugares nas ruas vizinhas, e uma contagem do atraso de quem segue de carro atrás de um autocarro parado.

## O problema

Nos troços com estacionamento dos dois lados (117,5 m), a largura livre mediana é de 4,90 m; dois autocarros lado a lado precisam de pelo menos 5,00 m só com a carroçaria (5,80 m com espelhos). Sem o estacionamento de um lado, a mediana passaria a 6,91 m. Nos dias úteis, às 17h–19h, a diferença entre o tempo dos autocarros no troço entre paragens e o que os troços vizinhos explicariam foi de +49% (intervalo de 90%: +34% a +65%), cerca de 14 s por passagem (6 a 24 s), segundo posições GPS arquivadas por terceiros (por ano: 2025: +60%; 2026: +4%, não confirmado: o intervalo inclui 0, com muito menos registos).

Esse excesso não está só nos troços estreitos: 5,7 s estão dentro deles e 8,1 s nos cruzamentos entre eles. No cruzamento 76,2–95,2 m, os autocarros têm um autocarro em sentido contrário na rua em 26% das vezes, contra 11% por acaso (p = 1,5 × 10⁻⁶): esperam ali que o troço seguinte fique livre. Por isso se conta como removível, no valor central, o excesso dos troços estreitos e desse cruzamento (72% do total).

## As opções

Cada opção retira o estacionamento de um dos lados nos troços indicados, sempre ou só a certas horas. A situação de referência é não fazer nada.

| opção | descrição | metros | lugares | quando |
| --- | --- | ---: | ---: | --- |
| B | Um lado, sempre, nos três troços com estacionamento dos dois lados | 117,5 | 21 | sempre |
| C | Um lado, sempre, só no troço B2 (o mais longo) | 54,0 | 10 | sempre |
| E | Um lado, das 7h às 20h nos dias úteis, nos três troços | 117,5 | 21 | dias úteis, 7h–20h |
| G | Um lado, das 16h às 20h nos dias úteis, nos três troços | 117,5 | 21 | dias úteis, 16h–20h |
| H | Um lado, das 16h às 20h nos dias úteis, só no troço B2 | 54,0 | 10 | dias úteis, 16h–20h |

Opções consideradas e não avaliadas:

- Sentido único para o trânsito geral, mantendo os autocarros nos dois sentidos: exige uma via BUS em contrassentido que não cabe em 4,90 m com estacionamento dos dois lados, e mudaria o trânsito das ruas vizinhas; fica fora deste estudo, que não tem modelo de tráfego.
- Desviar uma das carreiras: passa o problema para outra rua e tira paragens a quem as usa; é uma decisão de rede da Carris, fora deste estudo.
- Mais fiscalização do estacionamento: os carros estão em lugares marcados, por isso fiscalizar não alarga a faixa livre.

## Viabilidade

| dimensão | verificação | resultado | grau | fonte |
| --- | --- | --- | --- | --- |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a dois autocarros, só carroçaria | 6,91 m / 5,00 m: cumpre | I | without_parking.csv, width_budget.csv |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a dois autocarros, com espelhos | 6,91 m / 5,80 m: cumpre | I | without_parking.csv, width_budget.csv |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a Lisboa: o Desenho da Rua – Manual de espaço público, p. 152 | 6,91 m / 6,80 m: cumpre | D | standards_comparison.csv |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a Schriftliche Anfrage Drucksache 19/25490, Antwort vom 27.03.2026, p. 3 | 6,91 m / 6,50 m: cumpre | D | standards_comparison.csv |
| social | Lugares retirados face ao estacionamento cartografado a menos de 150 m | 2,5% a 3,0% | I | cartografia municipal: cerca de 779 lugares cartografados (área ÷ profundidade da faixa ÷ comprimento de um lugar); a ocupação não é conhecida |
| social | Lugares retirados face ao estacionamento cartografado a menos de 300 m | 0,9% a 1,1% | I | cartografia municipal: cerca de 2207 lugares cartografados (área ÷ profundidade da faixa ÷ comprimento de um lugar); a ocupação não é conhecida |
| legal | Numa faixa de rodagem estreitada por obras ou obstáculos ocasionais, salvo se houver circulação alternada, a largura deixada à circulação não pode ser inferior a 5,8 m onde circulem automóveis pesados. A regra é para obras e obstáculos, não para estacionamento; mas a largura livre medida, 4,90 m, fica abaixo dela, e a circulação alternada é o que os sinais B5 e B6 organizam. |  | D | Regulamento de Sinalização do Trânsito (Decreto Regulamentar n.º 22-A/98), art. 87.º, n.º 4 |
| legal | O sinal B5 obriga a ceder a passagem a quem vem em sentido contrário num estreitamento; o B6 dá prioridade sobre quem vem em sentido contrário. |  | D | Regulamento de Sinalização do Trânsito (Decreto Regulamentar n.º 22-A/98), sinais de cedência de passagem |
| legal | Compete à Câmara Municipal deliberar sobre o estacionamento de veículos nas vias públicas. |  | D | Lei n.º 75/2013, anexo I, art. 33.º, n.º 1, alínea rr) |
| legal | Uma proibição de estacionar sinaliza-se com o sinal C15; uma proibição por horas e dias, com um painel adicional do modelo n.º 7d (dias da semana e horas do dia). |  | D | Regulamento de Sinalização do Trânsito (Decreto Regulamentar n.º 22-A/98), sinais de proibição e painéis adicionais |
| operacional | A Carris registou em 2024 1 365 interrupções por estacionamento indevido, com 983 horas de impacto, e diz trabalhar com a Câmara em medidas na rede viária para cumprir horários. |  | D | Carris, Relatório e Contas 2024, p. 26–27 |
| social | O plano da EMEL para 2026-2029 prevê 11 parques novos (3 115 lugares), nenhum em Alvalade; a Junta de Freguesia pede um parque subterrâneo junto à Av. da Igreja para os moradores. |  | D | EMEL, Plano de Atividades e Orçamento 2026-2029, quadro 3-1; Junta de Freguesia de Alvalade, Plano de Atividades 2022 |

## Análise custo-benefício

Análise económica incremental de cada opção face a não fazer nada, segundo o *Economic Appraisal Vademecum 2021-2027* da Comissão Europeia: preços constantes de 2025, 10 anos, taxa social de desconto de 5% (e 3% / 7% como teste). Só se monetiza o tempo dos autocarros na ponta da tarde que cada opção pode remover; os custos são o valor dos lugares retirados, a obra e, numa proibição por horas, a fiscalização. Benefício e custo do estacionamento escalam com o cumprimento: um carro que fica bloqueia o autocarro e guarda o lugar.

### Valores usados

| valor | mínimo | central | máximo | unidade | grau | fonte |
| --- | ---: | ---: | ---: | --- | --- | --- |
| Valor do tempo de um passageiro | 3,88 | 6,00 | 7,76 | €/h | I | Eurostat lc_lci_lev, Portugal 2025: 19,40 €/h de custo da mão de obra; EAV 2021-2027, p. 55: deslocações pendulares a 25–40 % e outras a 20–35 % desse valor; na ponta da tarde admite-se uma maioria de regressos a casa (P) |
| Peso do tempo de atraso face ao tempo a bordo | 1,00 | 1,50 | 2,50 |  | P | EAV 2021-2027, quadro 7: tempo em congestionamento 1,5; atraso no transporte público 2,5–4, este para atrasos imprevistos; o atraso medido repete-se todos os dias úteis, por isso o valor central é o do congestionamento |
| Passageiros a bordo, na ponta da tarde | 13,10 | 20,00 | 30,00 | passageiros | P | Carris, Relatório e Contas 2024, p. 14 e 26–27: taxa de ocupação dos autocarros 19,58 % × 2 270 milhões de lugares·km ÷ 33,969 milhões de veículos·km = 13,1 passageiros em média no dia; a Carris não publica a ocupação por carreira nem por hora, e na ponta admite-se mais |
| Multiplicador para quem espera nas paragens seguintes | 1,00 | 1,00 | 1,50 |  | P | Quem espera mais adiante também perde o atraso; não se conta no valor central |
| Custo de uma hora de autocarro parado | 0,00 | 34,60 | 55,50 | €/h | I | Carris, Relatório e Contas 2024: gastos com o pessoal 94,07 M€ ÷ 2,718 milhões de veículos·hora = 34,6 €/h; todos os gastos operacionais (150,93 M€) dariam 55,5 €/h; 0 se o atraso não alterar horários nem turnos |
| Ocupação dos lugares retirados | 0,85 | 0,95 | 1,00 |  | P | A ocupação das ruas vizinhas não foi encontrada (NE); a Junta de Freguesia (Plano de Atividades 2022) pede um parque subterrâneo junto à Av. da Igreja para as necessidades dos moradores, e a EMEL (Plano 2026-2029) aponta a pressão dos dísticos de residente |
| Custo anual, para quem perde o lugar, de estacionar noutro sítio | 325,00 | 555,60 | 2 100,00 | €/ano | I | Mínimo: mais 10 min a pé por dia, ao valor do tempo de lazer (5,34 €/h). Central: avença R24 da EMEL para residentes, 46,30 €/mês (DN, citando a EMEL). Máximo: lugar de garagem arrendado em Alvalade, cerca de 175 €/mês (anúncios Imovirtual, 150–200 €/mês) |
| Opção E: parte do valor do lugar perdida das 7h às 20h nos dias úteis | 0,40 | 0,55 | 0,75 |  | I | Avenças da EMEL e Telpark: noturna (18h–10h e fins de semana) 22 €/mês contra 46,30 €/mês por 24 h, donde (46,30 − 22) ÷ 46,30 = 0,52 do valor está no dia útil |
| Opção G: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,25 | 0,45 | 0,70 |  | P | Quem deixa o carro durante o dia tem de o tirar antes das 16h, e quem chega entre as 16h e as 20h não pode estacionar desse lado: são as horas de chegada a casa; sem dados de uso dos lugares, é um pressuposto, e o valor de inversão diz quanto pode valer |
| Cumprimento de uma proibição permanente | 0,80 | 0,90 | 1,00 |  | P | Pressuposto; a Carris registou 1 365 interrupções por estacionamento indevido em 2024 (Relatório e Contas 2024, p. 26) |
| Cumprimento de uma proibição por horas | 0,60 | 0,80 | 0,95 |  | P | Pressuposto; uma proibição por horas pede fiscalização às horas certas |
| Sinal vertical colocado (C15, com painel adicional se houver horário) | 150,00 | 300,00 | 600,00 | € | P | Pressuposto: não se encontrou um preço unitário público em Portugal; a obra pesa pouco no resultado (appraisal_tornado.csv) |
| Marcação no pavimento, por metro | 2,00 | 5,00 | 15,00 | €/m | P | Pressuposto, como o anterior; metade é repintada a cada 5 anos |
| Fiscalização a mais de uma proibição por horas | 0,00 | 1 000,00 | 5 000,00 | €/ano | P | Pressuposto; 0 se couber nas rondas da EMEL e da Polícia Municipal |
| Comprimento de um lugar | 5,00 | 5,50 | 6,00 | m | P | Como no registo de factos (profiles.parking_space_m) |

| medido nas tabelas do caso | mínimo | central | máximo |
| --- | ---: | ---: | ---: |
| Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 5,60 | 14,50 | 23,90 |
| Opção B: parte do excesso que pode remover | 0,41 | 0,72 | 1,00 |
| Opção C: parte do excesso que pode remover | 0,28 | 0,59 | 0,87 |
| Opção E: parte do excesso que pode remover | 0,41 | 0,72 | 1,00 |
| Opção G: parte do excesso que pode remover | 0,41 | 0,72 | 1,00 |
| Opção H: parte do excesso que pode remover | 0,28 | 0,59 | 0,87 |
| Autocarros na rua na ponta, por dia útil (horário) | 18,00 | 18,00 | 18,00 |
| Dias úteis por ano (sem feriados) | 251,00 | 251,00 | 251,00 |
| Opção B: metros de estacionamento retirados | 117,50 | 117,50 | 117,50 |
| Opção C: metros de estacionamento retirados | 54,00 | 54,00 | 54,00 |
| Opção E: metros de estacionamento retirados | 117,50 | 117,50 | 117,50 |
| Opção G: metros de estacionamento retirados | 117,50 | 117,50 | 117,50 |
| Opção H: metros de estacionamento retirados | 54,00 | 54,00 | 54,00 |

### Resultados

| opção | benefício/ano | estacionamento e fiscalização/ano | obra | VAL (10 anos, 5%) | benefício/custo | VAL a 3% | VAL a 7% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B | 2 500 € | 10 100 € | 1 800 € | −61 100 € | 0,24 | −67 300 € | −55 700 € |
| C | 2 100 € | 4 700 € | 870 € | −21 100 € | 0,43 | −23 300 € | −19 300 € |
| E | 2 200 € | 6 000 € | 2 400 € | −31 500 € | 0,35 | −34 600 € | −28 900 € |
| G | 2 200 € | 5 100 € | 2 400 € | −24 600 € | 0,41 | −26 900 € | −22 500 € |
| H | 1 800 € | 2 900 € | 1 200 € | −9 300 € | 0,60 | −10 200 € | −8 600 € |

### Incerteza

Simulação de Monte Carlo com 20 000 sorteios de todos os valores (distribuições triangulares, semente fixa); os mesmos sorteios servem todas as opções.

| opção | VAL P10 | VAL mediano | VAL P90 | probabilidade de VAL > 0 | probabilidade de ser a melhor |
| --- | ---: | ---: | ---: | ---: | ---: |
| B | −197 300 € | −105 800 € | −49 000 € | 0% | 0% |
| C | −82 900 € | −40 200 € | −12 500 € | 2% | 16% |
| E | −109 900 € | −60 800 € | −28 200 € | 0% | 0% |
| G | −92 300 € | −49 300 € | −20 500 € | 1% | 0% |
| H | −46 900 € | −24 400 € | −5 300 € | 5% | 84% |

### O que teria de mudar

Para cada opção, o valor de cada entrada que poria o VAL a zero, mantendo as outras no valor central (— : nenhum valor possível o faz).

| opção | entrada | valor central | valor de inversão | dentro do intervalo testado? |
| --- | --- | ---: | ---: | --- |
| B | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 60,00 | ✗ |
| B | Opção B: parte do excesso que pode remover | 0,72 | — | ✗ |
| B | Passageiros a bordo, na ponta da tarde | 20,00 | 94,82 | ✗ |
| B | Ocupação dos lugares retirados | 0,95 | 0,21 | ✗ |
| B | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 122,45 | ✗ |
| C | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 33,75 | ✗ |
| C | Opção C: parte do excesso que pode remover | 0,59 | — | ✗ |
| C | Passageiros a bordo, na ponta da tarde | 20,00 | 51,65 | ✗ |
| C | Ocupação dos lugares retirados | 0,95 | 0,39 | ✗ |
| C | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 229,42 | ✗ |
| E | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 40,91 | ✗ |
| E | Opção E: parte do excesso que pode remover | 0,72 | — | ✗ |
| E | Passageiros a bordo, na ponta da tarde | 20,00 | 63,43 | ✗ |
| E | Ocupação dos lugares retirados | 0,95 | 0,17 | ✗ |
| E | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 98,42 | ✗ |
| E | Opção E: parte do valor do lugar perdida das 7h às 20h nos dias úteis | 0,55 | 0,10 | ✗ |
| E | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |
| G | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 35,08 | ✗ |
| G | Opção G: parte do excesso que pode remover | 0,72 | — | ✗ |
| G | Passageiros a bordo, na ponta da tarde | 20,00 | 53,84 | ✗ |
| G | Ocupação dos lugares retirados | 0,95 | 0,21 | ✗ |
| G | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 120,29 | ✗ |
| G | Opção G: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,10 | ✗ |
| G | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |
| H | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 24,05 | ✗ |
| H | Opção H: parte do excesso que pode remover | 0,59 | 0,97 | ✗ |
| H | Passageiros a bordo, na ponta da tarde | 20,00 | 35,71 | ✗ |
| H | Ocupação dos lugares retirados | 0,95 | 0,33 | ✗ |
| H | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 195,90 | ✗ |
| H | Opção G: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,16 | ✗ |
| H | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |

Entradas que mais mudam o VAL da opção H (do mínimo ao máximo de cada uma):

| entrada | VAL no mínimo | VAL no máximo |
| --- | ---: | ---: |
| Custo anual, para quem perde o lugar, de estacionar noutro sítio | −3 300 € | −49 400 € |
| Fiscalização a mais de uma proibição por horas | −1 600 € | −40 200 € |
| Excesso de tempo por passagem na ponta (s, intervalo de 90%) | −18 000 € | −150 € |
| Opção G: parte do valor do lugar perdida das 16h às 20h nos dias úteis | −2 900 € | −17 300 € |
| Opção H: parte do excesso que pode remover | −16 700 € | −2 500 € |
| Peso do tempo de atraso face ao tempo a bordo | −13 300 € | −1 400 € |

### Quem ganha e quem perde (valores centrais, por ano)

| opção | horas de passageiros poupadas | valor para os passageiros | horas de autocarro poupadas | valor para a Carris | lugares retirados | custo para quem estaciona |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B | 235 h | 2 100 € | 11,7 h | 410 € | 21 | −10 100 € |
| C | 192 h | 1 700 € | 9,6 h | 330 € | 10 | −4 700 € |
| E | 209 h | 1 900 € | 10,4 h | 360 € | 21 | −5 000 € |
| G | 209 h | 1 900 € | 10,4 h | 360 € | 21 | −4 100 € |
| H | 171 h | 1 500 € | 8,5 h | 300 € | 10 | −1 900 € |

## Uma alternativa sem retirar estacionamento

prioridade nos estreitamentos com os sinais B5 e B6, sem retirar estacionamento: custa cerca de 1 800 € (6 sinais) e não retira nenhum lugar. O efeito não se pode estimar com estes dados; paga-se se poupar 1,1 horas de autocarro por ano, ou seja 0,9 s por passagem na ponta, quando o excesso medido removível é de cerca de 10 s. Não alarga a rua: um dos autocarros continua a esperar, mas a espera fica organizada (circulação alternada) em vez de decidida no momento.

## O que não está monetizado e o que falta saber

Os benefícios estão subestimados, porque não se monetizam:

- A ocupação do estacionamento nas ruas vizinhas não foi encontrada: não se sabe se os carros deslocados têm lugar perto.
- O atraso medido vem de um arquivo de terceiros com poucos registos em 2026; os dados de localização da própria Carris mostrariam se se mantém.
- Não se monetizam o tempo perdido fora da ponta, o atraso de quem segue de carro, a segurança nem o acesso de emergência: os benefícios estão subestimados.

## Conclusões

1. Contando só o tempo dos autocarros na ponta da tarde, nenhuma opção de retirar estacionamento compensa os lugares que retira: a de menor perda é a H (VAL de −9 300 €, benefício/custo 0,60, probabilidade de VAL > 0 de 5%).
2. Para a opção H compensar, seria preciso, por exemplo, um excesso de 24,1 s por passagem (medido: 14,5 s, até 23,9 s); ou que um lugar valesse no máximo 200 € por ano a quem o perde (central: 560 €).
3. A alternativa P (prioridade nos estreitamentos com os sinais B5 e B6, sem retirar estacionamento) custa cerca de 1 800 € e paga-se com 0,9 s poupados por passagem na ponta: é a medida que menos arrisca, e pode experimentar-se primeiro.
4. O que mais mudaria estas conclusões: os dados de localização da própria Carris (o atraso atual, que o arquivo de 2026 já não mostra), a ocupação dos lugares nas ruas vizinhas, e uma contagem do atraso de quem segue de carro atrás de um autocarro parado.

## Fontes

- Comissão Europeia (2021), Economic Appraisal Vademecum 2021-2027: General Principles and Sector Applications, <https://jaspers.eib.org/LibraryNP/EC%20Reports/Economic%20Appraisal%20Vademecum%202021-2027%20-%20General%20Principles%20and%20Sector%20Applications.pdf>
- Eurostat, Labour cost levels by NACE Rev. 2 activity (lc_lci_lev), Portugal, 2025, <https://ec.europa.eu/eurostat/databrowser/view/lc_lci_lev/default/table>
- Carris, Relatório e Contas 2024, <https://carris.pt/media/ikvdezmc/relat%C3%B3rio-e-contas-carris-2024.pdf>
- EMEL, Plano de Atividades e Orçamento 2026-2029, <https://www.emel.pt/fotos/financeiro/emel_pao_2026-2029_signed_signed_133048145369a6e017b0094.pdf>
- Diário de Notícias, «Ninguém paga mais de 46,30 euros mensais nos parques da EMEL», <https://www.dn.pt/sociedade/ninguem-paga-mais-de-46-30-euros-mensais-nos-parques-da-emel-saiba-porque>
- Observador (20/03/2025), «Câmara de Lisboa disponibiliza 3 500 lugares de estacionamento noturno em parceria com EMEL e Telpark», <https://observador.pt/2025/03/20/camara-de-lisboa-disponibiliza-3-500-lugares-de-estacionamento-noturno-em-parceria-com-emel-e-telpark/>
- Imovirtual, garagens para arrendar em Alvalade (consultado em novembro de 2026), <https://www.imovirtual.com/pt/resultados/arrendar/garagem/lisboa/lisboa/alvalade>
- Junta de Freguesia de Alvalade, Plano de Atividades e Orçamento 2022: manutenção e gestão do espaço público, <https://www.jf-alvalade.pt/wp-content/uploads/manutencaogestaodoespacopublicoequipamentos-pao2022-jfa-web.pdf>
- Decreto Regulamentar n.º 22-A/98, Regulamento de Sinalização do Trânsito, <https://diariodarepublica.pt/dr/detalhe/decreto-regulamentar/22-a-1998-302974>
- Lei n.º 75/2013, de 12 de setembro, Regime Jurídico das Autarquias Locais (Diário da República, 1.ª série, n.º 176/2013)
