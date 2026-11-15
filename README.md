# mobilidados

*Português · [English](https://github.com/diogo4256/mobilidados/blob/main/README.en.md)*

**Ferramentas para reivindicações de mobilidade baseadas em dados, em Portugal, a começar por Lisboa.** O
mobilidados quer melhorar a forma como nos deslocamos na cidade, e o transporte público é parte da resposta.

Parte dos dados que as câmaras e os operadores já publicam e chega a factos que a própria Câmara pode confirmar:
cada número refaz-se a partir das fontes e cada afirmação diz em que se apoia. Assim, um morador, uma
associação, um jornalista ou um vereador pode levar um pedido à Câmara com factos, e não só com impressões.

Não pede a ninguém que observe, conte ou recolha seja o que for: trabalha com dados publicados e, onde os dados
acabam, ajuda a pedir o resto a quem o tem. Por agora responde a duas perguntas sobre uma rua:

* **O estacionamento deixa espaço para dois autocarros se cruzarem?** Mede a rua de lado a lado na cartografia de
  pormenor da Câmara, vai ao horário publicado pelo operador (GTFS) buscar as carreiras que lá passam e compara a
  largura que o estacionamento deixa livre com a largura dos veículos que ali se cruzam e com as referências de
  desenho de rua publicadas.
* **Os passeios têm a largura que a lei das acessibilidades exige?** Compara os passeios cartografados com o canal
  livre de 1,2 m do Decreto-Lei n.º 163/2006 e diz onde a cartografia, por si só, mostra um passeio estreito demais.

Para cada rua reúne tudo numa **lista de factos apurados**: cada número, em que se apoia, de onde vem e que
reservas tem. Depois:

* **`mobilidados screen`** ordena as ruas à volta com os mesmos problemas, para escolher onde agir;
* **`mobilidados draft`** escreve, a partir da lista, um primeiro rascunho de carta à Câmara ou ao operador, com um
  só pedido (que os serviços verifiquem e atuem, ou um pedido de documentos ao abrigo da lei de acesso);
* **`mobilidados lint`** e **`check-claims`** conferem o texto final com a lista.

Nasceu de um caso concreto, uma rua de Lisboa, que está incluído na íntegra como exemplo.

![Repartição da largura na Rua Ricardo Jorge, Lisboa](https://raw.githubusercontent.com/diogo4256/mobilidados/main/cases/lisboa-rua-ricardo-jorge/results/figures/width_budget.png)

*Rua Ricardo Jorge (Lisboa): a largura que fica livre entre o estacionamento dos dois lados, tal como está
cartografado, ao lado da largura dos veículos que ali se têm de cruzar. A figura sai da própria análise; todos
os números por trás dela, com a respetiva fonte, estão na [lista de factos apurados](https://github.com/diogo4256/mobilidados/blob/main/cases/lisboa-rua-ricardo-jorge/results/findings.md).*

## O que o exemplo mostra

Na Rua Ricardo Jorge, em Alvalade, a lista de factos apurados chega a isto:

* **[M]** Nos 117,5 m com estacionamento cartografado dos dois lados, a largura livre entre eles tem mediana de
  4,90 m.
* **[I]** Dois autocarros lado a lado ocupam pelo menos 5,00 m, só com a carroçaria e sem espaço nenhum entre
  eles: falta 0,10 m.
* **[D]** O manual de espaço público de Lisboa dá 6,80 m de referência entre as faixas de estacionamento de uma
  rua de dois sentidos com estacionamento dos dois lados (p. 152).
* **[I]** O horário da Carris prevê 6 a 7 encontros por dia entre autocarros em sentidos opostos nesta rua, 1 a 2
  deles nos troços com estacionamento dos dois lados.
* **[I]** Sem o estacionamento de um dos lados, a largura livre passaria a ter mediana de cerca de 6,9 m. Seriam
  retirados 117,5 m de estacionamento cartografado, cerca de 19 a 23 lugares.
* **[M]** Das 69 ruas da zona com autocarros no horário, só esta tem autocarros nos dois sentidos, dois sentidos
  de trânsito e estacionamento dos dois lados com menos de 5,5 m livres em pelo menos 30 m.
* **[I]** Nas posições GPS arquivadas dos autocarros, nos dias úteis às 17h–19h, o troço entre as paragens da rua
  leva mais 49% de tempo do que o abrandamento dos troços vizinhos das mesmas carreiras explicaria (intervalo de
  90%: 34% a 65%), cerca de mais 14 s por autocarro (6 a 24 s). O excesso é claro em 2025 (+60%) e não se
  confirma em 2026 (+4%, −17% a +31%), com muito menos posições. As posições vêm de um arquivo do feed em tempo
  real da Carris mantido por terceiros, não da Carris, e dizem onde se perde o tempo, não porquê.
* **[I]** Onde os passeios da rua estão cartografados até às construções (121 m), nenhum troço é mais estreito do
  que a lei das acessibilidades admite; a cartografia não mostra se estão livres (postes e carros não estão nela).
  **[M]** Na zona à volta, 7 ruas têm passeios cartografados até às construções e mais estreitos do que o
  Decreto-Lei n.º 163/2006 admite, mesmo contando com 0,30 m de erro em cada aresta cartografada (Rua das Mimosas,
  42 m; as travessas de São João de Brito; …): o [rastreio da zona](https://github.com/diogo4256/mobilidados/blob/main/cases/lisboa-rua-ricardo-jorge/results/screening.md) lista-as, com o sítio onde olhar.

Cada linha leva a fonte, o método e as reservas na [lista completa](https://github.com/diogo4256/mobilidados/blob/main/cases/lisboa-rua-ricardo-jorge/results/findings.md),
incluindo o que não foi verificado: não há observação no local de dois autocarros a cruzar-se ali, e a Carris
não publica atrasos por rua (o tempo medido acima vem de um arquivo mantido por terceiros).

## Para quem é, e o que não é

* **Moradores e associações:** encontrar as ruas da sua zona com um caso a fazer (`screen`) e levar à Câmara, à
  junta de freguesia ou à Carris um pedido sobre uma delas (`draft`), apoiado nos dados da própria Câmara, com o
  custo de cada opção dito tão claramente como o ganho.
* **Eleitos:** fazer uma pergunta ou uma recomendação que os serviços possam confirmar número a número.
* **Jornalistas:** verificar uma reivindicação antes de a publicar, com cada número ligado à sua fonte.
* **Serviços técnicos e operador:** passar em revista as ruas com autocarros de uma zona e ver onde o
  estacionamento aperta a passagem, antes de ir ao local.

Não é uma ferramenta de desenho de ruas: não propõe perfis, mede o que está cartografado. Não é um inventário de
estacionamento nem um mapa da repartição do espaço da cidade. Só mede o tempo dos autocarros num troço onde exista
um arquivo público do feed em tempo real do operador, e diz então até que ponto esse arquivo está completo.
Responde a uma pergunta sobre uma rua, a partir de dados públicos, e diz em que se apoia cada número.

## De onde vêm os dados

Só se usam ficheiros e serviços a que qualquer pessoa pode aceder sem registo nem palavra-passe. No caso de Lisboa,
a cartografia, os eixos de via e as ocorrências Na Minha Rua vêm dos serviços de informação geográfica e do portal
de dados abertos da Câmara. O horário GTFS é uma cópia do ficheiro publicado pela Carris, guardada no arquivo da
Mobility Database, de onde é descarregado; essa cópia fica fixada pela impressão digital (SHA-256). O sentido de
trânsito é consultado num serviço do Lisboa Interativa, o visualizador de mapas que a Câmara disponibiliza ao
público, com acesso de convidado. Esse serviço não declara licença, e o seu endereço inclui a data de uma cópia de
segurança, pelo que pode mudar. Em cada caso, o ficheiro `sources.lock.json` guarda, para cada dado, o endereço, a
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
  V[Posições arquivadas<br>dos autocarros, GTFS-RT] --> W[Tempo num troço<br>ponta face aos vizinhos]
  G --> W
  W --> L
  P --> E[Repartição da largura<br>autocarro e autocarro, autocarro e ligeiro]
  T --> E
  S[Referências de desenho<br>com página e âmbito] --> L
  O[Ocorrências<br>Na Minha Rua] --> L
  A --> SW[Passeios<br>face ao DL 163/2006] --> L
  L --> SC[Rastreio<br>da zona]
  L --> DR[Rascunho de carta]
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
| `delay` | tempo dos autocarros num troço entre paragens, a partir de posições em tempo real arquivadas: na ponta face a fora da ponta, para além do abrandamento dos troços vizinhos das mesmas carreiras, por ano, carreira e hora, com intervalos de 90% e as verificações que os sustentam |
| `sidewalks` | a parte mais larga do passeio cartografado de cada lado, face ao canal livre da lei das acessibilidades (Decreto-Lei n.º 163/2006): troços mais estreitos do que a lei admite para o seu comprimento, com e sem a margem de exatidão da cartografia, e troços a verificar |
| `occurrences` | ocorrências Na Minha Rua por cada 100 m de rua, comparadas com as ruas vizinhas |
| `area` | ruas com autocarros na zona à volta onde o estacionamento aperta a passagem da mesma maneira |
| `area_sidewalks` | todas as ruas da zona, com os passeios medidos da mesma maneira |
| `standards` | largura medida comparada com as referências de desenho de rua, cada uma com página e âmbito |
| `ledger` | `findings.md` / `findings.json`: cada afirmação com a sua base, fontes, método e reservas |
| `screening` | `screening.md`: as ruas da zona onde olhar, para os autocarros e para os passeios, e como fazer o seu caso |

E, a partir dos resultados: `mobilidados draft CASO --topic buses|sidewalks` escreve uma carta
(`results/letter-<tema>.md`); `mobilidados screen CASO` refaz só as etapas da zona e o rastreio.

## O que (ainda) não faz

* Lê os lugares de estacionamento desenhados na cartografia, não os carros que lá estão; os encontros vêm do
  horário, e os tempos medidos de um arquivo do feed em tempo real mantido por terceiros, não do registo do próprio
  operador; e compara larguras, sem simular o espaço que um autocarro varre numa
  curva. Uma rua estreita é motivo para pedir uma vistoria, não prova de que há uma infração. Para cada caso, a
  lista de factos diz o que ficou por verificar (NE).
* Por agora só há perfil de cidade para Lisboa. Os outros concelhos precisam do seu ([docs/adding-a-city.md](https://github.com/diogo4256/mobilidados/blob/main/docs/adding-a-city.md)).
* Compara os passeios tal como estão cartografados: postes, papeleiras, esplanadas e carros em cima deles não estão
  na cartografia, pelo que um passeio largo no mapa nunca é apresentado como livre, e um passeio que acaba num
  logradouro ou em algo não cartografado é um troço a verificar, não um troço abaixo da lei.
* Por agora trata do espaço que o estacionamento deixa aos autocarros e da largura dos passeios. Outras questões
  de mobilidade (passadeiras, paragens, ciclovias) são bem-vindas como novas ferramentas, com o mesmo rigor.

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
uv run mobilidados fetch cases/lisboa-rua-ricardo-jorge     # descarrega as fontes e confere-as com o sources.lock.json
uv run mobilidados verify cases/lisboa-rua-ricardo-jorge    # confere cada ficheiro guardado com a impressão digital registada
uv run mobilidados run cases/lisboa-rua-ricardo-jorge       # escreve os resultados em results/ (da primeira vez, consulta a rede viária)
git diff --exit-code cases/lisboa-rua-ricardo-jorge         # dá o mesmo que a análise de referência?
```

O pacote também está no [PyPI](https://pypi.org/project/mobilidados/) (`pip install mobilidados`), mas os casos e
os perfis de cidade ficam neste repositório: para refazer um caso ou começar outro, clone-o como acima.

Os serviços da Câmara vão sendo atualizados. Se uma fonte já não servir os ficheiros que a análise de referência
usou, o `fetch` recusa-os e não escreve nada; o `verify --live` volta a descarregar as fontes e diz quais mudaram,
sem mexer na cópia guardada, e o `fetch --refresh` aceita os dados novos de propósito (o `sources.lock.json` muda,
e os resultados podem mudar). Cada caso fixa o horário GTFS que usou, pela
impressão digital, e recusa correr com outro, a não ser que se mude isso de propósito. No caso de Lisboa, o
horário vem do arquivo da Mobility Database, onde o ficheiro exato continua disponível. `mobilidados snapshot
CASO PASTA` copia para uma pasta os dados que a licença deixa redistribuir, para os guardar (por exemplo no
Zenodo); `mobilidados fetch CASO --from-dir PASTA` volta a pô-los no sítio, só se forem exatamente os ficheiros
registados.

## Ferramentas com IA (opcionais)

`pip install 'mobilidados[agents]'` acrescenta as ferramentas da tabela abaixo, que usam o Claude. Em todas, **o
modelo propõe e o código confirma**: nada do que o modelo diz passa a contar como prova por si só. Mais pormenores
em [docs/ai-tools.md](https://github.com/diogo4256/mobilidados/blob/main/docs/ai-tools.md).

| Comando | O que o modelo faz | O que o código confirma a seguir |
| --- | --- | --- |
| `mobilidados check-claims CASO rascunho.md` | lê um rascunho de carta, separa cada afirmação e procura-a na lista de factos e nas fontes | as citações têm de estar tal e qual na fonte, perto da linha indicada; os números têm de bater com o facto citado; o que está entre aspas tem de ser citação literal |
| `mobilidados extract-standard manual.pdf --pages N` | lê uma página de um manual, incluindo as cotas dos desenhos | cada valor é procurado no texto do PDF e por reconhecimento ótico de caracteres (Tesseract), em várias passagens; as somas são refeitas; o que não se confirma fica marcado para uma pessoa ver, com a imagem da página |
| `mobilidados discover --city X --start URL` | percorre o portal de cartografia ou de dados abertos de um município (só endereços autorizados, só leitura) e propõe um perfil de cidade | cada camada proposta é consultada outra vez: os campos existem e, se a zona de teste for indicada com `--bbox`, os códigos aparecem mesmo nessa zona (sem `--bbox`, os códigos não são verificados) |

`mobilidados lint rascunho.md` faz, sem IA nenhuma, as verificações automáticas de uma carta: generalizações,
concessões feitas à partida, aspas, e palavras como "norma", "regra" ou "obrigatório" usadas para o que é só uma
recomendação.

## Analisar a sua rua

1. Se a sua cidade já tem um caso, basta o nome da rua:

   ```bash
   uv run mobilidados fetch cases/lisboa-rua-ricardo-jorge --only carris_gtfs   # uma vez: o horário que o caso usa
   uv run mobilidados new-case "Rua Teixeira de Pascoais" --like cases/lisboa-rua-ricardo-jorge
   uv run mobilidados fetch cases/lisboa-rua-teixeira-de-pascoais
   uv run mobilidados run cases/lisboa-rua-teixeira-de-pascoais
   ```

   Para escolher a rua, o `mobilidados screen cases/lisboa-rua-ricardo-jorge` (ou o
   [screening.md](https://github.com/diogo4256/mobilidados/blob/main/cases/lisboa-rua-ricardo-jorge/results/screening.md) do caso) lista as ruas à volta com um caso a fazer. Depois
   da análise, `uv run mobilidados draft cases/lisboa-rua-teixeira-de-pascoais --topic buses` escreve a carta.
   O nome não tem de estar escrito tal e qual: se não houver um eixo com esse nome, o `new-case` procura nomes
   parecidos e sugere-os. O `new-case` encontra a rua na cartografia da Câmara, divide-a em quarteirões nos cruzamentos, vai ao horário
   buscar as carreiras que lá passam e escreve o `case.toml`. O resto (fontes, horário, veículos, parâmetros) vem
   do caso indicado em `--like`. No topo do ficheiro fica a lista do que tem de confirmar antes de usar.
2. Se não tem, comece pelo perfil da cidade: [docs/adding-a-city.md](https://github.com/diogo4256/mobilidados/blob/main/docs/adding-a-city.md) (o `mobilidados discover` pode fazer um primeiro rascunho).

O método e os seus limites estão em [docs/methodology.md](https://github.com/diogo4256/mobilidados/blob/main/docs/methodology.md); conselhos para escrever à
Câmara ou a outra entidade com estes resultados, em [docs/writing-to-public-bodies.md](https://github.com/diogo4256/mobilidados/blob/main/docs/writing-to-public-bodies.md).
A documentação técnica está, por agora, em inglês.

## Organização do repositório

```text
src/mobilidados/          biblioteca e comandos (agents/ = ferramentas opcionais com IA)
src/mobilidados/data/     catálogo de veículos e de referências de desenho de rua, com fonte
src/mobilidados/locales/  textos das figuras, da lista de factos e dos relatórios, um ficheiro por língua
cities/                   perfis de cidade (serviços, códigos, licenças, parâmetros) e dados datados (horário, ocorrências)
cases/<caso>/             case.toml, sources.lock.json, results/ (no repositório), data/raw/ (fora dele)
docs/                     método, ferramentas com IA, nova cidade, cartas a entidades públicas, partes interessadas, manutenção
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
