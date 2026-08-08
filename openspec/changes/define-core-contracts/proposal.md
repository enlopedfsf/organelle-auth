## Why

The M0 bootstrap (`bootstrap-nfcore-repository`, archived) established the 5 spec domains and the governance skeleton, but the **executable contracts those specs reference are still placeholders** — the concrete samplesheet schema, the status model + reason-code dictionary, the tool/hypothesis registries, and the policy/compatibility frameworks. Per 总方案 §23 change #2, this change fills those structured contract files so the T0 CI (`spec-and-schema`) has real schemas to validate and the Requirement traceability matrix maps to concrete artifacts. It adds **no pipeline logic and no scientific thresholds** — every unvalidated value stays `null` (evidence-first, ENG-POL-001/002).

## What Changes

- **`assets/schema_input.json`** — JSON Schema for all 12 §4.1 fields (`sample_id`, `analysis_mode`, `taxon_group`, `targets`, `short_reads_1/2`, `long_reads`, `specimen_role`, `dna_integrity`, `reference_pack_id`, `policy_pack_id`, `batch_id`) with enums + conditional-required. Enforces **DATA-001** (JSON Schema validation) and **DATA-003** (forbids any expected-truth / taxonomy-truth column). **DATA-002/004** covered by schema constraints + CI; **DATA-005/006/007** enforced via CI test assertions + design notes (NOT schema-alone — they are runtime/preflight behaviours).
- **`assets/schema_status.json`** — JSON Schema for the full §5.5 status object: `sample_id`, `stage`, `status` (∈ PASS|WARN|FAIL|INCONCLUSIVE), `assembly_grade` (∈ REFERENCE|DRAFT|CANDIDATE|NOT_APPLICABLE), `decision` (∈ AUTHENTIC|NON_AUTHENTIC|INCONCLUSIVE|NOT_APPLICABLE), `reason_codes`, `policy_pack_id`, `evidence_files`.
- **`assets/reason_codes.yaml`** — versioned reason-code dictionary; **empty framework + 3 example codes** (report generators only interpret, never re-judge; pipeline failure vs scientific INCONCLUSIVE separately encoded).
- **`registries/tools.yaml`** — the §8.3 first-version candidates (13) at their initial admission tiers (fastp CONDITIONAL, NanoPlot APPROVED [descriptive QC only], Kraken2+self-built-db CONDITIONAL, GetOrganelle CONDITIONAL, NOVOPlasty EXPERIMENTAL, MitoFinder/MitoZ CONDITIONAL, Flye EXPERIMENTAL, PMAT2 EXPERIMENTAL, Racon EXPERIMENTAL, Polypolish EXPERIMENTAL, bcftools-consensus EXPERIMENTAL, NextPolish2 DEFERRED, GeSeq/PlastidHub DEFERRED) using the §8.2 entry structure; PLUS a **PROHIBITED section** — medaka, Nanopolish, Clair3-ONT (ONT-model-bound) and Oatk, TIPPo, MitoHiFi, hifiasm (HiFi-only) — each with `reason` (methods §7.2 model-binding tier: no CycloneSEQ-compatible model) and `re_evaluation_trigger`. A header comment distinguishes PROHIBITED (forbidden now for a stated scientific reason) from DEFERRED (not yet evaluable; activatable when evidence arrives). `container_digest`/`validation_record` null until validated.
- **`registries/hypotheses.yaml`** — the §9.4 state machine (`proposed → under_validation → validated | rejected → superseded`, with the 5 status meanings) + the **full HYP-DNA-001 entry** transcribed from §9.4 (statement, basis, scope_notes, metric_definitions distinguishing extracted-DNA fragment distribution vs sequencing read N50, derived_fields `[dna_integrity]`, status `proposed`, validation_protocol null).
- **`policies/`** — empty framework + one experimental example `policies/tcm-plant-experimental.yaml` (§9.2: status experimental; thresholds short_read_qc/callable_site/junction_support/uncertainty_zone all `null`; validation.protocol_id set, record_id null). **Production-null rejection (ENG-POL-002)** captured as a design note + an all-null policy fixture (no policy-loader code in M0 — no analysis modules yet).
- **compatibility manifest** — empty framework per §10.3 (compatibility_id + pipeline/method_spec/reference_pack/kraken_db/policy_pack/validation_dataset; independent versioning).
- **CI** — extend `spec-and-schema` to validate the new schemas/registries, run **2 samplesheet fixtures** (valid passes; truth-field rejected), and a **cheap T0 grep** asserting PROHIBITED tools are absent from `modules/` + `conf/`.
- **NOT in scope**: any Nextflow module/subworkflow, real threshold values (all `null`), reference-pack FASTA content, policy-loader code.

## Capabilities

### Modified Capabilities

This change adds executable contract requirements inside existing domains (no new domains, no rewrite of existing behavioural requirements):

- `scope-routing-and-input`: concrete samplesheet schema contract — DATA-001..007 (esp DATA-003 truth-forbidden, DATA-005 fail-fast).
- `asset-tool-and-policy`: tools.yaml (tool-admission registry, §8.3 + PROHIBITED), hypotheses.yaml (state machine + HYP-DNA-001), policy framework + experimental example + ENG-POL-002 production-null rejection (ENG-POL-001..005).
- `evidence-decision-and-status`: schema_status.json + reason_codes.yaml (§5.5 status model as an enforced schema).
- `provenance-and-release`: compatibility manifest framework (§10.3 independent versioning).

(`validation-and-go-no-go`: no requirement change this round.)

### New Capabilities

None.

## Impact

- **New files**: `assets/schema_input.json`, `assets/schema_status.json`, `assets/reason_codes.yaml`, `registries/tools.yaml`, `registries/hypotheses.yaml`, `policies/tcm-plant-experimental.yaml`, policies framework, compatibility manifest, test fixtures (`tests/fixtures/samplesheet_valid.csv`, `tests/fixtures/samplesheet_with_truth.csv`, `tests/fixtures/policy_all_null.yaml`).
- **CI**: `spec-and-schema.yml` + `check_schema_traceability.py` gain real schema/registry validation, the 2 samplesheet assertions, and the PROHIBITED-tools grep.
- **Traceability**: the 34 ReqIDs in `openspec/traceability.yaml` now map to concrete contract artifacts (DATA-001..007, ENG-POL-001..005, the status model, §10.3 manifest).
- **No scientific behavior change**: all thresholds remain `null`; no tool becomes production-eligible without validation; no analysis module is added.
