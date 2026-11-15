# Rua Ricardo Jorge (Alvalade): espaço para os autocarros se cruzarem

*Versão de 2026-11-15.*

**Dossier técnico a partir de dados públicos.** Cada número remete, entre parênteses retos, para um facto do anexo C,
que diz de onde vem, como foi obtido e que reservas tem. A letra diz em que se apoia: **M** medido em dados oficiais,
**D** escrito em documento oficial, **I** inferido desses dados, **P** pressuposto. As fontes estão no anexo B; são
todas públicas, e qualquer pessoa pode refazer os números a partir delas.

## Resumo

Na Rua Ricardo Jorge passam autocarros da Carris nos dois sentidos. Onde há estacionamento dos dois lados, a faixa
que fica livre entre os carros estacionados é 1,90 m mais estreita do que o perfil de referência do manual de espaço
público da própria Câmara para este tipo de rua, e mais estreita do que a largura de dois autocarros com espelhos.
Na zona à volta, é a única rua com autocarros nos dois sentidos nesta situação.

- **4,90 m** de largura livre mediana, nos 117,5 m da rua com estacionamento cartografado dos dois lados. [M `free_width`]
- **6,80 m** é o perfil de referência da Câmara para uma rua de dois sentidos com estacionamento dos dois lados
  (Manual de espaço público, p. 152): faltam 1,90 m. [D `standard_cml_manual_two_way_profile`]
- **5,00 m** ocupam dois autocarros lado a lado só com a carroçaria, e 5,80 m com espelhos. Mesmo admitindo um erro
  de 0,30 m em cada aresta da cartografia a favor da rua, a largura livre seria de 5,50 m: ainda abaixo dos 5,80 m.
  [I `width_budget`, `width_accuracy`]
- **6–7 encontros por dia** entre autocarros em sentidos opostos nesta rua, segundo o horário; 4–5 deles entre dois
  autocarros da carreira 744. [I `encounters`]
- **+49%** de tempo no troço entre paragens, às 17h–19h dos dias úteis, face ao que o abrandamento dos troços vizinhos
  explicaria (posições GPS arquivadas). Claro em 2025; não confirmado em 2026, com muito menos dados. [I `delay`]
- **A opção medida:** sem o estacionamento de um dos lados nesses 117,5 m, a largura livre passaria a ter mediana de
  6,91 m. Custaria 117,5 m de estacionamento cartografado, cerca de 19 a 23 lugares. [I `without_parking`, `parking_removed`]

**Pedido à Câmara:** que os serviços confirmem estas larguras no local, nos três pontos do anexo A, e avaliem o perfil
da rua para que os autocarros que ali circulam se possam cruzar, informando da decisão tomada.

## 1. A rua e os autocarros

A rua tem 209,25 m de eixo [M `length`] e, segundo a rede viária da Câmara, dois sentidos de trânsito em 8 de 8 pontos
verificados [M `traffic`]. Segundo o horário da Carris, passam as carreiras 744 e 46B: num dia útil (2026-10-27),
56 viagens SO→NE e 76 viagens NE→SO, no máximo 4 e 6 por hora [M `transit`]. A 744 percorre a rua nos dois sentidos.

O veículo de referência é o autocarro standard de 12 m da Carris, com 2,50 m de carroçaria; os 12 modelos de
autocarro standard que a Carris publica têm 2,5 a 2,6 m de largura, pelo que este é o mais estreito
[D `vehicle_carris_man_city_gold_body`]. Nas posições GPS arquivadas no troço, a carreira 744 aparece sobretudo com
veículos de números 26xx (79% das posições, 64 veículos), a série do veículo de referência (2643) [M `fleet`].

## 2. A largura que o estacionamento deixa

![Largura livre e faixas de estacionamento ao longo da rua](results/figures/free_width_profile.png)

Medida na cartografia municipal de pormenor, em perfis transversais a cada 0,5 m, a largura livre entre as duas faixas
de estacionamento vai de 4,78 a 5,68 m, com mediana de 4,90 m, nos 117,5 m com estacionamento dos dois lados
[M `free_width`]. Cada faixa de estacionamento ocupa 2,01 m (mediana) [M `parking_strips`]. Em 77% dos perfis contados,
a largura livre fica abaixo dos 5,00 m que ocupam duas carroçarias de autocarro [I `width_budget`].

| Termo de comparação | Largura | Diferença face aos 4,90 m | Base |
| --- | ---: | ---: | --- |
| Perfil de referência da Câmara, rua de dois sentidos com estacionamento dos dois lados (Manual de espaço público, p. 152) | 6,80 m | −1,90 m | D: recomendação municipal |
| Faixa para o cruzamento de dois autocarros de carreira (RASt 06, diretriz alemã, citada pelo Senado de Berlim) | 6,50 m | −1,60 m | D: referência estrangeira, não é lei portuguesa |
| Dois autocarros, com espelhos | 5,80 m | −0,90 m | I, com a largura dos espelhos pressuposta (P) |
| Dois autocarros, só a carroçaria, sem espaço nenhum entre eles | 5,00 m | −0,10 m | I |
| Um autocarro e um ligeiro, só a carroçaria | 4,30 m | +0,60 m | I, com a largura do ligeiro pressuposta (P) |

![Repartição da largura: a largura livre ao lado da largura dos veículos que ali se cruzam](results/figures/width_budget.png)

**O que resiste ao erro da cartografia.** Admitindo 0,30 m de erro em cada aresta cartografada, a favor da rua, a
largura livre mediana seria de 5,50 m: ainda 0,30 m abaixo dos 5,80 m de dois autocarros com espelhos, e 1,30 m abaixo
dos 6,80 m do perfil de referência da Câmara [I `width_accuracy`]. A diferença só com a carroçaria (−0,10 m) fica
dentro dessa margem e não é usada sozinha. A comparação admite que os carros estacionados ficam dentro das faixas
cartografadas; se saírem delas, a largura livre é menor [I `width_budget`].

## 3. Com que frequência, e com que efeito

Segundo o horário de 2026-10-27, há 6–7 encontros por dia entre autocarros em sentidos opostos nesta rua (a 15 ou
20 km/h constantes); 1–2 acontecem nos troços com estacionamento dos dois lados. Por pares de carreiras: 744 × 744,
4–5; 744 × 46B, 2 [I `encounters`]. São estimativas do horário, não encontros observados.

![Tempo no troço entre paragens, por hora, face aos troços vizinhos](results/figures/delay_by_hour.png)

As posições GPS dos autocarros arquivadas entre 2025-02-17 e 2026-11-13 (437 dias úteis) mostram que, às 17h–19h, o
troço entre as paragens da rua (145 m) leva mais 49% de tempo do que o abrandamento dos troços vizinhos das mesmas
carreiras faria esperar (intervalo de confiança de 90%: +34% a +65%). Em 2025, +60% (+42% a +80%); em 2026, +4%
(−17% a +31%), com muito menos posições, o que não confirma o excesso nesse ano [I `delay`]. Nas horas bem cobertas
pelo arquivo, são mais 14 s por passagem (6 a 24 s) [I `delay_seconds`]. Estes dados dizem onde se perde o tempo, não
porquê, e vêm de um arquivo do feed em tempo real da Carris mantido por terceiros, não do registo da própria Carris.

## 4. Na zona

Das 69 ruas da zona com autocarros no horário, 2 têm dois sentidos e estacionamento dos dois lados com menos de 5,5 m
de largura livre em pelo menos 30 m (Rua Ricardo Jorge e Rua Teixeira de Pascoais); destas, só a Rua Ricardo Jorge tem
autocarros nos dois sentidos [M `area_pattern`]. Nas outras ruas da zona com autocarros, esta combinação não se repete.

## 5. A opção medida, e o que custa

Sem o estacionamento do lado NO nos troços com estacionamento dos dois lados, a largura livre passaria a ter mediana
de 6,91 m; sem o do lado SE, 6,92 m. Dois autocarros teriam uma folga de +1,91 m (+1,11 m com espelhos)
[I `without_parking`]. Isso retiraria 117,5 m de estacionamento cartografado, cerca de 19 a 23 lugares, contados a
5,00–6,00 m cada (pressuposto); em toda a rua, o estacionamento cartografado mede 122,5 m do lado NO e 137,0 m do lado
SE [I `parking_removed`]. É uma opção medida, não um projeto: o desenho da rua cabe aos serviços.

## 6. O que estes dados não mostram, e como se supre

Nada disto exige observação no local por quem escreve: o que os dados públicos não cobrem, pede-se a quem o tem.

| O que falta | Porque importa | Como se supre |
| --- | --- | --- |
| A medição vem da cartografia (fotogrametria de 2016, completagem de campo em 2020), não do local | Uma marcação pode ter mudado | Os serviços medem nos três pontos do anexo A |
| Os encontros vêm do horário; o arquivo GPS regista cada autocarro de poucos em poucos minutos, e um autocarro atravessa o troço em menos de um minuto (27 s fora da ponta, 48 s na ponta) | Não há registo de encontros reais | Pedir à Carris os registos do seu sistema de apoio à exploração para o troço |
| A largura dos autocarros com espelhos não é publicada (aqui, 2,90 m, pressuposto) | A comparação com espelhos depende dela | Pedir à Carris a largura com espelhos dos veículos das carreiras 744 e 46B |
| A Carris não publica que modelos correspondem a que números de frota; a 46B aparece só com veículos de números 2xx | Se forem mais pequenos, os encontros 744 × 46B pedem menos largura; o caso assenta nos encontros 744 × 744 | Pedir à Carris os modelos das séries 26xx e 2xx |
| O tempo perdido não tem causa atribuída, e 2026 tem poucos dados | Estacionamento, autocarros em sentido contrário ou um semáforo podem contribuir | Pedir à Carris os tempos de percurso e as ocorrências registadas na rua |
| Não se sabe quando nem com que fundamento o estacionamento foi marcado dos dois lados | Saber se o perfil atual foi decidido tendo os autocarros em conta | Pedir à Câmara o projeto ou a deliberação (Lei n.º 26/2016) |

Os pedidos de documentos fazem-se por escrito ao abrigo da Lei n.º 26/2016, de 22 de agosto (artigos 12.º e 15.º),
que dá à entidade 10 dias para responder.

## Anexo A: pontos de verificação

Pontos ao longo do eixo da rua (s: distância desde a Av. do Rio de Janeiro) onde os serviços podem medir a largura
livre no local:

| s | Quarteirão | Coordenadas (lat, lon) | Largura livre cartografada |
| ---: | --- | --- | ---: |
| 60 m | B1 (Av. do Rio de Janeiro → R. Cor. Marques Leitão) | 38.756950, −9.139441 | 4,87 m |
| 122 m | B2 (R. Cor. Marques Leitão → R. Constantino Fernandes) | 38.757165, −9.138783 | 4,90 m |
| 180 m | B3 (R. Constantino Fernandes → R. Carlos Mayer) | 38.757363, −9.138165 | 5,04 m |

## Anexo B: fontes

Dados (a impressão digital SHA-256, aqui abreviada, identifica a versão exata usada):

- Câmara Municipal de Lisboa, *Cartografia numérica vetorial 1:1000* (fotogrametria de 2016, completagem de campo em
  2020, homologada pela DGT), serviço MapaBase_WGS84, camada 53,
  <https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/53>. Obtida em 2026-10-24. Licença
  CC BY 4.0. SHA-256 `87c633260730…` (rua) e `6d49fe735c72…` (zona).
- Câmara Municipal de Lisboa, *Eixos de via*, serviço MapaBase_WGS84, camada 79,
  <https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/79>. Obtidos em 2026-10-24. Licença não
  declarada pelo serviço. SHA-256 `902bbeda01db…` (rua) e `3096da389677…` (zona).
- Câmara Municipal de Lisboa, *Sentidos de trânsito* (rede viária do visualizador Lisboa Interativa, acesso de
  convidado), <https://websig.cm-lisboa.pt/MuniSIG/REST/sites/BCK_LisboaInterativa_22Set26/map/mapservices/43/rest/services/x/MapServer/identify>.
  Consultada em 2026-10-24. Licença não declarada. SHA-256 das respostas `71a5fe259fc7…` (rua) e `0f584f1874ef…` (zona).
- Carris, *horário GTFS*, cópia arquivada pela Mobility Database (feed mdb-2929, versão de 2026-10-20),
  <https://files.mobilitydatabase.org/mdb-2929/mdb-2929-202610200105/mdb-2929-202610200105.zip>. Obtido em 2026-10-24.
  Licença não declarada. SHA-256 `c7550ea2d2f0…`.
- Posições em tempo real dos autocarros da Carris, de 2025-02-17 a 2026-11-13, arquivo mantido por terceiros
  (LIVREpt/lisboa_carris_api, commit db6b8e782c0f),
  <https://github.com/LIVREpt/lisboa_carris_api/tree/db6b8e782c0ffaddf602fc3bcb04b335969967d8>. Obtidas em 2026-11-14.
  Licença não declarada. SHA-256 `70c6c40548d8…` (posições) e `3534640dd2ce…` (registos).

Documentos:

- Câmara Municipal de Lisboa, *Lisboa: o Desenho da Rua – Manual de espaço público*, 2018, ISBN 978-972-8403-46-1,
  p. 152, <https://recrutamento.cm-lisboa.pt/cmlisboa-wirerecruit/uploads/writer_file/document/161/manual_de_espaco_publico.pdf>.
  SHA-256 `5d540643094e…`.
- Abgeordnetenhaus Berlin, *Schriftliche Anfrage Drucksache 19/25490*, resposta de 27.03.2026, p. 3 (cita a
  diretriz alemã RASt 06), <https://pardok.parlament-berlin.de/starweb/adis/citat/VT/19/SchrAnfr/S19-25490.pdf>.
  SHA-256 `89da5cda9d62…`.
- Carris, fichas da frota, *Autocarros Standard*, <https://www.carris.pt/descubra/frota/autocarros-standard/>.
  Consultadas em 2026-11-15.
- Lei n.º 26/2016, de 22 de agosto (acesso aos documentos administrativos), artigos 12.º e 15.º.

## Anexo C: factos citados

Copiados, sem alterações, da lista de factos apurados do caso: os que o texto cita e aqueles em que estes se apoiam.

- **[M] `free_width`** Nos troços com estacionamento cartografado dos dois lados (117,5 m da rua), a largura livre entre eles vai de 4,78 a 5,68 m (mediana de 4,90 m).  
  *Método:* Perfis transversais a cada 0,5 m; as larguras são lidas só nos polígonos cartografados.  
  *Reservas:* Só contam os perfis com estacionamento cartografado dos dois lados e até 7,00 m de largura livre: 5 dos 240 perfis com estacionamento dos dois lados têm mais largura livre e ficaram de fora. Cartografia: fotogrametria aérea de maio de 2016, restituição e completagem de campo em 2020, homologada pela DGT (registo em dados.gov.pt). Exatidão planimétrica assumida em ≤0,30 m por aresta (valor da DGT para cartografia à escala de planta, citado num parecer da DGT de 2025); o erro médio quadrático da própria cartografia 1:1000 não foi encontrado.
- **[D] `standard_cml_manual_two_way_profile`** Lisboa: o Desenho da Rua – Manual de espaço público, p. 152 (perfil de referência): Rua de dois sentidos, duas vias, estacionamento longitudinal dos dois lados: largura entre as faixas de estacionamento: 6,80 m. Âmbito: Ruas de dois sentidos com duas vias de trânsito e estacionamento dos dois lados. Mediana medida: 4,90 m (−1,90 m).  
  *Reservas:* 0,40 m (sobrelargura) + 3,00 m + 3,00 m + 0,40 m (sobrelargura) = 6,80 m; nota ao desenho: sem sobrelargura, a largura recomendada por via é 3,25 m, ou seja 6,50 m
- **[I] `width_budget`** Com o estacionamento ocupado dos dois lados e os carros dentro dos lugares, dois autocarros precisam de pelo menos 5,00 m (só a carroçaria, sem espaço nenhum entre eles; 5,80 m com espelhos) e a largura livre mediana é de 4,90 m: folga de −0,10 m. Um autocarro e um ligeiro precisam de pelo menos 4,30 m: folga de +0,60 m (+0,35 m contando com os espelhos do ligeiro).  
  *Método:* Soma das larguras dos veículos lado a lado (envelope estático), sem simular a trajetória nem as curvas.  
  *Reservas:* Admite que os carros estacionados ficam dentro das faixas cartografadas; se saírem delas 0,10, 0,20 ou 0,30 m de cada lado, a folga entre dois autocarros, só com a carroçaria, passa a −0,30, −0,50 ou −0,70 m. Só com a carroçaria, a folga entre dois autocarros é de −0,22 m na largura livre mínima, −0,10 m na mediana e +0,08 m no percentil 95. Em 77% dos perfis contados, a largura livre fica abaixo dos 5,00 m que ocupam duas carroçarias de autocarro. Espelhos: entre dois autocarros contam os quatro espelhos; entre um autocarro e um ligeiro só contam os do ligeiro, porque se admite que os do autocarro passam por cima dele (pressuposto). Exatidão planimétrica assumida em ≤0,30 m por aresta (valor da DGT para cartografia à escala de planta, citado num parecer da DGT de 2025); o erro médio quadrático da própria cartografia 1:1000 não foi encontrado.
- **[I] `width_accuracy`** Mesmo que cada aresta cartografada estivesse 0,30 m fora do sítio a favor da rua, a largura livre mediana seria de 5,50 m, ainda 0,30 m abaixo dos 5,80 m que dois autocarros ocupam com espelhos; só com a carroçaria, a folga de −0,10 m fica dentro dessa margem. Com essa margem, ficaria 1,30 m abaixo dos 6,80 m do perfil de referência de Lisboa: o Desenho da Rua – Manual de espaço público (p. 152).  
  *Método:* Largura livre mediana mais duas vezes a exatidão declarada por aresta (as duas arestas da faixa livre, ambas a favor da rua).
- **[I] `encounters`** Segundo o horário, em 2026-10-27 há 6–7 encontros entre autocarros em sentidos opostos nesta rua (admitindo uma velocidade constante de 15/20 km/h); 1–2 acontecem nos troços com estacionamento dos dois lados. Por pares de carreiras: 744 x 744, 4–5; 744 x 46B, 2.  
  *Método:* Sobreposição dos intervalos em que cada autocarro está na rua, a velocidade constante e com as horas do horário; é o horário, não uma observação.  
  *Reservas:* Os pontos de encontro saem de um modelo de velocidade constante, sem tempo parado nas paragens: um encontro a poucos metros do limite de um troço pode acontecer dentro dele. A 12,7 km/h, a mais baixa das velocidades entre paragens em 2026-10-27 (distância em linha reta a dividir pelo tempo mediano do horário), o modelo dá 7.
- **[I] `delay`** Nos dias úteis de 2025-02-17 a 2026-11-13 (437 dias), às 17h–19h, a diferença entre o tempo dos autocarros das carreiras 744 e 46B no troço entre paragens (s = 45–190 m, 145 m) e o que o abrandamento dos troços vizinhos das mesmas carreiras, à mesma hora, faria esperar a partir das 10h–17h foi de +49% (intervalo de confiança de 90%: +34% a +65%). Por ano: em 2025, +60% (+42% a +80%; 217 dias); em 2026, +4% (−17% a +31%; 220 dias). O intervalo de 2026 inclui 0: os dados desse ano não confirmam o excesso.  
  *Método:* Ocupação (lei de Little): posições GPS no troço e em dois troços de controlo de 550 m, a 150 m antes e depois dele ao longo de cada carreira; o rácio entre a ponta e fora da ponta não depende do número de autocarros nem da frequência dos registos. Intervalos de confiança por reamostragem de dias inteiros (2000 réplicas).  
  *Reservas:* Por carreira e sentido: 46B NE→SO +46% (+15% a +86%); 744 SO→NE +42% (+22% a +63%); 744 NE→SO +57% (+36% a +81%). Com outras escolhas razoáveis (horas de ponta, distância e comprimento dos troços de controlo, idade máxima das posições, alcance da contagem de passagens), o rácio vai de +44% a +51%. Posições do arquivo público LIVREpt/lisboa_carris_api (commit db6b8e782c0f), que recolhe o feed em tempo real da Carris através de um intermediário (rt.jdcp.workers.dev): não é o registo da própria Carris, e nenhum dos dois indica licença. Mede onde se perde o tempo, não porquê: o estacionamento, os autocarros em sentido contrário, uma fila vinda de um cruzamento ou um semáforo podem todos contribuir. Dias úteis: de segunda a sexta, sem os feriados do perfil da cidade (18 nesse período).
- **[I] `without_parking`** Sem o estacionamento do lado NO, a largura livre passaria a ir de 6,79 a 7,68 m (mediana de 6,91 m); sem o do lado SE, de 6,78 a 8,06 m (mediana de 6,92 m); sem estacionamento nenhum, mediana de 8,92 m. Dois autocarros precisam de pelo menos 5,00 m (5,80 m com espelhos): só com estacionamento de um lado, a folga seria de +1,91 m (+1,11 m com espelhos).  
  *Método:* Largura livre mais a faixa (ou as faixas) de estacionamento cartografada no mesmo perfil, em cada perfil com estacionamento dos dois lados.  
  *Reservas:* Admite que o espaço do estacionamento passa para a faixa de rodagem e que nada mais o ocupa; mede uma opção, não é um projeto.
- **[I] `parking_removed`** Retirar o estacionamento de um lado, nos troços com estacionamento dos dois lados, retiraria 117,5 m de estacionamento cartografado (cerca de 19 a 23 lugares); dos dois lados, 235 m (cerca de 39 a 47 lugares). Lugares contados a 5,00–6,00 m cada (pressuposto). Em toda a rua, o estacionamento cartografado mede 122,5 m do lado NO e 137,0 m do lado SE.  
  *Método:* Comprimento dos troços com estacionamento dos dois lados (o mesmo da largura livre), por cada lado retirado, a dividir pelo comprimento mais longo e pelo mais curto de um lugar; os comprimentos em toda a rua somam todos os perfis com estacionamento de cada lado.  
  *Reservas:* Área de estacionamento cartografada, não lugares contados: entradas e outras interrupções dentro das faixas não são descontadas. O comprimento de um lugar é um pressuposto.
- **[M] `length`** O eixo da rua tem 209,25 m.  
  *Método:* Comprimento do eixo da rua, em coordenadas projetadas.
- **[M] `traffic`** Segundo a rede viária da Câmara, a rua tem dois sentidos: em 8 de 8 pontos verificados ao longo da rua, a circulação é permitida em ambos os sentidos.  
  *Método:* Consulta à rede viária municipal em pontos ao longo do eixo.
- **[M] `transit`** Segundo o horário, as carreiras 744, 46B passam nesta rua. Em 2026-10-27: 56 viagens SO→NE e 76 viagens NE→SO (no máximo 4 e 6 por hora).  
  *Método:* Viagens contadas numa paragem de referência em cada sentido; é o horário, não a operação observada.
- **[D] `vehicle_carris_man_city_gold_body`** Veículo de referência: Carris MAN 18.310 / Caetano City Gold (12 m). Carroçaria com 2,50 m de largura (ficha da frota da Carris (carris.pt › Descubra › Frota), veículo 2643; os 12 modelos de autocarro standard que a Carris publica têm 2,5 a 2,6 m de largura (consultado em 2026-11-15), pelo que este é o mais estreito).
- **[M] `fleet`** Nas posições arquivadas no troço, a carreira 46B aparece com veículos de números 2xx (100% das posições, 24 veículos); a carreira 744 aparece com veículos de números 26xx (79% das posições, 64 veículos) e 3xx (17% das posições, 7 veículos).  
  *Método:* Série de cada número de frota (os algarismos menos os dois últimos), nas posições que caem no troço medido.  
  *Reservas:* O arquivo não diz o modelo de cada veículo, e as fichas da frota publicadas pela Carris dão modelos, não números de frota: diz que séries passam na rua, não a sua largura.
- **[M] `parking_strips`** O estacionamento cartografado ocupa 2,01 m do lado NO e 2,01 m do lado SE (medianas).  
  *Método:* Área cartografada, não carros estacionados.
- **[I] `delay_seconds`** Nas 120 horas de ponta e 400 horas fora da ponta em que o arquivo tem posições a intervalos de 12 min no máximo (das de ponta, 118 em 2025 e 2 em 2026), um autocarro levou em média 27 s a percorrer o troço fora da ponta e 48 s na ponta, quando o abrandamento dos troços vizinhos faria esperar 33 s: mais 14 s por passagem (intervalo de confiança de 90%: 6 a 24 s).  
  *Método:* Segundos por passagem: posições no troço a dividir pelas passagens por segundo, contadas como viagens vistas a menos de 2000 m do troço, só nas horas em que os registos nunca distam mais de 12 min.  
  *Reservas:* O excesso em segundos depende muito da hora de ponta escolhida: só às 17h, 35 s; só às 18h, 2 s; o rácio muda pouco. As passagens contadas são 91% das do horário de 2026-10-27 nas mesmas horas; se faltarem passagens, os segundos estão sobrestimados na mesma proporção (o rácio não depende delas). Posições do arquivo público LIVREpt/lisboa_carris_api (commit db6b8e782c0f), que recolhe o feed em tempo real da Carris através de um intermediário (rt.jdcp.workers.dev): não é o registo da própria Carris, e nenhum dos dois indica licença.
- **[M] `area_pattern`** Das 69 ruas da zona com autocarros no horário, 2 têm dois sentidos e estacionamento dos dois lados, com menos de 5,5 m de largura livre em pelo menos 30 m (Rua Ricardo Jorge e Rua Teixeira de Pascoais); destas, 1 com autocarros nos dois sentidos: Rua Ricardo Jorge.  
  *Método:* Perfis a cada 3 m em todos os eixos de rua por onde passam autocarros, medidos com parâmetros próprios desta pesquisa (comprimento do perfil e tolerâncias), e não com os da rua do caso; o sentido de trânsito é lido na rede viária num só ponto por rua.  
  *Reservas:* Os limiares (5,5 m de largura livre, 30 m de extensão) são parâmetros escolhidos para esta análise, não valores de um documento técnico.
- **[P] `vehicle_carris_man_city_gold_mirrors`** Veículo de referência: Carris MAN 18.310 / Caetano City Gold (12 m). Largura com espelhos assumida em 2,90 m (pressuposto: não há largura oficial com espelhos; +0,40 m como na ficha do Mercedes-Benz eCitaro).
- **[P] `vehicle_car_typical_body`** Veículo de referência: Ligeiro típico. Carroçaria com 1,80 m de largura (pressuposto: largura típica de um ligeiro europeu; a validar no local).
- **[P] `vehicle_car_typical_mirrors`** Veículo de referência: Ligeiro típico. Largura com espelhos assumida em 2,05 m (pressuposto: largura típica com espelhos abertos; a validar no local).
