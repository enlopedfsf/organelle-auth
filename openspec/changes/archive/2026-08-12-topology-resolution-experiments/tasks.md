## 1. Frozen evidence and manifest

- [x] 1.1 Locate the archived M3 recruited subset across canonical and historical work roots and verify the recorded SHA-256 `93f4fd3c...531f3c8`.
- [x] 1.2 Create a versioned experiment manifest with at most six declared coverage/overlap combinations, retaining `(50,5000)` as control and recording all commands, versions, seed, and paths.
- [x] 1.3 Add fail-fast checks proving the input is non-empty and identical before any Flye process starts.

## 2. Flye parameter experiments

- [x] 2.1 Attempt the reduced two-point manifest in independent stable output directories under the fixed `runs/work` and `runs/output` roots; accept final `GRID_BLOCKED_RUNTIME_TERMINATION` after both attempts are killed during minimizer construction.
- [x] 2.2 Record the blocked combinations, Flye version, four-thread retry, termination logs, and resource-scaling estimate; defer the full grid to M4.
- [x] 2.3 Add regression tests proving parameter isolation, control reproducibility, and no writes to archived M3 files or decision channels.

## 3. MAPQ-0 junction recount

- [x] 3.1 Locate the archived read-to-contig alignments and existing high-quality junction count, recording their paths and checksums.
- [x] 3.2 Implement MAPQ-inclusive junction extraction with primary/secondary/supplementary retention and read-identity deduplication.
- [x] 3.3 Implement documented IR-copy-aware weighting and emit raw, high-quality-only, MAPQ-inclusive, and weighted comparison tables.
- [x] 3.4 Add tests for MAPQ-0 multi-copy reads, duplicate alignment inflation, supplementary alignments, and absent support.

## 4. Validation and closure

- [x] 4.1 Write `VALIDATION-topology-experiments.md` with A/B tables, explicit answers to both scientific questions, commands, versions, checksums, and ONT/experimental labels.
- [x] 4.2 Compare every topology claim against the `6.5 independent_alignment_support` definition; keep the formal state `INCONCLUSIVE` unless a separate change is proposed.
- [x] 4.3 Run strict OpenSpec validation and the existing plant-route regression evidence; verify archived files and IDENTIFY/DECISION outputs are unchanged.
