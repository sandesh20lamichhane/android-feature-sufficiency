# 0004. AndroZoo for the temporal axis

**Status:** OPEN — **start the access request now**

## Context
Neither Drebin (2010–2012) nor CICMalDroid (2017–2018) spans enough time for a
train-past/test-future protocol on its own. AndroZoo supplies `dex_date` for
real temporal ordering and a benign corpus with known provenance.

Access needs an academic email and takes days to weeks. It blocks two things,
so it is the first task regardless of which axis ends up leading the paper.

## Open questions
- Gap length between train_end and test_start. A gap prevents near-duplicate
  repackagings straddling the boundary from leaking the test set into training.
  Needs a near-duplicate analysis to set defensibly.
- `dex_date` is unreliable for some samples (forged or missing compile
  timestamps). Need a fallback and a documented exclusion rule.

## Decision
_(pending)_
