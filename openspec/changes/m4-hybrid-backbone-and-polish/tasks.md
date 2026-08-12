## 1. Preflight and frozen inputs

- [ ] 1.1 Confirm the clean `origin/dev` baseline, explicit plant/animal samplesheets, specimen matching, and reference/policy/tool compatibility records.
- [ ] 1.2 Verify all public evaluation inputs and any future CycloneSEQ inputs are present, non-empty, paired, readable, and checksum-recorded before compute-heavy work.
- [ ] 1.3 Freeze deterministic seeds, read ordering, subset sizes, parameters, tool versions, container identifiers, and input manifests.

## 2. Long-read backbone

- [ ] 2.1 Build or consume the taxon-specific long-read structural candidate using only the admitted experimental route and record its status as `EXPERIMENTAL/CANDIDATE/NOT_APPLICABLE`.
- [ ] 2.2 Evaluate the Racon arm independently, record round count and edit ledger, and checksum-freeze the selected common backbone before short-read polishing.
- [ ] 2.3 Add attribute-based tests for contig structure, core coverage, repeat evidence, and non-decision status; do not assert unsupported circularity.

## 3. Parallel short-read evidence routes

- [ ] 3.1 Run Polypolish and explicit alignment→bcftools call→consensus from the identical frozen backbone and identical paired-read manifest.
- [ ] 3.2 Record library insert/pairing metadata, multi-mapping behavior, applicability findings, and all route parameters without introducing unvalidated production thresholds.
- [ ] 3.3 Emit per-base edit ledgers for both routes and preserve pre/post sequences, support counts, depth, allele evidence, ambiguity, and filtering reasons.

## 4. Region and structure validation

- [ ] 4.1 Validate plant unique/IR/repeat regions and animal unique/D-loop/AT-rich/homopolymer regions separately.
- [ ] 4.2 Audit each claimed junction with read IDs, alignment geometry, identity, two-sided anchors, and chimera/repeat risk under the project independent-support definition.
- [ ] 4.3 Where feasible, create deterministic held-out read sets; otherwise label residual metrics in-sample and prohibit qualification claims.
- [ ] 4.4 Compare routes using region-level evidence, unsupported-edit counts, residual conflicts, core identity, and resource/manual-review burden; do not choose a winner from global identity alone.

## 5. Governance and tests

- [ ] 5.1 Keep all outputs marked `EXPERIMENTAL`, outside `IDENTIFY`/`DECISION`, with CycloneSEQ transfer `PENDING_REAL_DATA`.
- [ ] 5.2 Assert PMAT2 is not invoked while Issue #10 is OPEN and prohibited tools are absent.
- [ ] 5.3 Add nf-test and schema/status tests covering valid inputs, missing/checksum-invalid inputs, route isolation, edit-ledger fields, and expected non-decision status.
- [ ] 5.4 Produce the complete audit bundle and validation report; run `openspec validate --all --strict` and CI.

## 6. Review gate

- [ ] 6.1 Stop after proposal review; implementation requires explicit user approval and a separate `/opsx:apply` action.
