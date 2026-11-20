# Estudo de viabilidade e análise custo-benefício: Rua Ricardo Jorge

Gerado por `mobilidados run` a partir das tabelas em `tables/` e da configuração do caso (`[appraisal]`). Cada valor diz de onde vem e com que grau: **M** medido · **D** documento oficial · **I** inferido · **P** pressuposto · **NE** não encontrado. Método em docs/appraisal.md.

## Resumo

- Nos troços com estacionamento dos dois lados (117,5 m), a largura livre mediana é de 4,90 m; dois autocarros lado a lado precisam de pelo menos 5,00 m só com a carroçaria (5,80 m com espelhos).
- Nos dias úteis, às 17h–19h, a diferença entre o tempo dos autocarros no troço entre paragens e o que os troços vizinhos explicariam foi de +49% (intervalo de 90%: +34% a +65%), cerca de 14 s por passagem (6 a 24 s), segundo posições GPS arquivadas por terceiros (por ano: 2025: +60%; 2026: +4%, não informa: o arquivo guardou muito menos registos nesse ano).
- No núcleo, só com o medido e o documentado, nenhuma opção compensa os lugares que retira: a de menor perda é a H (VAL de −9 300 €, benefício/custo 0,60, probabilidade de VAL > 0 de 7%).
- Para a opção H compensar no núcleo, seria preciso, por exemplo, um excesso de 24,1 s por passagem (medido: 14,5 s, até 23,9 s); ou que um lugar valesse no máximo 200 € por ano a quem o perde (central: 560 €).
- Juntando os mecanismos que a medição ainda não vê, a valores centrais de fontes publicadas, a opção C compensa: VAL de 17 200 €, benefício/custo 1,51, positivo em 75% das simulações (benefício/custo de cada opção: B 0,92; C 1,51; E 0,99; G 0,73; H 0,94).
- O que mais pode mudar a decisão, e por isso mais vale medir: custo anual, para quem perde o lugar, de estacionar noutro sítio; excesso por passagem fora da ponta (todos os dias); opção C: parte do excesso que pode remover.
- Fora das contas, a opção C melhora: fiabilidade da viagem de autocarro (o stress de não saber quando se chega); acesso ao comboio e ao metro; ruído e ar na rua; acesso de veículos de socorro; referência municipal de desenho de rua; reversibilidade; e piora: qualidade de vida de quem estaciona na rua.
- A alternativa R (um espaço de cruzamento: o estacionamento de um lado retirado em cerca de 20 m a meio do troço B2, onde um autocarro espera enquanto o outro passa) retira cerca de 4 lugares e paga-se com 7,5 s poupados por passagem na ponta (0,8 s a qualquer hora): merece um estudo de geometria.
- Os dados que fecham estas contas: os registos de passagem pedidos à Carris (o atraso de hoje, a qualquer hora, e a sua dispersão), uma contagem noturna dos lugares livres a menos de 150 m, e uma contagem do tráfego na rua.

## O problema

Nos troços com estacionamento dos dois lados (117,5 m), a largura livre mediana é de 4,90 m; dois autocarros lado a lado precisam de pelo menos 5,00 m só com a carroçaria (5,80 m com espelhos). Sem o estacionamento de um lado, a mediana passaria a 6,91 m. Nos dias úteis, às 17h–19h, a diferença entre o tempo dos autocarros no troço entre paragens e o que os troços vizinhos explicariam foi de +49% (intervalo de 90%: +34% a +65%), cerca de 14 s por passagem (6 a 24 s), segundo posições GPS arquivadas por terceiros (por ano: 2025: +60%; 2026: +4%, não informa: o arquivo guardou muito menos registos nesse ano).

Esse excesso não está só nos troços estreitos: 5,7 s estão dentro deles e 8,1 s nos cruzamentos entre eles. No cruzamento (R. Cor. Marques Leitão, 76,2–95,2 m), os autocarros têm um autocarro em sentido contrário na rua em 26% das vezes, contra 11% por acaso (p = 1,5 × 10⁻⁶): esperam ali que o troço seguinte fique livre. Por isso se conta como removível, no valor central, o excesso dos troços estreitos e desse cruzamento (72% do total).

## As opções

Cada opção retira o estacionamento de um dos lados nos troços indicados, sempre ou só a certas horas. A situação de referência é não fazer nada.

| opção | descrição | metros | lugares | quando |
| --- | --- | ---: | ---: | --- |
| B | um lado, sempre, nos três troços com estacionamento dos dois lados | 117,5 | 21 | sempre |
| C | um lado, sempre, só no troço B2, o mais longo | 54,0 | 10 | sempre |
| E | um lado, das 7h às 20h nos dias úteis, nos três troços | 117,5 | 21 | dias úteis, 7h–20h |
| G | um lado, das 16h às 20h nos dias úteis, nos três troços | 117,5 | 21 | dias úteis, 16h–20h |
| H | um lado, das 16h às 20h nos dias úteis, só no troço B2 | 54,0 | 10 | dias úteis, 16h–20h |

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
| legal | Numa faixa de rodagem estreitada por obras ou obstáculos ocasionais, salvo se houver circulação alternada, a largura deixada à circulação não pode ser inferior a 5,8 m onde circulem automóveis pesados. A regra é para obras e obstáculos, não para estacionamento; mas mostra a largura que o próprio Regulamento considera necessária para pesados nos dois sentidos, e a largura livre medida, 4,90 m, fica abaixo dela. |  | D | Regulamento de Sinalização do Trânsito (Decreto Regulamentar n.º 22-A/98), art. 87.º, n.º 4 |
| legal | Compete à Câmara Municipal deliberar sobre o estacionamento de veículos nas vias públicas. |  | D | Lei n.º 75/2013, anexo I, art. 33.º, n.º 1, alínea rr) |
| legal | Uma proibição de estacionar sinaliza-se com o sinal C15; uma proibição por horas e dias, com um painel adicional do modelo n.º 7d (dias da semana e horas do dia). |  | D | Regulamento de Sinalização do Trânsito (Decreto Regulamentar n.º 22-A/98), sinais de proibição e painéis adicionais |
| operacional | A Carris registou 1 284 interrupções por estacionamento indevido em 2025 (1 365 em 2024), com 824 horas de impacto, em 229 arruamentos; a velocidade média de exploração desceu, e a Carris diz trabalhar com a Câmara em medidas na rede viária para cumprir horários. |  | D | Carris, Relatório e Contas 2025, p. 29–30; Relatório e Contas 2024, p. 26–27 |
| social | O plano da EMEL para 2026-2029 prevê 11 parques novos (3 115 lugares), nenhum em Alvalade; a Junta de Freguesia pede um parque subterrâneo junto à Av. da Igreja para os moradores. |  | D | EMEL, Plano de Atividades e Orçamento 2026-2029, quadro 3-1; Junta de Freguesia de Alvalade, Plano de Atividades 2022 |

## Análise custo-benefício

Análise económica incremental de cada opção face a não fazer nada, segundo o *Economic Appraisal Vademecum 2021-2027* da Comissão Europeia: preços constantes de 2025, 10 anos, taxa social de desconto de 5% (e 3% / 7% como teste). Os benefícios e o custo do estacionamento escalam com o cumprimento: um carro que fica bloqueia o autocarro e guarda o lugar. Taxas, tarifas e avenças são transferências e ficam de fora.

As contas fazem-se em duas camadas. O **núcleo** conta só o que os dados medem ou os documentos oficiais dizem: o tempo que os autocarros perdem na ponta da tarde, o valor dos lugares retirados para quem os perde, a obra e a fiscalização. A **camada alargada** junta-lhe o que a medição ainda não vê, cada mecanismo com um valor unitário de fonte publicada e um intervalo: o tempo perdido fora da ponta e ao fim de semana; a fiabilidade (um atraso imprevisto pesa mais do que um atraso habitual, e a quem muda para o comboio ou o metro pode custar a ligação); os carros retidos atrás dos autocarros; os novos passageiros que um autocarro mais rápido e mais certo atrai, e os custos externos das viagens que deixam o carro (congestionamento, acidentes, ruído, poluição, clima); os danos por toques. Do lado dos custos: quem encontra lugar perto perde só uma caminhada, e pode ser precisa acalmia de tráfego. O stress de conduzir que os novos passageiros deixam já está no ganho que os leva a mudar (a regra da metade): não se conta duas vezes. O resto (qualidade de vida, ruído e ar na rua, segurança, acesso de emergência) fica nos critérios sem preço, mais abaixo.

### Valores usados

| valor | camada | mínimo | central | máximo | unidade | grau | fonte |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| Valor do tempo de um passageiro | núcleo | 3,88 | 6,00 | 7,76 | €/h | I | Eurostat lc_lci_lev, Portugal 2025: 19,40 €/h de custo da mão de obra; EAV 2021-2027, p. 55: deslocações pendulares a 25–40 % e outras a 20–35 % desse valor; na ponta da tarde admite-se uma maioria de regressos a casa (P) |
| Peso do tempo de atraso face ao tempo a bordo | núcleo | 1,00 | 1,50 | 2,50 |  | P | EAV 2021-2027, quadro 7: tempo em congestionamento 1,5; atraso no transporte público 2,5–4, este para atrasos imprevistos; o atraso medido repete-se todos os dias úteis, por isso o valor central é o do congestionamento |
| Passageiros a bordo, na ponta da tarde | núcleo | 13,10 | 20,00 | 30,00 | passageiros | P | Carris, Relatório e Contas 2024, p. 14 e 26–27: taxa de ocupação dos autocarros 19,58 % × 2 270 milhões de lugares·km ÷ 33,969 milhões de veículos·km = 13,1 passageiros em média no dia; a Carris não publica a ocupação por carreira nem por hora, e na ponta admite-se mais |
| Multiplicador para quem espera nas paragens seguintes | núcleo | 1,00 | 1,00 | 1,50 |  | P | Quem espera mais adiante também perde o atraso; não se conta no valor central |
| Custo de uma hora de autocarro parado | núcleo | 0,00 | 34,60 | 55,50 | €/h | I | Carris, Relatório e Contas 2024: gastos com o pessoal 94,07 M€ ÷ 2,718 milhões de veículos·hora = 34,6 €/h; todos os gastos operacionais (150,93 M€) dariam 55,5 €/h; 0 se o atraso não alterar horários nem turnos |
| Ocupação dos lugares retirados | núcleo | 0,85 | 0,95 | 1,00 |  | P | A ocupação das ruas vizinhas não foi encontrada (NE); a Junta de Freguesia (Plano de Atividades 2022) pede um parque subterrâneo junto à Av. da Igreja para as necessidades dos moradores, e a EMEL (Plano 2026-2029) aponta a pressão dos dísticos de residente |
| Custo anual, para quem perde o lugar, de estacionar noutro sítio | núcleo | 325,00 | 555,60 | 2 100,00 | €/ano | I | Mínimo: mais 10 min a pé por dia, ao valor do tempo de lazer (5,34 €/h). Central: avença R24 da EMEL para residentes, 46,30 €/mês (DN, citando a EMEL). Máximo: lugar de garagem arrendado em Alvalade, cerca de 175 €/mês (anúncios Imovirtual, 150–200 €/mês) |
| Opção E: parte do valor do lugar perdida das 7h às 20h nos dias úteis | núcleo | 0,40 | 0,55 | 0,75 |  | I | Avenças da EMEL e Telpark: noturna (18h–10h e fins de semana) 22 €/mês contra 46,30 €/mês por 24 h, donde (46,30 − 22) ÷ 46,30 = 0,52 do valor está no dia útil |
| Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | núcleo | 0,25 | 0,45 | 0,70 |  | P | Quem deixa o carro durante o dia tem de o tirar antes das 16h, e quem chega entre as 16h e as 20h não pode estacionar desse lado: são as horas de chegada a casa; sem dados de uso dos lugares, é um pressuposto, e o valor de inversão diz quanto pode valer |
| Cumprimento de uma proibição permanente | núcleo | 0,80 | 0,90 | 1,00 |  | P | Pressuposto; a Carris registou 1 365 interrupções por estacionamento indevido em 2024 (Relatório e Contas 2024, p. 26) |
| Cumprimento de uma proibição por horas | núcleo | 0,60 | 0,80 | 0,95 |  | P | Pressuposto; uma proibição por horas pede fiscalização às horas certas |
| Sinal vertical colocado (C15, com painel adicional se houver horário) | núcleo | 150,00 | 300,00 | 600,00 | € | P | Pressuposto: não se encontrou um preço unitário público em Portugal; a obra pesa pouco no resultado (appraisal_tornado.csv) |
| Marcação no pavimento, por metro | núcleo | 2,00 | 5,00 | 15,00 | €/m | P | Pressuposto, como o anterior; metade é repintada a cada 5 anos |
| Fiscalização a mais de uma proibição por horas | núcleo | 0,00 | 1 000,00 | 5 000,00 | €/ano | P | Pressuposto; 0 se couber nas rondas da EMEL e da Polícia Municipal |
| Comprimento de um lugar | núcleo | 5,00 | 5,50 | 6,00 | m | P | Como no registo de factos (profiles.parking_space_m) |
| Excesso por passagem fora da ponta (todos os dias) | alargada | 0,00 | 3,00 | 8,00 | s | P | Não medido: o método compara a ponta com o resto do dia, que é a sua base. O horário prevê 1–2 encontros por dia útil nos troços estreitos, mas na ponta os autocarros cruzam-se lá muito mais do que o acaso explica (26 % contra 11 %); admite-se fora da ponta cerca de um quinto dos 14,5 s medidos na ponta, removível na mesma parte. Os registos de passagem pedidos à Carris medem-no |
| Passageiros a bordo, fora da ponta | alargada | 8,00 | 12,00 | 13,80 | passageiros | I | Carris, Relatório e Contas 2025, p. 16: 488,5 milhões de passageiros·km ÷ 35,4 milhões de veículos·km = 13,8 passageiros em média, todo o dia e toda a rede; fora da ponta, menos (P) |
| Parte do atraso que o passageiro não pode prever (um autocarro retido por outro) | alargada | 0,00 | 0,30 | 0,70 |  | P | Sem dados da distribuição dos tempos de passagem; a cauda dessa distribuição (passagens de minutos em vez de segundos) nos registos pedidos à Carris mede-a |
| Peso do atraso imprevisto face ao tempo a bordo | alargada | 2,50 | 3,00 | 4,00 |  | D | EAV 2021-2027, quadro 7: atraso no transporte público, 2,5 a 4 vezes o tempo a bordo |
| Parte dos passageiros que muda para o comboio ou o metro mais adiante | alargada | 0,10 | 0,25 | 0,40 |  | P | Horário GTFS da Carris: a 744 liga a rua à Estação de Entrecampos (cerca de 12 min; CP, Fertagus, metro) e à Gare do Oriente (cerca de 14 min); a 46B ao Campo Grande e a Entrecampos (metro). Um atraso faz perder o comboio marcado: para quem muda, o atraso pesa como atraso imprevisto. A parte dos que mudam não é publicada |
| Carros retidos atrás de um autocarro que espera | alargada | 0,00 | 0,50 | 2,00 |  | P | Sem contagem de tráfego na rua (NE); uma contagem num dia útil fixa-o |
| Pessoas por carro | alargada | 1,20 | 1,40 | 1,70 | pessoas | I | Handbook on the external costs of transport (2019), quadro 94: 1,7 pessoas por carro na UE28; nas deslocações urbanas e pendulares é menos (P) |
| Elasticidade da procura do autocarro ao tempo a bordo (valor absoluto) | alargada | 0,40 | 0,60 | 0,65 |  | D | RAND Europe e SYSTRA para o DfT (2018), secção 6.6: −0,60 a longo prazo (Wardman 2012: −0,55 lazer, −0,65 pendular); Paulley et al. (2006): cerca de −0,4 |
| Tempo a bordo de uma viagem de autocarro, em média | alargada | 10,00 | 16,00 | 25,00 | min | I | Carris, Relatório e Contas 2025, p. 16: 488,5 milhões de passageiros·km ÷ 131,8 milhões de passageiros = 3,7 km por viagem; a cerca de 14 km/h (P), cerca de 16 min |
| Parte dos novos passageiros que deixa o carro | alargada | 0,24 | 0,25 | 0,30 |  | D | RAND Europe e SYSTRA para o DfT (2018), quadro 26: numa melhoria do autocarro, 0,25 dos novos passageiros vinham do carro (áreas metropolitanas), 0,30 onde não há metro ligeiro, 0,24 na média nacional |
| Comprimento da viagem de carro substituída | alargada | 2,50 | 3,70 | 5,00 | km | I | Igual à viagem média de autocarro: 3,7 km (Carris, Relatório e Contas 2025) |
| Custos externos evitados por passageiro·km que deixa o carro | alargada | 0,04 | 0,20 | 0,48 | €/pkm | I | Handbook on the external costs of transport (2019), quadros 125 e 115, preços de 2016 × 1,240 (IHPC de Portugal, Eurostat, 2016 → 2025): acidentes 1,41, poluição 0,14–0,86, clima 0,88–1,00, ruído 0,5–1,1 e a montante 0,14–0,26 cêntimos por passageiro·km (tráfego metropolitano denso, de dia); congestionamento em Portugal, outras vias urbanas, 41,1 (perto da capacidade) a 57,7 (acima) cêntimos por veículo·km ÷ 1,7 pessoas por carro. Mínimo: sem congestionamento; central: metade das viagens perto da capacidade; máximo: todas acima |
| Danos em autocarros e carros estacionados por toques nos estreitamentos | alargada | 0,00 | 500,00 | 3 000,00 | €/ano | P | Em toda a rua, nos troços estreitos e nos cruzamentos entre eles; sem dados (NE): o registo de ocorrências pedido à Carris fixa-o; central: um espelho de autocarro por ano (P) |
| Parte dos carros deslocados que encontra lugar a menos de 150 m | alargada | 0,00 | 0,30 | 1,00 |  | P | Há cerca de 780 lugares cartografados a menos de 150 m (appraisal_feasibility.csv): bastam 21 livres (2,7 %) à noite. A ocupação noturna não é conhecida (NE), e a Junta e a EMEL apontam pressão; uma contagem noturna fixa-o |
| Custo anual, para quem estaciona perto, de procurar e andar mais | alargada | 65,00 | 130,00 | 260,00 | €/ano | I | Mais 2, 4 ou 8 minutos por dia, 365 dias, ao valor do tempo de lazer (5,34 €/h, como no mínimo do custo de estacionar noutro sítio) |
| Acalmia de tráfego, se a velocidade subir na faixa mais larga | alargada | 0,00 | 5 000,00 | 20 000,00 | € | P | Pressuposto: uma faixa mais larga convida a ir mais depressa; passadeiras sobrelevadas ou outras medidas, se a medição antes e depois o mostrar. Não se encontrou um preço unitário público |

| medido nas tabelas do caso | mínimo | central | máximo |
| --- | ---: | ---: | ---: |
| Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 5,6 | 14,5 | 23,9 |
| Opção B: parte do excesso que pode remover | 0,41 | 0,72 | 1,00 |
| Opção C: parte do excesso que pode remover | 0,28 | 0,59 | 0,87 |
| Opção E: parte do excesso que pode remover | 0,41 | 0,72 | 1,00 |
| Opção G: parte do excesso que pode remover | 0,41 | 0,72 | 1,00 |
| Opção H: parte do excesso que pode remover | 0,28 | 0,59 | 0,87 |
| Autocarros na rua na ponta, por dia útil (horário) | 18 | 18 | 18 |
| Dias úteis por ano (sem feriados) | 251 | 251 | 251 |
| Opção B: metros de estacionamento retirados | 117,5 | 117,5 | 117,5 |
| Opção C: metros de estacionamento retirados | 54,0 | 54,0 | 54,0 |
| Opção E: metros de estacionamento retirados | 117,5 | 117,5 | 117,5 |
| Opção G: metros de estacionamento retirados | 117,5 | 117,5 | 117,5 |
| Opção H: metros de estacionamento retirados | 54,0 | 54,0 | 54,0 |
| Opção B: passagens por ano na ponta, com a opção em vigor | 4 518 | 4 518 | 4 518 |
| Opção B: passagens por ano fora da ponta, com a opção em vigor | 36 694 | 36 694 | 36 694 |
| Opção C: passagens por ano na ponta, com a opção em vigor | 4 518 | 4 518 | 4 518 |
| Opção C: passagens por ano fora da ponta, com a opção em vigor | 36 694 | 36 694 | 36 694 |
| Opção E: passagens por ano na ponta, com a opção em vigor | 4 518 | 4 518 | 4 518 |
| Opção E: passagens por ano fora da ponta, com a opção em vigor | 23 343 | 23 343 | 23 343 |
| Opção G: passagens por ano na ponta, com a opção em vigor | 4 518 | 4 518 | 4 518 |
| Opção G: passagens por ano fora da ponta, com a opção em vigor | 4 016 | 4 016 | 4 016 |
| Opção H: passagens por ano na ponta, com a opção em vigor | 4 518 | 4 518 | 4 518 |
| Opção H: passagens por ano fora da ponta, com a opção em vigor | 4 016 | 4 016 | 4 016 |
| Passagens por ano (horário de um dia útil, um sábado e um domingo) | 41 212 | 41 212 | 41 212 |

### Resultados

**Núcleo** (só o medido e o documentado):

| opção | benefício/ano | estacionamento e fiscalização/ano | obra | VAL (10 anos, 5%) | benefício/custo | VAL a 3% | VAL a 7% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B | 2 500 € | 10 100 € | 1 800 € | −61 100 € | 0,24 | −67 300 € | −55 700 € |
| C | 2 100 € | 4 700 € | 870 € | −21 100 € | 0,43 | −23 300 € | −19 300 € |
| E | 2 200 € | 6 000 € | 2 400 € | −31 500 € | 0,35 | −34 600 € | −28 900 € |
| G | 2 200 € | 5 100 € | 2 400 € | −24 600 € | 0,41 | −26 900 € | −22 500 € |
| H | 1 800 € | 2 900 € | 1 200 € | −9 300 € | 0,60 | −10 200 € | −8 600 € |

**Camada alargada** (o núcleo e os mecanismos ainda não medidos), valores centrais por ano:

| opção | tempo dos passageiros | Carris | carros retidos | novos passageiros | custos externos evitados | danos evitados | benefício/ano | estacionamento e fiscalização/ano | obra | VAL | benefício/custo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B | 6 300 € | 1 100 € | 200 € | 0 € | 190 € | 320 € | 8 100 € | 7 800 € | 6 800 € | −5 200 € | 0,92 |
| C | 5 100 € | 890 € | 160 € | 0 € | 160 € | 260 € | 6 600 € | 3 600 € | 5 900 € | 17 200 € | 1,51 |
| E | 4 600 € | 750 € | 140 € | 0 € | 140 € | 190 € | 5 800 € | 4 800 € | 7 400 € | −450 € | 0,99 |
| G | 3 100 € | 430 € | 80 € | 0 € | 100 € | 60 € | 3 700 € | 4 100 € | 7 400 € | −10 800 € | 0,73 |
| H | 2 500 € | 350 € | 60 € | 0 € | 80 € | 50 € | 3 100 € | 2 400 € | 6 200 € | −1 500 € | 0,94 |

### Incerteza

Simulação de Monte Carlo com 20 000 sorteios de todos os valores (distribuições PERT entre o mínimo, o valor central e o máximo, semente fixa); os mesmos sorteios servem todas as opções.

| camada | opção | VAL P10 | VAL mediano | VAL P90 | probabilidade de VAL > 0 | probabilidade de ser a melhor |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| núcleo | B | −148 900 € | −82 200 € | −40 800 € | 0% | 0% |
| núcleo | C | −61 500 € | −30 400 € | −9 800 € | 2% | 13% |
| núcleo | E | −81 500 € | −45 600 € | −21 400 € | 0% | 0% |
| núcleo | G | −68 000 € | −36 500 € | −14 300 € | 1% | 0% |
| núcleo | H | −33 800 € | −16 800 € | −2 000 € | 7% | 86% |
| alargada | B | −64 400 € | −9 000 € | 37 900 € | 40% | 10% |
| alargada | C | −14 800 € | 16 300 € | 51 300 € | 75% | 75% |
| alargada | E | −38 400 € | −6 900 € | 23 700 € | 38% | 4% |
| alargada | G | −44 200 € | −18 100 € | 4 700 € | 16% | 0% |
| alargada | H | −24 300 € | −7 200 € | 10 700 € | 30% | 11% |

### O que teria de mudar

Para cada opção, o valor de cada entrada que poria o VAL a zero, mantendo as outras no valor central (— : nenhum valor possível o faz).

| camada | opção | entrada | valor central | valor de inversão | dentro do intervalo testado? |
| --- | --- | --- | ---: | ---: | --- |
| núcleo | B | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 60,00 | ✗ |
| núcleo | B | Opção B: parte do excesso que pode remover | 0,72 | — | ✗ |
| núcleo | B | Passageiros a bordo, na ponta da tarde | 20,00 | 94,82 | ✗ |
| núcleo | B | Ocupação dos lugares retirados | 0,95 | 0,21 | ✗ |
| núcleo | B | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 122,45 | ✗ |
| núcleo | C | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 33,75 | ✗ |
| núcleo | C | Opção C: parte do excesso que pode remover | 0,59 | — | ✗ |
| núcleo | C | Passageiros a bordo, na ponta da tarde | 20,00 | 51,65 | ✗ |
| núcleo | C | Ocupação dos lugares retirados | 0,95 | 0,39 | ✗ |
| núcleo | C | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 229,42 | ✗ |
| núcleo | E | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 40,91 | ✗ |
| núcleo | E | Opção E: parte do excesso que pode remover | 0,72 | — | ✗ |
| núcleo | E | Passageiros a bordo, na ponta da tarde | 20,00 | 63,43 | ✗ |
| núcleo | E | Ocupação dos lugares retirados | 0,95 | 0,17 | ✗ |
| núcleo | E | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 98,42 | ✗ |
| núcleo | E | Opção E: parte do valor do lugar perdida das 7h às 20h nos dias úteis | 0,55 | 0,10 | ✗ |
| núcleo | E | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |
| núcleo | G | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 35,08 | ✗ |
| núcleo | G | Opção G: parte do excesso que pode remover | 0,72 | — | ✗ |
| núcleo | G | Passageiros a bordo, na ponta da tarde | 20,00 | 53,84 | ✗ |
| núcleo | G | Ocupação dos lugares retirados | 0,95 | 0,21 | ✗ |
| núcleo | G | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 120,29 | ✗ |
| núcleo | G | Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,10 | ✗ |
| núcleo | G | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |
| núcleo | H | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 24,05 | ✗ |
| núcleo | H | Opção H: parte do excesso que pode remover | 0,59 | 0,97 | ✗ |
| núcleo | H | Passageiros a bordo, na ponta da tarde | 20,00 | 35,71 | ✗ |
| núcleo | H | Ocupação dos lugares retirados | 0,95 | 0,33 | ✗ |
| núcleo | H | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 195,90 | ✗ |
| núcleo | H | Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,16 | ✗ |
| núcleo | H | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |
| alargada | B | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 17,14 | ✓ |
| alargada | B | Opção B: parte do excesso que pode remover | 0,72 | 0,78 | ✓ |
| alargada | B | Passageiros a bordo, na ponta da tarde | 20,00 | 24,19 | ✓ |
| alargada | B | Ocupação dos lugares retirados | 0,95 | 0,87 | ✓ |
| alargada | B | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 502,85 | ✓ |
| alargada | B | Excesso por passagem fora da ponta (todos os dias) | 3,00 | 3,50 | ✓ |
| alargada | B | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | 0,39 | ✓ |
| alargada | C | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 3,82 | ✗ |
| alargada | C | Opção C: parte do excesso que pode remover | 0,59 | 0,39 | ✓ |
| alargada | C | Passageiros a bordo, na ponta da tarde | 20,00 | 3,08 | ✗ |
| alargada | C | Ocupação dos lugares retirados | 0,95 | — | ✗ |
| alargada | C | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 934,86 | ✓ |
| alargada | C | Excesso por passagem fora da ponta (todos os dias) | 3,00 | 0,98 | ✓ |
| alargada | C | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | — | ✗ |
| alargada | E | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 14,75 | ✓ |
| alargada | E | Opção E: parte do excesso que pode remover | 0,72 | 0,72 | ✓ |
| alargada | E | Passageiros a bordo, na ponta da tarde | 20,00 | 20,40 | ✓ |
| alargada | E | Ocupação dos lugares retirados | 0,95 | 0,94 | ✓ |
| alargada | E | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 546,37 | ✓ |
| alargada | E | Opção E: parte do valor do lugar perdida das 7h às 20h nos dias úteis | 0,55 | 0,54 | ✓ |
| alargada | E | Fiscalização a mais de uma proibição por horas | 1 000,00 | 942,30 | ✓ |
| alargada | E | Excesso por passagem fora da ponta (todos os dias) | 3,00 | 3,08 | ✓ |
| alargada | E | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | 0,32 | ✓ |
| alargada | G | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 20,63 | ✓ |
| alargada | G | Opção G: parte do excesso que pode remover | 0,72 | 0,98 | ✓ |
| alargada | G | Passageiros a bordo, na ponta da tarde | 20,00 | 29,73 | ✓ |
| alargada | G | Ocupação dos lugares retirados | 0,95 | 0,53 | ✗ |
| alargada | G | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 283,24 | ✗ |
| alargada | G | Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,25 | ✗ |
| alargada | G | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |
| alargada | G | Excesso por passagem fora da ponta (todos os dias) | 3,00 | 13,58 | ✗ |
| alargada | G | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | 0,75 | ✓ |
| alargada | H | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 15,57 | ✓ |
| alargada | H | Opção H: parte do excesso que pode remover | 0,59 | 0,62 | ✓ |
| alargada | H | Passageiros a bordo, na ponta da tarde | 20,00 | 21,69 | ✓ |
| alargada | H | Ocupação dos lugares retirados | 0,95 | 0,82 | ✗ |
| alargada | H | Custo anual, para quem perde o lugar, de estacionar noutro sítio | 555,60 | 471,30 | ✓ |
| alargada | H | Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,39 | ✓ |
| alargada | H | Fiscalização a mais de uma proibição por horas | 1 000,00 | 801,86 | ✓ |
| alargada | H | Excesso por passagem fora da ponta (todos os dias) | 3,00 | 4,84 | ✓ |
| alargada | H | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | 0,44 | ✓ |

Entradas que mais mudam o VAL da opção C na camada alargada (do mínimo ao máximo de cada uma):

| entrada | VAL no mínimo | VAL no máximo |
| --- | ---: | ---: |
| Custo anual, para quem perde o lugar, de estacionar noutro sítio | 27 700 € | −52 900 € |
| Excesso por passagem fora da ponta (todos os dias) | −8 400 € | 59 900 € |
| Opção C: parte do excesso que pode remover | −9 200 € | 41 800 € |
| Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 2 900 € | 32 400 € |
| Parte dos carros deslocados que encontra lugar a menos de 150 m | 8 900 € | 36 500 € |
| Valor do tempo de um passageiro | 2 800 € | 29 200 € |
| Acalmia de tráfego, se a velocidade subir na faixa mais larga | 22 200 € | 2 200 € |
| Multiplicador para quem espera nas paragens seguintes | 17 200 € | 37 000 € |

### O que vale a pena medir

Quanto vale saber cada entrada antes de decidir, em valor atual (valor esperado da informação perfeita parcial, da simulação da camada alargada): só conta o que pode mudar a decisão. Saber tudo valeria cerca de 5 400 €.

| entrada | valor de saber antes de decidir |
| --- | ---: |
| Custo anual, para quem perde o lugar, de estacionar noutro sítio | 700 € |
| Excesso por passagem fora da ponta (todos os dias) | 390 € |
| Opção C: parte do excesso que pode remover | 220 € |

### Quem ganha e quem perde (camada alargada, valores centrais, por ano)

Em euros por ano; positivo é ganho, negativo é perda.

| grupo | B | C | E | G | H |
| --- | ---: | ---: | ---: | ---: | ---: |
| Viagens de passageiros com a opção em vigor (por ano) | 530 688 | 530 688 | 370 476 | 138 552 | 138 552 |
| Segundos poupados por viagem de passageiro | 3,2 | 2,6 | 3,3 | 6,0 | 4,9 |
| Lugares retirados | 21 | 10 | 21 | 21 | 10 |
| Passageiros dos autocarros: tempo | 6 300 € | 5 100 € | 4 600 € | 3 100 € | 2 500 € |
| Carris: horas de autocarro | 1 100 € | 890 € | 750 € | 430 € | 350 € |
| Quem segue de carro atrás de um autocarro | 200 € | 160 € | 140 € | 80 € | 60 € |
| Novos passageiros | 0 € | 0 € | 0 € | 0 € | 0 € |
| Toda a gente: custos externos das viagens que deixam o carro | 190 € | 160 € | 140 € | 100 € | 80 € |
| Carris e donos de carros: danos evitados | 320 € | 260 € | 190 € | 60 € | 50 € |
| Quem estaciona na rua | −7 800 € | −3 600 € | −3 800 € | −3 100 € | −1 400 € |
| Câmara e EMEL: obra e fiscalização | −880 € | −760 € | −2 000 € | −2 000 € | −1 800 € |

## O que não tem preço

Efeitos que as contas não medem em dinheiro, ou só em parte: ++ melhora muito · + melhora · 0 não muda · − piora · −− piora muito · ? depende, ou não se sabe. Os pesos entre eles são da Câmara: não se dão.

| critério | indicador | B | C | E | G | H | grau | porquê |
| --- | --- | :---: | :---: | :---: | :---: | :---: | --- | --- |
| Fiabilidade da viagem de autocarro (o stress de não saber quando se chega) | Dispersão do tempo de passagem; impasses por semana | ++ | + | + | + | + | I | Sem o estacionamento de um lado, dois autocarros cruzam-se sem esperar (6,91 m livres; precisam de 5,80 m com espelhos): acabam os impasses e a espera no cruzamento com a R. Cor. Marques Leitão. B em toda a rua e a toda a hora; C só no troço mais longo; E, G e H só nas horas em que vigoram. |
| Acesso ao comboio e ao metro | Ligações perdidas em Entrecampos, no Oriente e no Campo Grande | + | + | + | + | + | I | A 744 liga a rua à Estação de Entrecampos (cerca de 12 min) e à Gare do Oriente (cerca de 14 min); a 46B ao Campo Grande e a Entrecampos. Um comboio perdido custa o intervalo até ao seguinte; a camada alargada conta o atraso de quem muda como atraso imprevisto, mas não a confiança de poder contar com a ligação. |
| Qualidade de vida de quem estaciona na rua | Minutos a mais por dia a procurar lugar e a andar; lugares de cargas e de pessoas com mobilidade reduzida | −− | − | − | − | − | I | Cerca de 21 lugares em B, E e G; 10 em C e H; nas opções por horas, só nessas horas. O custo em dinheiro está nas contas; aqui fica o resto: a incerteza de encontrar lugar, as cargas e descargas, quem tem mobilidade reduzida. |
| Ruído e ar na rua | Arranques e esperas de autocarros com o motor ligado; carros a circular à procura de lugar | + | + | + | + | + | P | Menos esperas e arranques de autocarros numa rua estreita, com prédios dos dois lados; do outro lado, mais carros às voltas à procura de lugar se não houver lugares livres perto. A camada alargada conta os custos externos das viagens tiradas ao carro; o ruído na própria rua não tem medição. |
| Segurança | Toques e manobras de recuo; velocidade; visibilidade nos cruzamentos | ? | ? | ? | ? | ? | P | Acabam os toques entre autocarros e carros estacionados e as manobras de recuo, e vê-se melhor quem atravessa; mas uma faixa mais larga convida a ir mais depressa (a camada alargada inclui medidas de acalmia). O efeito líquido só se sabe medindo a velocidade e os incidentes antes e depois. |
| Acesso de veículos de socorro | Veículos de socorro retidos na rua | + | + | + | + | + | NE | Uma ambulância ou um pronto-socorro também não cruza um autocarro em 4,90 m. A paragem seguinte chama-se Bombeiros Alvalade, mas não se verificou se os veículos do Regimento de Sapadores Bombeiros ou do INEM usam a rua. |
| Referência municipal de desenho de rua | Largura livre face ao perfil do manual (6,80 m entre faixas de estacionamento) | ++ | + | + | + | + | D | Com estacionamento só de um lado, a largura livre passa a 6,91 m, acima dos 6,80 m do manual: em toda a rua em B, só no troço mais longo em C, e só nas horas em que vigoram em E, G e H. |
| Quem ganha e quem perde | Viagens de passageiros por ano face a lugares retirados | ? | ? | ? | ? | ? | I | Os ganhos repartem-se por cerca de meio milhão de viagens de passageiros por ano, muitas de quem não tem carro; a perda concentra-se em cerca de 21 lugares. Quanto pesa cada grupo é uma escolha da Câmara: o quadro de quem ganha e quem perde dá os números. |
| Reversibilidade | Custo e tempo de desfazer | + | + | + | + | + | I | Sinais e tinta: qualquer opção se desfaz em dias e por pouco dinheiro. |

## Uma alternativa a estudar

Um espaço de cruzamento: o estacionamento de um lado retirado em cerca de 20 m a meio do troço B2, onde um autocarro espera enquanto o outro passa: retira cerca de 4 lugares e custa, com eles, cerca de 15 500 € em valor atual. O efeito depende da geometria e não se pode estimar com estes dados; paga-se se poupar 9,4 horas de autocarro por ano: 7,5 s por passagem na ponta, ou 0,8 s por passagem a qualquer hora, quando o excesso removível medido na ponta é de cerca de 10 s.

## O que falta saber

O que falta saber, e o que mais mudaria estas conclusões:

- A ocupação do estacionamento nas ruas vizinhas não foi encontrada: não se sabe se os carros deslocados têm lugar perto.
- O atraso medido vem de um arquivo de terceiros que, em 2026, guardou uma cópia do feed a cada 8 a 45 minutos, em vez de 3 a 4 em 2025: o valor de 2026 não informa. Os registos de passagem pedidos à Carris (Lei n.º 26/2016) e os dados da PGIL pedidos à Câmara mostrariam o atraso atual.
- O tempo fora da ponta, os carros retidos, a fiabilidade, as ligações ao comboio, os novos passageiros e os danos só entram na camada alargada, com valores pressupostos até serem medidos; a segurança, o acesso de emergência e a qualidade de vida ficam nos critérios sem preço.

## Conclusões

1. No núcleo, só com o medido e o documentado, nenhuma opção compensa os lugares que retira: a de menor perda é a H (VAL de −9 300 €, benefício/custo 0,60, probabilidade de VAL > 0 de 7%).
2. Para a opção H compensar no núcleo, seria preciso, por exemplo, um excesso de 24,1 s por passagem (medido: 14,5 s, até 23,9 s); ou que um lugar valesse no máximo 200 € por ano a quem o perde (central: 560 €).
3. Juntando os mecanismos que a medição ainda não vê, a valores centrais de fontes publicadas, a opção C compensa: VAL de 17 200 €, benefício/custo 1,51, positivo em 75% das simulações (benefício/custo de cada opção: B 0,92; C 1,51; E 0,99; G 0,73; H 0,94).
4. O que mais pode mudar a decisão, e por isso mais vale medir: custo anual, para quem perde o lugar, de estacionar noutro sítio; excesso por passagem fora da ponta (todos os dias); opção C: parte do excesso que pode remover.
5. Fora das contas, a opção C melhora: fiabilidade da viagem de autocarro (o stress de não saber quando se chega); acesso ao comboio e ao metro; ruído e ar na rua; acesso de veículos de socorro; referência municipal de desenho de rua; reversibilidade; e piora: qualidade de vida de quem estaciona na rua.
6. A alternativa R (um espaço de cruzamento: o estacionamento de um lado retirado em cerca de 20 m a meio do troço B2, onde um autocarro espera enquanto o outro passa) retira cerca de 4 lugares e paga-se com 7,5 s poupados por passagem na ponta (0,8 s a qualquer hora): merece um estudo de geometria.
7. Os dados que fecham estas contas: os registos de passagem pedidos à Carris (o atraso de hoje, a qualquer hora, e a sua dispersão), uma contagem noturna dos lugares livres a menos de 150 m, e uma contagem do tráfego na rua.

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
- Carris, Relatório e Contas 2025, <https://www.carris.pt/media/huxjvfft/relat%C3%B3rio-e-contas-carris-2025_vers%C3%A3o-site.pdf>
- Comissão Europeia, DG MOVE (2019), Handbook on the external costs of transport, versão 2019 – 1.1, CE Delft, <https://op.europa.eu/en/publication-detail/-/publication/9781f65f-8448-11ea-bf12-01aa75ed71a1>
- Eurostat, HICP – índice anual (prc_hicp_aind), Portugal, 2016 e 2025, <https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/default/table>
- RAND Europe e SYSTRA para o Department for Transport (2018), Bus fare and journey time elasticities and diversion factors for all modes, <https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/719278/bus-fare-journey-time-elasticities.pdf>
- Paulley, N. et al. (2006), The demand for public transport: the effects of fares, quality of service, income and car ownership, Transport Policy 13(4), 295–306, <https://doi.org/10.1016/j.tranpol.2005.12.004>
