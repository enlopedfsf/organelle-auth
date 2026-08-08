## Why

The M0 bootstrap (`bootstrap-nfcore-repository`, archived) established the 5 spec domains and the governance skeleton, but the **executable contracts those specs reference are still placeholders** — the concrete samplesheet schema, the status model + reason-code dictionary, the tool/hypothesis registries, and the policy/compatibility frameworks. Per 总方案 §23 change #2, this change fills those structured contract files so the T0 CI (`spec-and-schema`) has real schemas to validate and the Requirement traceability matrix maps to concrete artifacts. It adds **no pipeline logic and no scientific thresholds** — every unvalidated value stays `null` (evidence-first, ENG-POL-001/002).

## What Changes

- **`assets/schema_input.json`** — full samplesheet schema (§4.1): `sample_id`, `analysis_mode`, `taxon_group`, `targets`, `short_reads_1/2`, `long_reads`, `specimen_role`, `dna_integrity`, `reference_pack_id`, `policy_pack_id`, `batch_id` with enums + conditional-required rules; truthset isolation enforced (DATA-001/002/003/006).
- **`assets/schema_status.json` + `assets/reason_codes.yaml`** — machine-readable status model (§5.5): `status`/`assembly_grade`/`decision` enumerations + a versioned reason-code dictionary (report generator only interprets, never re-judges).
- **`registries/tools.yaml`** — tool registry with §8.3 initial admission tiers (fastp `CONDITIONAL`, NanoPlot `APPROVED` [descriptive QC only], Kraken2 `CONDITIONAL`, GetOrganelle `CONDITIONAL`, PMAT2/Flye/Racon/Polypolish/NOVOPlasty `EXPERIMENTAL`, NextPolish2 `DEFERRED`, medaka/Nanopolish/Clair3-ONT/Oatk/MitoHiFi `PROHIBITED`); `container_digest`/`validation_record` null until validated.
- **`registries/hypotheses.yaml`** — HYP-DNA-001 entry (status `proposed`, `validation_protocol` null).
- **`policies/` skeleton + compatibility manifest** — empty frameworks (independent versioning per §10.3; pipeline/method-spec/reference-pack/policy/kraken-db/validation-set versioned separately).
- **Wire `spec-and-schema` CI** to validate these schemas/registries (today it checks structure only).
- **NOT in scope**: any Nextflow module/subworkflow, real test data, any scientific threshold value (all `null` until validation), reference-pack FASTA content.

## Capabilities

### Modified Capabilities

This change concretises contracts inside the 5 existing spec domains (no new domains):

- `scope-routing-and-input`: add the concrete samplesheet schema contract (DATA-001/002/003/004/006 details become machine-checkable).
- `asset-tool-and-policy`: add tools.yaml / hypotheses.yaml / policy / compatibility-manifest structure (ENG-POL-004/005 + tool admission registry + the HYP-DNA-001 registry entry).
- `evidence-decision-and-status`: add schema_status.json + reason_codes.yaml (the §5.5 status model becomes an enforced schema).
- `validation-and-go-no-go`: minimal (validation-protocol references only).
- `provenance-and-release`: minimal (compatibility manifest referenced).

### New Capabilities

None (no new spec domain).

## Impact

- **New files**: `assets/schema_input.json`, `assets/schema_status.json`, `assets/reason_codes.yaml`, `registries/tools.yaml`, `registries/hypotheses.yaml`, `policies/<framework>.yaml`, compatibility manifest.
- **CI**: `spec-and-schema.yml` gains real schema/registry validation (beyond today's structural check).
- **Traceability**: the 34 ReqIDs in `openspec/traceability.yaml` now map to concrete contract artifacts.
- **No scientific behavior change**: all thresholds remain `null`; no tool becomes production-eligible without validation.
