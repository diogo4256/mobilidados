# Stakeholders

Who has a stake in a claim built with mobilidados, what each needs from it, and what would make each distrust it.
A change to the tools, the method or the wording is weighed against this list before it is made. The aim is
better mobility, with public transport as part of the solution; the toolset serves that aim by giving facts that
every party below can check.

The parties are named by their role. Where a public body is named, it is because of its responsibilities; no
organisation listed here is involved in this project or endorses it.

## Who they are

### Those who make claims

| Who | Role and responsibilities | Needs from the toolset | Would distrust it if |
| --- | --- | --- | --- |
| Residents | Raise a problem in their street, often alone and without technical training | A short path from a street name to findings they understand, in Portuguese; limits stated plainly | It needs a programmer, or its results read as a verdict they cannot defend |
| Civic associations (mobility, public space, accessibility) | Campaign across many streets; meet the municipality; publish positions | The same method on many streets; results they can compare and cite | It looks like one side's argument dressed as data |
| Passengers and their committees | Use the buses every day; speak for reliability and access | Evidence about the service as scheduled, and what the street costs it | The framing treats buses as the problem rather than the people on them |
| Journalists | Check claims before publishing; quote numbers | Every number traceable to a public source, with its grade and its caveats | A number cannot be traced, or the caveats are hidden |
| Elected representatives (councillors, municipal assembly members, parish councils) | Table motions and questions; answer to voters on both sides | Findings they can put to the services and defend in public | Results depend on assumptions they cannot see |

### Those who answer them

| Who | Role and responsibilities | Needs from the toolset | Would distrust it if |
| --- | --- | --- | --- |
| Câmara Municipal de Lisboa: mobility and public-space services | Decide street layouts, apply the municipal public-space manual, weigh every user of the street | Measurements from their own data, design references cited with page and scope, no claim beyond the evidence | A reference is applied outside its scope, or a model output is presented as fact |
| EMEL | Manages on-street parking | A clear statement of what a change would remove (metres or places of parking) | The parking lost by an option is left unsaid |
| Carris | Runs the buses; publishes the timetable (GTFS) and the fleet sheets | Vehicle widths from its own sheets, the timetable read correctly, its data attributed | Timetable estimates are presented as observed operation, or delays are claimed without data |
| Those who enforce parking rules | Act on parking where it is not allowed | Reports and measurements kept apart from proof of infractions | Citizens' reports are presented as proven infractions |

### Those affected by a change

| Who | Stake | What the toolset owes them |
| --- | --- | --- |
| Bus passengers | Faster, more reliable trips | Findings about the space buses need, framed for them |
| Residents and businesses who park in the street | Lose parking if space is reallocated | The cost of each option stated as plainly as its benefit |
| Pedestrians, including people with reduced mobility | Sidewalk width, crossings | Their space measured, not traded away unseen (sidewalks are profiled today; a dedicated tool is welcome) |
| People on bikes | Lane space and safety | The same, in future tools |
| Emergency services (Regimento de Sapadores Bombeiros) and waste collection | Need access for wide vehicles | Their vehicles can be added to the catalogue, with an official width source |

### Those whose data the toolset uses

| Who | Role | What the toolset owes them |
| --- | --- | --- |
| CML open-data and GIS teams; dados.gov.pt | Publish the cartography, street axes, routing network and Na Minha Rua reports | Attribution as their licences require; downloads cached so their services are not queried again for nothing; a User-Agent that names the tool (and a contact, if set) |
| Carris and the Mobility Database | Publish and archive the timetable | The exact feed pinned and cited; the feed not redistributed while its licence is not stated |
| Direção-Geral do Território | Homologates the municipal cartography | Its stated accuracy quoted, not assumed better |

### Those who keep the toolset alive

| Who | Role | Needs |
| --- | --- | --- |
| Maintainer and contributors | Volunteers who review, fix and extend it | Little code, few dependencies, offline tests, one place for each fact |
| Other cities | Add their own profile and cases | A city profile that is the only city-specific part |
| Technical reviewers (traffic engineers, planners, researchers; IMT and AMT for national standards and regulation) | Judge whether the method is sound | The method and its limits written down, results reproducible bit for bit |

## Questions to ask before a change

1. **The services:** would a technician of the Câmara accept this number, with its grade, its source and its
   scope? If a reference does not cover the case, it is not applied.
2. **The people affected:** does the change keep the people on the buses as the goal, and state what an option
   costs those who lose something (parking, a loading bay) as plainly as what it gains?
3. **The publishers:** is their data attributed as required, cached, and not redistributed beyond its licence?
4. **The claimants:** can a resident run it and read the result in Portuguese without help?
5. **Privacy:** are individual reports and anything identifying a person kept out of every output, aggregates
   only?
6. **The maintainers:** does it remove code or fix a root cause, or does it add something a volunteer will have
   to carry?

## What a toolset like this can and cannot do

It can:

* measure a street from the municipality's own cartography and count the buses its timetable schedules;
* compare a measured width with published design references, within their stated scope;
* measure options such as giving the space of one parking strip back to the carriageway;
* make every number reproducible from pinned public inputs, and grade every statement by its evidence;
* draft a case for another street from its name, and check a letter's claims against the findings.

It cannot:

* observe the street: parked cars, actual bus operation, delays, near misses. Those need a site visit,
  operator data or observation, and the findings say so (grade NE);
* decide what a street should be. Layouts are the municipality's responsibility, weighed against every user and
  usually after consultation; the toolset informs that decision, it does not make it;
* replace an engineer's swept-path study or safety audit;
* speak for the residents who park, the operator or the services: it can only state, with evidence, what each
  option means for them;
* guarantee that the municipal services stay online or keep their addresses: it pins and archives what it used,
  and fails with a clear message when a service is down or moved;
* give legal advice.

## Decisions taken with this list in mind

* The project states its purpose, and the first tool asks whether parking leaves room for the buses, not whether
  the buses fit the street (passengers, services).
* The option without parking is measured, but not compared with design references whose scope assumes the
  parking it removes (services).
* Pins and dated data files keep every published result reproducible (services, journalists, reviewers).
* Citizens' reports are counted per street, never shown one by one, and are not presented as proven infractions
  (privacy, those who enforce parking rules).
* Downloads are cached and locked; a failed or unchanged download does not leave the repository changed
  (publishers, maintainers).
* A drafted case states in its header what it assumed: each reference stop with its distance from the street,
  compass labels that could be read either way, and, where buses run one way, a question that supposes a car
  beside the bus (claimants, services).

Open, from this list: state the parking an option removes (metres per side, and places as a stated assumption),
so that EMEL and the residents who park see the cost next to the gain.
