# 0002. Drebin benign corpus

**Status:** OPEN — blocks `load_drebin`

## Context
Drebin ships 5,560 malware samples with family labels (Aug 2010 – Oct 2012).
It does **not** ship the ~123k benign apps used in the original paper. Every
reproduction picks its own benign set, which is why cross-paper comparison on
"Drebin" is largely meaningless.

This is the single most attackable choice in the study. If benign apps come
from Play Store and malware from a flagged corpus, manifest features may encode
market packaging conventions and ad-SDK boilerplate rather than intent —
exactly the provenance leakage we are accusing others of.

## Options
1. **AndroZoo, date- and market-matched to Drebin's window.** Controls the
   obvious confound. Requires API key.
2. Whatever benign set a prior reproduction used. Comparable to that paper,
   inherits its problems.
3. Contemporary Play Store crawl. Introduces a temporal confound that would
   invalidate the whole point.

## Decision
_(pending)_ — leaning option 1.

## To record when decided
Exact date range, market filter, VT detection threshold for "benign",
sample count, and the AndroZoo snapshot date. All of it goes in the paper.
