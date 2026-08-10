## Why

M2-① now produces a frozen animal `assembly_qc` contract, but the pipeline still lacks the animal reference-first identification half: a versioned decision reference pack, animal policy, nuclear-marker evidence slot, and an honest multi-evidence decision output. M2-② consumes M2-① read-only and adds the identify-stage decision without silently promoting assembly evidence to authentication. The implementation is symmetric with M1-②'s plant identify gating, while preserving the animal-specific evidence and reference caveats recorded in M2-①.

## What Changes

- Add an animal reference pack v0.1 using `CM084263` as the decision reference. Its metadata MUST disclose circularity: the reference and validation data derive from the same BioProject, so the consistency result demonstrates workflow reproducibility rather than independent biological validation.
- Register `NC_023928` as `QUARANTINED`, with the observed 87.6% divergence, the M2-① stop-and-report record, and the Ye et al. (2015) misidentification evidence; it MUST NOT participate in decision calls. Place diagnostic windows away from the D-loop high-variation region and the M2-① observed assembly gap.
- Add an animal policy pack v0.1 with versioned, independently reconciled policy identifiers. Engineering-test placeholder thresholds are explicitly headed and traceable to the same-data high-consistency expectation; production remains all-null and emits `INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED` (ENG-POL-001/002).
- Add the `SCI-007` nuclear-marker input/status interface with an empty panel placeholder; no animal marker may be invented or implemented in this change.
- Reuse the frozen M2-① `assembly_qc` paths/status as read-only inputs and emit an `identify` status with a populated `decision`.
- Reuse the evidence-combination decision engine; no single distance, assembly grade, or CycloneSEQ result may force `AUTHENTIC`/`NON_AUTHENTIC`.
- Handle missing reference, insufficient coverage, conflicting evidence, `DRAFT`, `FAIL`, and NUMT-risk signals as explicit uncertainty or review outcomes.
- Add T1 logic, T2 animal branch, and T3 end-to-end coverage plus `VALIDATION-animal-identify.md` for normal, low coverage, and missing-reference scenarios. Expected states are: engineering-test normal may be callable, low coverage is `INCONCLUSIVE` or downgraded, and missing reference fails fast.
- Link GitHub issue #6 and require **M2-② 归档前 T1–T3 CI 必须全绿（含 M2-① 遗留的镜像问题已解决）** before this change can be archived.

### Explicitly out of scope

- NUMT confirmation by nuclear flanks, premature-stop/frameshift analysis, or long-read evidence; this belongs to a future NUMT-confirmation change.
- Kraken2 self-built contaminant DB and cross-kingdom contamination reactivation; track as a separate change.
- Long-read or hybrid assembly/authentication (M3/M4), threshold calibration, and a validated production SOP.
- Three-generation/hybrid routes, Kraken2 self-built DB, NUMT confirmation, nuclear marker panel implementation, and threshold calibration; these land in later changes.
- The GHCR publication implementation may be completed by the issue #6 local-push or CI-build path, but M2-② cannot be archived until the image problem is resolved and its T1–T3 CI gate is green.

## Capabilities

### New Capabilities

None. This change extends the existing animal short-read capability.

### Modified Capabilities

- `animal-short-read-analysis`: add the animal reference-first identify stage, CM084263/NC_023928 reference governance, production-null policy behavior, empty SCI-007 interface, evidence-combination decision behavior, and `stage = identify` status contract while preserving the M2-① `assembly_qc` contract.

## Impact

- **Pipeline:** animal identify subworkflow and routing after `ANIMAL_SR_ASSEMBLY`/`ASSEMBLY_QC`; decision/status emission.
- **Assets:** animal reference pack v0.1, CM084263 circularity disclosure, quarantined NC_023928 evidence, diagnostic/callable-region data, animal policy pack, empty SCI-007 marker interface, and compatibility metadata.
- **Contracts:** `assets/schema_status.json`, `assets/reason_codes.yaml`, compatibility manifest, and traceability entries for SCI-001, SCI-003, SCI-005, SCI-007, ENG-POL-001/002, TEST, and REL requirements.
- **Tests/validation:** T1 logic, T2 animal identify branch, T3 stub smoke, local real-data `VALIDATION-animal-identify.md`, and CI evidence linked to issue #6.
- **Release discipline:** no archive of M2-② until `openspec validate --strict` passes, the image problem is resolved, T1–T3 CI is fully green, and the image/build evidence is traceable.
