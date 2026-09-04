# VALIDATION — CycloneSEQ transfer engineering skeleton

## Scope and current state

This apply stage implements governance and engineering-test contracts only. No real CycloneSEQ file was supplied, opened, or analyzed. It does not calibrate a threshold, qualify the platform, alter a production route, or issue Go/No-Go.

| Field | Current value |
|---|---|
| Apply scope | engineering skeleton only |
| Real CycloneSEQ data | absent |
| Transfer outcome | `PENDING_REAL_DATA` |
| Status | `INCONCLUSIVE` |
| Decision | `NOT_APPLICABLE` |
| Production thresholds | all `null` |
| PMAT2 | `GATED_ISSUE_10` |
| mitoVGP | `OUT_OF_SCOPE_UNADMITTED` |
| Historical worktrees / `runs/` | untouched |

## Approved condition closeout

1. `PENDING_REAL_DATA` is registered as the pre-entry state followed by exactly six active validation stages.
2. Temporary numeric values exist only in `assets/policies/cycloneseq-transfer-validation/engineering-test-v0.1.json`, whose header labels them uncalibrated and engineering-only. `production-null-v0.1.json` retains every numeric threshold as `null`; real-data protocol validation fails closed with `THRESHOLD_NOT_CONFIGURED`.

## Implemented skeleton

- machine-readable lifecycle and allowed transition registry;
- all nine pre-written transfer outcomes and fixed status/decision vocabularies;
- signed arrival-manifest schema plus deterministic file, FASTQ/gzip, checksum, pairing, uniqueness, provenance, HMW-QC, matched-platform, allow-list, and repair-version checks;
- transfer-protocol schema with explicit plant/animal scope, route roles, metrics, denominators, versions, owners, policies, and hashes;
- coded blind-samplesheet checks, separate truth custody, result-freeze hashing, and authorized-unblinding records;
- separated platform, sequence, structure, blind-decision, operations, and denominator evidence fields;
- CycloneSEQ-only output isolation from `IDENTIFY`/`DECISION`, with PMAT2 and mitoVGP governance assertions;
- synthetic engineering fixtures covering every outcome and arrival failure class.

## Current-state artifact

The current-state command is:

```text
python3 scripts/cycloneseq_transfer_guard.py evaluate \
  --policy assets/policies/cycloneseq-transfer-validation/production-null-v0.1.json \
  --metrics openspec/changes/cycloneseq-transfer-validation/evidence/no-real-data-metrics.json \
  --route-role CYCLONESEQ_ONLY_RESEARCH \
  --output openspec/changes/cycloneseq-transfer-validation/evidence/current-transfer-status.json
```

It must emit exactly `status=INCONCLUSIVE`, `transfer_outcome=PENDING_REAL_DATA`, and `decision=NOT_APPLICABLE`. The absence of real data takes precedence over threshold evaluation; it is not a scientific negative result.

## Verification

- focused Python engineering contracts: `25 passed`;
- Nextflow native lint for the local evidence gate: PASS;
- OpenSpec strict validation: `11 passed, 0 failed`;
- schema/traceability contract check: PASS;
- manifest verification: 16/16 PASS;
- full Python regression: `86 passed, 2 failed`; both failures reproduce unchanged in a clean pre-change ancestor worktree at `539f1f4` (an ancestor of `origin/dev`) and are outside this change: one requires an intentionally uncommitted historical `runs/output/animal-long-read-pilot/preflight.json`, and one references an absent historical `scripts/check_flye_runtime.py` artifact. No unrelated repair is included here;
- nf-core pipeline lint completed locally without a reported finding;
- local nf-test body: `INFRASTRUCTURE_BLOCKED` before test execution because the nf-test plugin index at GitHub could not be downloaded, with and without the configured proxy; authoritative PR CI remains required;
- OpenSpec strict validation, broader regression, manifest/diff checks, PR CI, acceptance, merge, and archive: pending apply closeout.

## Pending real-data work

No transition beyond the pre-entry state is claimed. Real-data execution requires an arrival-valid signed package and a separate owner-approved protocol revision with calibrated production thresholds before outcome access. Until then, task 5.2 and formal closeout remain open.
