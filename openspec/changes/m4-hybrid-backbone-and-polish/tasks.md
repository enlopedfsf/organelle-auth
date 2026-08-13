## 1. Preflight and frozen inputs

- [ ] 1.1 Confirm the clean `origin/dev` baseline, explicit plant/animal samplesheets, specimen matching, and reference/policy/tool compatibility records.
- [ ] 1.2 Verify all public evaluation inputs and any future CycloneSEQ inputs are present, non-empty, paired, readable, and checksum-recorded before compute-heavy work.
- [ ] 1.3 Freeze deterministic seeds, read ordering, subset sizes, parameters, tool versions, container identifiers, and input manifests.

## 2. Long-read backbone

- [ ] 2.1 Build or consume the taxon-specific long-read structural candidate using only the admitted experimental route and record its status as `EXPERIMENTAL/CANDIDATE/NOT_APPLICABLE`.
- [ ] 2.2 Evaluate the Racon arm independently, record round count and edit ledger, and checksum-freeze the selected common backbone before short-read polishing.
- [ ] 2.3 Freeze B0 and R1 separately using the declared graph/path, core coverage, structural evidence, Racon ledger, SHA256, and validation/evidence-owner sign-off; do not allow silent backbone replacement.
- [ ] 2.4 Add attribute-based tests for contig structure, core coverage, repeat evidence, and non-decision status; do not assert unsupported circularity.

## 3. Parallel short-read evidence routes

- [ ] 3.1 Run exactly the six pre-registered arms per taxon: B0, R1, B0→Polypolish, B0→bcftools consensus, R1→Polypolish, and R1→bcftools consensus; do not add arms during execution.
- [ ] 3.2 Record library insert/pairing metadata, multi-mapping behavior, applicability findings, and all route parameters without introducing unvalidated production thresholds.
- [ ] 3.3 Emit per-base edit ledgers for both routes and preserve pre/post sequences, support counts, depth, allele evidence, ambiguity, and filtering reasons.

## 4. Region and structure validation

- [ ] 4.1 Validate plant unique/IR/repeat regions and animal unique/D-loop/AT-rich/homopolymer regions separately.
- [ ] 4.2 Audit each claimed junction with read IDs, alignment geometry, identity, two-sided anchors, and chimera/repeat risk under the project independent-support definition.
- [ ] 4.3 Where feasible, create deterministic held-out read sets; otherwise label residual metrics in-sample and prohibit qualification claims.
- [ ] 4.4 Compare all arms with the same core identity, read-back consistency, SNV, indel, homopolymer, unsupported-edit, residual-conflict, resource, and manual-review metrics; annotate every reference-comparison metric as proxy evidence.
- [ ] 4.5 Apply the pre-registered dominance rule; if no arm dominates on unsupported edits, evaluable homopolymers, and non-decreasing core identity, report `CONDITIONAL` with multiple routes and no post hoc winner.
- [ ] 4.6 For animal data, restrict route-ranking metrics to the double-assembler-consensus core; count unresolved AT-rich-repeat edits separately as `NOT_EVALUABLE`.

## 5. Governance and tests

- [ ] 5.1 Keep all outputs marked `EXPERIMENTAL`, outside `IDENTIFY`/`DECISION`, with CycloneSEQ transfer `PENDING_REAL_DATA`.
- [ ] 5.2 Assert PMAT2 is not invoked while Issue #10 is OPEN and prohibited tools are absent.
- [ ] 5.3 Add nf-test and schema/status tests covering valid inputs, missing/checksum-invalid inputs, route isolation, edit-ledger fields, and expected non-decision status.
- [ ] 5.4 Produce the complete audit bundle and validation report; run `openspec validate --all --strict` and CI.

## 6. Review gate

- [ ] 6.1 Stop after proposal review; implementation requires explicit user approval and a separate `/opsx:apply` action.
