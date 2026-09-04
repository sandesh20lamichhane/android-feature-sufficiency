# 0005. Attacker cost model

**Status:** accepted (provisional, revisit after pilot)

## Context
The paper's central claim rests entirely on the cost model, so it is explicit
and configurable rather than buried in code. See `src/afs/attack/feasibility.py`.

## Decision
Per-feature add and remove costs, with direction mattering as much as magnitude:

| Feature type | Add | Remove | Rationale |
|---|---|---|---|
| `perm::` | 1.0 | 4.0 | Free to add; removing a needed permission breaks function |
| manifest (intent/component) | 1.5 | 6.0 | Renameable, near-free to add |
| `api::`, `opcode::`, `url::` | 8.0 | ∞ | Removing a live call removes the behaviour the malware exists for |
| `syscall::`, `binder::` | 20.0 | ∞ | Requires re-engineering the payload or sandbox evasion |

Removal of code/dynamic features is treated as **infeasible**, not merely
expensive. This is the conservative direction: it can only make evasion look
*harder*, so it cannot manufacture the result we are hoping to find.

## Consequences
Absolute costs are ordinal, not physical — they support "P is cheaper to evade
than S", not "evasion costs $X". The paper must say so. A sensitivity analysis
over `remove_penalty` and the cost ratios is required, since a reviewer will
reasonably ask whether the conclusion is an artifact of these numbers.
