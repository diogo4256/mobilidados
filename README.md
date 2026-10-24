# mobilidados

*Português · [English](https://github.com/diogo4256/mobilidados/blob/main/README.en.md)*

**Dados abertos ao serviço da mobilidade, em Portugal, a começar por Lisboa.** O mobilidados quer melhorar a
forma como nos deslocamos na cidade, e o transporte público é parte da resposta. As suas ferramentas medem como
está repartido o espaço da rua e quanto sobra para quem anda a pé, de autocarro ou de bicicleta.

Parte dos dados que as câmaras e os operadores já publicam e chega a factos que a própria Câmara pode confirmar:
cada número refaz-se a partir das fontes e cada afirmação diz em que se apoia. Assim, um morador, uma
associação, um jornalista ou um vereador pode levar um pedido à Câmara com factos, e não só com impressões.

A primeira ferramenta responde a uma pergunta: **o estacionamento deixa espaço para dois autocarros se
cruzarem?** Mede a rua de lado a lado na cartografia de pormenor da Câmara, vai ao horário publicado pelo
operador (GTFS) buscar as carreiras que lá passam, compara a largura que o estacionamento deixa livre com a
largura dos veículos que ali se cruzam e com as normas de desenho de rua publicadas, e reúne tudo numa **lista
de factos apurados**: cada número, em que se apoia, de onde vem e que reservas tem.

Nasceu de um caso concreto, uma rua de Lisboa, que está incluído na íntegra como exemplo.

![Repartição da largura na Rua Ricardo Jorge, Lisboa](https://raw.githubusercontent.com/diogo4256/mobilidados/main/cases/lisboa-rua-ricardo-jorge/results/figures/width_budget.png)

*Rua Ricardo Jorge (Lisboa): a largura que fica livre entre o estacionamento dos dois lados, tal como está
cartografado, ao lado da largura dos veículos que ali se têm de cruzar. A figura sai da própria análise; todos
os números por trás dela, com a respetiva fonte, estão na [lista de factos apurados](https://github.com/diogo4256/mobilidados/blob/main/cases/lisboa-rua-ricardo-jorge/results/findings.md).*

## De onde vêm os dados

Só se usam ficheiros e serviços que uma entidade pública ou um operador põe à disposição de qualquer pessoa, sem
registo nem palavra-passe. Em cada caso, o ficheiro `sources.lock.json` guarda, para cada dado, o endereço, a
data em que foi obtido, a impressão digital (SHA-256) e a licença, ou a indicação de que o editor não declara
nenhuma. O que não tem licença declarada é usado, mas não é redistribuído. Quem quiser pode ir buscar os mesmos
ficheiros e confirmar os mesmos resultados.

## O que faz

```mermaid
flowchart LR
  A[Cartografia<br>municipal] --> P[Perfis<br>transversais]
  B[Eixos de via] --> P
  C[Rede viária] --> D[Sentido de trânsito]
  G[Horários GTFS] --> T[Carreiras, viagens por hora,<br>cruzamentos previstos]
  P --> E[Repartição da largura<br>autocarro e autocarro, autocarro e ligeiro]
  T --> E
  S[Normas de desenho<br>com página e âmbito] --> L
  O[Ocorrências<br>Na Minha Rua] --> L
  E --> L[Factos apurados<br>M · D · I · P · NE]
  D --> L
  L --> R[findings.md / .json<br>figuras, tabelas]
  L -. confere .-> X[Rascunho de carta]
```

| Etapa | O que produz |
| --- | --- |
| `profiles` | largura livre, estacionamento de cada lado, largura entre lancis e passeios ao longo da rua; resumo por quarteirão |
| `direction` | sentido único ou duplo, segundo a rede viária da Câmara |
| `transit` | carreiras que passam na rua, em que sentido, quantas viagens por hora num dia de serviço, tempos previstos entre paragens |
| `envelope` | folgas para dois autocarros, autocarro e ligeiro, e dois ligeiros, com e sem espelhos; efeito de carros estacionados que ficam fora do lugar; largura livre sem o estacionamento de um lado ou dos dois |
| `encounters` | autocarros em sentidos opostos que, segundo o horário, se cruzam na rua, e em que ponto |
| `occurrences` | ocorrências Na Minha Rua por cada 100 m de rua, comparadas com as ruas vizinhas |
| `area` | ruas com autocarros na zona à volta onde o estacionamento aperta a passagem da mesma maneira |
| `standards` | largura medida comparada com as normas de desenho de rua, cada uma com página e âmbito |
| `ledger` | `findings.md` / `findings.json`: cada afirmação com a sua base, fontes, método e reservas |

## O que (ainda) não faz

* Lê os lugares de estacionamento desenhados na cartografia, não os carros que lá estão; usa o horário, não o
  que os autocarros fazem na realidade; e compara larguras, sem simular o espaço que um autocarro varre numa
  curva. Uma rua estreita é motivo para pedir uma vistoria, não prova de que há uma infração. Para cada caso, a
  lista de factos diz o que ficou por verificar (NE).
* Por agora só há perfil de cidade para Lisboa. Os outros concelhos precisam do seu ([docs/adding-a-city.md](https://github.com/diogo4256/mobilidados/blob/main/docs/adding-a-city.md)).
* Por agora só trata do espaço que o estacionamento deixa aos autocarros. Outras questões de mobilidade
  (passeios, passadeiras, paragens, ciclovias) são bem-vindas como novas ferramentas, com o mesmo rigor.

## Em que se apoia cada afirmação

Cada facto da lista traz uma letra que diz em que se apoia ([docs/evidence-standard.md](https://github.com/diogo4256/mobilidados/blob/main/docs/evidence-standard.md)):

| Letra | Quer dizer |
| --- | --- |
| **M** | medido ou contado em dados oficiais (cartografia, horários, dados abertos) |
| **D** | escrito num documento oficial (lei, manual, ficha técnica), com a página |
| **I** | inferido a partir de M, D ou P (um modelo, uma conta) |
| **P** | pressuposto, assumido como tal (por exemplo, a largura com espelhos, que ninguém publica) |
| **NE** | não encontrado ou não verificado, o que não quer dizer que não exista |

## Como usar

```bash
git clone https://github.com/diogo4256/mobilidados.git && cd mobilidados
uv sync                      # ou: python -m venv .venv && .venv/bin/pip install -e .
uv run mobilidados fetch cases/lisboa-rua-ricardo-jorge     # descarrega as fontes e escreve sources.lock.json
uv run mobilidados verify cases/lisboa-rua-ricardo-jorge    # confere cada ficheiro com a impressão digital guardada
uv run mobilidados run cases/lisboa-rua-ricardo-jorge       # escreve os resultados em results/
git diff --exit-code cases/lisboa-rua-ricardo-jorge/results/tables   # dá o mesmo que a análise de referência?
```

Os serviços da Câmara vão sendo atualizados, por isso um `fetch` feito hoje pode não dar exatamente o mesmo que
a análise de referência; o `verify` diz que ficheiros mudaram. Cada caso fixa o horário GTFS que usou, pela
impressão digital, e recusa correr com outro, a não ser que se mude isso de propósito. No caso de Lisboa, o
horário vem do arquivo da Mobility Database, onde o ficheiro exato continua disponível. `mobilidados snapshot
CASO PASTA` copia para uma pasta os dados que a licença deixa redistribuir, para os guardar (por exemplo no
Zenodo); `mobilidados fetch CASO --from-dir PASTA` volta a pô-los no sítio.

## Ferramentas com IA (opcionais)

`pip install 'mobilidados[agents]'` acrescenta três ferramentas que usam o Claude. Em todas, **o modelo propõe
e o código confirma**: nada do que o modelo diz passa a contar como prova por si só. Mais pormenores em
[docs/ai-tools.md](https://github.com/diogo4256/mobilidados/blob/main/docs/ai-tools.md).

| Comando | O que o modelo faz | O que o código confirma a seguir |
| --- | --- | --- |
| `mobilidados check-claims CASO rascunho.md` | lê um rascunho de carta, separa cada afirmação e procura-a na lista de factos e nas fontes | as citações têm de estar tal e qual na fonte, perto da linha indicada; os números têm de bater com o facto citado; o que está entre aspas tem de ser citação literal |
| `mobilidados extract-standard manual.pdf --pages N` | lê uma página de um manual, incluindo as cotas dos desenhos | cada valor é procurado no texto do PDF e por reconhecimento ótico de caracteres (Tesseract), em várias passagens; as somas são refeitas; o que não se confirma fica marcado para uma pessoa ver, com a imagem da página |
| `mobilidados discover --city X --start URL` | percorre o portal de cartografia ou de dados abertos de um município (só endereços autorizados, só leitura) e propõe um perfil de cidade | cada camada proposta é consultada outra vez: os campos existem e os códigos aparecem mesmo na zona de teste |

`mobilidados lint rascunho.md` faz, sem IA nenhuma, as verificações automáticas de uma carta: generalizações,
concessões feitas à partida, aspas, e "regra" ou "mínimo" usados para o que é só uma recomendação.

## Analisar a sua rua

1. Se a sua cidade já tem um caso, basta o nome da rua:

   ```bash
   uv run mobilidados fetch cases/lisboa-rua-ricardo-jorge      # uma vez: o horário GTFS que o caso usa
   uv run mobilidados new-case "Rua Teixeira de Pascoais" --like cases/lisboa-rua-ricardo-jorge
   uv run mobilidados fetch cases/lisboa-rua-teixeira-de-pascoais
   uv run mobilidados run cases/lisboa-rua-teixeira-de-pascoais
   ```

   O `new-case` encontra a rua na cartografia da Câmara, divide-a em quarteirões nos cruzamentos, vai ao horário
   buscar as carreiras que lá passam e escreve o `case.toml`. O resto (fontes, horário, veículos, parâmetros) vem
   do caso indicado em `--like`. No topo do ficheiro fica a lista do que tem de confirmar antes de usar.
2. Se não tem, comece pelo perfil da cidade: [docs/adding-a-city.md](https://github.com/diogo4256/mobilidados/blob/main/docs/adding-a-city.md) (o `mobilidados discover` pode fazer um primeiro rascunho).

O método e os seus limites estão em [docs/methodology.md](https://github.com/diogo4256/mobilidados/blob/main/docs/methodology.md); conselhos para escrever à
Câmara ou a outra entidade com estes resultados, em [docs/writing-to-public-bodies.md](https://github.com/diogo4256/mobilidados/blob/main/docs/writing-to-public-bodies.md).
A documentação técnica está, por agora, em inglês.

## Organização do repositório

```text
src/mobilidados/          biblioteca e comandos (agents/ = ferramentas opcionais com IA)
src/mobilidados/data/     catálogo de veículos e normas de desenho de rua, com fonte
src/mobilidados/locales/  textos das figuras, da lista de factos e dos relatórios, um ficheiro por língua
cities/                   perfis de cidade (serviços, códigos, licenças, parâmetros) e dados datados (horário, ocorrências)
cases/<caso>/             case.toml, sources.lock.json, results/ (no repositório), data/raw/ (fora dele)
docs/                     método, ferramentas com IA, nova cidade, cartas a entidades públicas
tests/                    testes com dados fictícios e teste que refaz cada caso
```

## Agradecimentos

Às entidades que publicam os dados em que este trabalho assenta: a Câmara Municipal de Lisboa (cartografia,
eixos de via, rede viária e ocorrências Na Minha Rua), a Carris (horários GTFS) e a
[Mobility Database](https://mobilitydatabase.org), que guarda os horários antigos e permite repetir uma análise
feita no passado.

## Contacto

Diogo Adegas, <diogo.adegas@gmail.com> (também para questões do código de conduta).

## Contribuir, licença, citação

Todas as contribuições são bem-vindas, sobretudo novas cidades e novos casos: ver [CONTRIBUTING.md](https://github.com/diogo4256/mobilidados/blob/main/CONTRIBUTING.md) e o
[código de conduta](https://github.com/diogo4256/mobilidados/blob/main/CODE_OF_CONDUCT.md). O código está sob a licença [Apache-2.0](https://github.com/diogo4256/mobilidados/blob/main/LICENSES/Apache-2.0.txt); a documentação e os
resultados, sob [CC-BY-4.0](https://github.com/diogo4256/mobilidados/blob/main/LICENSES/CC-BY-4.0.txt). Os dados de terceiros mantêm a licença de origem, registada
para cada fonte no `sources.lock.json` do caso (ver [REUSE.toml](https://github.com/diogo4256/mobilidados/blob/main/REUSE.toml)), e os ficheiros originais não são
redistribuídos aqui. Para citar o projeto: [CITATION.cff](https://github.com/diogo4256/mobilidados/blob/main/CITATION.cff).
