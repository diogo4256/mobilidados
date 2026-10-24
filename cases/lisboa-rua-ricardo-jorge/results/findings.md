# Rua Ricardo Jorge (Alvalade, Lisboa)

> A faixa livre entre as duas faixas de estacionamento deixa cruzar dois autocarros programados nos dois sentidos?

Gerado por `mobilidados run` a partir das tabelas em `tables/`. Cada afirmação diz em que se apoia: **M** medido em dados oficiais · **D** escrito em documento oficial · **I** inferido · **P** pressuposto · **NE** não encontrado ou não verificado (≠ não existe).

- **[M]** O eixo da rua tem 209,25 m.  
  <sub>Axis polyline length (projected CRS).</sub>
- **[M]** Segundo a rede viária da Câmara, a rua tem dois sentidos (verificado em 8 pontos ao longo da rua).  
  <sub>Identify on the routing network at stations along the axis.</sub>
- **[M]** Nos troços com estacionamento cartografado dos dois lados (116 m da rua), a largura livre entre eles vai de 4,78 a 5,68 m (mediana de 4,90 m).  
  <sub>Transects every 0.5 m, widths read from mapped polygons only. · Planimetric accuracy assumed ≤0.30 m per edge (DGT figure for plan-scale cartography, as quoted in a 2025 DGT opinion); the 1:1000 RMSE itself was not found.</sub>
- **[M]** O estacionamento cartografado ocupa 2,01 m do lado NO e 2,01 m do lado SE (medianas).  
  <sub>Mapped area, not parked vehicles.</sub>
- **[M]** Segundo o horário, as carreiras 744, 46B passam nesta rua. Em 2026-10-27: 56 viagens SO→NE e 76 viagens NE→SO (no máximo 4 e 6 por hora).  
  <sub>Trips counted at a reference stop per direction; timetable, not observed operation.</sub>
- **[M]** Tempo previsto da paragem 11315 à seguinte (11317 Esc. Padre António Vieira, a 321 m em linha reta): mediana de 65 s em todas as viagens do horário (pelo menos 17,8 km/h) e de 82 s em 2026-10-27 (pelo menos 14,1 km/h).  
  <sub>Arrival at the next stop minus departure from the reference stop; straight-line distance between stops.</sub>
- **[M]** Tempo previsto da paragem 11318 à seguinte (11314 Bombeiros Alvalade, a 222 m em linha reta): mediana de 50 s em todas as viagens do horário (pelo menos 16,0 km/h) e de 63 s em 2026-10-27 (pelo menos 12,7 km/h).  
  <sub>Arrival at the next stop minus departure from the reference stop; straight-line distance between stops.</sub>
- **[D]** Veículo de referência «Carris MAN 18.310 / Caetano City Gold (12 m)»: carroçaria com 2,50 m de largura (ficha da frota da Carris (carris.pt › Descubra › Frota), veículo 2643).
- **[P]** Largura de «Carris MAN 18.310 / Caetano City Gold (12 m)» com espelhos assumida em 2,90 m (pressuposto: não há largura oficial com espelhos; +0,40 m como na ficha do Mercedes-Benz eCitaro).
- **[P]** Veículo de referência «Ligeiro típico»: carroçaria com 1,80 m de largura (pressuposto: largura típica de um ligeiro europeu; a validar no local).
- **[P]** Largura de «Ligeiro típico» com espelhos assumida em 2,05 m (pressuposto: largura típica com espelhos abertos; a validar no local).
- **[I]** Com o estacionamento ocupado dos dois lados e os carros dentro dos lugares, dois autocarros precisam de 5,00 m (só a carroçaria; 5,80 m com espelhos) e a largura livre mediana é de 4,90 m: folga de −0,10 m. Um autocarro e um ligeiro precisam de 4,30 m: folga de +0,60 m (+0,35 m contando com o espelho do ligeiro).  
  <sub>Static envelope (sum of widths), not a swept-path simulation. · Assumes parked vehicles stay inside the mapped strips; see overhang_sensitivity.csv.</sub>
- **[I]** Sem o estacionamento do lado NO, a largura livre passaria a ir de 6,79 a 7,68 m (mediana de 6,91 m); sem o do lado SE, de 6,78 a 8,06 m (mediana de 6,92 m); sem estacionamento nenhum, mediana de 8,92 m. Dois autocarros precisam de 5,00 m (5,80 m com espelhos): só com estacionamento de um lado, a folga seria de +1,91 m (+1,11 m com espelhos).  
  <sub>Free width plus the mapped parking strip(s) on the same transect, at every station with parking on both sides. · Assumes the strip's space becomes carriageway and nothing else takes it; it measures an option, it is not a design.</sub>
- **[I]** Retirar o estacionamento de um lado, nos troços com estacionamento dos dois lados, retiraria 116 m de estacionamento cartografado (cerca de 19 a 23 lugares); dos dois lados, 232 m (cerca de 38 a 46 lugares). Lugares contados a 5,00–6,00 m cada (pressuposto). Em toda a rua, o estacionamento cartografado mede 122,5 m do lado NO e 137,0 m do lado SE.  
  <sub>Length of the stretches with parking on both sides (as in free_width), per side removed, divided by the longest and the shortest space length; the whole-street lengths are parking_strip_lengths.csv. · Mapped parking area, not counted spaces: entrances and other gaps inside the strips are not subtracted. The length of a space is an assumption.</sub>
- **[I]** Segundo o horário, há 6–7 encontros por dia útil entre autocarros em sentidos opostos nesta rua (admitindo uma velocidade constante de 15/20 km/h); 1–2 acontecem nos troços com estacionamento dos dois lados.  
  <sub>Presence-interval overlap at constant speed from scheduled times; timetable, not observation. · A 12,7 km/h, a velocidade mais baixa entre paragens que o horário de 2026-10-27 permite (é um mínimo), o modelo dá 7.</sub>
- **[M]** Foram atribuídas à rua 6 ocorrências da categoria «Estacionamento abusivo» (2017-05-05 – 2026-05-31, a ≤12 m do eixo): 2,87 por 100 m, 1.ª de 25 ruas com pelo menos 100 m na envolvente.  
  <sub>Nearest-street attribution of geolocated open-data records. · A report is not a proven infraction; counts are small.</sub>
- **[M]** Das 69 ruas da zona com autocarros no horário, 2 têm dois sentidos e estacionamento dos dois lados, com menos de 5,5 m de largura livre em pelo menos 30 m (Rua Ricardo Jorge e Rua Teixeira de Pascoais); destas, 1 com autocarros nos dois sentidos: Rua Ricardo Jorge.  
  <sub>Stations every 3 m on every street axis with buses; same width method as the case street; traffic direction from the routing network at one station per street.</sub>
- **[D]** Lisboa: o Desenho da Rua – Manual de espaço público, p. 152 (perfil de referência): Rua de dois sentidos, duas vias, estacionamento longitudinal dos dois lados: largura entre as faixas de estacionamento: 6,80 m. Âmbito: Ruas de dois sentidos com duas vias de trânsito e estacionamento dos dois lados. Mediana medida: 4,90 m (−1,90 m).  
  <sub>0,40 m (sobrelargura) + 3,00 m + 3,00 m + 0,40 m (sobrelargura) = 6,80 m; nota ao desenho: sem sobrelargura, a largura recomendada por via é 3,25 m, ou seja 6,50 m</sub>
- **[D]** Schriftliche Anfrage Drucksache 19/25490, Antwort vom 27.03.2026, p. 3 (citado em documento oficial): Faixa de rodagem para o cruzamento de dois autocarros de carreira (RASt 06, citada): 6,50 m. Âmbito: Norma técnica alemã para ruas urbanas (RASt 06), citada pelo Senado de Berlim; não é lei portuguesa. Mediana medida: 4,90 m (−1,60 m).  
  <sub>Espaço livre de 7,50 m (7,00 m em condições restritas) com distâncias de segurança, donde 6,50 m de faixa de rodagem; 6,00 m é referido como mínimo da RASt 06</sub>
- **[NE]** Não há observação de campo de dois autocarros a cruzar-se nesta rua: os encontros são estimativas do horário.
- **[NE]** A Carris não publica atrasos nem incidentes por rua.
- **[NE]** A largura dos autocarros com espelhos não foi encontrada em ficha oficial (2,90 m é pressuposto).
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
