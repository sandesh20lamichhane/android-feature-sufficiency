# Lab notebook

Append-only. Newest at the bottom. One entry per working session: what you ran,
what run_id it produced, what you concluded, what you changed as a result.

Reconstructing your reasoning from memory six months out does not work, and for
a paper whose contribution is that other people's evaluations were sloppy, being
unable to justify a choice is fatal.

---

## 2026-__-__ — Session 1: scaffold

Set up repo, checkpointing, synthetic pipeline. Verified end to end:
19 tests pass, smoke experiment completes, crash-resume recovers correctly.

Synthetic sanity check reproduced the target phenomenon by construction:
P and S arms both hit AUC 1.0 while median evasion cost differed (40 vs 60).
This confirms the *instrument* works. It proves nothing about real data.

Next: AndroZoo API key request (blocking, start immediately), then data audit.

---
