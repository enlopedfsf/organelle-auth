## Why

① `plant-short-read-assembly-evidence` (archived 2026-08-09) produces the assembly + read-back
evidence and a `stage = assembly_qc` status with `decision = NOT_APPLICABLE`. The authentication
**decision** (`AUTHENTIC` / `NON_AUTHENTIC` / `INCONCLUSIVE`) is not yet produced, so a normal
plant sample currently cannot be authenticated end-to-end. This change fills the **judgment half**
of M1: a reference-first, policy-driven `IDENTIFY` workflow that consumes ①'s frozen outputs and
emits `stage = identify` with the decision filled.

①'s real-data finding makes one design question unavoidable: a **normal** plant sample (刻叶紫堇
SRR38978846) produces a **6-scaffold `DRAFT`** assembly at **99.95 % identity** (see ①
`VALIDATION-7.1`). Therefore ② **must** decide how `assembly_grade` gates `decision` — if `DRAFT`
were automatic `INCONCLUSIVE`, a normal sample could never be authenticated and the pipeline would
fail its primary purpose.

## What Changes

- **Add the `IDENTIFY` subworkflow (reference-first)**: consume ①'s selected plastome FASTA +
  read-back evidence (BAM/depth/flagstat) + the `assembly_qc` status (esp. `assembly_grade`,
  `reason_codes`) → evaluate against the loaded `reference_pack` (callable-region coverage +
  diagnostic-site identity) → run the decision engine → emit `stage = identify` status with
  `decision` filled.
- **Decision gating anchored to SCI-001 / SCI-005** (the required `assembly_grade ↔ decision`
  decision): "high identity" is defined **site-level** — all reference-pack `diagnostic_sites` must be
  covered and callable (not a single global identity number). `DRAFT + all diagnostic sites callable +
  adequate callable coverage → AUTHENTIC + WARN [INCOMPLETE_ASSEMBLY]`; diagnostic sites falling in a
  missing/uncallable region → `INCONCLUSIVE + [DIAGNOSTIC_SITES_NOT_CALLABLE]` even if the assembled
  part is 100% identical. Full matrix in `design.md`.
- **Threshold-from-policy**: read `callable_site` + `uncertainty_zone` from the policy pack; a `null`
  threshold at the **identify-module layer** → `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]`
  (**no crash**, no forced call). Reconciled with `ENG-POL-002` (the production *startup* gate) —
  both layers coexist by design.
- **Reference-pack mechanism**: `reference_pack_id` → load → `DATA-005` fail-fast on
  missing/incompatible (no silent fallback to a public DB). Decision rules are read from the
  reference pack, never hardcoded as "正品四要素" natural language.
- **Engineering-test policy**: an uncalibrated policy (`callable_site`/`uncertainty_zone` filled
  with measured numbers) for validating the decision *logic flow* only — explicitly **not** a
  scientific calibration (that is M3 experiments + M5 policy v1.0).
- **Extend `reason_codes.yaml`** with identify-stage codes (`THRESHOLD_NOT_CONFIGURED`,
  `IDENTITY_BELOW_THRESHOLD`, `CONTAMINATION_SUSPECTED`, `INCOMPLETE_ASSEMBLY`,
  `DIAGNOSTIC_SITES_NOT_CALLABLE`) and a new `non_authentic` category.
- **Passthrough contract**: `assembly_grade = NOT_APPLICABLE` or `status = FAIL` from ① →
  `INCONCLUSIVE` (no judgment).
- **Four-scenario real-data validation** (recorded, not in CI): normal / low-coverage /
  contamination (柳叶蚂蟥 `SRR27841063`) / reference-missing; plus production-null → `INCONCLUSIVE`.

## Capabilities

### New Capabilities

_(none — identification is the second half of the existing `plant-short-read-analysis` domain.)_

### Modified Capabilities

- `plant-short-read-analysis`: add the `IDENTIFY` half — the reference-first identify workflow,
  the `assembly_grade ↔ decision` gating, the `stage = identify` status output, and the
  null-threshold → `INCONCLUSIVE` module-layer behaviour. The domain currently ends at
  `stage = assembly_qc`; this change extends it to `stage = identify` with `decision` filled.

## Impact

- **New code**: `modules/local/` identify processes (reference-pack loader, evidence/callable-region
  evaluator, decision engine), `subworkflows/local/identify/`, an identify status emitter; reuses
  ①'s nf-core `minimap2`/`samtools` where read-back re-mapping to the reference is needed.
- **Assets**: `assets/reason_codes.yaml` (4 new codes), `policies/` (engineering-test policy),
  a test `reference_pack` v0.1 built from `PZ405204.1` for the normal scenario.
- **Consumes ① outputs** under the frozen interface contract (`design.md` §1-4 of the archived ①
  change) — **no changes to ①**.
- **Tests**: T1-T3 (module/subworkflow/pipeline) enter CI; the four-scenario real-data validation is
  recorded in a `VALIDATION` doc (not CI), like ①'s `VALIDATION-7.1`.
- **Non-goals** (explicit): no animal branch (M2-animal), no 三代/混合 (M3/M4), no Kraken2 self-built
  db (separate change), no NOVOPlasty cross-check, no plant mitochondria, no full decision engine
  (M5); engineering-test thresholds are not calibrated as scientific.
