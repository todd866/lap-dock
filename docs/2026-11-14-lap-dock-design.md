# Lap Dock: design

14 November 2026. Working name "Lap Dock". Status: draft for the owner's approval.

Items marked **(owner)** were decided by the owner. Items marked **(call)** are the
designer's choices and can be overturned. Items marked **(measure)** are estimates that
Phase 0 replaces with measurements.

## 1. Intent

A lap tray for a 13-inch M5 MacBook Air that does two jobs a bought cooling pad does
badly or not at all:

1. Cools the Air where it is actually hot, so sustained heavy work does not throttle.
2. Carries its own battery, so the owner can work for hours on a couch or outdoors with
   no cable to a wall or side table.

The owner wants to "sit the laptop down for a good 5–6 hours of heavy work without
thinking about it", to gold-plate the design, to assemble it himself with help from a
local repair shop and an outside 3D-print service, and then to publish it as an open
design.

Nothing like it is sold: searches on 14 November 2026 found no cooling pad with a battery
that powers the laptop.

## 2. Goals, non-goals, anti-goals

**Goals**

- Two identical pads **(owner)**. One is on the lap while the other charges; they are
  exchanged around the middle of the day.
- About 150 Wh of battery per pad, fixed inside the pad, not hot-swappable **(owner)**.
- At least 3 hours of heavy work per pad from the pad's battery alone, at the measured
  heavy draw, before the Air's own battery is touched **(call)**. Across two pads that
  is at least 6 hours, which meets the owner's 5–6 hour target with the Air's own
  battery as reserve.
- The Air stays unmodified **(owner, 14 November)**. On it, sustained performance is
  measurably better than on the Klim, in shade at about 25 °C. The thermal model
  expects about 5–10%, so cooling is a modest extra, not the point of the pad.
  Performance at about 35 °C is measured and published, not promised. Use in direct sun
  is outside the design.
- The tray has a mounting for an optional finned contact plate, for builders who fit a
  thermal pad inside their Air. With both, the model expects about 80% more sustained
  chip power than a stock Air on a lap **(call)**.
- Under load, no louder than the Klim at the owner's usual setting, measured in Phase 0
  **(call)**.
- It keeps the lap cool as well as the laptop: moving air across the thighs and groin,
  as the Klim does, not a warm slab sitting on them **(owner)**.
- The Air mates snugly and lands in the same place every time, without looking **(owner)**.
- Thinner than the Klim pad it replaces, and about the Air's own footprint **(owner)**.
- The Air tells the pad how hot it is, and the pad raises its fan speed to match
  **(owner)**.
- Parts cost no more than A$250 per pad **(owner; read as per pad, since A$250 for the
  pair would not cover the cells)**. Shop labour and the thermal-pad modification are
  outside this figure.
- About 1.5 kg per pad is acceptable **(owner)**.
- Quiet: fans off or inaudible when the Air is idle.
- Buildable by one person plus a repair shop, from bought parts and outsourced prints.
- Published as an open design once the first pair works.

**Non-goals**

- Any laptop other than the 13-inch M5 Air **(owner)**. No adjustable fit.
- Hot-swappable or removable battery cartridges (considered and dropped, section 5).
- Airline carry-on compliance **(owner)**.
- Depending on software on the Mac. The pad must work fully on its own; the link to the
  Air is an improvement, not a requirement.
- A phone app or any cloud service.
- Adjustable tilt, lights for decoration, a USB hub.

**Anti-goals** (it has failed if any of these is true, even if it works)

- The owner has to think about power during a session.
- It is a lump on the lap: thick, heavy at one end, or warm against the legs. A pad that
  cools the laptop but leaves the lap hotter than the Klim does has failed.
- The battery pack can be assembled unsafely by someone following the published design.
- It heats the Air's own battery, which sits under the front two-thirds of the laptop.

## 3. Facts and constraints

Measured on the owner's Mac on 14 November 2026:

| Fact | Value |
|---|---|
| Model | MacBook Air, Mac17,3, Apple M5, 32 GB, 13.6-inch (2560 × 1664) |
| Battery | 53.8 Wh (Apple); 4,629 mAh design capacity as reported by the Mac |
| Size and weight (Apple) | 304.1 mm wide, 215 mm deep, 11.3 mm high, 1.23 kg |
| Charging (Apple) | MagSafe 3 or USB-C; 30 W minimum; fast charge needs a 70 W or larger USB PD source |
| The Klim being replaced (KLIM Ultimate, maker's figures) | 425 × 315 × 43 mm, 960 g, one 200 mm fan at 750 rpm |
| System load at light work, outdoors | 10.3 W |
| Current tether | a small INIU power bank feeding both the Klim and the Air; the Air receives only 5 V, 7.2 W, less than its load |

Not yet measured **(measure)**:

- Draw under sustained heavy work. Estimate 25–35 W, possibly more outdoors at full
  screen brightness. This sets the cell count.
- Where the underside is hottest. In M1–M3 Airs the logic board is a strip along the
  back near the hinge, roughly centred; this is assumed for the M5 and not confirmed.
- Apple publishes no mechanical drawing of the Air (its accessory drawings page lists
  only the MacBook Neo), so foot positions, foot height and corner radius are not
  available. The design is arranged not to need them (section 4.2).

Constraints:

- The stock Air has an air gap between the chip's heat spreader and the bottom case, so
  cooling the base does little. A thermal pad in that gap (documented on M1–M3 Airs,
  roughly doubling time-to-throttle on the M2) makes the base the heatsink.
- The owner has decided against that modification for now **(owner)**: the gap is what
  keeps the base at a safe touch temperature when the Air is used off the tray, and a
  padded Air's base reaches about 60 °C on a bare lap in the model. The decision is
  revisited once the draw log shows whether his real work throttles the Air at all.
- The Air's feet hold its base a millimetre or two off any flat surface, so a flat plate
  will not touch it. The contact surface has to rise between the feet.
- Used outdoors: warm air, sun, dust, grass, drinks nearby.
- Lithium cells must be joined by spot welding. Soldering directly to cells is not
  acceptable. The local phone repair shop may not have a welder; this is unconfirmed.
- This laptop stays cool and responsive while in use, so benchmark loads are
  run when the owner agrees to them.

## 4. The design

### 4.1 Layout

A wedge about the Air's footprint plus a margin, roughly 340 × 240 mm **(call)**, low at
the front and higher at the back, with a fixed tilt of 3–5° **(call)**. The Klim is
43 mm thick and 425 × 315 mm. The pad must be no more than 40 mm at its thickest point,
ribs included, and is about 60% of the Klim's footprint; the tilt is the dimension that
gives way to meet the 40 mm limit. Estimated 18 mm at the front edge and 32 mm at the
back before the ribs.

Three bands from front to back. Depths are estimates from the wedge geometry: a cell
bay needs about 27 mm of thickness, which the wedge reaches about 100 mm from the front.

1. **Front band, 0 to about 100 mm (thin):** electronics, the charge gauge on the front
   edge.
2. **Middle band, about 100 to 155 mm:** the battery pack in a single layer, cells lying
   left to right in two rows of four placed end to end (about 280 × 42 mm), in an
   enclosed bay with a screwed cover on the underside. A ten-cell pack takes a third
   row and about 20 mm more depth.
3. **Rear band, about 135 to 240 mm:** the air channel under the Air's hot zone and the
   blower beside it. Published temperature maps of the M5 Air put the heat in the
   hinge-side third, centre to left of centre, with the front third cool.

The blower is about 30 mm thick, which with the ribs brings the rear to the 40 mm limit.

The bands are separated by solid walls. The wall between the fan band and the battery
bay is insulated so heat does not reach the cells.

The underside is an air floor, not a smooth slab: rounded ribs about 6–8 mm tall run
front to back, so the pad rests on the ribs and the gaps between them are open channels
along the thighs. This adds to the thickness figures above; the total is settled in
Phase 1.

The band depths and the duct position are parameters, fixed after the hot-spot map.

### 4.2 Mating with the Air

- The Air is located by its outline, which Apple publishes (304.1 × 215 mm): a low,
  soft-lined lip along the front and both sides, open at the back for the hinge and the
  leads. The lip clears the Air by about 0.5 mm a side and its corners are relieved, so
  the unknown corner radius does not matter **(call)**.
- The Air's feet land on a flat deck. No pockets are cut for them, so their positions
  are not needed.
- The seal around the cooling zone is a soft foam gasket about 4 mm tall that compresses
  under the Air's weight, so the unknown foot height (a millimetre or two) is absorbed
  by the foam, not designed around **(call)**.
- The first print of Phase 1 is a plain outline ring, to confirm the fit on the real
  laptop before anything else is printed.
- Nothing clamps the Air; it lifts straight out.

### 4.3 Cooling

Set by the thermal study in `docs/cooling-study.md` (a model calibrated to published
temperature maps of the M5 Air). What it found:

- **A stock Air is limited inside, not outside.** Its chip sits near 100 °C while the
  case above it is about 44 °C. No tray gains more than about 20% on a stock Air.
- **Thin flat fans do not work here.** In a tray this thin, fed through channels under a
  lap, they deliver under a fifth of their rated airflow. They are dropped.
- **With a thermal pad inside the Air, a finned contact plate is far the best**, about
  80% more sustained chip power than a stock Air on a lap.

The baseline arrangement, for the unmodified Air **(owner's decision; layout is a call)**:

1. One centrifugal blower (75 mm class) at the right rear draws air in through the rib
   channels on the underside, so the air crosses the lap first.
2. It drives that air through a 4 mm channel between the tray deck and the Air's base,
   across the hinge-side third where the heat is, sealed at the sides by a soft gasket.
3. The air leaves at the back edge, away from the user. Air is never blown downward.
4. The blower normally runs at about 70% speed, where the model gives about 28 dBA.
   Speed follows the chip temperature sent by the Mac (section 4.6), with a low minimum
   for the lap whenever the Air is awake.

Model prediction, to be confirmed in Phase 1: about 8.8 W sustained in the chip at
25 °C, against 7.7 W bare on a lap and 8.4 W on the Klim, with the hottest point of the
base about 40 °C instead of 50 °C bare. The base running cooler is the larger benefit.

The optional upgrade **(call)**: the channel floor under the hot zone is a removable
panel, about 160 × 75 mm. A builder who fits a thermal pad inside the Air replaces it
with a finned aluminium plate (bought heatsink stock) that touches the base through a
thin, very soft thermal sheet, and the same blower drives air through the fins. The
published guide states plainly that a padded Air used off the tray runs dangerously hot
at full load.

If Phase 1 shows the channel no better than the Klim, the pad continues as a battery
tray with the blower kept for lap airflow, since the battery was the owner's first
request.

### 4.4 Battery

- Eight 21700 lithium-ion cells, 4 in series and 2 in parallel, about 144 Wh nominal and
  about 0.56 kg **(call, pending the draw measurement)**. After conversion losses, the
  protection cut-off and the fans, expect about 120–125 Wh delivered to the Air: about
  4 hours at 30 W and 3.5 hours at 35 W.
- If measured heavy draw is above about 40 W, eight cells no longer give 3 hours and the
  pack becomes ten cells (5 in series, about 180 Wh nominal), taking a third row.
- Cylindrical cells in a steel can are chosen over flat pouch cells **(call)**: pouch
  cells would make the pad about 10 mm thinner but swell with age and are easier to
  puncture, which is the wrong trade for something on a lap.
- A protection board with cell balancing, over-current, over- and under-voltage and
  temperature cut-off. A fuse on the pack's main lead. A temperature sensor on the cells.
- The pack is a single sub-assembly on a plug, in a cell holder, welded by someone with a
  spot welder. It is replaceable when it ages, through the underside cover, with the pad
  powered off.
- The battery bay is printed in a flame-retardant material and has a vent path that
  points away from the user's legs.

### 4.5 Power electronics

- **USB-C in:** charges the pack from any USB-C charger. Charge power is capped at what
  the chosen cells allow, likely 70–80 W, since 100 W into this pack exceeds the
  standard charge rate of most high-capacity cells. Charging stops if the cells are
  above about 45 °C, so the pad is charged indoors or in shade.
- **USB-C out:** feeds the Air at 20 V, 70 W minimum (Apple's threshold for fast
  charging), 100 W preferred. The pack runs at
  12–16.8 V, so this stage must step the voltage up as well as down.
- With a charger connected, the pad charges its pack and feeds the Air together. If no
  bought board does both well, the fallback is one two-way port and charging only when
  the pad is off the lap, which the two-pad routine already allows **(call)**.
- The pad connects to the Air by MagSafe **(owner)**. MagSafe 3 is fed from an ordinary
  USB-C power source, so the out port stays USB-C and the lead is a USB-C to MagSafe 3
  cable, as short as can be had, routed and retained at the pad end so only the magnetic
  end is loose. This leaves both of the Air's USB-C ports free and keeps the breakaway.
  The Air's MagSafe port is at its left rear, so the out port is at the pad's left rear.
- A power switch that isolates the pack.
- Bought modules, not a custom circuit board, for the first pair **(call)**. A custom
  board is a later refinement once the design is proven.

### 4.6 Controller and gauge

- One small microcontroller with Bluetooth Low Energy reads the airstream sensor, drives
  the fans, reads the pack voltage and drives the gauge.
- **Link to the Air.** MagSafe carries power only, and a data cable would take one of the
  Air's two ports, so the link is Bluetooth Low Energy **(call)**. A small helper on the
  Mac sends the chip temperature every few seconds, and the pad sets fan speed from it.
  This reacts sooner than the pad's own sensor, which only sees heat after it has soaked
  through the base.
- If the pad hears nothing for about ten seconds it falls back to its own sensor, so it
  works with the helper absent, asleep or uninstalled.
- The pad reports its charge and temperatures back over the same link, so the Mac can
  show the pad's battery in the menu bar **(call)**. The owner's Glancebar app is the
  natural place for that row and for the helper.
- How the helper reads the chip temperature on Apple silicon is for the builder to
  establish; the public thermal-state reading is the fallback if finer data needs
  private interfaces.
- A row of five small LEDs on the front edge shows charge at a glance. It lights briefly
  on a button press or when the charger is connected, and is otherwise dark.
- No other lights.

### 4.7 Shell

- 3D printed, in sections no larger than 250 mm in any direction so that common printers
  and any print service can make them **(call)**. Sections bolt together with threaded
  inserts.
- ASA or a comparable material for sun and heat resistance, in a light colour so it
  gains less heat outdoors **(call)**; a flame-retardant grade for the battery bay.
- Electronics sit on raised bosses above the shell floor, so a small spill does not reach
  them.
- Modelled in code (CadQuery or build123d, in Python) **(call)**, so every dimension is a
  named parameter, the model is diffable, and the published design can be regenerated.

### 4.8 Estimates

| | Per pad |
|---|---|
| Mass | about 1.5 kg (cells 0.56, shell 0.5, plate and fins 0.2 if used, the rest 0.2); about 2.8 kg on the lap with the Air |
| Parts cost | ceiling A$250 per pad (owner). Unpriced estimate for the bare-base variant with economical parts is A$225–325, so the ceiling is tight |
| Recharge time | about 2–2.5 hours |
| Runtime, heavy work | about 4 hours at 30 W or 3.5 hours at 35 W, plus the Air's own 53 Wh |

What the A$250 ceiling rules in and out **(call)**:

- Bought heatsink stock, never a custom-machined plate. The bare-base cooling variant is
  preferred if it performs, since it has no plate at all.
- One ordinary blower. The finned plate is an optional extra and outside the ceiling.
- The printed shell is the least certain cost. If a print service quotes more than about
  A$80 per pad, the shell is printed at a makerspace or library instead.
- A third-party USB-C to MagSafe 3 lead; Apple's own costs about a third of the budget.
- The priced parts list is produced before any part is bought, and anything that breaks
  the ceiling comes back to the owner.

## 5. Approaches considered

**Where the battery comes from**

| Approach | Trade-off | Outcome |
|---|---|---|
| A. Bought power banks in a printed bay | Certified, no wiring; but shaped around someone else's brick, heaviest | Rejected: a holder, not a device |
| B. Power-tool batteries on a dock | Tough, sold everywhere, swappable; but about 70 mm tall | Rejected: a lump on the lap |
| C. Purpose-built flat pack | Thin and integrated; needs a welded pack | **Chosen (owner)** |

**How the battery is used**

| Approach | Trade-off | Outcome |
|---|---|---|
| One pad, fixed 200 Wh | Simplest; must be plugged in mid-day | Not chosen |
| One pad, two swappable cartridges | Unlimited runtime; thicker, more parts, most shop labour | Considered, dropped |
| Two pads, fixed 150 Wh each | Double the build; each pad lighter and simpler; exchange at lunch | **Chosen (owner)** |

**Cooling path**

| Approach | Trade-off | Outcome |
|---|---|---|
| Whole-base airflow, like the Klim | Simple, cools the lap; most air misses a small fanless laptop | Rejected as is; its lap cooling is kept |
| Closed cross-flow duct, side to side | Thinnest; gives the lap no airflow | Dropped (owner) |
| Air drawn across the lap, thin flat fans blowing up at the base | Simple; the model shows the fans choke to under a fifth of rated flow | Dropped after the thermal study |
| Air drawn across the lap, one blower through a channel along the bare base | Works on an unmodified Air; modest gain; blower is 30 mm thick and louder than a big slow fan | **Chosen (owner: no laptop modification)** |
| The same blower through a finned contact plate, with a thermal pad in the Air | Best in the model by far; makes the Air's base unsafe to hold off the tray | Optional upgrade, not built for the owner |

## 6. Phases

Each phase ends with something tested. Later phases depend on the numbers from earlier
ones.

- **Phase 0, measure.** Log the Air's power draw and thermal-pressure level across real
  heavy sessions (automatic); this also shows whether the owner's work throttles the Air
  at all. Record a throttling baseline on the Klim, and bare if convenient. Ask the
  repair shop whether it has a spot welder. Published dimensions replace hand
  measurement.
- **Phase 1, thermal prototype.** The blower and channel from section 4.3 in a plain
  printed cradle, powered from USB, no battery. Measure against the baseline and
  against the model, on a real lap as well as a bench. No shell is drawn before this
  phase reports.
- **Phase 2, power on the bench.** Pack, protection, charge and output stages wired on a
  bench, not in a shell. Verify output to the Air, charge time, temperatures, cut-offs.
- **Phase 3, pad one.** Full shell, everything integrated. Used daily for two weeks.
- **Phase 4, pad two and publication.** Build the second from the documents alone, fix
  the documents where that fails, then publish.

## 7. Publication

- Hardware under CERN-OHL-P v2, firmware and the Mac helper under MIT, documents under
  CC BY 4.0 **(call)**.
- Published contents: the CAD source and exported models, a priced parts list, wiring
  diagram, firmware, assembly guide with photographs, and the measurements from each
  phase.
- The assembly guide tells builders to buy the pack welded or have it welded, and does
  not describe home welding.
- The thermal-pad modification is documented as optional, with its risks stated.
- Nothing is published or pushed until the owner says so for that action.

## 8. Left to the builder

- Exact parts: cells, protection board, charge and output boards, fans, heatsink stock,
  microcontroller, connectors. Each chosen from current Australian-available stock and
  verified against its datasheet.
- Fin geometry, duct cross-section and fan count, from the Phase 1 measurements.
- The compliant mounting for the contact plate.
- Section split lines, fasteners and wall thicknesses of the shell.
- Firmware fan curve and gauge thresholds.
- The pass mark for "no measurable throttling", set from the Phase 0 baseline.
