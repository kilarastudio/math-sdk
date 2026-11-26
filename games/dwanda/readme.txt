# Dwanda — Cluster Pays with Phoenix and Dragon Territory

Kilara's fifth game (working name, not yet confirmed; Phoenix vs Dragon). The rules below are
what the simulation implements; the game's rules page and paytable are written from this file.
The design, its targets and the last measurements are in MATH.md.

#### Summary

* 7 reels × 7 rows. A cluster of 5 or more of one symbol, touching side to side or top to
  bottom, pays.
* Winning symbols are removed and the board tumbles until it stops paying.
* 8 paying symbols on two sides: phoenix P1–P4 (warm) and dragon D1–D4 (cool), paying the same
  by rank; and a scatter (S). No wilds.
* Max win 25,000× the base bet in every mode. Reaching it ends the round.
* High volatility. RTP 96.70% in every mode.

#### Paytable (multiples of the base bet)

| symbol  | 5   | 6–8 | 9–12 | 13+ |
|---------|-----|-----|------|-----|
| P1 / D1 | 5   | 13  | 32   | 80  |
| P2 / D2 | 2   | 5   | 13   | 40  |
| P3 / D3 | 0.8 | 2   | 5    | 16  |
| P4 / D4 | 0.4 | 1   | 3.2  | 8   |

#### Territory and Clash cells

Every board position can be phoenix territory, dragon territory, or a Clash cell. Territory
belongs to the position: it does not fall with the symbols.

* After a cascade's clusters are paid, every winning cluster marks its cells for its side.
* A cell already marked for the other side becomes a **Clash cell** worth ×2.
* A Clash cell under a later winning cluster (either side) doubles, up to ×1,024.
* A cluster is paid times the **sum** of the Clash cells under it (none: ×1).
* Base game: the territory is cleared at the start of every round.

#### The Duel (free spins)

* 3, 4 or 5 scatters award 10, 12 or 15 free spins; 3 or more scatters during the Duel add 5.
* The Duel starts on an empty territory, and the territory stays for the whole feature.
* In the Duel a winning cluster's mark also spreads to the cells next to it (side to side and
  top to bottom). A spread mark on the other side's territory makes a Clash cell at ×2; a spread
  mark does not double an existing Clash cell.

#### Bet modes

| mode    | cost | what it does |
|---------|------|--------------|
| base    | 1×   | normal play |
| ante    | 3×   | the Duel about 4.5× as often |
| bonus   | 160× | starts the Duel with 10 free spins |
| blaze   | 250× | the Duel with 5 Clash cells at ×4 on random cells |
| eclipse | 500× | the Duel with 9 Clash cells at ×8 on random cells |

A bought round's opening board shows exactly 3 scatters.

#### Events (beyond the SDK's standard ones)

* `territory` — the whole territory after it changes: `marks` [reel][row] (0 none, 1 phoenix,
  2 dragon, 3 clash) and `clash` values, rows without padding; `reason` is "marked" (after a
  winning cascade) or "start" (a bought Duel begins with Clash cells).
