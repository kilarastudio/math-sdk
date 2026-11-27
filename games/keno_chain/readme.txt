Keno Chain (math id keno_chain)

Rules as the math implements them.

Names: the player reads "lucky number", "lucky ball" and "lucky round". The math's code and the
book events call a lucky number "kilau" (the game's first name for it): the fields kilau,
kilauRound and kilauHits below.

Board and draw
- The board has 40 numbers. The player picks 3, 4, 5, 6, 8 or 10 numbers and a level before the
  round.
- Calm, Bold and Wild cost 1x the bet and draw 10 numbers, one at a time, without replacement.
  They are three volatility levels of the same draw: the chance of every number of hits is the
  same in all three, only the pay table differs. Calm pays often and small, Wild seldom and
  large, Bold in between. Each plays every size (3, 4, 5, 6, 8, 10).
- Chain costs 10x the bet and Chain Max costs 100x the bet. Both play 10 picks and draw 12 numbers.
- A drawn number that the player picked is a hit.
- Lucky numbers: before the draw, numbers the player did not pick are marked. Calm, Bold, Wild and
  Chain mark 1 number. Chain Max marks 3. A marked number that is drawn is a lucky ball.
- Lucky round: in Calm, Bold, Wild and Chain, 1 round in 5 marks 3 lucky numbers instead of 1. Which
  rounds are lucky rounds is part of the round's outcome, like the draw. Chain Max marks 3 in
  every round and has no lucky rounds.

Win
- Win = pay for the number of hits (table of the chosen level and pick count) x multiplier.
- Meter level = best run of hits + number of lucky balls drawn.
  Level 1: x1, 2: x2, 3: x3, 4: x5, 5: x10, 6: x15, 7 or more: x25.
- Calm / Bold / Wild: a run is hits drawn one after another. A miss ends the run. A lucky ball does not.
- Chain / Chain Max: a hit raises the run by one, a miss lowers it by one (never below zero), a
  lucky ball leaves it. The highest run reached counts.
- A round with no hit pays nothing.
- The highest meter level of a round is its picks plus its lucky numbers, so with 3 to 5 picks the
  top multiplier needs a lucky round: 3 picks x15, 4 and 5 picks x25.
- The highest win of the game is 100,000x the bet (Chain Max). Wild reaches 50,000x (8 and 10
  picks), Bold 10,000x and Calm 2,500x (10 picks).

Pay tables (x bet, before the multiplier; index = number of hits, from 0)
- calm_3   0, 0.8, 1.5, 7.8
- calm_4   0, 0.3, 1.5, 2.5, 18
- calm_5   0, 0.3, 1, 1.2, 6, 30
- calm_6   0, 0, 0.8, 1.3, 2.5, 12, 50
- calm_8   0, 0, 0.2, 1, 1.3, 2, 10, 40, 60
- calm_10  0, 0, 0, 0.5, 0.6, 1.5, 5, 10, 20, 100, 100
- bold_3   0, 0, 2.8, 16.5
- bold_4   0, 0, 1, 5.5, 38
- bold_5   0, 0, 0.6, 2.2, 11, 80
- bold_6   0, 0, 0.5, 1.2, 4, 20, 160
- bold_8   0, 0, 0, 0.5, 1.5, 6.5, 20, 100, 300
- bold_10  0, 0, 0, 0, 1, 1.5, 6, 25, 120, 400, 400
- wild_3   0, 0, 1, 32.5
- wild_4   0, 0, 0.6, 2.5, 100
- wild_5   0, 0, 0.3, 2, 8.4, 250
- wild_6   0, 0, 0.2, 0.8, 6, 25, 500
- wild_8   0, 0, 0, 0.3, 1.2, 4.4, 40, 400, 2000
- wild_10  0, 0, 0, 0, 0.5, 1.2, 5, 50, 600, 2000, 2000
- chain_10  0, 0, 1.2, 2.5, 5, 5, 10, 20, 500, 2000, 2000
- chainmax_10  0, 0, 0, 20, 40, 40, 120, 300, 2500, 4000, 4000

Highest win per mode (x bet): calm_3 117, calm_4 450, calm_5 750, calm_6 1,250, calm_8 1,500,
calm_10 2,500, bold_3 247.5, bold_4 950, bold_5 2,000, bold_6 4,000, bold_8 7,500, bold_10 10,000,
wild_3 487.5, wild_4 2,500, wild_5 6,250, wild_6 12,500, wild_8 50,000, wild_10 50,000,
chain_10 50,000, chainmax_10 100,000. In every level the highest win and the volatility rise with
the numbers played, and at every size Calm is below Bold and Bold below Wild.

Modes: <level>_<picks>, 20 in total: calm, bold and wild each with 3, 4, 5, 6, 8 and 10 picks,
chain_10, chainmax_10. RTP 96.55% to 96.69% by mode.

Books
- Every possible round of a mode (an order of hits, misses and lucky balls, on a board that
  marks 1 or 3 lucky numbers) is published the same number of times, each copy with its own
  numbers, so a mode holds a little over 100,000 different rounds (Chain: 237,518, Chain Max:
  208,871). A book's weight is the number of real ordered draws that give its order, times the
  share of rounds that mark its number of lucky numbers (4 for 1 number, 1 for 3, in the levels
  with lucky rounds), divided by a common factor. So the lookup table is the exact keno
  distribution, with lucky rounds at exactly 1 in 5. No sampling and no optimizer.
- Event "draw": level, picks, draws, selected (the book's own selected numbers, ascending),
  kilau (the book's lucky numbers, ascending: 1 or 3), kilauRound (true when a level that marks
  1 number marks 3 in this round), numbers (the numbers drawn, in order), pattern
  (1 = hit, 2 = lucky ball, 0 = miss, in draw order), hits, streak (best run), kilauHits,
  multiplier, pay (hundredths of the bet).
- Live play: the player's numbers stand in for the book's. The i-th smallest number in
  "selected" is shown as the player's i-th smallest number, and the i-th smallest of the other
  numbers as the i-th smallest number the player did not choose. Lucky numbers are among the
  other numbers and move with them. This is a relabelling of the board: hits, lucky balls, order
  and win are unchanged, and the frontend draws nothing at random.
- Replay: the RGS gives the mode and the book only, so a replay shows the book's own
  "selected", "kilau" and "numbers". The draw order, hits, multiplier and win are those of the round.
- Event "finalWin": the round's win.
