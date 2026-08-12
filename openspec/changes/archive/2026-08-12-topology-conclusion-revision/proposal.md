## Why

The archived M3 plant pilot correctly retained topology as `INCONCLUSIVE`, while the follow-up MAPQ-inclusive recount found 587 read-identity junction candidates (293.5 under two-copy weighting) versus 2 MAPQ>=20 reads. A separate governed review is needed to determine whether any candidates satisfy the full `6.5 independent_alignment_support` definition, especially unique flanking anchors, before revising the conclusion.

## What Changes

- Audit every candidate junction read against both junction flanks, unique-anchor criteria, alignment class, MAPQ, and copy identity.
- Produce an evidence ledger separating qualifying independent reads from copy-ambiguous or non-qualifying candidates.
- Decide whether topology remains `INCONCLUSIVE` or can be revised to an explicitly qualified state; do not infer circularity from counts alone.
- Record any revised label (for example `DE_NOVO`) only with direct evidence and preserve ONT/experimental provenance.

Out of scope: rerunning Flye, changing the archived M3 report in place, production decision thresholds, animal long-read work, or CycloneSEQ validation.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `plant-long-read-analysis`: add governed conclusion-revision evidence review requirements.

## Impact

Adds an evidence ledger, review report, tests, and an auditable conclusion delta. No decision path changes occur unless the explicit support contract is satisfied.
