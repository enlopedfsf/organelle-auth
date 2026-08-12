## Why

The archived plant long-read pilot left one bounded scientific question unresolved: Flye produced two contigs (200,144 bp) with asymmetric junction support, so whole-plastome topology remains `INCONCLUSIVE`. A small, isolated parameter and MAPQ-0 re-count experiment can test whether the result is sensitive to the processing cap or to multi-mapping evidence without reopening the archived route.

## What Changes

- Freeze and checksum the exact 122,132,426-bp recruited subset used by the formal M3 run.
- Run a Flye parameter grid with `--asm-coverage` values 50, 150, 200, and unlimited, crossed with `--min-overlap` 3000, 5000, and 8000, bounded to at most six documented combinations.
- Record each combination's contigs, GFA, junction support, circularity state, command, versions, seed/policy, runtime, and output checksums.
- Recompute junction support including MAPQ-0 alignments with copy-aware IR weighting and compare it with the existing high-quality-only count.
- Write all observations to a standalone `VALIDATION-topology-experiments.md` appendix and preserve `INCONCLUSIVE` unless a separately governed change revises it.

Out of scope: changing the archived `plant-long-read-pmat2-pilot` or `correct-plant-long-read-reference-first` artifacts, changing `VALIDATION-plant-lr.md`, modifying production policies or decision paths, running PMAT2, or starting the animal pilot.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `plant-long-read-analysis`: Add experimental governance requirements for frozen-input topology sensitivity experiments and copy-aware junction recounts.

## Impact

- Adds an experimental-only analysis script/workflow, parameter manifest, result tables, and validation appendix under the current repository.
- Reads the archived M3 subset and existing alignments as immutable evidence; does not publish outputs to IDENTIFY or DECISION_ENGINE.
- All outputs remain ONT-labelled, `decision=NOT_APPLICABLE`, and non-production.
