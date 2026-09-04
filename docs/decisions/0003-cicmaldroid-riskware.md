# 0003. CICMalDroid: riskware and sandbox attrition

**Status:** OPEN — blocks `load_cicmaldroid`

## Context
Two issues, both of which bias toward the permissions-only arm winning:

1. **Riskware** is a labelled class in CICMalDroid. Riskware is definitionally
   over-permissioned software. Including it structurally advantages arm P and
   would let us "confirm" the premise for the wrong reason.
2. **Sandbox attrition.** Not all samples executed successfully under
   CopperDroid, so the dynamic-feature subset is smaller and non-randomly so —
   samples that detect or crash the sandbox are plausibly the more sophisticated
   ones, which is precisely the population where deep features should matter.

## Decision
_(pending)_ — plan is to report every result twice, with and without riskware,
and to characterise the attrition (what fraction failed, and whether failure
correlates with class) rather than silently dropping it.

## To record when decided
Attrition rate by class, and whether the P-vs-D gap differs between the
executed and non-executed subsets.
