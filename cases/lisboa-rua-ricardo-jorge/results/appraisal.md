# Estudo de viabilidade e análise custo-benefício: Rua Ricardo Jorge

Gerado por `mobilidados run` a partir das tabelas em `tables/` e da configuração do caso (`[appraisal]`). Cada valor diz de onde vem e com que grau: **M** medido · **D** documento oficial · **I** inferido · **P** pressuposto · **NE** não encontrado. Método em docs/appraisal.md.

## Resumo

- Nos troços com estacionamento dos dois lados (117,5 m), a largura livre mediana é de 4,90 m; dois autocarros lado a lado precisam de pelo menos 5,00 m só com a carroçaria (5,80 m com espelhos).
- Nos dias úteis, às 17h–19h, a diferença entre o tempo dos autocarros no troço entre paragens e o que os troços vizinhos explicariam foi de +49% (intervalo de 90%: +34% a +65%), cerca de 14 s por passagem (6 a 24 s), segundo posições GPS arquivadas por terceiros (por ano: 2025: +60%; 2026: +4%, não informa: o arquivo guardou muito menos registos nesse ano).
- No núcleo, só com o medido e o documentado, nenhuma opção compensa os lugares que retira: a de menor perda é a H (VAL de −9 300 €, benefício/custo 0,61, probabilidade de VAL > 0 de 8%).
- Para a opção H compensar no núcleo, seria preciso, por exemplo, um excesso de 23,6 s por passagem (medido: 14,5 s, até 23,9 s); ou que um lugar valesse no máximo 210 € por ano a quem o perde (central: 560 €).
- Juntando os mecanismos que a medição ainda não vê, a valores centrais de fontes publicadas, a opção C compensa: VAL de 25 800 €, benefício/custo 1,82, positivo em 86% das simulações (benefício/custo de cada opção: B 1,07; C 1,82; E 1,21; G 0,93; H 1,24).
- O que mais pode mudar a decisão, e por isso mais vale medir: excesso por passagem fora da ponta (todos os dias).
- Fora das contas, a opção C melhora: fiabilidade da viagem de autocarro (o stress de não saber quando se chega); acesso ao comboio e ao metro; ruído e ar na rua; acesso de veículos de socorro; referência municipal de desenho de rua; reversibilidade; e piora: qualidade de vida de quem estaciona na rua.
- A alternativa R (um espaço de cruzamento: o estacionamento de um lado retirado em cerca de 20 m a meio do troço B2, onde um autocarro se desvia para o outro passar) retira cerca de 4 lugares e paga-se com 7,5 s poupados por passagem na ponta (0,8 s a qualquer hora): merece um estudo de geometria.
- Os dados que fecham estas contas: os registos de passagem pedidos à Carris (o atraso de hoje, a qualquer hora, e a sua dispersão), uma contagem noturna dos lugares livres a menos de 150 m, e uma contagem do tráfego na rua.

## O problema

Nos troços com estacionamento dos dois lados (117,5 m), a largura livre mediana é de 4,90 m; dois autocarros lado a lado precisam de pelo menos 5,00 m só com a carroçaria (5,80 m com espelhos). Sem o estacionamento de um lado, a mediana passaria a 6,91 m. Nos dias úteis, às 17h–19h, a diferença entre o tempo dos autocarros no troço entre paragens e o que os troços vizinhos explicariam foi de +49% (intervalo de 90%: +34% a +65%), cerca de 14 s por passagem (6 a 24 s), segundo posições GPS arquivadas por terceiros (por ano: 2025: +60%; 2026: +4%, não informa: o arquivo guardou muito menos registos nesse ano).

Esse excesso não está só nos troços estreitos: 5,7 s estão dentro deles e 8,1 s nos cruzamentos entre eles. No cruzamento (R. Cor. Marques Leitão, 76,2–95,2 m), os autocarros têm um autocarro em sentido contrário na rua em 26% das vezes, contra 11% por acaso (p < 0,001, reamostrando dias inteiros): é ali que os autocarros perdem tempo quando outro vem em sentido contrário. As posições, guardadas de minutos a minutos, não mostram o que fazem (esperar, ficar frente a frente, recuar); mas um autocarro de 12 m não cabe de lado num cruzamento destes para deixar passar outro. Por isso se conta como removível, no valor central, o excesso dos troços estreitos e desse cruzamento (72% do total).

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
- Desviar uma das carreiras: medido na rede de ruas em appraisal_reroutes.csv. Acaba com os encontros entre autocarros, mas não com os encontros com ligeiros e furgões; alonga o percurso e tira paragens a quem as usa. A decisão é de rede, da Carris, com as entradas e saídas por paragem.
- Mais fiscalização do estacionamento: os carros estão em lugares marcados, por isso fiscalizar não alarga a faixa livre.

## Viabilidade

| dimensão | verificação | resultado | grau | fonte |
| --- | --- | --- | --- | --- |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a dois autocarros, só carroçaria | 6,91 m / 5,00 m: cumpre | I | without_parking.csv, width_budget.csv |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a dois autocarros, com espelhos | 6,91 m / 5,80 m: cumpre | I | without_parking.csv, width_budget.csv |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a Lisboa: o Desenho da Rua – Manual de espaço público, p. 152 | 6,91 m / 6,80 m: cumpre | D | standards_comparison.csv |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a Buses in Urban Developments, p. 25 | 6,91 m / 6,20 m: cumpre | D | standards_comparison.csv |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a Portaria n.º 135/2020, de 2 de junho: alteração ao Regulamento Técnico de Segurança contra Incêndio em Edifícios (RT-SCIE, Portaria n.º 1532/2008), republicado em anexo, p. 69 | 6,91 m / 6,00 m: cumpre | D | standards_comparison.csv |
| técnica | Largura livre sem o estacionamento de um lado (mediana) face a Schriftliche Anfrage Drucksache 19/25490, Antwort vom 27.03.2026, p. 3 | 6,91 m / 6,50 m: cumpre | D | standards_comparison.csv |
| social | Lugares retirados face ao estacionamento cartografado a menos de 150 m | 2,5% a 3,0% | I | cartografia municipal: cerca de 779 lugares cartografados (área ÷ profundidade da faixa ÷ comprimento de um lugar); a ocupação não é conhecida |
| social | Lugares retirados face ao estacionamento cartografado a menos de 300 m | 0,9% a 1,1% | I | cartografia municipal: cerca de 2207 lugares cartografados (área ÷ profundidade da faixa ÷ comprimento de um lugar); a ocupação não é conhecida |
| legal | Numa faixa de rodagem estreitada por obras ou obstáculos ocasionais, salvo se houver circulação alternada, a largura deixada à circulação não pode ser inferior a 5,8 m onde circulem automóveis pesados. A regra é para obras e obstáculos, não para estacionamento; mas mostra a largura que o próprio Regulamento considera necessária para pesados nos dois sentidos, e a largura livre medida, 4,90 m, fica abaixo dela. |  | D | Regulamento de Sinalização do Trânsito (Decreto Regulamentar n.º 22-A/98), art. 87.º, n.º 4 |
| legal | Compete à Câmara Municipal deliberar sobre o estacionamento de veículos nas vias públicas. |  | D | Lei n.º 75/2013, anexo I, art. 33.º, n.º 1, alínea rr) |
| legal | Uma proibição de estacionar sinaliza-se com o sinal C15; uma proibição por horas e dias, com um painel adicional do modelo n.º 7d (dias da semana e horas do dia). |  | D | Regulamento de Sinalização do Trânsito (Decreto Regulamentar n.º 22-A/98), sinais de proibição e painéis adicionais |
| operacional | A Carris registou 1 284 interrupções por estacionamento indevido em 2025 (1 365 em 2024), com 824 horas de impacto, em 229 arruamentos; a velocidade média de exploração desceu, e a Carris diz trabalhar com a Câmara em medidas na rede viária para cumprir horários. |  | D | Carris, Relatório e Contas 2025, p. 29–30; Relatório e Contas 2024, p. 26–27 |
| social | O plano da EMEL para 2026-2029 prevê 11 parques novos (3 115 lugares), nenhum em Alvalade; a Junta de Freguesia pede um parque subterrâneo junto à Av. da Igreja para os moradores. |  | D | EMEL, Plano de Atividades e Orçamento 2026-2029, quadro 3-1; Junta de Freguesia de Alvalade, Plano de Atividades 2022 |
| legal | O Código da Estrada obriga quem conduz a manter «distância lateral suficiente para evitar acidentes» dos veículos que transitam na mesma faixa, no mesmo sentido ou em sentido oposto (coima de 60 € a 300 €), e fixa 1,5 m para ultrapassar uma bicicleta. Com 4,90 m livres, um autocarro e um ligeiro que se cruzam ficam com 0,60 m entre eles e os carros estacionados, dos dois lados somados. |  | D | Código da Estrada, art. 18.º, n.os 2 a 4; width_budget.csv, passing_practice.csv |
| legal | O regulamento de segurança contra incêndio em edifícios pede 6 m de largura útil nas vias de acesso a edifícios com mais de 9 m de altura e admite outras características, fundamentadas, em zonas edificadas cuja rede viária não possa ser corrigida. Aplica-se no licenciamento dos edifícios; para esta rua é uma referência, não uma regra que ela viole. Hoje há 4,90 m livres; com um lado livre, 6,91 m. |  | D | Portaria n.º 1532/2008, republicada pela Portaria n.º 135/2020, art. 4.º, n.º 7, e art. 5.º, n.º 1, al. a) |
| operacional | A cartografia municipal mostra um quartel de bombeiros a cerca de 36 m da rua (a paragem no extremo sudoeste chama-se Bombeiros Alvalade). Um veículo de bombeiros (até 2,55 m) e um autocarro precisam de 6,25 m para se cruzarem com a margem dos guias de desenho; hoje há 4,90 m. Se os veículos de socorro usam a rua, o Regimento de Sapadores Bombeiros o dirá. |  | D | Cartografia municipal 1:1000, camada QuartelDeBombeiros; passing_practice.csv |
| social | Há escolas perto: uma escola básica e secundária a cerca de 90 m, uma creche a cerca de 100 m e escolas primárias a partir de cerca de 130 m. As saídas das escolas podem explicar parte do atraso concentrado entre as 17h e as 18h; e, numa rua mais larga junto a escolas, a velocidade dos automóveis tem de ser medida antes e durante o ensaio. |  | D | Cartografia municipal 1:1000, camadas EscolaPrimaria, EscolaPreparatoriaEOuSecundaria, Creche e JardimDeInfancia; delay_by_hour.csv |

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
| Preço anual de estacionar noutro sítio, para quem perde o lugar | núcleo | 264,00 | 555,60 | 2 100,00 | €/ano | I | Mínimo: avença noturna da EMEL e da Telpark, 22 €/mês (Observador, 20/03/2025). Central: avença R24 da EMEL para residentes, 46,30 €/mês (DN, citando a EMEL). Máximo: lugar de garagem arrendado em Alvalade, cerca de 175 €/mês (anúncios Imovirtual, 150–200 €/mês). O tempo a pé até ao parque conta à parte (carpark_walk) |
| Opção E: parte do valor do lugar perdida das 7h às 20h nos dias úteis | núcleo | 0,40 | 0,55 | 0,75 |  | I | Avenças da EMEL e Telpark: noturna (18h–10h e fins de semana) 22 €/mês contra 46,30 €/mês por 24 h, donde (46,30 − 22) ÷ 46,30 = 0,52 do valor está no dia útil |
| Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | núcleo | 0,25 | 0,45 | 0,70 |  | P | Quem deixa o carro durante o dia tem de o tirar antes das 16h, e quem chega entre as 16h e as 20h não pode estacionar desse lado: são as horas de chegada a casa; sem dados de uso dos lugares, é um pressuposto, e o valor de inversão diz quanto pode valer |
| Cumprimento de uma proibição permanente | núcleo | 0,80 | 0,90 | 1,00 |  | P | Pressuposto; a Carris registou 1 365 interrupções por estacionamento indevido em 2024 (Relatório e Contas 2024, p. 26) |
| Cumprimento de uma proibição por horas | núcleo | 0,60 | 0,80 | 0,95 |  | P | Pressuposto; uma proibição por horas pede fiscalização às horas certas |
| Sinal vertical colocado (C15, com painel adicional se houver horário) | núcleo | 150,00 | 300,00 | 600,00 | € | P | Pressuposto: não se encontrou um preço unitário público em Portugal; a obra pesa pouco no resultado (appraisal_tornado.csv) |
| Marcação no pavimento, por metro | núcleo | 2,00 | 5,00 | 15,00 | €/m | P | Pressuposto, como o anterior; metade é repintada a cada 5 anos |
| Fiscalização a mais de uma proibição por horas | núcleo | 0,00 | 1 000,00 | 5 000,00 | €/ano | P | Pressuposto; 0 se couber nas rondas da EMEL e da Polícia Municipal |
| Crescimento real do rendimento por pessoa | alargada | 0,00 | 0,01 | 0,02 | por ano | P | EAV 2021-2027, p. 59: os valores unitários crescem com o PIB por pessoa (elasticidade 1 para o valor do tempo calculado do custo da mão de obra do Eurostat, 0,8 para as externalidades); aqui também o custo da Carris e o valor de um lugar, para que os dois lados cresçam por igual. Banco de Portugal (junho de 2026): PIB real +1,8 % em 2026, +1,6 % em 2027, +1,8 % em 2028; o crescimento da população não foi verificado (NE), por isso se admite 1 % por pessoa, entre 0 e o crescimento do PIB |
| Comprimento de um lugar | núcleo | 5,00 | 5,50 | 6,00 | m | P | Como no registo de factos (profiles.parking_space_m) |
| Excesso por passagem fora da ponta (todos os dias) | alargada | 0,00 | 2,50 | 8,00 | s | I | Inferido, não medido: o método compara a ponta com o resto do dia, que é a sua base, e não pode medir o resto do dia. O valor central (que substitui o 3,0 acima) é o excesso medido na ponta multiplicado pela razão entre o excesso de encontros fora da ponta e na ponta, no cruzamento onde os autocarros comprovadamente se encontram (delay_copresence.csv): admite o mesmo tempo perdido por encontro. Mínimo 0: fora da ponta, o tempo no troço é igual ao dos troços de controlo à mesma escala (delay_by_hour.csv), e o excesso de encontros fora da ponta não é significativo (p ≈ 0,10). Os registos de passagem pedidos à Carris medem-no |
| Passageiros a bordo, fora da ponta | alargada | 8,00 | 12,00 | 13,80 | passageiros | I | Carris, Relatório e Contas 2025, p. 16: 488,5 milhões de passageiros·km ÷ 35,4 milhões de veículos·km = 13,8 passageiros em média, todo o dia e toda a rede; fora da ponta, menos (P) |
| Parte do atraso que o passageiro não pode prever (um autocarro retido por outro) | alargada | 0,00 | 0,30 | 0,70 |  | P | Sem dados da distribuição dos tempos de passagem; a cauda dessa distribuição (passagens de minutos em vez de segundos) nos registos pedidos à Carris mede-a |
| Peso do atraso imprevisto face ao tempo a bordo | alargada | 2,50 | 3,00 | 4,00 |  | D | EAV 2021-2027, quadro 7: atraso no transporte público, 2,5 a 4 vezes o tempo a bordo |
| Parte dos passageiros que muda para o comboio ou o metro mais adiante | alargada | 0,10 | 0,25 | 0,40 |  | P | Horário GTFS da Carris: a 744 liga a rua à Estação de Entrecampos (cerca de 12 min; CP, Fertagus, metro) e à Gare do Oriente (cerca de 14 min); a 46B ao Campo Grande e a Entrecampos (metro). Um atraso faz perder o comboio marcado: para quem muda, o atraso pesa como atraso imprevisto. A parte dos que mudam não é publicada |
| Parte do atraso nos cruzamentos sem autocarros em sentido contrário que se deve a ligeiros, furgões e pesados | alargada | 0,00 | 0,50 | 1,00 |  | P | O Código da Estrada exige «distância lateral suficiente» entre veículos que se cruzam (art. 18.º, n.º 2). Com as margens dos guias de desenho de ruas (CIHT 2018, B.2.2: 6,2 m para dois autocarros), um autocarro também não se cruza com um ligeiro, um furgão ou um pesado em 4,90 m (passing_practice.csv); no cruzamento da R. Constantino Fernandes perdem-se 3,9 s sem mais autocarros em sentido contrário do que o acaso dá. Admite-se que metade se deve a esses encontros, que a supressão também resolve; a outra metade, ao trânsito do cruzamento. Uma contagem classificada com vídeo fixa-o |
| Quilómetros a mais por dia, à procura de lugar, de quem encontra lugar perto | alargada | 0,00 | 0,50 | 1,30 | km por dia | P | Pressuposto: dos 4 minutos por dia de procura e caminhada de quem encontra lugar a menos de 150 m (walk_cost), cerca de 2 a circular a 15 km/h (0,5 km); máximo: os 4 minutos a circular a 20 km/h (1,3 km). Valorizados aos custos externos por passageiro·km (external_cost_pkm) × pessoas por carro: congestionamento, poluição, clima, ruído e acidentes |
| Carros retidos atrás de um autocarro parado ou preso | alargada | 0,00 | 0,50 | 2,00 |  | P | Sem contagem de tráfego na rua (NE); uma contagem num dia útil fixa-o |
| Pessoas por carro | alargada | 1,20 | 1,40 | 1,70 | pessoas | I | Handbook on the external costs of transport (2019), quadro 94: 1,7 pessoas por carro na UE28; nas deslocações urbanas e pendulares é menos (P) |
| Elasticidade da procura do autocarro ao tempo a bordo (valor absoluto) | alargada | 0,40 | 0,60 | 0,65 |  | D | RAND Europe e SYSTRA para o DfT (2018), secção 6.6: −0,60 a longo prazo (Wardman 2012: −0,55 lazer, −0,65 pendular); Paulley et al. (2006): cerca de −0,4 |
| Tempo a bordo de uma viagem de autocarro, em média | alargada | 10,00 | 16,00 | 25,00 | min | I | Carris, Relatório e Contas 2025, p. 16: 488,5 milhões de passageiros·km ÷ 131,8 milhões de passageiros = 3,7 km por viagem; a cerca de 14 km/h (P), cerca de 16 min |
| Parte dos novos passageiros que deixa o carro | alargada | 0,24 | 0,25 | 0,30 |  | D | RAND Europe e SYSTRA para o DfT (2018), quadro 26: numa melhoria do autocarro, 0,25 dos novos passageiros vinham do carro (áreas metropolitanas), 0,30 onde não há metro ligeiro, 0,24 na média nacional |
| Comprimento da viagem de carro substituída | alargada | 2,50 | 3,70 | 5,00 | km | I | Igual à viagem média de autocarro: 3,7 km (Carris, Relatório e Contas 2025) |
| Custos externos evitados por passageiro·km que deixa o carro | alargada | 0,04 | 0,20 | 0,48 | €/pkm | I | Handbook on the external costs of transport (2019), quadros 125 e 115, preços de 2016 × 1,240 (IHPC de Portugal, Eurostat, 2016 → 2025): acidentes 1,41, poluição 0,14–0,86, clima 0,88–1,00, ruído 0,5–1,1 e a montante 0,14–0,26 cêntimos por passageiro·km (tráfego metropolitano denso, de dia); congestionamento em Portugal, outras vias urbanas, 41,1 (perto da capacidade) a 57,7 (acima) cêntimos por veículo·km ÷ 1,7 pessoas por carro. Mínimo: sem congestionamento; central: metade das viagens perto da capacidade; máximo: todas acima |
| Danos em autocarros e carros estacionados por toques nos estreitamentos | alargada | 0,00 | 500,00 | 3 000,00 | €/ano | P | Em toda a rua, nos troços estreitos e nos cruzamentos entre eles; sem dados (NE): o registo de ocorrências pedido à Carris fixa-o; central: um espelho de autocarro por ano (P) |
| Parte dos carros deslocados que encontra lugar a menos de 150 m | alargada | 0,00 | 0,30 | 1,00 |  | P | Há cerca de 780 lugares cartografados a menos de 150 m (appraisal_feasibility.csv): bastam 21 livres (2,7 %) à noite. A ocupação noturna não é conhecida (NE), e a Junta e a EMEL apontam pressão; uma contagem noturna fixa-o |
| Custo anual, para quem passa a estacionar num parque, do tempo a pé até casa | alargada | 65,00 | 195,00 | 390,00 | €/ano | P | Mais 2, 6 ou 12 minutos por dia, 365 dias, ao valor do tempo de lazer (5,34 €/h, como walk_cost); a distância ao parque mais próximo com avença não é conhecida (NE) |
| Parte do preço do parque que é uma transferência: o parque tem lugares vagos | alargada | 0,00 | 0,50 | 1,00 |  | P | A ocupação dos parques perto não é conhecida (NE). Em 2025 a Câmara abriu 3 500 lugares noturnos em parques da EMEL e da Telpark (Observador, 20/03/2025), sinal de capacidade livre à noite. Com lugares vagos, a avença é uma transferência para o operador do parque e fica fora das contas da sociedade (EAV 2021-2027; DfT TAG A1.3: as tarifas de estacionamento são transferências entre utilizadores e operadores), e só o tempo a pé é custo; num parque cheio, o preço mede o custo de oportunidade do lugar. A EMEL pode dar a ocupação |
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
| B | 2 500 € | 10 100 € | 1 800 € | −64 200 € | 0,24 | −70 800 € | −58 400 € |
| C | 2 100 € | 4 700 € | 870 € | −22 200 € | 0,43 | −24 500 € | −20 200 € |
| E | 2 200 € | 6 000 € | 2 400 € | −32 600 € | 0,36 | −35 900 € | −29 800 € |
| G | 2 200 € | 5 100 € | 2 400 € | −25 300 € | 0,42 | −27 700 € | −23 200 € |
| H | 1 800 € | 2 900 € | 1 200 € | −9 300 € | 0,61 | −10 200 € | −8 600 € |

**Camada alargada** (o núcleo e os mecanismos ainda não medidos), valores centrais por ano:

| opção | tempo dos passageiros | Carris | carros retidos | novos passageiros | custos externos evitados | danos evitados | benefício/ano | estacionamento e fiscalização/ano | obra | VAL | benefício/custo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B | 6 600 € | 1 100 € | 200 € | 0 € | −70 € | 390 € | 8 200 € | 6 800 € | 6 800 € | 4 200 € | 1,07 |
| C | 5 600 € | 930 € | 170 € | 0 € | 50 € | 330 € | 7 000 € | 3 100 € | 5 900 € | 25 800 € | 1,82 |
| E | 5 100 € | 820 € | 150 € | 0 € | 20 € | 230 € | 6 300 € | 4 300 € | 7 400 € | 8 900 € | 1,21 |
| G | 3 600 € | 500 € | 90 € | 10 € | 0 € | 70 € | 4 300 € | 3 700 € | 7 400 € | −2 600 € | 0,93 |
| H | 3 100 € | 420 € | 80 € | 0 € | 40 € | 60 € | 3 700 € | 2 200 € | 6 200 € | 5 700 € | 1,24 |

### Valor pelo dinheiro

Duas convenções para a mesma conta. O EAV divide todos os benefícios por todos os custos, com o valor dos lugares perdidos nos custos. O DfT conta os lugares perdidos como um prejuízo de quem os usa, abatido aos benefícios, e divide pelo que paga o orçamento público (obra, fiscalização); as suas categorias são: muito alto a partir de 4, alto de 2 a 4, médio de 1,5 a 2, baixo de 1 a 1,5, fraco de 0 a 1, muito fraco abaixo de 0. O VAL é o mesmo nas duas: é ele que decide. A razão do DfT sobe muito quando a obra é barata, por isso não se lê sozinha; e o próprio DfT diz que a categoria se ajusta pelo que não tem preço.

| camada | opção | VAL | benefício/custo (EAV) | benefício/custo para o orçamento (DfT) | categoria (DfT) |
| --- | --- | ---: | ---: | ---: | --- |
| núcleo | B | −64 200 € | 0,24 | −28,20 | muito fraco |
| núcleo | C | −22 200 € | 0,43 | −19,97 | muito fraco |
| núcleo | E | −32 600 € | 0,36 | −2,10 | muito fraco |
| núcleo | G | −25 300 € | 0,42 | −1,40 | muito fraco |
| núcleo | H | −9 300 € | 0,61 | −0,03 | muito fraco |
| alargada | B | 4 200 € | 1,07 | 1,58 | médio |
| alargada | C | 25 800 € | 1,82 | 5,25 | muito alto |
| alargada | E | 8 900 € | 1,21 | 1,57 | médio |
| alargada | G | −2 600 € | 0,93 | 0,83 | fraco |
| alargada | H | 5 700 € | 1,24 | 1,41 | baixo |

### Do núcleo à camada alargada, mecanismo a mecanismo

Quanto acrescenta cada mecanismo ao VAL, ligado um de cada vez por esta ordem, a valores centrais. Mostra em que assenta o resultado da camada alargada: é aí que estão os pressupostos a confirmar.

| passo | B | C | E | G | H |
| --- | ---: | ---: | ---: | ---: | ---: |
| VAL do núcleo | −64 200 € | −22 200 € | −32 600 € | −25 300 € | −9 300 € |
| Tempo fora da ponta e ao fim de semana | +17 200 € | +14 000 € | +10 800 € | +1 900 € | +1 500 € |
| Fiabilidade: o atraso imprevisto | +9 100 € | +7 400 € | +7 000 € | +5 000 € | +4 100 € |
| Ligações ao comboio e ao metro | +5 300 € | +4 300 € | +4 100 € | +2 900 € | +2 400 € |
| Carros retidos atrás dos autocarros | +1 400 € | +1 100 € | +1 000 € | +620 € | +500 € |
| Autocarros retidos por ligeiros, furgões e pesados em sentido contrário | +10 500 € | +10 500 € | +8 100 € | +5 600 € | +5 600 € |
| Novos passageiros e viagens tiradas ao carro | +1 700 € | +1 400 € | +1 300 € | +950 € | +800 € |
| Danos por toques | +3 000 € | +2 500 € | +1 800 € | +550 € | +470 € |
| Lugares livres perto para os carros deslocados | +19 000 € | +8 700 € | +9 300 € | +7 600 € | +3 500 € |
| Tempo a pé de quem passa a estacionar num parque | −20 300 € | −9 300 € | −9 900 € | −8 100 € | −3 700 € |
| Voltas à procura de lugar (custos externos) | −2 200 € | −1 000 € | −1 100 € | −890 € | −410 € |
| Avença paga a um parque com lugares vagos: transferência | +28 900 € | +13 300 € | +14 100 € | +11 500 € | +5 300 € |
| Acalmia de tráfego | −5 000 € | −5 000 € | −5 000 € | −5 000 € | −5 000 € |
| **VAL da camada alargada** | **4 200 €** | **25 800 €** | **8 900 €** | **−2 600 €** | **5 700 €** |

### Incerteza

Simulação de Monte Carlo com 20 000 sorteios de todos os valores (distribuições PERT entre o mínimo, o valor central e o máximo, semente fixa); os mesmos sorteios servem todas as opções.

| camada | opção | VAL P10 | VAL mediano | VAL P90 | probabilidade de VAL > 0 | probabilidade de ser a melhor escolha, contando com não fazer nada |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| núcleo | B | −159 000 € | −85 200 € | −37 600 € | 0% | 0% |
| núcleo | C | −65 500 € | −31 300 € | −8 100 € | 3% | 2% |
| núcleo | E | −85 500 € | −46 600 € | −19 800 € | 1% | 0% |
| núcleo | G | −71 300 € | −37 200 € | −13 300 € | 2% | 0% |
| núcleo | H | −34 800 € | −16 700 € | −1 400 € | 8% | 7% |
| alargada | B | −45 800 € | 5 800 € | 59 000 € | 56% | 10% |
| alargada | C | −4 800 € | 28 800 € | 71 200 € | 86% | 71% |
| alargada | E | −26 400 € | 6 300 € | 43 400 € | 59% | 4% |
| alargada | G | −33 100 € | −8 200 € | 16 900 € | 33% | 0% |
| alargada | H | −17 200 € | 1 500 € | 22 100 € | 54% | 2% |

### O que teria de mudar

Para cada opção, o valor de cada entrada que poria o VAL a zero, mantendo as outras no valor central (— : nenhum valor possível o faz).

| camada | opção | entrada | valor central | valor de inversão | dentro do intervalo testado? |
| --- | --- | --- | ---: | ---: | --- |
| núcleo | B | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 59,92 | ✗ |
| núcleo | B | Opção B: parte do excesso que pode remover | 0,72 | — | ✗ |
| núcleo | B | Passageiros a bordo, na ponta da tarde | 20,00 | 94,69 | ✗ |
| núcleo | B | Ocupação dos lugares retirados | 0,95 | 0,21 | ✗ |
| núcleo | B | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 123,23 | ✗ |
| núcleo | C | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 33,70 | ✗ |
| núcleo | C | Opção C: parte do excesso que pode remover | 0,59 | — | ✗ |
| núcleo | C | Passageiros a bordo, na ponta da tarde | 20,00 | 51,57 | ✗ |
| núcleo | C | Ocupação dos lugares retirados | 0,95 | 0,39 | ✗ |
| núcleo | C | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 230,23 | ✗ |
| núcleo | E | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 40,47 | ✗ |
| núcleo | E | Opção E: parte do excesso que pode remover | 0,72 | — | ✗ |
| núcleo | E | Passageiros a bordo, na ponta da tarde | 20,00 | 62,71 | ✗ |
| núcleo | E | Ocupação dos lugares retirados | 0,95 | 0,18 | ✗ |
| núcleo | E | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 106,03 | ✗ |
| núcleo | E | Opção E: parte do valor do lugar perdida das 7h às 20h nos dias úteis | 0,55 | 0,10 | ✗ |
| núcleo | E | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |
| núcleo | G | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 34,64 | ✗ |
| núcleo | G | Opção G: parte do excesso que pode remover | 0,72 | — | ✗ |
| núcleo | G | Passageiros a bordo, na ponta da tarde | 20,00 | 53,11 | ✗ |
| núcleo | G | Ocupação dos lugares retirados | 0,95 | 0,22 | ✗ |
| núcleo | G | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 129,59 | ✗ |
| núcleo | G | Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,10 | ✗ |
| núcleo | G | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |
| núcleo | H | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 23,59 | ✓ |
| núcleo | H | Opção H: parte do excesso que pode remover | 0,59 | 0,95 | ✗ |
| núcleo | H | Passageiros a bordo, na ponta da tarde | 20,00 | 34,94 | ✗ |
| núcleo | H | Ocupação dos lugares retirados | 0,95 | 0,36 | ✗ |
| núcleo | H | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 213,36 | ✗ |
| núcleo | H | Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,17 | ✗ |
| núcleo | H | Fiscalização a mais de uma proibição por horas | 1 000,00 | — | ✗ |
| alargada | B | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 13,58 | ✓ |
| alargada | B | Opção B: parte do excesso que pode remover | 0,72 | 0,67 | ✓ |
| alargada | B | Passageiros a bordo, na ponta da tarde | 20,00 | 17,35 | ✓ |
| alargada | B | Ocupação dos lugares retirados | 0,95 | — | ✗ |
| alargada | B | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 635,52 | ✓ |
| alargada | B | Excesso por passagem fora da ponta (todos os dias) | 2,50 | 2,15 | ✓ |
| alargada | B | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | 0,20 | ✓ |
| alargada | C | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 7,78 | ✓ |
| alargada | C | Opção C: parte do excesso que pode remover | 0,59 | 0,26 | ✗ |
| alargada | C | Passageiros a bordo, na ponta da tarde | 20,00 | 0,59 | ✗ |
| alargada | C | Ocupação dos lugares retirados | 0,95 | — | ✗ |
| alargada | C | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 1 634,71 | ✓ |
| alargada | C | Excesso por passagem fora da ponta (todos os dias) | 2,50 | — | ✗ |
| alargada | C | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | — | ✗ |
| alargada | E | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 11,95 | ✓ |
| alargada | E | Opção E: parte do excesso que pode remover | 0,72 | 0,57 | ✓ |
| alargada | E | Passageiros a bordo, na ponta da tarde | 20,00 | 13,62 | ✓ |
| alargada | E | Ocupação dos lugares retirados | 0,95 | — | ✗ |
| alargada | E | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 905,38 | ✓ |
| alargada | E | Opção E: parte do valor do lugar perdida das 7h às 20h nos dias úteis | 0,55 | 0,72 | ✓ |
| alargada | E | Fiscalização a mais de uma proibição por horas | 1 000,00 | 2 150,61 | ✓ |
| alargada | E | Excesso por passagem fora da ponta (todos os dias) | 2,50 | 1,30 | ✓ |
| alargada | E | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | — | ✗ |
| alargada | G | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 15,58 | ✓ |
| alargada | G | Opção G: parte do excesso que pode remover | 0,72 | 0,78 | ✓ |
| alargada | G | Passageiros a bordo, na ponta da tarde | 20,00 | 21,89 | ✓ |
| alargada | G | Ocupação dos lugares retirados | 0,95 | 0,84 | ✗ |
| alargada | G | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 428,79 | ✓ |
| alargada | G | Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,40 | ✓ |
| alargada | G | Fiscalização a mais de uma proibição por horas | 1 000,00 | 658,70 | ✓ |
| alargada | G | Excesso por passagem fora da ponta (todos os dias) | 2,50 | 4,56 | ✓ |
| alargada | G | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | 0,45 | ✓ |
| alargada | H | Excesso de tempo por passagem na ponta (s, intervalo de 90%) | 14,50 | 11,72 | ✓ |
| alargada | H | Opção H: parte do excesso que pode remover | 0,59 | 0,45 | ✓ |
| alargada | H | Passageiros a bordo, na ponta da tarde | 20,00 | 15,15 | ✓ |
| alargada | H | Ocupação dos lugares retirados | 0,95 | — | ✗ |
| alargada | H | Preço anual de estacionar noutro sítio, para quem perde o lugar | 555,60 | 1 154,76 | ✓ |
| alargada | H | Opções G e H: parte do valor do lugar perdida das 16h às 20h nos dias úteis | 0,45 | 0,70 | ✓ |
| alargada | H | Fiscalização a mais de uma proibição por horas | 1 000,00 | 1 741,11 | ✓ |
| alargada | H | Excesso por passagem fora da ponta (todos os dias) | 2,50 | — | ✗ |
| alargada | H | Parte dos carros deslocados que encontra lugar a menos de 150 m | 0,30 | — | ✗ |

Entradas que mais mudam o VAL da opção C na camada alargada (do mínimo ao máximo de cada uma):

| entrada | VAL no mínimo | VAL no máximo |
| --- | ---: | ---: |
| Excesso por passagem fora da ponta (todos os dias) | 710 € | 80 900 € |
| Excesso de tempo por passagem na ponta (s, intervalo de 90%) | −8 300 € | 61 800 € |
| Preço anual de estacionar noutro sítio, para quem perde o lugar | 32 700 € | −11 100 € |
| Opção C: parte do excesso que pode remover | 1 500 € | 37 000 € |
| Valor do tempo de um passageiro | 9 300 € | 39 400 € |
| Parte do preço do parque que é uma transferência: o parque tem lugares vagos | 12 500 € | 39 000 € |
| Multiplicador para quem espera nas paragens seguintes | 25 800 € | 48 400 € |
| Parte do atraso nos cruzamentos sem autocarros em sentido contrário que se deve a ligeiros, furgões e pesados | 14 500 € | 37 000 € |

### O que vale a pena medir

Quanto vale saber cada entrada antes de decidir, em valor atual (valor esperado da informação perfeita parcial, da simulação da camada alargada): só conta o que pode mudar a decisão. Saber tudo valeria cerca de 3 400 €.

| entrada | valor de saber antes de decidir |
| --- | ---: |
| Excesso por passagem fora da ponta (todos os dias) | 160 € |

### Cenários

VAL de cada opção em cenários com nome. Prudente: cada entrada que a medição ainda não cobre no extremo do seu intervalo menos favorável à opção, todas ao mesmo tempo; favorável: no extremo oposto. É um limite, não uma probabilidade: a simulação diz quão provável é cada resultado.

| opção | núcleo, 10 anos | prudente, 10 anos | central, 10 anos | favorável, 10 anos | núcleo, 20 anos | central, 20 anos |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B | −64 200 € | −145 900 € | 4 200 € | 306 700 € | −106 500 € | 11 400 € |
| C | −22 200 € | −69 800 € | 25 800 € | 271 600 € | −36 600 € | 47 100 € |
| E | −32 600 € | −81 900 € | 8 900 € | 204 200 € | −52 600 € | 20 300 € |
| G | −25 300 € | −68 900 € | −2 600 € | 80 800 € | −40 300 € | 1 100 € |
| H | −9 300 € | −39 500 € | 5 700 € | 71 900 € | −14 400 € | 14 300 € |

### Quem ganha e quem perde (camada alargada, valores centrais, por ano)

Em euros por ano; positivo é ganho, negativo é perda.

| grupo | B | C | E | G | H |
| --- | ---: | ---: | ---: | ---: | ---: |
| Viagens de passageiros com a opção em vigor (por ano) | 530 688 | 530 688 | 370 476 | 138 552 | 138 552 |
| Segundos poupados por viagem de passageiro | 3,4 | 2,8 | 3,7 | 7,1 | 6,0 |
| Lugares retirados | 21 | 10 | 21 | 21 | 10 |
| Passageiros dos autocarros: tempo | 6 600 € | 5 600 € | 5 100 € | 3 600 € | 3 100 € |
| Carris: horas de autocarro | 1 100 € | 930 € | 820 € | 500 € | 420 € |
| Quem segue de carro atrás de um autocarro | 200 € | 170 € | 150 € | 90 € | 80 € |
| Novos passageiros | 0 € | 0 € | 0 € | 10 € | 0 € |
| Toda a gente: custos externos das viagens que deixam o carro | 200 € | 170 € | 160 € | 110 € | 100 € |
| Toda a gente: custos externos das voltas à procura de lugar | −280 € | −130 € | −140 € | −110 € | −50 € |
| Carris e donos de carros: danos evitados | 390 € | 330 € | 230 € | 70 € | 60 € |
| Quem estaciona na rua | −10 300 € | −4 700 € | −5 000 € | −4 100 € | −1 900 € |
| Parques de estacionamento: avenças pagas por quem é deslocado (transferência) | 3 600 € | 1 600 € | 1 700 € | 1 400 € | 650 € |
| Câmara e EMEL: obra e fiscalização | −930 € | −780 € | −2 000 € | −2 000 € | −1 800 € |

## O que não tem preço

Efeitos que as contas não medem em dinheiro, ou só em parte: ++ melhora muito · + melhora · 0 não muda · − piora · −− piora muito · ? depende, ou não se sabe. Os pesos entre eles são da Câmara: não se dão.

| critério | indicador | B | C | E | G | H | grau | porquê |
| --- | --- | :---: | :---: | :---: | :---: | :---: | --- | --- |
| Fiabilidade da viagem de autocarro (o stress de não saber quando se chega) | Dispersão do tempo de passagem; impasses por semana | ++ | + | + | + | + | I | Sem o estacionamento de um lado, dois autocarros cruzam-se sem esperar (6,91 m livres; precisam de 5,80 m com espelhos): acabam os impasses e o tempo perdido no cruzamento com a R. Cor. Marques Leitão. B em toda a rua e a toda a hora; C só no troço mais longo; E, G e H só nas horas em que vigoram. |
| Acesso ao comboio e ao metro | Ligações perdidas em Entrecampos, no Oriente e no Campo Grande | + | + | + | + | + | I | A 744 liga a rua à Estação de Entrecampos (cerca de 12 min) e à Gare do Oriente (cerca de 14 min); a 46B ao Campo Grande e a Entrecampos. Um comboio perdido custa o intervalo até ao seguinte; a camada alargada conta o atraso de quem muda como atraso imprevisto, mas não a confiança de poder contar com a ligação. |
| Qualidade de vida de quem estaciona na rua | Minutos a mais por dia a procurar lugar e a andar; lugares de cargas e de pessoas com mobilidade reduzida | −− | − | − | − | − | I | Cerca de 21 lugares em B, E e G; 10 em C e H; nas opções por horas, só nessas horas. O custo em dinheiro está nas contas; aqui fica o resto: a incerteza de encontrar lugar, as cargas e descargas, quem tem mobilidade reduzida. |
| Ruído e ar na rua | Paragens, recuos e arranques de autocarros com o motor ligado; carros a circular à procura de lugar | + | + | + | + | + | P | Menos paragens, recuos e arranques de autocarros numa rua estreita, com prédios dos dois lados; do outro lado, mais carros às voltas à procura de lugar se não houver lugares livres perto. A camada alargada conta os custos externos das viagens tiradas ao carro; o ruído na própria rua não tem medição. |
| Segurança | Toques e manobras de recuo; velocidade; visibilidade nos cruzamentos | ? | ? | ? | ? | ? | P | Acabam os toques entre autocarros e carros estacionados e as manobras de recuo, e vê-se melhor quem atravessa; mas uma faixa mais larga convida a ir mais depressa (a camada alargada inclui medidas de acalmia). O efeito líquido só se sabe medindo a velocidade e os incidentes antes e depois. |
| Acesso de veículos de socorro | Veículos de socorro retidos na rua | + | + | + | + | + | NE | Uma ambulância ou um pronto-socorro também não cruza um autocarro em 4,90 m. A paragem seguinte chama-se Bombeiros Alvalade, mas não se verificou se os veículos do Regimento de Sapadores Bombeiros ou do INEM usam a rua. |
| Referência municipal de desenho de rua | Largura livre face ao perfil do manual (6,80 m entre faixas de estacionamento) | ++ | + | + | + | + | D | Com estacionamento só de um lado, a largura livre passa a 6,91 m, acima dos 6,80 m do manual: em toda a rua em B, só no troço mais longo em C, e só nas horas em que vigoram em E, G e H. |
| Quem ganha e quem perde | Viagens de passageiros por ano face a lugares retirados | ? | ? | ? | ? | ? | I | Os ganhos repartem-se por cerca de meio milhão de viagens de passageiros por ano, muitas de quem não tem carro; a perda concentra-se em cerca de 21 lugares. Quanto pesa cada grupo é uma escolha da Câmara: o quadro de quem ganha e quem perde dá os números. |
| Reversibilidade | Custo e tempo de desfazer | + | + | + | + | + | I | Sinais e tinta: qualquer opção se desfaz em dias e por pouco dinheiro. |

## Uma alternativa a estudar

Um espaço de cruzamento: o estacionamento de um lado retirado em cerca de 20 m a meio do troço B2, onde um autocarro se desvia para o outro passar: retira cerca de 4 lugares e custa, com eles, cerca de 15 500 € em valor atual. O efeito depende da geometria e não se pode estimar com estes dados; paga-se se poupar 9,4 horas de autocarro por ano: 7,5 s por passagem na ponta, ou 0,8 s por passagem a qualquer hora, quando o excesso removível medido na ponta é de cerca de 10 s.

## O que falta saber

O que falta saber, e o que mais mudaria estas conclusões:

- A ocupação do estacionamento nas ruas vizinhas não foi encontrada: não se sabe se os carros deslocados têm lugar perto.
- O atraso medido vem de um arquivo de terceiros que, em 2026, guardou uma cópia do feed a cada 8 a 45 minutos, em vez de 3 a 4 em 2025: o valor de 2026 não informa. Os registos de passagem pedidos à Carris (Lei n.º 26/2016) e os dados da PGIL pedidos à Câmara mostrariam o atraso atual.
- O tempo fora da ponta, os carros retidos, a fiabilidade, as ligações ao comboio, os novos passageiros e os danos só entram na camada alargada, com valores pressupostos até serem medidos; a segurança, o acesso de emergência e a qualidade de vida ficam nos critérios sem preço.
- Na plataforma Na Minha Rua, a Rua Ricardo Jorge tem a maior densidade de queixas de estacionamento abusivo das 25 ruas da zona (2,9 por 100 m, de maio de 2017 a maio de 2026), mas são apenas 6: um sinal, não uma prova.

## Conclusões

1. No núcleo, só com o medido e o documentado, nenhuma opção compensa os lugares que retira: a de menor perda é a H (VAL de −9 300 €, benefício/custo 0,61, probabilidade de VAL > 0 de 8%).
2. Para a opção H compensar no núcleo, seria preciso, por exemplo, um excesso de 23,6 s por passagem (medido: 14,5 s, até 23,9 s); ou que um lugar valesse no máximo 210 € por ano a quem o perde (central: 560 €).
3. Juntando os mecanismos que a medição ainda não vê, a valores centrais de fontes publicadas, a opção C compensa: VAL de 25 800 €, benefício/custo 1,82, positivo em 86% das simulações (benefício/custo de cada opção: B 1,07; C 1,82; E 1,21; G 0,93; H 1,24).
4. O que mais pode mudar a decisão, e por isso mais vale medir: excesso por passagem fora da ponta (todos os dias).
5. Fora das contas, a opção C melhora: fiabilidade da viagem de autocarro (o stress de não saber quando se chega); acesso ao comboio e ao metro; ruído e ar na rua; acesso de veículos de socorro; referência municipal de desenho de rua; reversibilidade; e piora: qualidade de vida de quem estaciona na rua.
6. A alternativa R (um espaço de cruzamento: o estacionamento de um lado retirado em cerca de 20 m a meio do troço B2, onde um autocarro se desvia para o outro passar) retira cerca de 4 lugares e paga-se com 7,5 s poupados por passagem na ponta (0,8 s a qualquer hora): merece um estudo de geometria.
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
- Department for Transport (2025), Value for Money Framework, maio de 2025, caixa 5.1, <https://assets.publishing.service.gov.uk/media/682ccabf1be3f53ed5f4534e/value-for-money-framework.pdf>
- Rádio Renascença (15/06/2026), «Banco de Portugal prevê défice de 0,2% este ano e de 0,5% em 2027» (projeções do Boletim Económico de junho de 2026), <https://rr.pt/noticia/economia/2026/06/15/banco-de-portugal-preve-defice-de-02-este-ano-e-de-05-em-2027/474408/>
- Paulley, N. et al. (2006), The demand for public transport: the effects of fares, quality of service, income and car ownership, Transport Policy 13(4), 295–306, <https://doi.org/10.1016/j.tranpol.2005.12.004>
- ISEG – CEsGE para a ANSR (2021), O Impacto Económico e Social da Sinistralidade Rodoviária em Portugal (dados de 2019), secção 5.4 e quadro 5.1, <https://ansr.pt/sites/default/files/noticias-docs/O%20Impacto%20Economico%20e%20Social%20da%20Sinistralidade%20-%20PT.pdf>
- Código da Estrada, art. 18.º (Distância entre veículos), n.os 2 a 4, versão consolidada, <https://diariodarepublica.pt/dr/legislacao-consolidada/decreto-lei/1994-34485875>
- Portaria n.º 135/2020, de 2 de junho, que altera e republica o Regulamento Técnico de Segurança contra Incêndio em Edifícios (Portaria n.º 1532/2008), art. 4.º, n.º 7, e art. 5.º, n.º 1, <https://diariodarepublica.pt/dr/detalhe/portaria/135-2020-134991810>
