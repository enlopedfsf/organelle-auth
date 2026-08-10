# M2-② animal identify validation (engineering record)

Status: local real-data scenarios completed; final release remains gated on T1–T3 CI and issue #6.

## Data and provenance

The FASTQ inputs were checked for existence, non-zero size, and gzip integrity before execution.
The normal sample is `WTM_NORMAL`; the low-coverage scenario is an actual 0.02 downsample of the
M2-① low-coverage reads (`seed=42`), named `WTM_ULTRALOW`. The CM084263 reference and validation
data share the same BioProject provenance chain, so this demonstrates workflow reproducibility and
lineage consistency, not independent biological validation. `NC_023928.1` is `QUARANTINED` and
decision-ineligible; its 87.62% divergence and Ye et al. (2015) evidence are linked from the pack
manifest to the archived M2-① validation record.

The early `out/normal/` result is a stale pre-isolation run and must not be used as final evidence:
it was produced before the animal identify output root was separated from M2-①. The authoritative
normal result is under `out/normal_isolated/`.

## Scenario commands and results

All commands were run from the repository root with `NXF_OFFLINE=true`, profile
`docker,experimental`, config `conf/ci_test.config`, and the validation work root
`/mnt/ssd_pool/home/iris-hp/zhongyao/whitmania_test/m2_animal_identify_validation_v2`.

| Scenario | Command/policy | Expected | Actual |
|---|---|---|---|
| normal | `--input validation_inputs/normal.samplesheet.csv --outdir .../normal_isolated --policy_pack_file policies/tcm-animal-engineering-test.json` | Engineering-callable; DRAFT may be `AUTHENTIC + WARN` | `AUTHENTIC`, status `WARN`, grade `DRAFT`, reason `INCOMPLETE_ASSEMBLY`; 3/3 diagnostic sites callable, callable coverage `1.0`, identity `1.0`, mean readback depth `391.1373`; NUMT risk `false`; marker state explicitly `MISSING`/`MARKER_PANEL_MISSING`, not required by v0.1 pack |
| low coverage | `--input validation_inputs/lowcov.samplesheet.csv --outdir .../lowcov --policy_pack_file policies/tcm-animal-engineering-test.json` | `INCONCLUSIVE` or explicit downgrade; never forced call | `INCONCLUSIVE`, reason `DIAGNOSTIC_SITES_NOT_CALLABLE`; 1/3 diagnostic sites callable, callable coverage `0.363472`, mean readback depth `2.8826`, identity on callable sites `1.0`; no strong call |
| reference missing | low-coverage input with `--reference_pack_dir .../missing_reference_packs` and engineering policy | Fail-fast before `DECISION_ENGINE`; no public-DB fallback | `LOAD_REFERENCE_PACK` failed with `DATA-005: reference pack not found`; workflow stopped before `DECISION_ENGINE` and emitted no identify decision |
| production replay | normal input with `--outdir .../normal_production_null --policy_pack_file policies/tcm-animal-production-null.json` | `INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED` | Exactly `INCONCLUSIVE`, reason `THRESHOLD_NOT_CONFIGURED`; callable coverage remained `1.0`, but all production thresholds were null |

Authoritative JSON outputs:

- `.../normal_isolated/animal_sr_identify/WTM_NORMAL/WTM_NORMAL.identify.status.json`
- `.../normal_isolated/decision/WTM_NORMAL.decision.json`
- `.../lowcov/animal_sr_identify/WTM_ULTRALOW/WTM_ULTRALOW.identify.status.json`
- `.../lowcov/decision/WTM_ULTRALOW.decision.json`
- `.../normal_production_null/animal_sr_identify/WTM_NORMAL/WTM_NORMAL.identify.status.json`
- `.../normal_production_null/decision/WTM_NORMAL.decision.json`
- Missing-reference failure log: `LOAD_REFERENCE_PACK` `DATA-005` in the run `.nextflow.log`.

## Evidence and marker audit

Animal identify publishes mitogenome scaffold, annotation, read-back BAM/depth/flagstat, and the
decision JSON under `animal_sr_identify/<sample>/`. It does not claim the animal annotation is
nrdna or an assembly graph; those generic plant-only evidence labels are omitted for animal output.
The SCI-007 empty interface is propagated in both decision and status JSON with explicit state and
reason code. No marker sequence or taxon-specific panel is fabricated.

## Gate status

The local strict OpenSpec validation passes 8/8, and the local schema/traceability gate passes all
checks. The canonical CI run is
`https://github.com/enlopedfsf/organelle-auth/actions/runs/31407939848`; its immutable image is
`ghcr.io/enlopedfsf/mitofinder@sha256:174e1384dc549acb77ea57ab1ddfe55974dfcee9fe9c1965b6c8d3248bbfe4c2`.
The image build, T1–T3 animal smoke, both Nextflow matrices, pre-commit, schema, nf-core, and
confirm-pass checks are all green. The merged PR is #7 (`b6e9caa5e39e9c0544e9cbff9dc94dffe1eaa63e`).
