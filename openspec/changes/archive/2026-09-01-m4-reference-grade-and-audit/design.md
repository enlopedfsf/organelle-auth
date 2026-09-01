## Context

M4-① already froze and evaluated the six-arm evidence. This change packages and audits that evidence; it does not rerun polishing or reinterpret topology.

## Goals / Non-Goals

**Goals:** produce reproducible plant and animal candidate packages, preserve R1P1 and animal CONDITIONAL outcomes, and make release blockers explicit.

**Non-Goals:** new arms, threshold tuning, topology revision, REFERENCE promotion, authentication, or CycloneSEQ Go/No-Go.

## Decisions

1. Freeze M4-① manifests and source checksums before packaging; missing or mismatched evidence blocks the package.
2. Use R1P1 as plant primary only under the prior common-callability result; retain animal `CONDITIONAL` when the dominance rule is not met.
3. Emit one status contract for every package: `INCONCLUSIVE / CANDIDATE / NOT_APPLICABLE`.
4. Keep topology fields and unresolved repeat ledgers separate from route ranking; both plant and animal topology remain `INCONCLUSIVE`.
5. Generate a release-blocker ledger rather than silently promoting a candidate.

## Assembly-grade promotion decision table

The table is an audit contract, not a claim that the current M4-② candidates meet any higher grade. A package MUST remain at the highest level whose complete evidence row is satisfied; missing evidence is a hard stop.

| Grade transition | Required evidence conditions | Current M4-② disposition |
|---|---|---|
| `DRAFT → CANDIDATE` | Source assembly and route manifest are checksum-frozen; provenance/tool/container identities are recorded; candidate sequence is non-empty and reproducible; core-region read-backed audit is complete; unresolved loci, repeat edits, and topology exclusions are explicitly ledgered; machine status is `INCONCLUSIVE` and decision is `NOT_APPLICABLE`. | Eligible as a package ceiling; plant R1P1 and animal `CONDITIONAL` may be packaged only when these records exist. |
| `CANDIDATE → REFERENCE` | All Candidate conditions plus independently reproducible production-grade evidence; no unresolved release blocker; calibrated production policy is present; required callable/core regions meet the approved release contract; topology and adjacency claims pass their independent evidence gate; real CycloneSEQ transfer/Go-No-Go requirements are satisfied where applicable; Owner release approval is recorded. | **Not eligible.** M4-② explicitly forbids `REFERENCE` promotion. |
| `REFERENCE` maintenance | Versioned compatibility manifest, immutable source/evidence checksums, production policy IDs, regression evidence, and release approval remain valid for the exact released artifact. | Out of scope for this change. |

## Release-blocker checklist

Any one of the following MUST keep the package at `assembly_grade=CANDIDATE`, `status=INCONCLUSIVE`, and `decision=NOT_APPLICABLE`; the blocker MUST be named in the machine-readable audit ledger:

- Plant or animal topology remains `INCONCLUSIVE`, including circularity, IR adjacency/copy number, animal AT-rich repeat adjacency/copy number, or unresolved junction claims.
- CycloneSEQ transfer data are absent or not independently validated; `CycloneSEQ=PENDING_REAL_DATA`.
- Production policy thresholds are `null`/`THRESHOLD_NOT_CONFIGURED` or otherwise uncalibrated.
- Source, candidate, held-out, core-mask, or evidence checksums are missing, stale, or inconsistent.
- Required read-backed evidence, callable-region definition, unique-core rule, or unresolved-locus ledger is missing or not reproducible.
- Tool/container identity, version, license/admission state, or route provenance is incomplete.
- Animal route dominance is not established under the pre-registered rule; retain `CONDITIONAL` rather than selecting post hoc.
- Any evidence would enter `IDENTIFY`/`DECISION`, or any PMAT2/CycloneSEQ gate is bypassed.

## Risks / Trade-offs

- [Proxy reference disagreement] → retain read-level evidence and label reference metrics as proxies.
- [Animal unresolved repeat] → exclude it from grade promotion and preserve the CONDITIONAL route set.
- [Stale source path] → fail checksum/provenance validation before packaging.

## Migration Plan

Apply creates only candidate audit artifacts and tests. A future release change would be required for any REFERENCE-grade promotion.
