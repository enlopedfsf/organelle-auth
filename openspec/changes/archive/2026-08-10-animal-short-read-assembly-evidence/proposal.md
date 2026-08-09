## Why

M1 (§18) delivered the plant short-read route end-to-end (fastp → GetOrganelle → read-back evidence → `assembly_qc` status → reference-first identify). M2 extends the system to **animal** TCM material. Per the agreed split, this change is **M2-①**: the data-production half — animal short-read **mitogenome assembly + read-back evidence + NUMT risk screening + assembly-stage status** (samplesheet → mitogenome assembly), validated against a published *Whitmania acranulata* mitogenome. The reference-first **decision**, animal **reference pack v0.1**, animal **policy**, and the **nuclear-marker interface (SCI-007)** are deferred to M2-② (`animal-short-read-identify`), which consumes ①'s frozen output contract. ① maximally reuses the M1 plant branch (fastp QC_SHORT, ASSEMBLY_QC read-back, status model) and adds only the animal-specific pieces.

## What Changes

- **Animal routing** — extend the `ORGANELLEAUTH` workflow so `taxon_group=animal` samples with short reads and `targets ⊇ {mitome}` route explicitly (§3.3 / DATA-006) through the reused `QC_SHORT` → new `ANIMAL_SR_ASSEMBLY` → reused `ASSEMBLY_QC` → `assembly_qc` status emission. Nothing inferred from filenames/descriptions (DATA-006). Plant route regression must stay lossless.
- **ANIMAL_SR_ASSEMBLY (MitoFinder route)** — per methods §3.3/§4.3 adapted to short reads and tools.yaml admission (`mitofinder_mitoz` CONDITIONAL, dnbseq):
  1. **Multi-reference bait extraction** — `minimap2 -x sr` against a set of circumscribed mitogenome references to extract candidate mitochondrial reads before assembly (a single reference can miss the hypervariable control region / D-loop, which is exactly the high-discrimination region for animal authentication, methods §4.3). This is the short-read adaptation of the "多参考提取" principle; it is NOT Flye sub-set assembly (that is the M3 long-read path).
  2. **MitoFinder assembly + annotation** — run MitoFinder on the baited (or clean) reads to assemble + annotate + standardize gene order (methods §3.3). Scientific parameters follow methods verbatim; runtime/algorithm knobs are tool parameters (decision pattern from M1 ① Decision 2), NOT acceptance thresholds.
  3. **Local output adapter** — mirror the M1 `getorganelle_result_adapter`: grade the result `CANDIDATE` (single circular contig) vs `DRAFT` (scaffold/linear, no forced circularization per §3.6/SCI-005), rename to the frozen ①→② interface paths (`<sample_id>_mitogenome.fasta` / `_mitogenome.scaffold.fasta`), collect annotation + assembly graph (Bandage-ready), emit `versions.yml`. Containerized + Docker config.
- **NUMT risk screening (minimal version)** — an executable NUMT **risk-screening** module (not confirmation): re-map reads to the mitogenome assembly and check **coverage heterogeneity** (valley regions vs median, per methods §3.5) and **multi-mapping / abnormal-depth signals** (methods §3.3 NUMT 排检). Any signal emits a **WARN-level reason code** (e.g. `NUMT_RISK_SUSPECTED`) in the `assembly_qc` status. The minimal version is explicitly a **screening**, not NUMT confirmation — confirmation requires nuclear-flanking / premature-stop-codon / frameshift checks + long-read evidence, recorded in design.md known limitations (non-goal this change).
- **Status emission** — emit status JSON per `schema_status.json` / §5.5 at `stage = assembly_qc`, `decision = NOT_APPLICABLE` (① never decides). Field-level animal output contract frozen in design.md "①→② 接口合同" (mirrors M1 ①).
- **Reason codes** — add animal assembly-stage codes to `reason_codes.yaml` (e.g. `NUMT_RISK_SUSPECTED` WARN; reuse `NO_CIRCULARIZATION`/`ASSEMBLY_FAILED`). Code addition is registry data, not a spec change.
- **Validation (local real data, recorded)** — *Whitmania acranulata* (柳叶蚂蟥) `SRR27841063` subsampled ~2 Gb (and a low-coverage ~0.5 Gb run) end-to-end under `whitmania_test/`: normal + low-coverage assembly runs; identity vs a published conspecific circular mitogenome (GenBank has ≥5 complete *W. acranulata* mitogenomes, e.g. `NC_023928` 14,462 bp / `KC688271` / `MK347500` / `CM084263` — no congeneric proxy needed) recorded via mash/dnadiff, following the M1 `VALIDATION-7.1.md` format. Local run + record, not CI.
- **Tests** — T1 (MitoFinder module + NUMT-screening module nf-test), T2 (animal routing branch + status propagation), T3 (animal end-to-end micro-data stub smoke, in CI).
- **Registry** — populate `container_digest` for MitoFinder (and minimap2 if not yet recorded); admission unchanged (CONDITIONAL until project validation).

## Capabilities

### New Capabilities

- `animal-short-read-analysis`: the animal short-read mitogenome assembly + read-back evidence + NUMT risk screening + assembly-stage status behavior (M2-① increment). ② will later add reference-first identify requirements to this same domain.

### Modified Capabilities

None at the spec level. (Status model, tool-admission rules, and routing rules already exist from earlier changes; ① implements them for animal. Tool `container_digest`s are populated as registry data updates, not spec changes.)

## Impact

- **New code**: local `mitofinder` module (assembly+annotation) with `versions.yml`; multi-reference bait-extraction step (minimap2 `-x sr`); `animal_result_adapter` (CANDIDATE/DRAFT grading + interface naming); `numt_risk_screen` module; subworkflow `ANIMAL_SR_ASSEMBLY`; routing + status wiring in the `ORGANELLEAUTH` workflow for animal short-read samples.
- **Registries/policies**: populate `container_digest` for MitoFinder; add `NUMT_RISK_SUSPECTED` (WARN) to `reason_codes.yaml`; no scientific thresholds hardcoded (coverage-valley ratio reads from policy, `null` in experimental → flagged, never forced).
- **CI**: enable animal T1–T3 (nf-test + pipeline stub smoke).
- **Assets**: reference-pack/diagnostic-site assets for animal, animal policy, nuclear-marker interface, and decision-engine reuse → M2-②.
- **Out of scope (M2-② or later)**: reference-first identify for animal, animal reference pack v0.1, animal test policy, nuclear-marker interface slot (SCI-007), 3-scenario decision validation, Kraken2 self-built DB (independent change), NUMT confirmation, threshold calibration, any 3rd-gen/hybrid route (M3/M4).
