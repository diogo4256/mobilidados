# Rua Ricardo Jorge (Alvalade, Lisboa)

> A faixa livre entre as duas faixas de estacionamento deixa cruzar dois autocarros programados nos dois sentidos?

Gerado por `mobilidados run` a partir das tabelas em `tables/`. Cada afirmação diz em que se apoia: **M** medido em dados oficiais · **D** escrito em documento oficial · **I** inferido · **P** pressuposto · **NE** não encontrado ou não verificado (≠ não existe).

- **[M]** O eixo da rua tem 209,25 m.  
  <sub>Comprimento do eixo da rua, em coordenadas projetadas.</sub>
- **[M]** Segundo a rede viária da Câmara, a rua tem dois sentidos: em 8 de 8 pontos verificados ao longo da rua, a circulação é permitida em ambos os sentidos.  
  <sub>Consulta à rede viária municipal em pontos ao longo do eixo.</sub>
- **[M]** Nos troços com estacionamento cartografado dos dois lados (116 m da rua), a largura livre entre eles vai de 4,78 a 5,68 m (mediana de 4,90 m).  
  <sub>Perfis transversais a cada 0,5 m; as larguras são lidas só nos polígonos cartografados. · Só contam os perfis com estacionamento cartografado dos dois lados e até 7,00 m de largura livre: 5 dos 240 perfis com estacionamento dos dois lados têm mais largura livre e ficaram de fora. Cartografia: fotogrametria aérea de maio de 2016, restituição e completagem de campo em 2020, homologada pela DGT (registo em dados.gov.pt). Exatidão planimétrica assumida em ≤0,30 m por aresta (valor da DGT para cartografia à escala de planta, citado num parecer da DGT de 2025); o erro médio quadrático da própria cartografia 1:1000 não foi encontrado.</sub>
- **[M]** O estacionamento cartografado ocupa 2,01 m do lado NO e 2,01 m do lado SE (medianas).  
  <sub>Área cartografada, não carros estacionados.</sub>
- **[M]** Segundo o horário, as carreiras 744, 46B passam nesta rua. Em 2026-10-27: 56 viagens SO→NE e 76 viagens NE→SO (no máximo 4 e 6 por hora).  
  <sub>Viagens contadas numa paragem de referência em cada sentido; é o horário, não a operação observada.</sub>
- **[M]** Tempo previsto da paragem 11315 à seguinte (11317 Esc. Padre António Vieira, a 321 m em linha reta): mediana de 65 s em todas as viagens do horário (pelo menos 17,8 km/h) e de 82 s em 2026-10-27 (pelo menos 14,1 km/h).  
  <sub>Chegada à paragem seguinte menos partida da paragem de referência; distância em linha reta entre as duas.</sub>
- **[M]** Tempo previsto da paragem 11318 à seguinte (11314 Bombeiros Alvalade, a 222 m em linha reta): mediana de 50 s em todas as viagens do horário (pelo menos 16,0 km/h) e de 63 s em 2026-10-27 (pelo menos 12,7 km/h).  
  <sub>Chegada à paragem seguinte menos partida da paragem de referência; distância em linha reta entre as duas.</sub>
- **[D]** Veículo de referência: Carris MAN 18.310 / Caetano City Gold (12 m). Carroçaria com 2,50 m de largura (ficha da frota da Carris (carris.pt › Descubra › Frota), veículo 2643).
- **[P]** Veículo de referência: Carris MAN 18.310 / Caetano City Gold (12 m). Largura com espelhos assumida em 2,90 m (pressuposto: não há largura oficial com espelhos; +0,40 m como na ficha do Mercedes-Benz eCitaro).
- **[P]** Veículo de referência: Ligeiro típico. Carroçaria com 1,80 m de largura (pressuposto: largura típica de um ligeiro europeu; a validar no local).
- **[P]** Veículo de referência: Ligeiro típico. Largura com espelhos assumida em 2,05 m (pressuposto: largura típica com espelhos abertos; a validar no local).
- **[I]** Com o estacionamento ocupado dos dois lados e os carros dentro dos lugares, dois autocarros precisam de pelo menos 5,00 m (só a carroçaria, sem espaço nenhum entre eles; 5,80 m com espelhos) e a largura livre mediana é de 4,90 m: folga de −0,10 m. Um autocarro e um ligeiro precisam de pelo menos 4,30 m: folga de +0,60 m (+0,35 m contando com os espelhos do ligeiro).  
  <sub>Soma das larguras dos veículos lado a lado (envelope estático), sem simular a trajetória nem as curvas. · Admite que os carros estacionados ficam dentro das faixas cartografadas; overhang_sensitivity.csv mostra quanto a folga diminui se saírem delas. Só com a carroçaria, a folga entre dois autocarros é de −0,22 m na largura livre mínima, −0,10 m na mediana e +0,08 m no percentil 95. Em 77% dos perfis contados na largura livre, ela fica abaixo dos 5,00 m de duas carroçarias de autocarro. Espelhos: entre dois autocarros contam os quatro espelhos; entre um autocarro e um ligeiro só contam os do ligeiro, porque se admite que os do autocarro passam por cima dele (pressuposto). Exatidão planimétrica assumida em ≤0,30 m por aresta (valor da DGT para cartografia à escala de planta, citado num parecer da DGT de 2025); o erro médio quadrático da própria cartografia 1:1000 não foi encontrado.</sub>
- **[I]** Sem o estacionamento do lado NO, a largura livre passaria a ir de 6,79 a 7,68 m (mediana de 6,91 m); sem o do lado SE, de 6,78 a 8,06 m (mediana de 6,92 m); sem estacionamento nenhum, mediana de 8,92 m. Dois autocarros precisam de pelo menos 5,00 m (5,80 m com espelhos): só com estacionamento de um lado, a folga seria de +1,91 m (+1,11 m com espelhos).  
  <sub>Largura livre mais a faixa (ou as faixas) de estacionamento cartografada no mesmo perfil, em cada perfil com estacionamento dos dois lados. · Admite que o espaço do estacionamento passa para a faixa de rodagem e que nada mais o ocupa; mede uma opção, não é um projeto.</sub>
- **[I]** Retirar o estacionamento de um lado, nos troços com estacionamento dos dois lados, retiraria 116 m de estacionamento cartografado (cerca de 19 a 23 lugares); dos dois lados, 232 m (cerca de 38 a 46 lugares). Lugares contados a 5,00–6,00 m cada (pressuposto). Em toda a rua, o estacionamento cartografado mede 122,5 m do lado NO e 137,0 m do lado SE.  
  <sub>Comprimento dos troços com estacionamento dos dois lados (o mesmo da largura livre), por cada lado retirado, a dividir pelo comprimento mais longo e pelo mais curto de um lugar; os comprimentos em toda a rua vêm de parking_strip_lengths.csv. · Área de estacionamento cartografada, não lugares contados: entradas e outras interrupções dentro das faixas não são descontadas. O comprimento de um lugar é um pressuposto.</sub>
- **[I]** Segundo o horário, em 2026-10-27 há 6–7 encontros entre autocarros em sentidos opostos nesta rua (admitindo uma velocidade constante de 15/20 km/h); 1–2 acontecem nos troços com estacionamento dos dois lados.  
  <sub>Sobreposição dos intervalos em que cada autocarro está na rua, a velocidade constante e com as horas do horário; é o horário, não uma observação. · Os pontos de encontro saem de um modelo de velocidade constante, sem tempo parado nas paragens: um encontro a poucos metros do limite de um troço pode acontecer dentro dele. A 12,7 km/h, a mais baixa das velocidades entre paragens em 2026-10-27 (distância em linha reta a dividir pelo tempo mediano do horário), o modelo dá 7.</sub>
- **[M]** Foram atribuídas à rua 6 ocorrências da categoria «Estacionamento abusivo» (2017-05-05 – 2026-05-31, a ≤12 m do eixo): 2,87 por 100 m, 1.ª de 25 ruas com pelo menos 100 m na envolvente.  
  <sub>Cada ocorrência georreferenciada dos dados abertos é atribuída ao eixo de rua mais próximo. · Uma ocorrência não é uma infração provada e as contagens são pequenas. A ordenação divide as ocorrências contadas dentro da janela de atribuição (um retângulo que vai 300 m além da rua) pelo comprimento total de cada rua, incluindo a parte fora da janela: isso favorece as ruas que cabem inteiras na janela, como a deste caso.</sub>
- **[M]** Das 69 ruas da zona com autocarros no horário, 2 têm dois sentidos e estacionamento dos dois lados, com menos de 5,5 m de largura livre em pelo menos 30 m (Rua Ricardo Jorge e Rua Teixeira de Pascoais); destas, 1 com autocarros nos dois sentidos: Rua Ricardo Jorge.  
  <sub>Perfis a cada 3 m em todos os eixos de rua por onde passam autocarros, medidos com parâmetros próprios desta pesquisa (comprimento do perfil e tolerâncias), e não com os da rua do caso; o sentido de trânsito é lido na rede viária num só ponto por rua. · Os limiares (5,5 m de largura livre, 30 m de extensão) são parâmetros escolhidos para esta análise, não valores de um documento técnico.</sub>
- **[D]** Lisboa: o Desenho da Rua – Manual de espaço público, p. 152 (perfil de referência): Rua de dois sentidos, duas vias, estacionamento longitudinal dos dois lados: largura entre as faixas de estacionamento: 6,80 m. Âmbito: Ruas de dois sentidos com duas vias de trânsito e estacionamento dos dois lados. Mediana medida: 4,90 m (−1,90 m).  
  <sub>0,40 m (sobrelargura) + 3,00 m + 3,00 m + 0,40 m (sobrelargura) = 6,80 m; nota ao desenho: sem sobrelargura, a largura recomendada por via é 3,25 m, ou seja 6,50 m</sub>
- **[D]** Schriftliche Anfrage Drucksache 19/25490, Antwort vom 27.03.2026, p. 3 (citado em documento oficial): Faixa de rodagem para o cruzamento de dois autocarros de carreira (RASt 06, citada): 6,50 m. Âmbito: Diretriz técnica alemã para ruas urbanas (RASt 06), citada pelo Senado de Berlim; não é lei portuguesa. Mediana medida: 4,90 m (−1,60 m).  
  <sub>Espaço livre de 7,50 m (7,00 m em condições restritas) com distâncias de segurança, donde 6,50 m de faixa de rodagem; 6,00 m é referido como mínimo da RASt 06</sub>
- **[NE]** Não há observação de campo de dois autocarros a cruzar-se nesta rua: os encontros são estimativas do horário.
- **[NE]** A Carris não publica atrasos nem incidentes por rua.
- **[NE]** A largura dos autocarros com espelhos não foi encontrada em ficha oficial: a largura com espelhos usada é um pressuposto.
- **[NE]** A posição real dos carros estacionados (sobressaída das faixas) não foi medida no local.

## Fontes

| id | origem | obtido | licença | sha256 |
| --- | --- | --- | --- | --- |
| area_axes | <https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/79> | 2026-10-24 | not stated by the service (CML MapaBase; the open 'Rede Viária' dataset is CC0, identity with this layer not verified) | `3096da389677…` area_axes.json |
| area_cartography | <https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/53> | 2026-10-24 | CC-BY-4.0 | `6d49fe735c72…` area_cartography.json |
| area_network_identify | <https://websig.cm-lisboa.pt/MuniSIG/REST/sites/BCK_LisboaInterativa_22Set26/map/mapservices/43/rest/services/x/MapServer/identify> | 2026-10-24 | not stated (Lisboa Interativa public viewer, guest access) | `0f584f1874ef…` area_network_identify.json |
| carris_gtfs | <https://files.mobilitydatabase.org/mdb-2929/mdb-2929-202610200105/mdb-2929-202610200105.zip> | 2026-10-24 | not stated at the download endpoint (not redistributed) | `c7550ea2d2f0…` carris_gtfs.zip |
| cartography | <https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/53> | 2026-10-24 | CC-BY-4.0 | `87c633260730…` cartography.json |
| na_minha_rua | 10 ficheiros, p. ex. <https://dados.cm-lisboa.pt/dataset/fe6c4ef5-c021-48d0-9d1b-d4388769e3be/resource/d66d2141-5a5e-4725-9593-ac2da4e65f17/download/2017.csv> | 2026-10-22 | CC-BY-4.0 | `5be40828a57b…` na_minha_rua/2017.csv<br>`ef31c04e2e67…` na_minha_rua/2018.csv<br>`dd1283b12cc5…` na_minha_rua/2019.csv<br>+7 |
| network_identify | <https://websig.cm-lisboa.pt/MuniSIG/REST/sites/BCK_LisboaInterativa_22Set26/map/mapservices/43/rest/services/x/MapServer/identify> | 2026-10-24 | not stated (Lisboa Interativa public viewer, guest access) | `71a5fe259fc7…` network_identify.json |
| street_axes | <https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/79> | 2026-10-24 | not stated by the service (CML MapaBase; the open 'Rede Viária' dataset is CC0, identity with this layer not verified) | `902bbeda01db…` street_axes.json |

## Atribuição

- © Câmara Municipal de Lisboa, <https://dados.gov.pt/datasets/cartografia-numerica-vetorial>, CC-BY-4.0 (<https://creativecommons.org/licenses/by/4.0/>).
- © Câmara Municipal de Lisboa, <https://dados.gov.pt/datasets/ocorrencias-na-minha-rua-lx>, CC-BY-4.0 (<https://creativecommons.org/licenses/by/4.0/>).

Os dados foram trabalhados: as tabelas e as figuras são medições, contagens e agregações feitas pelo mobilidados; não são publicações da entidade de origem, que não as subscreve.
