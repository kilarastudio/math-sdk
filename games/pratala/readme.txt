# Pratala — Scatter Pays with Glint Spots

Kilara's release game. The rules below are what the simulation implements; the game's rules
page and paytable are written from this file. The design, its targets and the last
measurements are in MATH.md.

#### Summary

* 6 reels × 5 rows, pay anywhere: 8+ of a symbol anywhere on the board pays.
* Winning symbols explode and the board tumbles until it stops paying.
* 8 paying symbols (H1–H4, L1–L4) and a scatter (S, the dragon's eye). No wilds, no multiplier symbols.
* Max win 25,000× the base bet in every mode. Reaching it ends the round.
* High volatility. RTP 96.70% in every mode.

#### Paytable (multiples of the base bet)

| symbol | 8–9  | 10–11 | 12+  |
|--------|------|-------|------|
| H1     | 10   | 25    | 50   |
| H2     | 5    | 12    | 25   |
| H3     | 3    | 6     | 15   |
| H4     | 2    | 4     | 12   |
| L1     | 1    | 2     | 8    |
| L2     | 0.6  | 1.2   | 5    |
| L3     | 0.4  | 1     | 4    |
| L4     | 0.3  | 0.8   | 3    |

#### Glint Spots

Every board position has a Glint Spot.

* An explosion on an unlit spot primes it. An explosion on a primed spot lights it at 2×.
  Each further explosion doubles it, up to 8×. Past 8× only the Dragon's Gaze doubles a spot.
* A symbol win is multiplied by the highest lit spot under its symbols (1× when none is lit).
  Primed spots do not multiply.
* Wins are evaluated with the spots as they are, then the spots under the winning symbols grow.
* Base game: spots reset at the start of every round. Free spins: spots start as the trigger
  and the mode set them and persist for the whole feature.

#### Glint Strike

The dragon lights random spots at 2×, 4× or 8× (a spot already brighter keeps its value):

* 3–6 spots before a base game board is evaluated, on 10% of spins in base and ante and on
  every spin in boost;
* 8–15 spots at the start of every free spins session, triggered or bought.

#### Dragon's Gaze

Free spins only. Every scatter that lands looks down its reel: each of the five spots on that
reel doubles, up to 4,096× (an unlit or primed spot lights at 2×).

* A scatter gazes once, when it lands: with the spin's reveal, or when it falls in with a
  tumble. Either way the gaze comes before the board is evaluated.
* Two scatters on one reel double that reel twice.
* The scatters that retrigger gaze like any other.

#### Free spins

* 4 / 5 / 6+ scatters award 10 / 12 / 15 free spins.
* With 6+ scatters every spot starts lit at 128×.
* 3+ scatters during free spins award 5 more.
* A round with free spins always pays something: the books hold no free spins round that
  returns nothing.

#### Modes

Mode names are the same in the math, the game and the replay (Stake social rules).

| mode  | cost    | what it is                                                              |
|-------|---------|-------------------------------------------------------------------------|
| base  | 1×      | normal play                                                             |
| ante  | 3×      | free spins trigger about 7 times as often                               |
| boost | 1.85×   | a Glint Strike on every spin                                            |
| bonus | 100×    | free spins straight away, same rules as triggered ones                  |
| super | 205×    | free spins that start with every spot lit at 8×                         |
| hoard | 435×    | free spins that start with every spot lit at 4×, with a Dragon's Gaze   |
|       |         | before every free spin: it doubles one reel, moving one reel to the     |
|       |         | right each spin (reel 1 before the first spin, wrapping after reel 6)   |

A bought session draws its 4, 5 or 6 scatters in the proportions the base reels give them
(93.5% / 6.2% / 0.24%), so a bought session can be a six-scatter one.

Costs follow what each mode is naturally worth: a bought session costs its natural average
÷ 96.7%, and the spin modes cost what their base game and free spins rate return.

#### Book events (beyond the standard SDK events)

* `glintStrike` — `spots`: [{reel, row, value}] with rows including the padding row (like
  winInfo positions), and `glint`: the whole grid after the strike. In free spins it comes
  right after the opening `updateGlint`, before the first `updateFreeSpin`.
* `glintGaze` — `eyes`: the scatters that just landed and caused it, [{reel, row}] with rows
  including the padding row (empty for the hoard sweep); `reels`: one reel per gaze, so a reel
  listed twice was doubled twice; `glint`: the whole grid afterwards. In free spins it comes
  after a `reveal` or a `tumbleBoard` and before the next `winInfo`; the hoard sweep comes
  after `updateFreeSpin` and before `reveal`.
* `updateGlint` — `glint`: the whole grid, indexed [reel][row] without padding rows. Sent at
  the start of free spins (showing the spots a super, hoard or six-scatter session starts
  with) and after every winning tumble step.
* winInfo `meta.clusterMult` is the Glint multiplier applied to that symbol win.

#### Files

* `MATH.md`, `math_targets.json` — the design sheet and its machine-readable targets.
* `reels/make_reels.py` generates BR0 (base) and FR0 (free spins) from symbol counts. No reel
  exists only to reach the max win.
* `game_weights.py` builds the lookup tables. It does not use the Rust optimizer: every book
  keeps the frequency the reels give it, and the only solved number per spin mode is the free
  spins rate (which lands next to the natural rate in base and boost). No round is forced to
  the max win: max-win rounds are free spins that got there.
* `freegame_tail` books are free spins sampled from a minimum win upward (2,000× in the spin
  modes and bonus, 5,000× in super; hoard reaches the top often enough without them), so the
  rare top of the range has books in every mode; they share the probability the reels give
  that range (tail books kept ÷ rounds tried).
* `run.py [--sims N] [--raw] [--skip-sims] [--natural N] [--modes ...]` runs the pipeline;
  `--raw` stops after the books, `--skip-sims` reweights and re-checks existing books,
  `--natural` measures unforced base spins (library/natural.json). Ante's books are the base
  mode's books (same rules and seeds), simulated once and copied.
* `verify_books.py` replays every published book against the rules above, independently of the
  game code (pays, multipliers, spot growth, gazes, starting floors, the hoard sweep,
  retriggers, totals against the lookup table). Run it after every simulation.
* `analyze_books.py` reads the published books for the counters MATH.md quotes (tumble wins
  per board, RTP through multipliers, top multiplier per round).
