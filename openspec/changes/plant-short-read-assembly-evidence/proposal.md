## Why

M0 + `define-core-contracts` delivered the skeleton + executable contracts. M1 (§18) is the first **real** pipeline behavior. Per the agreed split, this change is **M1-①**: produce a trusted plant short-read **assembly + read-back evidence + assembly-stage status** (samplesheet → plastome/nrDNA assembly), validated against the published *Corydalis* chloroplast **PZ405204**. The reference-first **decision** is deferred to M1-② (`plant-short-read-identify`), which consumes ①'s frozen output contract (see design.md "①→② 接口合同"). Installing the first real nf-core module (fastp) also **resolves issue #2's 8 `container_configs` lint deviations**.

## What Changes

- **QC_SHORT** — install the real nf-core `fastp` module. fastp parameters follow methods §2.1 (`--detect_adapter_for_pe --qualified_quality_phred 15 --length_required 50`) but are placed in the **`experimental` profile only** — per §5.1 / ENG-POL-001, unvalidated Q/length/dup/adapter thresholds MUST NOT be production defaults (production reads them from an approved policy pack; here still `null`).
- **PLANT_SR_ASSEMBLY** — a **self-built local `getorganelle` module** (nf-core has no GetOrganelle module; bioconda package available), implementing methods Scenario A's two commands exactly: `embplant_pt` (`-R 15 -k 21,45,65,85,105`) and `embplant_nr` (`-k 35,85,115`). `-R`/`-k` are **GetOrganelle algorithm parameters** (§9.3 → tool registry + design), NOT scientific acceptance thresholds. The module MUST emit `versions.yml`. No forced circularization: low-coverage → scaffold + `DRAFT`.
- **ASSEMBLY_QC (read-back evidence)** — clean reads re-mapped to the assembly with **minimap2 `-ax sr`** (approved; matches methods §3.5 and stays consistent with future long-read use), then `samtools depth`/`flagstat` → coverage + uniformity metrics. The coverage-valley ratio is a **scientific threshold read from policy** (`null` in experimental → flagged, never hardcoded). Outputs feed `evidence_files`.
- **Status emission** — emit a status JSON (per `schema_status.json` / §5.5) at `stage = assembly_qc` with `decision = NOT_APPLICABLE` (no decision logic in ①). Field-level output contract frozen in design.md "①→② 接口合同".
- **Validation** — normal *Corydalis* (SRR38978846, subsampled ~2 Gb under `corydalis_test/`) → assembled plastome highly consistent with **PZ405204** (identity recorded). Local run + record, not CI.
- **Tests** — T1 (module nf-test), T2 (subworkflow branch/status propagation), T3 (micro-data pipeline smoke, in CI).
- **Issue #2** — fastp install regenerates the 8 container configs → resolve per issue #2's restoration criteria.

## Capabilities

### New Capabilities

- `plant-short-read-analysis`: the plant short-read assembly + read-back evidence + assembly-stage status behavior (M1-① increment). ② will later add reference-first identify requirements to this same domain.

### Modified Capabilities

None at the spec level. (Status model, tool-admission rules, and routing rules already exist from earlier changes; ① implements them. Tool `container_digest`s are populated as a registry data update, not a spec change.)

## Impact

- **New code**: nf-core `fastp` module; local `getorganelle` module (2 `-F` modes); `minimap2/align` + `samtools/depth` + `samtools/flagstat` (nf-core modules); subworkflows `QC_SHORT`, `PLANT_SR_ASSEMBLY`, `ASSEMBLY_QC`; status emitter wired into the `ORGANELLEAUTH` workflow for plant short-read samples.
- **Registries/policies**: populate `container_digest` for fastp/getorganelle/minimap2/samtools (admission unchanged: CONDITIONAL until project validation); add assembly-stage reason codes (`NO_CIRCULARIZATION`, `ASSEMBLY_FAILED`) to `reason_codes.yaml`.
- **CI**: enable T1–T3 (nf-test + pipeline smoke); issue #2's 8 container_configs resolved → lint can be re-evaluated as blocking.
- **No scientific thresholds hardcoded**: fastp params experimental-only; GetOrganelle `-R`/`-k` are tool params; acceptance thresholds (coverage-valley, etc.) read from policy (`null` → INCONCLUSIVE/flag, never a forced call).
- **Out of scope (M1-② or later)**: reference-first decision logic, test reference pack wiring, 4-scenario decision validation, Kraken2 self-built lib (contamination via coverage/assembly signal in ①; gap documented in design), NOVOPlasty cross-check, animal branch, any 3rd-gen/hybrid route, full decision engine.
