# DEEP GLINT — Scatter Pays with Glint Spots

Kilara's release game, grown from the kilara_poc proof of concept. Prototype math: the rules
below are what the simulation implements; tuning values may still change before submission.

#### Summary

* 6 reels × 5 rows, pay anywhere: 8+ of a symbol anywhere on the board pays.
* Winning symbols explode and the board tumbles until it stops paying.
* 8 paying symbols (H1–H4, L1–L4) and a scatter (S). No wilds, no multiplier symbols.
* Max win 15,000× the base bet in every mode. Reaching it ends the round.
* High volatility. RTP 96.5% in every mode.

#### Glint Spots

Every board position has a Glint Spot.

* An explosion on an unlit spot primes it. An explosion on a primed spot lights it at 2×.
  Each further explosion doubles it, up to 256×.
* A symbol win is multiplied by the highest lit spot under its symbols (1× when none is lit).
  Primed spots do not multiply.
* Wins are evaluated with the spots as they are, then the spots under the winning symbols grow.
* Base game: spots reset at the start of every round. Free spins: spots start clear and
  persist for the whole feature.

#### Glint Strike

The character lights 3–6 random spots at 2×, 4× or 8× (a spot already brighter keeps its value):

* before a base game board is evaluated, on 5% of spins in base and ante and every spin in boost;
* at the start of every free spins session, triggered or bought.

#### Free spins

* 4 / 5 / 6+ scatters award 12 / 14 / 17 free spins.
* 3+ scatters during free spins award 5 more.

#### Modes

Mode names are the same in the math, the game and the replay (Stake social rules).

| mode  | cost  | what it is                                              |
|-------|-------|---------------------------------------------------------|
| base  | 1×    | normal play                                             |
| ante  | 1.5×  | twice the base chance of triggering free spins          |
| boost | 1.75× | a Glint Strike on every spin                            |
| bonus | 140×  | free spins straight away, same rules as triggered ones  |
| super | 250×  | free spins that start with every spot lit at 2×         |

Costs follow what each mode is naturally worth, so its books keep their simulated shape: a
bought session costs its natural average at 96.5%, and twice the base free spins chance costs 1.5×.

#### Book events (beyond the standard SDK events)

* `glintStrike` — `spots`: [{reel, row, value}] with rows including the padding row (like
  winInfo positions), and `glint`: the whole grid after the strike. In free spins it comes
  right after the opening `updateGlint`, before the first `updateFreeSpin`.
* `updateGlint` — `glint`: the whole grid, indexed [reel][row] without padding rows. Sent at
  the start of free spins and after every winning tumble step.
* winInfo `meta.clusterMult` is the Glint multiplier applied to that symbol win.

#### Files

* `reels/make_reels.py` generates BR0 (base), FR0 (free spins) and WCAP (only used to find
  max-win rounds) from symbol weights.
* `game_weights.py` builds the lookup tables. It does not use the Rust optimizer: every book
  keeps its natural frequency, each category (zero, base game, free spins, max win) is set to
  its target frequency, and an average that must move is shifted by a smooth power tilt.
  The optimizer reshaped categories into its own trial curves and left gaps (1–10× rarer than
  10–50× in base; free spins above 500× nearly gone).
* `freegame_tail` books are free spins sampled at 2,000×+ only, so the rare 5,000×+ range has
  books in every mode; they share the tail's natural probability (see game_weights.py).
* `run.py --sims N [--raw] [--skip-sims] [--modes ...]` runs the pipeline; `--raw` stops after
  the books, `--skip-sims` reweights and re-checks existing books.
