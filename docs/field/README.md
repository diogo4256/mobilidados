# Field counts

Three counts anyone can make in the street, with a pen or a phone, that close the gaps the appraisal leaves open
(docs/appraisal.md, *What is worth measuring*). Each one replaces an assumed input (grade P) with a measured one
(grade M). The templates are in Portuguese, the language of the Lisbon cases; the columns are explained below.

Do not record number plates, faces or anything that identifies a person. Keep any video private: the counts are what
the study uses, not the images.

## 1. Night count of free places (`contagem_noturna.csv`)

**What it settles:** `room_nearby`, the share of displaced cars that would find a place within 150 m. It is the input
that moves the cost side most.

**How:** on three working-day nights (Monday to Thursday), between 23h and 24h, walk every street within about 150 m of
the stretch. For each section of street and each side, write down the free legal places and the occupied ones; cars
parked outside a marked place go in `carros_fora_de_lugar`, not in the occupied places.

| column | what |
| --- | --- |
| `data`, `hora_inicio`, `hora_fim` | date (YYYY-MM-DD) and the times you started and finished that section |
| `rua`, `troco_de`, `troco_ate` | the street and the two cross streets (or numbers) that bound the section |
| `lado` | the side: odd numbers (`impar`) or even numbers (`par`) |
| `lugares_livres`, `lugares_ocupados` | free and occupied legal places |
| `carros_fora_de_lugar` | cars parked where parking is not allowed (on corners, on the pavement, double-parked) |

If, on the fullest of the three nights, the free places within 150 m are more than the places an option removes (about
21 for one side of the three narrow sections), the displaced cars fit.

## 2. Deadlock log (`registo_impasses.csv`)

**What it settles:** how often buses are held by oncoming vehicles, and for how long. It informs `offpeak_s` and
`unexpected_share`, and checks the passage records requested from Carris.

**How:** whenever you see a bus held because it cannot pass an oncoming vehicle, write down one line. Ten minutes
standing at the junction at the peak (17h–19h on a working day) are worth more than a vague memory of many days.

| column | what |
| --- | --- |
| `data`, `hora` | date and time it began |
| `local` | where: the junction or the stretch between two cross streets |
| `carreiras` | the lines of the buses involved (e.g. `744 / 46B`) |
| `veiculos` | what met: `autocarro/autocarro`, `autocarro/camião`, `autocarro/carrinha`, `autocarro/ligeiro` |
| `duracao_s` | seconds from when the bus stopped until it moved on |
| `recuo` | `sim` if any vehicle had to reverse |
| `carros_retidos` | cars waiting behind |
| `video` | `sim` if you filmed it (kept private) |

## 3. Traffic count (`contagem_trafego.csv`)

**What it settles:** `cars_behind` (how many cars a held bus holds) and how often a bus meets a heavy vehicle (a bus
and a 2.55 m lorry need 5.05 m; the street leaves 4.90 m).

**How:** on one working day, count in 15-minute blocks from 17h to 19h and for one hour off-peak (e.g. 11h–12h), each
direction separately.

| column | what |
| --- | --- |
| `data`, `hora_inicio`, `hora_fim` | date and the 15-minute block |
| `sentido` | the direction (e.g. `SO-NE` or `NE-SO`, as in the findings) |
| `ligeiros`, `carrinhas`, `pesados`, `autocarros`, `motos`, `bicicletas` | vehicles of each kind; `pesados` are lorries, refuse collection and other heavy vehicles |
