# Feasibility and cost-benefit appraisal

The `appraisal` stage (`src/mobilidados/appraisal.py`, configured by `[appraisal]` in a case) answers the question a
municipality must answer before it acts: **is giving one parking strip back to the carriageway worth what it costs,
and is it feasible?** It writes a study, `results/appraisal.md`, in the case's language, its tables
(`results/tables/appraisal_*.csv`), a figure (`figures/appraisal_npv.png`) and one ledger finding per option.

It needs `[delay]`: the benefit it starts from is the time buses lose at the evening peak, measured from archived
vehicle positions (docs/methodology.md, *Time on a stretch*).

## Standard and practice

Portugal has no national appraisal manual for municipal transport schemes; the reference for public investment in
Portugal is the European Commission's *Economic Appraisal Vademecum 2021-2027* (EAV), and the most complete public
practice on the points the EAV leaves open is the UK Department for Transport's (TAG, and its *Value for Money
Framework*, May 2025). The appraisal takes:

* from the EAV: the incremental analysis at constant prices, the discount rate for cohesion countries, the values of
  time and their real growth with income (p. 59: elasticity 1 for values of time set from Eurostat labour costs, 0.8
  for externalities), the weights of delay and lateness (Table 7), safety treated qualitatively for small projects,
  and **proportionality**: the effort matches what is at stake;
* from the DfT: two benefit-cost ratios (below), the value-for-money categories, a table of the effects without a
  price beside the money (its *Appraisal Summary Table*), distributional analysis (who gains and who loses), switching
  values, and the rule that the category is adjusted for what has no price. The UK Treasury's *Green Book Review
  2025* also warns against reading benefit-cost ratios against fixed thresholds: the NPV and the effects without a
  price decide together.

What a larger scheme would add and this one does not: a traffic model, local stated-preference surveys for the
values of time and of a parking place, and an optimism-bias uplift on costs (the works here are a small share of the
costs). Each is listed among the study's limits.

## Method

An incremental economic analysis of each option against doing nothing, following the EAV: constant prices of
`price_year`, `horizon_years` years, a social discount rate of `discount_rate` (5% for cohesion countries such as
Portugal, EAV p. 20; `discount_rates_tested` as a test). Each option removes the parking on one side in the sections
with parking on both sides of the `blocks` it names, always or only on some days and hours. Fees, fares and permits
are transfers between parties and stay out.

Unit values grow in real terms with income per head (`income_growth`): the values of time, the operator's cost and the
value of a place at elasticity 1, the external costs at 0.8 (`GROWTH` in the code); damage, works and enforcement stay
at their prices. Both sides of the account grow alike, so growth does not favour removing parking or keeping it.

## Value for money

Two conventions divide the same account differently:

* **the EAV's ratio**: all the benefits over all the costs, with the value of the places lost among the costs;
* **the DfT's ratio**: the places lost are a disbenefit to those who use them, netted from the benefits, over what the
  public budget pays (works, calming, enforcement). Its categories (Value for Money Framework, box 5.1): very high from
  4, high from 2 to 4, medium from 1.5 to 2, low from 1 to 1.5, poor from 0 to 1, very poor below 0.

The NPV is the same in both, and it is what decides. The DfT's ratio rises steeply when the works are cheap and the
users' losses are large, so the study never reports it alone.

## Two layers

Better buses are worth more than the minutes they save at one hour of the day, but not everything they are worth can
be measured yet. The appraisal keeps the two apart:

* **the core** counts only what the data measure or official documents state;
* **the extended layer** adds the mechanisms the measurement cannot see yet, each with a unit value from a published
  source, a range and a grade (`P` until it is measured).

The core is the extended layer with those mechanisms switched off (`MECHANISMS` in the code), so the two differ only
by them. A case that does not configure a mechanism leaves it out of both layers.

### Benefits

| mechanism | layer | inputs | how it is counted |
| --- | --- | --- | --- |
| Time at the evening peak | core | measured excess, attribution, `load_peak`, `vot`, `time_weight`, `bus_cost_h` | bus-hours = excess × attribution × peak passages ÷ 3600 × compliance; valued for the passengers on board and for the operator |
| Time at every other hour and day | extended | `offpeak_s`, `load_offpeak` | the same, for an excess of `offpeak_s` per passage, removed in the same share, for the passages the timetable schedules while the option is in force |
| Reliability | extended | `unexpected_share`, `lateness_weight` | the unpredictable part of the delay (a bus held by an oncoming one) is weighted as public-transport lateness (EAV Table 7: 2.5–4) instead of congestion |
| Connections to rail and metro | extended | `transfer_share` | the delay of those who change to a train or the metro further on is weighted as lateness too: a missed train costs the wait for the next |
| Cars held behind a bus | extended | `cars_behind`, `car_occupancy` | their occupants' time, at the same value of time |
| New passengers | extended | `elasticity_ivt`, `journey_min` | new trips = elasticity × time saved ÷ trip time × trips; their gain by the rule of a half. The stress of driving they leave behind is part of that gain, so it is not counted again |
| Car trips left | extended | `diversion_car`, `trip_km`, `external_cost_pkm` | the external costs those trips no longer cause (congestion, accidents, air pollution, climate, noise, upstream emissions), from the EC *Handbook on the external costs of transport* |
| Damage | extended | `damage_year` | scrapes to buses and parked cars, in the share of the stretch widened and the part of the passages the option is in force |

The passages come from the timetable: the passages at the reference stops in each clock hour of a working day (the
service day), the first Saturday and the first Sunday after it that are not holidays (`appraisal_passages.csv`), times
the days of each kind in the reference year (holidays run the Sunday timetable). The evening peak is `[delay]`'s peak
hours on working days.

### Costs

| cost | layer | inputs | how it is counted |
| --- | --- | --- | --- |
| The places removed | core | `car_value`, `occupancy`, `stall_m`, the option's `parking_share` | places × occupancy × what parking elsewhere costs, for the share of the day the restriction applies |
| Room nearby | extended | `room_nearby`, `walk_cost` | the displaced cars that find a free place within 150 m lose only a walk; the others what parking elsewhere costs |
| Works | core | `signs`, `sign_cost`, `marking_cost_m` | signs and markings; half the marking repainted every `repaint_every_years` |
| Traffic calming | extended | `calming_cost` | a wider carriageway invites higher speeds; measures if the speed rises |
| Enforcement | core | `enforcement_year` | for a restriction by hours |

Both the benefits and the parking cost scale with `compliance`: a car that stays blocks the bus and keeps its place.

## Attribution: how much of the excess an option removes

The `delay` stage also measures the excess on each part of the stretch on its own (`delay_by_part.csv`): each section
with parking on both sides, and each piece between them (usually a junction). And it counts, for buses on each part
at peak, how often a bus in the other direction is on the street at the same snapshot, against how often one is
there at any snapshot (`delay_copresence.csv`, with an exact binomial p-value). A part where buses have an oncoming bus
present far more often than chance is where they **lose time to oncoming buses**. Snapshots minutes apart cannot show
what the buses do there (wait, stand face to face, reverse), only that the time is lost there when another bus is
coming; the attribution needs no more than that.
For an option widening the sections of some blocks:

* **low**: the excess inside those sections;
* **central**: plus the excess at the junctions next to them where buses lose time to oncoming buses (p below `significance`);
* **high**: plus the excess at every junction next to them.

Shares are of the sum of the parts' excesses. In Rua Ricardo Jorge, more than half the excess sits at the two
junctions between the narrow sections; at the first one, buses have an oncoming bus present 26% of the time against
11% by chance (p ≈ 1.5 × 10⁻⁶), and at the second, no more than chance: the central attribution counts the first
junction and not the second. The same share applies off-peak: where the time is lost along the stretch does not
depend on the hour.

## Uncertainty

Every input has a low, central and high value, a grade (docs/evidence-standard.md) and a source
(`appraisal_inputs.csv`, with its layer; measured ones in `appraisal_measured.csv`).

* **Switching values** (`appraisal_switching.csv`, both layers): the value of each input, the others central, at which
  the NPV is zero, and whether it lies within the range tested. A share is searched within [0, 1]; a positive
  quantity never at zero.
* **Tornado** (`appraisal_tornado.csv`, extended layer): the NPV at each input's low and high value.
* **Monte Carlo** (`appraisal_montecarlo.csv`, both layers): `draws` draws of every input from a PERT
  distribution on its low, central and high value (fixed `seed`, so every run gives the same numbers). PERT, the usual
  distribution for three-point estimates, keeps most of its weight near the central value: a long range on one side
  (a place worth up to a garage's rent) does not drag the mean far from the value the evidence points to, as a
  triangular distribution would. The same draws serve every option and both layers. The probability that an option
  is the best counts doing nothing as a choice: an option is best in a draw only if it beats every other and pays.
* **Correlated inputs** (`correlations`): two inputs that move together, such as the peak and the off-peak excess (the
  same encounters in the same sections), are paired by Iman-Conover rank reordering: each keeps its own distribution,
  and their ranks follow a correlated normal pair with correlation `rho`.
* **Scenarios** (`appraisal_scenarios.csv`): the core; the extended layer with every input the measurement does not
  cover at the end of its range least favourable to the option (*cautious*), central, and most favourable
  (*favourable*); and the central NPV over each of `horizons_tested` years. The cautious scenario is a bound, the worst
  combination of those ends, not a probability.
* **Value of information** (`appraisal_voi.csv`): what knowing each input before deciding is worth, in present value:
  the expected value of partial perfect information, estimated from the extended layer's draws by grouping them by
  the input. The decision is to do the best option or nothing, so an input is worth measuring only if knowing it could
  change that decision. The expected value of perfect information (all inputs known) bounds them all. It ranks the
  field counts and the data requests by what they can change.

## From the core to the extended layer

`appraisal_bridge.csv` switches the mechanisms on one at a time, at central values, from the core's NPV to the
extended layer's, and records what each adds. It is the most direct answer to "what does this result rest on?": a
positive extended result that depends on one assumed mechanism is only as good as that assumption, and the bridge says
which.

## Who gains and who loses

`appraisal_distribution.csv` splits each option's yearly flows (extended layer, central values) by who receives
them: the bus passengers, the operator, the people driving behind buses, the new passengers, everyone (external
costs), the owners of damaged vehicles, those who park in the street, the municipality and its parking company. The
study adds the passenger trips while the option is in force, the seconds saved per trip and the places removed: the
gains are spread thin over many people, the loss is concentrated on a few, and the weight between them is the
municipality's to set.

## What has no price

`[[appraisal.criteria]]` lists the effects the accounts do not price, or price only in part: the reliability of the
trip and the stress of not knowing when one arrives, access to rail and metro, the quality of life of those who park
in the street, noise and air in the street, safety (which can go either way: fewer scrapes and better sight lines,
but higher speeds on a wider carriageway), emergency access, the municipal design references, equity, reversibility.
For each, the case says how each option moves it (`++`, `+`, `0`, `−`, `−−` or `?`), with the indicator that would
measure it, the grade of the evidence and why (`appraisal_criteria.csv`). No weights are given: they are the
decision-maker's.

## Alternatives whose effect cannot be estimated

`[[appraisal.alternatives]]` lists measures the data cannot value, such as a passing place: the parking on one side
removed over a short length where one bus can pull aside while the other passes. A junction between two narrow
sections is a natural test of one: if buses lose the most time there, a passing place no longer than the junction is
unlikely to work. For each, the study gives its cost (the
places it removes, `parking_m`, valued as an option's places, and its works) and the bus-hours a year (and seconds per
peak passage, and per passage at any hour) it must save to pay for itself (`appraisal_alternatives.csv`), not an NPV
the data could not support.

## Feasibility

`appraisal_feasibility.csv` and the study's *Feasibility* section:

* **technical**: the median free width without one side's parking against two buses (bodies, mirrors) and the design
  references the case compares;
* **social**: the places removed against the parking mapped within 150 m and 300 m (from the cartography; its
  occupancy is not published, which the study says);
* **legal, operational, social and evidence notes** from `[[appraisal.notes]]`: who decides, how it is signed, what the
  operator and the municipal parking company say, and what is not known. Each note has its grade and source.

## Field counts

docs/field/ has three templates anyone can fill in the street (a night count of free places, a deadlock log, a traffic
count), each replacing an assumed input with a measured one.

## What it does not do

* It has no traffic model: options that change circulation (one-way streets, rerouting) are screened out in the study
  with the reason, not appraised, and the cars held behind a bus are an input, not a simulation.
* Its inputs are independent in the simulation; inputs that move together (more passengers when buses are later)
  would widen the spread.
* The extended layer's values are assumptions until measured. They are there so the study shows what each mechanism
  would be worth and what it would take, not to replace the measurement; the core stays the measured answer.
* It is a study to inform a decision, not the decision: the weights between residents who park and passengers who ride
  are the municipality's to set, and the switching values say where the answer turns.
