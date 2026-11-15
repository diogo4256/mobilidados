# Rastreio da zona à volta da Rua Ricardo Jorge

Gerado por `mobilidados run` (ou `mobilidados screen`) a partir das tabelas em `tables/`. Diz onde olhar, não o que concluir: cada rua da lista precisa do seu caso para os troços, os pontos e as reservas. Os dados são os mesmos do caso (cartografia municipal, horário do operador), numa zona de cerca de 1,2 km à volta da rua.

## Espaço para os autocarros

Ruas com autocarros no horário onde o estacionamento dos dois lados deixa menos de 5,5 m de largura livre em pelo menos 30 m (area_streets.csv).

| Rua | Autocarros por dia | Carreiras | Autocarros nos dois sentidos | Trânsito | Largura livre mediana (m) | Metros nessa situação |
| --- | ---: | --- | --- | --- | ---: | ---: |
| Rua Vitor Hugo | 170 | 705 718 793 | não | sentido único | 5,07 | 141 |
| Rua Ricardo Jorge | 132 | 46B 744 | sim | dois sentidos | 5,06 | 117 |
| Rua Augusto Gil | 29 | 49B | não | sentido único | 4,20 | 93 |
| Rua Teixeira de Pascoais | 72 | 727 | não | dois sentidos | 5,72 | 84 |
| Avenida São João de Deus | 29 | 49B 705 718 793 | não | sentido único | 6,57 | 81 |
| Avenida de Roma | 219 | 206 46B 49B 717 722 727 731 735 736 750 755 767 783 | não | sentido único | 9,63 | 78 |
| Rua Reinaldo Ferreira | 76 | 46B 744 | não | sentido único | 8,96 | 78 |
| Avenida Frei Miguel Contreiras | 76 | 727 | não | sentido único | 5,42 | 72 |
| Rua Marquês do Soveral | 77 | 46B 744 | não | sentido único | 7,47 | 48 |

## Passeios

Ruas da zona com troços em que o passeio cartografado vai até às construções e é mais estreito do que o Decreto-Lei n.º 163/2006 admite (canal livre de 1,20 m; troços curtos, secção 4.3.3), e metros a verificar onde o passeio tem menos de 1,20 m mas não vai até às construções (area_sidewalks.csv).

| Rua | Metros abaixo do admitido | Dos quais, mesmo com a exatidão da cartografia | Troço mais estreito (m) | Metros a verificar | Onde (lat, lon) |
| --- | ---: | ---: | ---: | ---: | --- |
| Rua das Mimosas | 42 | 42 | 0,34 | 44 | 38.762722, -9.138029 |
| Largo Machado de Assis | 15 | 14 | 0,55 | 0 | 38.747020, -9.139001 |
| Rua de Entrecampos | 12 | 12 | 0,34 | 0 | 38.748244, -9.147444 |
| Travessa do Chafariz ao Bairro de São João de Brito | 11 | 10 | 0,38 | 5 | 38.761716, -9.131734 |
| Travessa da Fonte | 8 | 8 | 0,34 | 17 | 38.761767, -9.131371 |
| Rua Castelo Branco Chaves | 11 | 3 | 0,47 | 4 | 38.751472, -9.144489 |
| Avenida de Madrid | 2 | 2 | 0,32 | 27 | 38.744227, -9.136443 |
| Rua Eugénio de Castro Rodrigues | 34 | 0 | 0,98 | 0 | 38.758180, -9.136959 |
| Rua Francisco de Holanda | 31 | 0 | 0,81 | 10 | 38.744488, -9.155987 |
| Avenida da República | 30 | 0 | 0,79 | 1 | 38.744143, -9.147060 |
| Rua das Murtas | 18 | 0 | 0,78 | 69 | 38.760936, -9.147306 |
| Rua General Pimenta de Castro | 18 | 0 | 0,65 | 62 | 38.746730, -9.134039 |
| Rua Reinaldo Ferreira | 18 | 0 | 0,93 | 0 | 38.759579, -9.136332 |
| Rua David de Almeida | 13 | 0 | 0,78 | 3 | 38.762560, -9.133500 |
| Rua Maria Teresa Ramalho (Tareka) | 12 | 0 | 0,75 | 12 | 38.761817, -9.134937 |
| Estrada da Portela ao Bairro São João de Brito | 12 | 0 | 1,09 | 1 | 38.761940, -9.137494 |
| Rua Engenheiro Manuel Rocha | 10 | 0 | 0,93 | 130 | 38.759675, -9.137198 |
| Rua João Ribas | 9 | 0 | 1,06 | 32 | 38.762150, -9.132170 |
| Rua Antónia Pusich | 8 | 0 | 0,70 | 48 | 38.753730, -9.148816 |
| Rua Professor Veiga Beirão | 8 | 0 | 0,85 | 6 | 38.755836, -9.134045 |
| Rua Flores de Lima | 6 | 0 | 0,88 | 8 | 38.748646, -9.144651 |
| Rua Alfredo Cortês | 6 | 0 | 0,64 | 0 | 38.745878, -9.145840 |
| Rua das Camélias | 5 | 0 | 0,71 | 10 | 38.761419, -9.134309 |
| Avenida das Forças Armadas | 5 | 0 | 0,80 | 0 | 38.748165, -9.149064 |
| Rua José Pinheiro de Melo | 3 | 0 | 0,65 | 0 | 38.747286, -9.138851 |
| Travessa Aboím Ascensão | 2 | 0 | 0,81 | 24 | 38.749665, -9.147597 |
| Campo Grande | 2 | 0 | 1,16 | 23 | 38.751714, -9.149331 |
| Rua José Lins do Rego | 2 | 0 | 1,19 | 0 | 38.755151, -9.148812 |
| Rua Quinta da Graça | 0 | 0 | — | 309 | — |
| Rua Rosália de Castro | 0 | 0 | — | 267 | — |
| … (+73) | | | | | |

## Próximo passo

Para fazer o caso de uma destas ruas, com os seus troços, pontos de verificação e reservas:

```bash
mobilidados new-case "Rua Vitor Hugo" --like cases/lisboa-rua-ricardo-jorge
mobilidados fetch cases/<…>
mobilidados run cases/<…>
mobilidados draft cases/<…> --topic buses      # --topic sidewalks
```
