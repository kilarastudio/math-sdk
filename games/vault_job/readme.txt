# The Vault Job — 5×4 Lines with Crew Wilds

Kilara's third game (working title). The rules below are what the simulation implements; the
game's rules page and paytable are written from this file. The design, its targets and the last
measurements are in MATH.md.

#### Summary

* 5 reels × 4 rows, 20 fixed lines. A line pays for 3, 4 or 5 like symbols from the leftmost
  reel. Only the highest win per line is paid; wins on different lines are added.
* 8 paying symbols (H1–H4, L1–L4), four crew wilds (WD Driver, WC Safecracker, WM Muscle,
  WH Hacker) and a scatter (S). Crew land on reels 2–5 only; scatters on any reel.
* Max win 20,000× the base bet in every mode. Reaching it ends the round.
* High volatility. RTP 96.70% in every mode.

#### Paytable (multiples of the base bet, per line)

| symbol | 3    | 4    | 5    |
|--------|------|------|------|
| H1     | 1.5  | 6    | 25   |
| H2     | 1    | 3    | 12   |
| H3     | 0.5  | 2    | 8    |
| H4     | 0.4  | 1.5  | 6    |
| L1     | 0.3  | 0.7  | 2.5  |
| L2     | 0.2  | 0.5  | 2    |
| L3     | 0.1  | 0.4  | 1.5  |
| L4     | 0.1  | 0.3  | 1.2  |

A line made only of crew pays as H1. When a line starts with crew followed by a paying symbol,
it pays whichever is higher: the paying symbol's line or the crew-only line.

#### Lines (row per reel, 0 = top)

 1 00000   2 11111   3 22222   4 33333   5 01210
 6 12321   7 32123   8 21012   9 00100  10 11211
11 22322  12 33233  13 22122  14 11011  15 01110
16 12221  17 23332  18 32223  19 21112  20 10001

#### Crew wilds

Every crew member is a wild and substitutes for every paying symbol (not the scatter). A line
win is multiplied by the **sum** of the multipliers of the crew on its winning positions that
carry more than ×1; a line with no such crew is paid ×1.

* **Driver (WD)** carries ×2.
* **Safecracker (WC)** carries ×2 in the base game.
* **Muscle (WM)** carries ×1 and fills its whole reel with Muscle wilds when it lands. Cells
  holding a scatter or another crew member keep them.
* **Hacker (WH)** copies the highest multiplier any other crew member on the board carries,
  ×2 at least. Several Hackers all take the same value.

Order on every board: the board is revealed, Muscles fill their reels, Hackers copy, then the
lines are paid.

#### The Job (free spins)

* 3, 4 or 5 scatters in the base game award 10, 12 or 15 free spins.
* The Job always starts with a Safecracker at ×1 on a random cell of reel 2.
* Drivers and Safecrackers that land in The Job are sticky for the rest of the feature.
  Muscles and Hackers act only on the spin they land, as in the base game.
* In The Job a Safecracker carries ×1 when it lands, and every time it is on a winning line it
  climbs one step of its ladder after the spin is paid:
  1 → 2 → 3 → 5 → 8 → 12 → 20 → 30 → 50 → 80 → 120 → 200 → 300 → 500 → 1,000 (top).
* Before every free spin each sticky Driver drives one reel to the left, keeping its row and
  its ×2. It passes over cells other sticky crew hold. A Driver on reel 1 drives off the board.
* Sticky crew cover whatever the reels show in their cells.
* Every scatter that lands during The Job adds one free spin.

#### Bet modes

| mode   | cost  | what it does |
|--------|-------|--------------|
| base   | 1×    | normal play |
| ante   | 2×    | The Job about 3× as often |
| bonus  | 130×  | starts The Job with 10 free spins |
| inside | 290×  | The Job with 10 free spins and a second Safecracker at ×2 on reel 2 |
| heist  | 600×  | The Job with 10 free spins and two more Safecrackers at ×3 on reel 2 |

A bought round's opening board shows exactly 3 scatters; its own line wins are paid.

#### Events (beyond the SDK's standard ones)

Cells are {reel, row} with rows counting the padding row, like winInfo.

* `crewStart` — The Job begins: the crew it starts with (cell, crew, multiplier).
* `crewMove` — before a free spin: Drivers move (from, to; to is null when one drives off).
* `crewExpand` — Muscles fill their reels (reel, the Muscle's cell).
* `crewHack` — Hackers take a multiplier (cell, multiplier).
* `crewBoard` — every crew member on the board as the lines are paid (cell, crew, multiplier,
  sticky). Sent after the reveal and the crew actions on every board that holds crew.
* `crewUpgrade` — after a free spin is paid: Safecrackers that climbed (cell, new multiplier).
