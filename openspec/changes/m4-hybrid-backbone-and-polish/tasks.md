## 1. Preflight and frozen inputs

- [ ] 1.1 Confirm the clean `origin/dev` baseline, explicit plant/animal samplesheets, specimen matching, and reference/policy/tool compatibility records.
- [ ] 1.2 Verify all public evaluation inputs and any future CycloneSEQ inputs are present, non-empty, paired, readable, and checksum-recorded before compute-heavy work.
- [ ] 1.3 Implement and register the exact paired-read split rule: canonical pair ID, SHA256 salt `m4-hybrid-v1`, residues 0-1 held-out and 2-9 training; freeze both split products, counts, rule text, and SHA256 values with the backbone.
- [ ] 1.4 Freeze deterministic ordering, parameters, tool versions, container identifiers, and input manifests; reject mate leakage or overlap between training and held-out sets.

## 2. Long-read backbone

- [ ] 2.1 Build or consume the taxon-specific long-read structural candidate using only admitted experimental tools; record tool/evidence tier `EXPERIMENTAL` separately from `status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE`.
- [ ] 2.2 Run R1 as exactly two Racon rounds. In each round map the same frozen recruited long-read set to the current candidate using minimap2 `-x map-ont`, then run `racon -w 500 -q 10.0 -e 0.3 -m 3 -x -5 -g -4 -t 4` with no `-u`, `--no-trimming`, or CUDA flags; remap for round two and stop without result-driven additions.
- [ ] 2.3 Freeze B0 and R1 separately using the declared graph/path, core coverage, structural evidence, two-round Racon ledger, recruited-long-read manifest, SHA256, and validation/evidence-owner sign-off; do not allow silent backbone replacement.
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
- [ ] 4.6 Before all twelve evaluations, generate the animal Flye/Raven-consensus core BED in the B0/Flye coordinate frame using the registered collinearity, single-copy, training-read callability, uniqueness, repeat, graph-edge, and junction rules; record exact coordinates, liftover rule, owner, manifest, and BED SHA256.
- [ ] 4.7 Restrict animal ranking to that frozen core; retain unresolved AT-rich/D-loop edits in the ledger as `NOT_EVALUABLE`, outside all ranking metrics.

## 5. Governance and tests

- [ ] 5.1 Keep `EXPERIMENTAL` only as evidence/tool tier; assert every candidate has `status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE`, remains outside `IDENTIFY`/`DECISION`, and keeps CycloneSEQ transfer `PENDING_REAL_DATA`.
- [ ] 5.2 Assert PMAT2 is not invoked while Issue #10 is OPEN and prohibited tools are absent.
- [ ] 5.3 Add nf-test and schema/status tests covering valid inputs, missing/checksum-invalid inputs, route isolation, edit-ledger fields, and expected non-decision status.
- [ ] 5.4 Produce the complete audit bundle and validation report; run `openspec validate --all --strict` and CI.

## 6. Review gate

- [ ] 6.1 Stop after proposal review; implementation requires explicit user approval and a separate `/opsx:apply` action.
