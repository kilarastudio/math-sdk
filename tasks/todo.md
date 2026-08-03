# Keris Wild v2.2 RGS Todo

- [x] Copy and hash-check locked reel strips.
- [x] RED: config/reel/paytable tests.
- [x] GREEN: game config and reel loader.
- [x] RED: line/scatter/expansion/sticky math tests.
- [x] GREEN: Keris math helpers.
- [x] RED: base respin/free-spin/event/wincap lifecycle tests.
- [x] GREEN: game state, executables, overrides, and custom events.
- [x] Configure base, ante, and bonus-buy distributions.
- [x] Add optimizer and run entry points.
- [x] Run focused tests after each slice.
- [x] Run full pytest, compileall, cargo check, and smoke simulation.
- [x] Review final diff for correctness, simplicity, architecture, security, and performance.

- [x] Retune the paytable to RGS-compatible 0.10x increments.
- [x] Run the 10M/5M/4.3M lock simulation and update all three RTP targets.
- [x] Relock deterministic regression vectors and optimizer criteria contributions.
- [x] Fix cross-mode compressed payout sidecar leakage and pass the RGS format gate.
- [x] Replace uniform 100-book smoke publish LUTs with optimized 10k production LUTs.
- [x] Lock optimizer HRs to feature, non-feature hit, and FS nonzero probabilities.
- [x] Add regression coverage for the production-default publish pipeline.
- [x] Raise the final Stake Engine production library to 100k outcomes per mode.
- [x] Retarget ante RTP to 96.25% so every mode stays within 0.5pp of base.
