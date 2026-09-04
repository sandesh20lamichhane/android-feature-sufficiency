# 0001. Record methodological decisions

**Status:** accepted

## Context
This project's contribution is that standard evaluations of Android malware
detectors are methodologically weak. That makes our own methodology the primary
attack surface in review.

## Decision
Every methodological choice gets a numbered file here before it is implemented:
what was chosen, what alternatives were rejected, and why. A choice not recorded
here is treated as not yet made, and the corresponding loader stays stubbed.

## Consequences
Slower to start. Much faster to defend, and the decisions section of the paper
writes itself from these files.
