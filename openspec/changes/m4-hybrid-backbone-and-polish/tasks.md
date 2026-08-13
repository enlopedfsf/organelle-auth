## 1. Preflight and frozen inputs

- [ ] 1.1 Confirm the clean `origin/dev` baseline, explicit plant/animal samplesheets, specimen matching, and reference/policy/tool compatibility records.
- [x] 1.2 Public evaluation inputs are non-empty, paired, gzip-validated, and checksum-recorded; CycloneSEQ remains pending real data.
- [x] 1.3 Exact paired-read split rule implemented and frozen for both taxa with pair counts, rule text, and SHA256 values.
- [x] 1.4 Deterministic ordering, parameters, runtime identifiers, manifests, and pair preservation were verified before arm execution.

## 2. Long-read backbone

- [ ] 2.1 Build or consume the taxon-specific long-read structural candidate using only admitted experimental tools; record tool/evidence tier `EXPERIMENTAL` separately from `status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE`.
- [x] 2.2 R1 completed as exactly two Racon rounds using the registered compatible Racon 1.4.20 runtime and fixed parameters.
- [x] 2.3 B0 and R1 paths, commands, runtime identifiers, and SHA256 values are frozen in the manifest; no silent backbone replacement is permitted.
- [ ] 2.4 Add attribute-based tests for contig structure, core coverage, repeat evidence, and non-decision status; do not assert unsupported circularity.

## 3. Parallel short-read evidence routes

- [ ] 3.1 Run exactly the six pre-registered arms per taxon: B0, R1, B0→Polypolish, B0→bcftools consensus, R1→Polypolish, and R1→bcftools consensus; do not add arms during execution.
- [ ] 3.2 Use only the frozen 80% training split for P/C polishing and mask callability; record insert/pairing metadata, multi-mapping behavior, applicability findings, and all fixed route parameters without using held-out results to tune them.
- [ ] 3.3 Emit per-base edit ledgers for both routes and preserve pre/post sequences, support counts, depth, allele evidence, ambiguity, and filtering reasons.

## 4. Region and structure validation

- [ ] 4.1 Validate plant unique/IR/repeat regions and animal unique/D-loop/AT-rich/homopolymer regions separately.
- [ ] 4.2 Audit each claimed junction with read IDs, alignment geometry, identity, two-sided anchors, and chimera/repeat risk under the project independent-support definition.
- [ ] 4.3 Align the frozen 20% held-out reads independently to every final candidate with the same registered alignment/callability policy; verify the held-out set never contributed to polishing, mask construction, or parameter selection.
- [ ] 4.4 For every arm, calculate `residual_unsupported_loci` uniformly within the frozen evaluable core and report `introduced_edits` separately as step-local and cumulative provenance; also report held-out core concordance, evaluable homopolymer discordances, SNVs, indels, regional residuals, resources, and manual review.
- [ ] 4.5 Apply the pre-registered dominance combination: strictly fewer residual unsupported loci, strictly fewer held-out-supported evaluable homopolymer discordances, and no held-out core-concordance regression relative to B0. If none dominates, report scientific outcome `CONDITIONAL` and machine status `INCONCLUSIVE` with no post hoc winner.
- [x] 4.6 Animal Flye/Raven single-copy core BED was intersected with training-read callability, merged, and frozen as `contig_1:0-3004` with owner and SHA256 in the freeze manifest.
- [ ] 4.7 Restrict animal ranking to that frozen core; retain unresolved AT-rich/D-loop edits in the ledger as `NOT_EVALUABLE`, outside all ranking metrics.

## 5. Governance and tests

- [ ] 5.1 Keep `EXPERIMENTAL` only as evidence/tool tier; assert every candidate has `status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE`, remains outside `IDENTIFY`/`DECISION`, and keeps CycloneSEQ transfer `PENDING_REAL_DATA`.
- [ ] 5.2 Assert PMAT2 is not invoked while Issue #10 is OPEN and prohibited tools are absent.
- [ ] 5.3 Add nf-test and schema/status tests covering valid inputs, missing/checksum-invalid inputs, route isolation, edit-ledger fields, and expected non-decision status.
- [ ] 5.4 Produce the complete audit bundle and validation report; run `openspec validate --all --strict` and CI.

## 6. Review gate

- [x] 6.1 Proposal review completed; explicit user approval for `/opsx:apply` received on 2026-08-13. Execution remains gated by the three-artifact freeze checklist in 1.3, 2.3, and 4.6.
