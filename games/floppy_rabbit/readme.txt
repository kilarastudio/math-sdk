# Floppy Rabbit — Cluster Pays with Hop & Flop

Kilara's second game. The rules below are what the simulation implements; the game's rules page
and paytable are written from this file. The design, its targets and the last measurements are in
MATH.md.

#### Summary

* 7 reels × 7 rows. A cluster of 5 or more of one symbol, touching side to side or top to
  bottom, pays.
* Winning symbols are removed and the board cascades until it stops paying.
* 7 paying symbols (H1–H4, L1–L3) and a scatter (S). No wilds.
* Max win 25,000× the base bet in every mode. Reaching it ends the round.
* High volatility. RTP 96.70% in every mode.

#### Paytable (multiples of the base bet)

| symbol | 5   | 6–8 | 9–12 | 13+ |
|--------|-----|-----|------|-----|
| H1     | 5   | 12  | 25   | 60  |
| H2     | 2   | 5   | 10   | 40  |
| H3     | 1.2 | 3   | 7    | 30  |
| H4     | 0.9 | 2.4 | 6    | 20  |
| L1     | 0.6 | 1.4 | 4    | 10  |
| L2     | 0.4 | 1.1 | 3.5  | 8   |
| L3     | 0.2 | 0.7 | 2.5  | 5   |

#### Footprints

Every board position can hold a footprint, a multiplier that belongs to the position (it does
not fall with the symbols).

* A footprint starts at 2× and doubles up to 4,096×.
* A cluster is paid times the sum of the footprints under its symbols (1× when there is none).
* Base game: footprints are cleared at the start of every round. Flop Time: footprints stay
  for the whole feature.

#### Hop and Flop

The rabbit sits on the board and takes one of two actions:

* Hop: it jumps to another position, at most two positions away in any direction (never onto
  another rabbit), and leaves a footprint there: 2× on a bare position, or the footprint that
  is already there doubles.
* Flop: it stays where it is and every footprint on the board doubles.

Base game:

* When the board is revealed the rabbit hops once, to any position.
* After every winning cascade, once the new symbols are in, the rabbit takes one action before
  the board is evaluated again: a hop after the first cascade; a hop or a flop from the second
  cascade on.

#### Flop Time (free spins)

* 3 or more scatters award 12 free spins. Scatters are counted when the board has stopped
  cascading.
* 3 scatters bring one rabbit, 4 bring two, 5 or more bring three. Flop Time starts on a clear
  board; each rabbit takes a random position and leaves a 2× footprint on it.
* Before every free spin is evaluated, and after every winning cascade, each rabbit takes one
  action, a hop or a flop.
* Before the 9th free spin the first rabbit always flops, so every Flop Time has at least one
  flop.
* Footprints and the rabbits' positions stay until Flop Time ends.
* 3 or more scatters on a free spin award 5 more. The number of rabbits does not change.
* A round with Flop Time always pays something: the books hold no Flop Time round that returns
  nothing.

#### Modes

Mode names are the same in the math, the game and the replay (Stake social rules).

| mode    | cost | what it is                                                        |
|---------|------|-------------------------------------------------------------------|
| base    | 1×   | normal play                                                       |
| ante    | 3×   | Flop Time triggers about 7 times as often                         |
| bonus   | 110× | Flop Time straight away with 3 scatters: one rabbit               |
| double  | 250× | Flop Time straight away with 4 scatters: two rabbits              |
| fluffle | 500× | Flop Time straight away with 5 scatters: three rabbits            |

A bought round shows exactly the scatters its mode names.

How often an action is a flop is set by the books and is not the same in every mode: with more
rabbits on the board each one flops less often.
