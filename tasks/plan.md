# Implementation Plan: Keris Wild v2.2 RGS MathLock

## Overview

Implement the Keris Wild 5x4, 40-line model as a new `games/keris_wild` game.
Mechanics follow `Keris_Wilds_v2.1_MathLock.docx`; v2.2 retunes only the paytable
to the RGS 0.10x payout contract and relocks RTP/regression outputs. The reference
simulator and locked reel CSV take precedence where the prose is stale or internally
inconsistent.

## Architecture Decisions

- Keep all Keris-specific calculations and events inside `games/keris_wild`; do
  not change shared SDK calculators or event contracts.
- Load the exact long-form locked reel CSV and verify both its file SHA-256 and the
  three semantic strip hashes at config construction time.
- Use a game-owned PCG64 generator for stop/boost consumption so the five-stop,
  then boost-roll/choice order matches the v2.1 RNG contract. Held reels still
  consume a stop and are overridden afterward, matching the simulator.
- Evaluate lines with a game-owned calculator because sticky reel multipliers are
  products limited to the paid winning span and capped at 20x; the shared SDK
  multiplier strategy adds symbol multipliers and cannot represent this rule.
- Apply the 10,000x cap to remaining round value before wallet/event updates, then
  stop respins/free spins. This keeps book, wallet, and event amounts consistent.
- Criteria are exclusive: `wincap`, then zero-pay `0`, then `freegame`, then
  `basegame`. The zero-pay exception is required by the locked bonus-buy quotas.

## Task List

### Phase 1: Contract tests and locked assets

- [ ] Add the locked reel CSV under the game and verify published hashes.
- [ ] Add failing tests for paytable/lines, scatter 6+, expansion, winning-span
      multipliers, sticky increments, and reel loading.

### Checkpoint: Math foundation

- [ ] Focused tests fail for the missing Keris implementation, then pass after the
      minimal calculator/config slice is added.
- [ ] Existing 13 SDK tests remain green.

### Phase 2: Round lifecycle and events

- [ ] Implement base reveal, expansion, one respin, scatter ordering, and FS entry.
- [ ] Implement additive first-spin boost, per-reel sticky state, multiplier growth,
      retriggers, and global wincap.
- [ ] Add custom events and lifecycle tests with contiguous indexes and hundredths
      monetary units.

### Checkpoint: Mechanics

- [ ] Deterministic forced-stop tests match reference behavior.
- [ ] State does not leak between rounds; retrigger and wincap stop conditions pass.

### Phase 3: Modes and pipeline

- [ ] Configure base, ante, and 72x bonus-buy modes with exclusive distributions.
- [ ] Add optimizer setup and a production-default pipeline that always publishes optimized LUTs.
- [ ] Generate a small uncompressed sample and inspect book/LUT invariants.

### Checkpoint: Complete

- [ ] Full pytest suite, compileall, and Rust optimizer check pass.
- [ ] Small simulation produces all requested books without rejection-loop stalls.
- [ ] Five-axis diff review has no unresolved correctness or architecture findings.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Rare natural wincap makes smoke runs impractical | High | Use a reproducible, reachable forced-stop trajectory only for the oversampled wincap criterion. |
| Shared line multiplier semantics differ | High | Keep a tested Keris calculator local to the game. |
| Prose and simulator disagree | High | Record precedence decisions above and test simulator behavior. |
| Forced quotas distort raw observed RTP | Medium | Treat raw books as conditional samples; optimizer weights define published RTP and never ship uniform smoke weights. |
| Custom event order is frontend-sensitive | Medium | Assert exact order, indexes, positions, and integer amounts in tests. |

## Open Questions

- Production provider metadata and final marketing title are not supplied. The
  implementation uses provider number `0`, provider name `kilara`, and working title
  `Keris Wilds: Pusaka Sang Raja` as explicit placeholders.
