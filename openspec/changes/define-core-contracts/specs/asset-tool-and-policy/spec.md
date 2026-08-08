## ADDED Requirements

### Requirement: 工具注册表（registries/tools.yaml）

The system SHALL provide `registries/tools.yaml` registering the §8.3 first-version candidate tools at their initial admission tiers — `fastp` CONDITIONAL, `NanoPlot` APPROVED (descriptive QC only), `Kraken2` + self-built-db CONDITIONAL, `GetOrganelle` CONDITIONAL, `NOVOPlasty` EXPERIMENTAL, `MitoFinder`/`MitoZ` CONDITIONAL, `Flye` EXPERIMENTAL, `PMAT2` EXPERIMENTAL, `Racon` EXPERIMENTAL, `Polypolish` EXPERIMENTAL (applicability per §6.4 four-layer), `bcftools`-consensus EXPERIMENTAL, `NextPolish2` DEFERRED, `GeSeq`/`PlastidHub` DEFERRED. Each entry SHALL follow the §8.2 structure (tool_id, version, role, admission_status, supported_platforms, project_validated_platforms, container_digest, validation_record, review_date) with `container_digest`/`validation_record` null until project-validated.

The registry SHALL include a **PROHIBITED section** listing `medaka`, `Nanopolish`, `Clair3-ONT` (ONT-model-bound) and `Oatk`, `TIPPo`, `MitoHiFi`, `hifiasm` (HiFi-only). Each PROHIBITED entry MUST carry a `reason` (per methods §7.2 model-binding tier: no CycloneSEQ-compatible model) and a `re_evaluation_trigger` (e.g. "re-evaluate when an official CycloneSEQ-compatible model is released, or when project transfer validation passes"). A registry header comment MUST distinguish the semantics: **PROHIBITED** = explicitly forbidden now for a stated scientific reason; **DEFERRED** = not yet evaluable, activatable when evidence arrives.

#### Scenario: PROHIBITED 工具不进生产模块

- **WHEN** CI scans `modules/` and `conf/`
- **THEN** no PROHIBITED tool (`medaka`/`Nanopolish`/`Clair3-ONT`/`Oatk`/`TIPPo`/`MitoHiFi`/`hifiasm`) appears as a production process or container

#### Scenario: 未验证工具 digest/record 为 null 且被 production 拒绝

- **WHEN** a tool is not yet project-validated
- **THEN** its `container_digest` and `validation_record` are null and the production profile refuses to use it

### Requirement: 假设注册表（registries/hypotheses.yaml）

The system SHALL provide `registries/hypotheses.yaml` encoding the §9.4 state machine — `proposed → under_validation → validated | rejected → superseded` with the five status meanings — and the **full HYP-DNA-001 entry** transcribed from §9.4: statement, basis, scope_notes, `metric_definitions` that explicitly distinguishes (a) extracted-DNA fragment distribution (Qsep/FemtoPulse) from (b) sequencing read N50 (NanoPlot), `derived_fields: [dna_integrity]`, `status: proposed`, `validation_protocol: null`. The pipeline MUST NOT depend on a hypothesis in `proposed` or `rejected` status as a validated parameter.

#### Scenario: HYP-DNA-001 完整登记且双指标区分

- **WHEN** `registries/hypotheses.yaml` is inspected
- **THEN** HYP-DNA-001 carries statement, basis, scope_notes, and `metric_definitions` distinguishing the two metrics, with `status: proposed` and `validation_protocol: null`

### Requirement: policy pack 框架 + experimental 示例 + production null 拒绝（ENG-POL-002）

The system SHALL provide a `policies/` framework (empty) plus one experimental example `policies/tcm-plant-experimental.yaml` per §9.2 (status `experimental`; thresholds `short_read_qc`/`callable_site`/`junction_support`/`uncertainty_zone` all `null`; `validation.protocol_id` set, `record_id` null). The production profile MUST reject (fail-fast, ENG-POL-002) any policy_pack in which a rule-referenced threshold is `null`/uncalibrated. For M0 this is specified as a design note plus an all-null policy fixture (`tests/fixtures/policy_all_null.yaml`) that a future loader must reject — no policy-loader code is added in M0 (no analysis modules yet).

#### Scenario: production 拒绝全 null policy

- **WHEN** a production run loads a policy_pack with any null rule-referenced threshold
- **THEN** the run fails before producing a formal conclusion (ENG-POL-002)
