# Rua Ricardo Jorge (Alvalade, Lisboa)

> A faixa livre entre as duas faixas de estacionamento deixa cruzar dois autocarros programados nos dois sentidos?

Gerado por `streetfit run` a partir das tabelas em `tables/`. Cada afirmação tem um grau de evidência: **M** medido em dados oficiais · **D** texto de documento oficial · **I** inferência · **P** pressuposto · **NE** não encontrado / não verificado (≠ não existe).

- **[M]** O eixo da rua tem 209,25 m.  
  <sub>Axis polyline length (projected CRS).</sub>
- **[M]** A rede viária municipal marca a rua como de dois sentidos (arestas verificadas em 8 pontos ao longo da rua).  
  <sub>Identify on the routing network at stations along the axis.</sub>
- **[M]** Onde há faixas de estacionamento cartografadas dos dois lados (116 m da rua), a faixa livre cartografada entre elas mede 4,78–5,68 m (mediana 4,90 m).  
  <sub>Transects every 0.5 m, widths read from mapped polygons only. · Planimetric accuracy assumed ≤0.30 m per edge (DGT figure for plan-scale cartography, as quoted in a 2025 DGT opinion); the 1:1000 RMSE itself was not found.</sub>
- **[M]** As faixas de estacionamento cartografadas têm 2,01 m (lado NO) e 2,01 m (lado SE) (medianas).  
  <sub>Mapped area, not parked vehicles.</sub>
- **[M]** As carreiras 744, 46B estão programadas ao longo da rua. Em 2026-10-27: 56 viagens SO→NE e 76 viagens NE→SO (no máximo 4 e 6 por hora).  
  <sub>Trips counted at a reference stop per direction; timetable, not observed operation.</sub>
- **[D]** Veículo de referência «Carris MAN 18.310 / Caetano City Gold (12 m)»: largura da carroçaria 2,50 m (ficha da frota da Carris (carris.pt › Descubra › Frota), veículo 2643).
- **[P]** Largura com espelhos de «Carris MAN 18.310 / Caetano City Gold (12 m)» considerada 2,90 m (pressuposto: não há largura oficial com espelhos; +0,40 m como na ficha do Mercedes-Benz eCitaro).
- **[P]** Veículo de referência «Ligeiro típico»: largura da carroçaria 1,80 m (pressuposto: largura típica de um ligeiro europeu; a validar no local).
- **[P]** Largura com espelhos de «Ligeiro típico» considerada 2,05 m (pressuposto: largura típica com espelhos abertos; a validar no local).
- **[I]** Com as duas faixas ocupadas e os veículos estacionados dentro delas, dois autocarros precisam de 5,00 m (só carroçaria; 5,80 m com espelhos) para uma faixa livre mediana de 4,90 m: folga −0,10 m. Um autocarro e um ligeiro precisam de 4,30 m: folga +0,60 m (+0,35 m com o espelho do ligeiro).  
  <sub>Static envelope (sum of widths), not a swept-path simulation. · Assumes parked vehicles stay inside the mapped strips; see overhang_sensitivity.csv.</sub>
- **[I]** O horário implica 6–7 encontros por dia útil entre autocarros em sentidos opostos na rua (modelo de velocidade constante a 15/20 km/h); 1–2 caem nos troços com estacionamento dos dois lados.  
  <sub>Presence-interval overlap at constant speed from scheduled times; timetable, not observation.</sub>
- **[M]** Foram atribuídas à rua 6 ocorrências da categoria «Estacionamento abusivo» (2017-05-05 – 2026-05-31, a ≤12 m do eixo): 2,87 por 100 m, 1.ª de 25 ruas com pelo menos 100 m na envolvente.  
  <sub>Nearest-street attribution of geolocated open-data records. · A report is not a proven infraction; counts are small.</sub>
- **[M]** Das 69 ruas com autocarros programados na envolvente, 2 são de dois sentidos e combinam estacionamento dos dois lados com uma faixa livre inferior a 5,5 m em pelo menos 30 m (Rua Ricardo Jorge e Rua Teixeira de Pascoais); destas, 1 com autocarros nos dois sentidos: Rua Ricardo Jorge.  
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
|---|---|---|---|---|
| area_axes | https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/79 | 2026-10-22 | not stated by the service | `0bbc8dd0c85c…` area_axes.json |
| area_cartography | https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/53 | 2026-10-22 | CC-BY (dados.gov.pt record of 'Cartografia Numérica Vetorial'; version not stated) | `2693bdbdf020…` area_cartography.json |
| area_network_identify | https://websig.cm-lisboa.pt/MuniSIG/REST/sites/BCK_LisboaInterativa_22Set26/map/mapservices/43/rest/services/x/MapServer/identify | 2026-10-24 | not stated (Lisboa Interativa public viewer, guest access) | `e21fdddff4b2…` area_network_identify.json |
| carris_gtfs | https://gateway.carris.pt/gateway/gtfs/api/v2.11/GTFS | 2026-10-20 | not stated at the download endpoint (not redistributed) | `c7550ea2d2f0…` carris_gtfs.zip |
| cartography | https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/53 | 2026-10-20 | CC-BY (dados.gov.pt record of 'Cartografia Numérica Vetorial'; version not stated) | `d6fb67b9b3d7…` cartography.json |
| na_minha_rua |  | 2026-10-22 | CC-BY (dados.gov.pt record 'Ocorrências "Na Minha Rua Lx"') | `5be40828a57b…` na_minha_rua/2017.csv<br>`ef31c04e2e67…` na_minha_rua/2018.csv<br>`dd1283b12cc5…` na_minha_rua/2019.csv<br>+7 |
| network_identify | https://websig.cm-lisboa.pt/MuniSIG/REST/sites/BCK_LisboaInterativa_22Set26/map/mapservices/43/rest/services/x/MapServer/identify | 2026-10-24 | not stated (Lisboa Interativa public viewer, guest access) | `71a5fe259fc7…` network_identify.json |
| street_axes | https://gisbase.cm-lisboa.pt/arcgis/rest/services/MapaBase_WGS84/MapServer/79 | 2026-10-20 | not stated by the service | `b266ddefc9ca…` street_axes.json |
