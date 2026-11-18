# Feasibility and cost-benefit appraisal

The `appraisal` stage (`src/mobilidados/appraisal.py`, configured by `[appraisal]` in a case) answers the question a
municipality must answer before it acts: **is giving one parking strip back to the carriageway worth what it costs,
and is it feasible?** It writes a study, `results/appraisal.md`, in the case's language, its tables
(`results/tables/appraisal_*.csv`), a figure (`figures/appraisal_npv.png`) and one ledger finding per option.

It needs `[delay]`: the benefit it values is the time buses lose at the evening peak, measured from archived vehicle
positions (docs/methodology.md, *Time on a stretch*).

## Method

An incremental economic analysis of each option against doing nothing, following the European Commission's
*Economic Appraisal Vademecum 2021-2027* (EAV): constant prices of `price_year`, `horizon_years` years, a social
discount rate of `discount_rate` (5% for cohesion countries such as Portugal, EAV p. 20; `discount_rates_tested` as a
test). Each option removes the parking on one side in the sections with parking on both sides of the `blocks` it
names, always or only on some days and hours.

**Benefit:** the buses' time at the evening peak that the option can remove, a year:

    bus-hours = excess per passage × attribution × buses at peak per working day × working days ÷ 3600 × compliance
    benefit   = bus-hours × (passengers on board × downstream multiplier × value of time × weight of delay + cost of a bus-hour)

* *excess per passage* is the `delay` stage's measurement (with its 90% interval as the range);
* *buses at peak* come from the timetable on the case's service day, and *working days* from the reference year
  without the city profile's holidays;
* *attribution* is the share of the excess the option can remove, read from the data, not assumed (next section).

**Costs:** the value of the places removed to whoever loses them (`car_value`, for the `parking_share` of it the
restricted hours take, times `occupancy`), the works (`signs` × `sign_cost` + metres × `marking_cost_m`, half the
marking repainted every `repaint_every_years`) and, for a restriction by hours, its enforcement (`enforcement_year`).
Both the benefit and the parking cost scale with `compliance`: a car that stays blocks the bus and keeps its place.
Parking fees are transfers and stay out.

**Results** per option: the yearly flows, present values, net present value (NPV), benefit-cost ratio, the NPV at the
tested discount rates, and who gains and who loses (passenger hours, bus-hours and places).

## Attribution: how much of the excess an option removes

The `delay` stage also measures the excess on each part of the stretch on its own (`delay_by_part.csv`): each section
with parking on both sides, and each piece between them (usually a junction). And it counts, for buses on each part
at peak, how often a bus in the other direction is on the street at the same snapshot, against how often one is
there at any snapshot (`delay_copresence.csv`, with an exact binomial p-value). A part where buses have an oncoming bus
present far more often than chance is where they **give way**: they wait there for the narrow section ahead to clear.
For an option widening the sections of some blocks:

* **low**: the excess inside those sections;
* **central**: plus the excess at the junctions next to them where buses give way (p below `significance`);
* **high**: plus the excess at every junction next to them.

Shares are of the sum of the parts' excesses. In Rua Ricardo Jorge, more than half the excess sits at the two
junctions between the narrow sections; at the first one, buses have an oncoming bus present 26% of the time against
11% by chance (p ≈ 1.5 × 10⁻⁶), and at the second, no more than chance: the central attribution counts the first
junction and not the second.

## Uncertainty

Every input has a low, central and high value, a grade (docs/evidence-standard.md) and a source
(`appraisal_inputs.csv`; measured ones in `appraisal_measured.csv`).

* **Switching values** (`appraisal_switching.csv`): the value of each input, the others central, at which the NPV is
  zero, and whether it lies within the range tested. A share is searched within [0, 1]; a positive quantity never at
  zero.
* **Tornado** (`appraisal_tornado.csv`): the NPV at each input's low and high value.
* **Monte Carlo** (`appraisal_montecarlo.csv`): `draws` draws of every input, independently, from a PERT distribution
  on its low, central and high value (fixed `seed`, so every run gives the same numbers). PERT, the usual distribution
  for three-point estimates, keeps most of its weight near the central value: a long range on one side (a place worth
  up to a garage's rent) does not drag the mean far from the value the evidence points to, as a triangular
  distribution would. The same draws serve every option: the probability that each is positive, and that each is the
  best, are comparable.

## Alternatives whose effect cannot be estimated

`[[appraisal.alternatives]]` lists measures the data cannot value, such as priority at the narrowings (signs B5 and
B6, which organise alternating traffic instead of widening). For each, the study gives its cost and the bus-hours a
year (and seconds per peak passage) it must save to pay for itself (`appraisal_alternatives.csv`), not an NPV the data
could not support.

## Feasibility

`appraisal_feasibility.csv` and the study's *Feasibility* section:

* **technical**: the median free width without one side's parking against two buses (bodies, mirrors) and the design
  references the case compares;
* **social**: the places removed against the parking mapped within 150 m and 300 m (from the cartography; its
  occupancy is not published, which the study says);
* **legal, operational, social and evidence notes** from `[[appraisal.notes]]`: who decides, how it is signed, what the
  operator and the municipal parking company say, and what is not known. Each note has its grade and source.

## What it does not do

* It monetises only the peak time the measurement supports. The time lost off-peak (the measurement's baseline, so not
  separable), the delay of people in cars, reliability, safety and emergency access are listed, not valued: the
  benefits are understated, and the study says so.
* It has no traffic model: options that change circulation (one-way streets, rerouting) are screened out in the study
  with the reason, not appraised.
* Its inputs are independent in the simulation; inputs that move together (more passengers when buses are later) would
  widen the spread.
* It is a study to inform a decision, not the decision: the weights between residents who park and passengers who ride
  are the municipality's to set, and the switching values say where the answer turns.
