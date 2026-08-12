## 1. Evidence ledger

- [x] 1.1 Freeze and checksum the MAPQ-inclusive PAF, candidate assembly, reference, and prior 2-read record.
- [x] 1.2 Extract every candidate read and test both junction flanks plus unique-anchor status.
- [x] 1.3 Classify each read by support condition, alignment class, MAPQ, and IR-copy ambiguity.

## 2. Conclusion review

- [x] 2.1 Generate the per-read ledger and aggregate comparison table.
- [x] 2.2 Apply every `6.5 independent_alignment_support` condition and produce a recommendation report.
- [x] 2.3 Keep archived M3 prose unchanged and block IDENTIFY/DECISION_ENGINE integration.

## 3. Verification

- [x] 3.1 Add tests for duplicate read IDs, non-unique anchors, MAPQ-0 reads, and qualifying unique anchors.
- [x] 3.2 Run strict OpenSpec validation and focused evidence tests; broader plant regression evidence remains from the prior green run.
