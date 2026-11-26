Kilara Keno (working id kilara_keno; the public name is not chosen yet)

Rules as the math implements them.

Board and draw
- The board has 40 numbers. The player picks 2 to 10 numbers and a level before the round.
- Low and High cost 1x the bet and draw 10 numbers, one at a time, without replacement.
- Chain costs 10x the bet and Chain Max costs 100x the bet. Both play 10 picks and draw 12 numbers.
- A drawn number that the player picked is a hit.
- Kilau numbers: before the draw, numbers the player did not pick are marked. Low, High and Chain
  mark 1 number; Chain Max marks 3. A marked number that is drawn is a Kilau ball.

Win
- Win = pay for the number of hits (table of the chosen level and pick count) x multiplier.
- Meter level = best run of hits + number of Kilau balls drawn.
  Level 1: x1, 2: x2, 3: x3, 4: x5, 5: x10, 6: x15, 7 or more: x25.
- Low / High: a run is hits drawn one after another. A miss ends the run. A Kilau ball does not.
- Chain / Chain Max: a hit raises the run by one, a miss lowers it by one (never below zero), a
  Kilau ball leaves it. The highest run reached counts.
- A round with no hit pays nothing.
- The highest win of the game is 100,000x the bet (Chain Max). High reaches 50,000x (8 and 10 picks).

Pay tables (x bet, before the multiplier; index = number of hits, from 0)
- low_2   0, 1, 6
- low_3   0, 1, 1.2, 8.4
- low_4   0, 0.3, 1.5, 3.6, 15
- low_5   0, 0.2, 1, 1.5, 8, 50
- low_6   0, 0, 0.8, 1.5, 3, 10, 40
- low_7   0, 0, 0.6, 1, 2, 5, 15, 40
- low_8   0, 0, 0.3, 0.8, 1.5, 4, 6, 12, 20
- low_9   0, 0, 0.3, 0.5, 1, 2.5, 6, 8, 20, 20
- low_10  0, 0, 0, 0.5, 0.8, 1.5, 5, 7.5, 10, 20, 20
- high_2   0, 0.4, 9.5
- high_3   0, 0, 1, 35
- high_4   0, 0, 0.5, 7.5, 50
- high_5   0, 0, 0.4, 2, 9, 250
- high_6   0, 0, 0.2, 1, 5, 35, 500
- high_7   0, 0, 0, 0.6, 3, 12, 100, 1000
- high_8   0, 0, 0, 0.3, 1.2, 5, 44, 400, 2000
- high_9   0, 0, 0, 0.2, 0.8, 2.3, 15, 100, 1500, 1500
- high_10  0, 0, 0, 0, 0.5, 1.2, 5, 60, 600, 2000, 2000
- chain_10  0, 0, 2, 3, 5, 5, 10, 25, 500, 2000, 2000
- chainmax_10  0, 0, 10, 25, 40, 40, 75, 300, 1500, 4000, 4000

Modes: <level>_<picks>, 20 in total: low_2 to low_10, high_2 to high_10, chain_10, chainmax_10.
RTP 96.54% to 96.69% by mode (see MATH.md).

Books
- Every possible order of hits, misses and Kilau balls of a mode's draw is published the same
  number of times, each copy with its own numbers, so a mode holds a little over 100,000
  different rounds (Chain Max: 208,871). A book's weight is the number of real ordered draws that
  give its order (divided by a common factor), so the lookup table is the exact keno
  distribution. No sampling and no optimizer.
- Event "draw": level, picks, draws, selected (the book's own selected numbers, ascending),
  kilau (the book's Kilau numbers, ascending), numbers (the numbers drawn, in order), pattern
  (1 = hit, 2 = Kilau ball, 0 = miss, in draw order), hits, streak (best run), kilauHits,
  multiplier, pay (hundredths of the bet).
- Live play: the player's numbers stand in for the book's. The i-th smallest number in
  "selected" is shown as the player's i-th smallest number, and the i-th smallest of the other
  numbers as the i-th smallest number the player did not choose. Kilau numbers are among the
  other numbers and move with them. This is a relabelling of the board: hits, Kilau balls, order
  and win are unchanged, and the frontend draws nothing at random.
- Replay: the RGS gives the mode and the book only, so a replay shows the book's own
  "selected", "kilau" and "numbers". The draw order, hits, multiplier and win are those of the round.
- Event "finalWin": the round's win.
