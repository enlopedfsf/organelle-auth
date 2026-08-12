## 1. A: Frozen subsample audit

- [x] 1.1 Record gzip integrity, seqkit stats, source/output sizes, read/base counts, N50, and the existing seed/fraction manifest for the user-verified subsample.
- [x] 1.2 Reconcile the sampling command and provenance; record any unavailable shell history as unverifiable rather than infer it.

## 2. B: Recruitment purity audit

- [x] 2.1 Add PAF/read-level parser reporting alignment length, query length, identity, MAPQ, target rotation, and read-identity deduplication.
- [x] 2.2 Add descriptive low-complexity/entropy statistics without introducing pass/fail thresholds.
- [x] 2.3 Align recruited reads to the frozen M2-① anchor and report read-ID intersection, breadth, identity, and competing evidence classes.
- [x] 2.4 Emit `VALIDATION-animal-lr.md` appendix plus JSON/TSV manifests with commands, versions, checksums, and the 824/5,816/5,215 and 41 kb versus 14.5 kb findings.
- [x] 2.5 Add unit tests for MAPQ-0 retention, duplicate read deduplication, complexity summaries, and missing/corrupt inputs.

## 3. Review gate before repair

- [x] 3.1 Run strict validation and focused tests; stop for user review of A/B evidence.
- [x] 3.2 Defer animal-specific parameter selection, re-recruitment, and Flye rerun to a separately approved C/D stage; keep PMAT2 blocked by Issue #10.

## 4. Approved C/D and Flye sensitivity closeout

- [x] 4.1 Apply the reviewed coherent animal recruitment policy and record the repaired Flye runs, runtime failure attribution, length-filter negative control, and run/read-order sensitivity evidence.
- [x] 4.2 Add Flye complete-runtime preflight, deterministic variance reduction, property-based test governance, and the project topology evidence gate.

## 5. Raven independent comparator

- [x] 5.1 Verify Raven version/runtime, record it in `registries/tools.yaml` as `EXPERIMENTAL` comparator-only, and verify both non-empty inputs and the M2-① anchor before execution.
- [x] 5.2 Run Raven once on the original coherent read order and once on one fixed-seed shuffled order; report contig properties, circularity, anchor identity/breadth, and Flye core agreement.

## 6. HYP-DNA-002 direct read audit

- [x] 6.1 Audit all 13 excluded reads of at least 30 kb using self-alignment/dotplot, per-copy anchor alignments, anchor coverage, and flank evidence.
- [x] 6.2 Emit a per-read evidence table and classify each read plus the hypothesis strength as `CONFIRMED`, `SUGGESTIVE`, or `REJECTED` without changing topology.

## 7. Closeout and verification

- [x] 7.1 Promote the five-link failure attribution and final animal ONT status into the main body of `VALIDATION-animal-lr.md`.
- [x] 7.2 Run focused tests and `openspec validate --strict`; record the infrastructure-blocked nf-test status separately from scientific/test failures and assess archive readiness.
