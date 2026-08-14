## 1. Protocol and state contracts

- [x] 1.1 Define the machine-readable lifecycle and allowed transitions from `PENDING_REAL_DATA` through owner review, with fail-closed invalid-transition tests.
- [x] 1.2 Define a versioned transfer protocol schema containing taxa/sample scope, route roles, metrics, denominator definitions, explicit threshold nulls, harm/gain gates, orthogonal evidence, versions, owners, and checksums.
- [x] 1.3 Encode the pre-written negative-outcome precedence and tests for every registered branch, including negative/control failure and a rule that no run self-approves GO or invents a new machine-status vocabulary.

## 2. Arrival gate

- [x] 2.1 Define a signed delivery-manifest schema for coded sample identity, specimen/DNA relationship, platform/library/basecalling/batch provenance, file size/checksum, and HMW/QC metadata.
- [x] 2.2 Implement deterministic non-empty, format/compression, checksum, paired synchronization, sample uniqueness, allow-listed path, and metadata validation before scientific channel creation.
- [x] 2.3 Emit immutable arrival status/reason records; require repaired deliveries to use a new manifest version and preserve earlier failure evidence.
- [x] 2.4 Add positive and failure fixtures covering truncation, empty files, checksum mismatch, swapped mates, duplicate IDs, identity mismatch, missing provenance, and absent real data.

## 3. Blind-sample governance

- [x] 3.1 Define coded analysis samplesheets that reject truth-bearing columns, filenames, paths, labels, and free-text fields.
- [x] 3.2 Define separate truth-custodian and result-freeze manifests with owner, timestamp, access record, truth/result SHA256, and authorized-unblinding event.
- [x] 3.3 Implement tests showing truth is unavailable before result freeze and any leakage or post-unblinding retuning produces `BLINDING_INVALIDATED`.

## 4. Engineering evidence framework

- [x] 4.1 Implement fixed short-read baseline, CycloneSEQ-only research, and hybrid evidence roles without enabling result-driven arm expansion.
- [x] 4.2 Emit separate platform/error-spectrum, sequence-callability, structural-junction, blind-decision, resource/failure, and manual-review records with explicit denominators.
- [x] 4.3 Add synthetic/public smoke fixtures proving schemas, routing, evidence isolation, negative branches, and `PENDING_REAL_DATA` without claiming scientific validation.
- [x] 4.4 Assert CycloneSEQ-only outputs never enter `IDENTIFY`/`DECISION`, PMAT2 remains gated by Issue #10, and mitoVGP remains outside scope.

## 5. Real-data execution gate and closeout

- [x] 5.1 Before real-data execution, require owner approval of all required numeric thresholds/scope values and freeze the full protocol before outcome access; null gates fail fast.
- [ ] 5.2 Execute only after the arrival, protocol, and blinding gates pass; freeze every sample result and deviation before authorized unblinding.
- [x] 5.3 Emit exactly one pre-written transfer outcome with reproducible numerators/denominators and preserve `INCONCLUSIVE`/negative branches honestly.
- [ ] 5.4 Run focused tests, nf-test property assertions, OpenSpec strict validation, manifest checks, and CI; complete PR/acceptance/merge/archive without deleting historical worktrees or `runs/` data.
