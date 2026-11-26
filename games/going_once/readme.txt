# Going Once — 5×3 Lines with an Auction (hold & win)

Kilara's fourth game (working title). The rules below are what the simulation implements; the
game's rules page and paytable are written from this file. The design, its targets and the last
measurements are in MATH.md.

There is no player choice anywhere in a round: every auction runs by itself from the opening
board to the fall of the hammer.

#### Summary

* 5 reels × 3 rows, 20 fixed lines. A line pays for 3, 4 or 5 like symbols from the leftmost
  reel. Only the highest win per line is paid; wins on different lines are added.
* 8 paying symbols (H1–H4, L1–L4), a wild (W, reels 2–4), lots (P, every reel) and a gavel
  (G, base game: reel 3 only). A lot carries a value in multiples of the base bet.
* 6 or more lots on a base game board start the Auction.
* Max win 25,000× the base bet in every mode. Reaching it ends the round.
* High volatility. RTP 96.70% in every mode.

#### Paytable (multiples of the base bet, per line)

| symbol | 3   | 4   | 5   |
|--------|-----|-----|-----|
| H1     | 3   | 12  | 45  |
| H2     | 2   | 7.5 | 25  |
| H3     | 1.5 | 4.5 | 15  |
| H4     | 1.2 | 3   | 12  |
| L1     | 0.8 | 1.5 | 6   |
| L2     | 0.6 | 1.2 | 4.5 |
| L3     | 0.4 | 1   | 3.8 |
| L4     | 0.3 | 0.8 | 3   |

W substitutes for every paying symbol. A line of wilds alone pays as H1. Lots and gavels do not
pay on lines and break a line.

#### Lines (row per reel, 0 = top)

 1 11111   2 00000   3 22222   4 01210   5 21012
 6 00100   7 22122   8 10001   9 12221  10 01010
11 21212  12 11011  13 11211  14 01110  15 21112
16 10101  17 12121  18 00200  19 22022  20 02020

#### Base game gavel

A gavel on reel 3 multiplies all of that spin's line wins by 2.

#### The Auction

* Lot values: 1, 2, 3, 5, 10, 25 or 50× the base bet.
* The lots on the triggering board stay; every other cell is empty. The auction has 3 respins.
* On every respin each empty cell independently shows nothing, a lot, a gavel or a buyer.
  Anything landing resets the respins to 3 ("going once, going twice, sold").
* After the respin's symbols land: each **buyer** becomes a lot worth the sum of every other lot
  in its reel (at least 1×); then each **gavel** doubles every lot on the board and leaves (its
  cell stays empty).
* The auction ends when the respins run out or all 15 cells hold lots.
* **Last Bid**: when the hammer falls the final bid multiplies the total of all lots by ×1 (no
  raise), ×2, ×3, ×5, ×10, ×25, ×50 or ×100.
* **Full House**: an auction that ends with all 15 cells holding lots pays twice its total.
* The auction pays its total once, at the end.

#### Bet modes

| mode    | cost | what it does |
|---------|------|--------------|
| base    | 1×   | normal play |
| ante    | 1.5× | the Auction about 1.8× as often |
| bonus   | 110× | starts the Auction with 6 lots |
| gavel   | 190× | starts the Auction with 6 lots and a gavel strike |
| private | 340× | starts the Auction with 9 lots and two gavel strikes |

A bought round's opening board shows exactly the lots its mode names; its own line wins are paid.
Gavel strikes a mode starts with happen right after the auction opens.

#### Events (beyond the SDK's standard ones)

Cells are {reel, row} with rows counting the padding row, like winInfo.

* `baseGavel` — base game: a gavel multiplies the spin's line wins (cell, multiplier).
* `auctionStart` — the lots that stay (cell, value) and the respins (3).
* `auctionRespin` — one respin: what landed (cell, kind P/G/B, value for lots) and respins left.
* `buyerCollect` — a buyer becomes a lot (cell, value).
* `gavelStrike` — a gavel doubles every lot (cell, null for a strike a buy mode starts with;
  lots after the strike).
* `lastBid` — the hammer falls (multiplier, the lots' total before it).
* `auctionEnd` — the final lots, the auction's total and whether it was a Full House.
