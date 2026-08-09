## MODIFIED Requirements

### Requirement: 机器可读状态 schema（assets/schema_status.json + assets/reason_codes.yaml）

The system SHALL provide `assets/schema_status.json` as a JSON Schema encoding the full §5.5 status object — `sample_id`, `stage`, `status` (∈ `PASS` | `WARN` | `FAIL` | `INCONCLUSIVE`), `assembly_grade` (∈ `REFERENCE` | `DRAFT` | `CANDIDATE` | `NOT_APPLICABLE`), `decision` (∈ `AUTHENTIC` | `NON_AUTHENTIC` | `INCONCLUSIVE` | `NOT_APPLICABLE`), `reason_codes`, `policy_pack_id`, `evidence_files`.

The system SHALL provide `assets/reason_codes.yaml` as a versioned reason-code dictionary. The dictionary MUST distinguish depth-driven coverage insufficiency from callable-region coverage insufficiency, and MUST register `CONTAMINATION_SUSPECTED` as dormant with a documented reactivation condition.

#### Scenario: status object 符合三组枚举
- **WHEN** a status JSON is validated against `schema_status.json`
- **THEN** `status`, `assembly_grade`, and `decision` each fall within their allowed enumerations

#### Scenario: reason code 来自受控字典
- **WHEN** a subworkflow emits a reason code
- **THEN** it references a code defined in the versioned `reason_codes.yaml`, not free text
- **AND** depth/callable coverage codes are distinct (`LOW_SEQUENCING_DEPTH` vs `LOW_CALLABLE_COVERAGE`)
- **AND** dormant codes are not emitted until their reactivation conditions are met

#### Scenario: reason code 区分深度与 callable-region 覆盖
- **WHEN** `reason_codes.yaml` is inspected
- **THEN** it contains `LOW_SEQUENCING_DEPTH` for read depth below policy threshold
- **AND** `LOW_CALLABLE_COVERAGE` for callable-region fraction below policy threshold
- **AND** the legacy `LOW_COVERAGE` code is removed or marked superseded

#### Scenario: 污染码登记为 dormant
- **WHEN** `reason_codes.yaml` is inspected
- **THEN** `CONTAMINATION_SUSPECTED` remains in the dictionary
- **AND** it carries a `dormant: true` marker or equivalent note stating it is not emitted by current ①/② code
- **AND** it records the reactivation trigger (Kraken2 self-built DB + close-relative plant mixture validation)

## ADDED Requirements

### Requirement: 判定引擎按深度与 callable 覆盖分别触发 reason code

`DECISION_ENGINE` SHALL emit `LOW_SEQUENCING_DEPTH` when `mean_readback_depth < min_mean_depth`, and SHALL emit `LOW_CALLABLE_COVERAGE` when `callable_coverage < min_callable_fraction`. The two conditions MUST NOT share a single ambiguous code.

#### Scenario: 测序深度不足
- **WHEN** `mean_readback_depth` is below the policy `min_mean_depth`
- **THEN** the decision is `INCONCLUSIVE`
- **AND** `reason_codes` contains `LOW_SEQUENCING_DEPTH`

#### Scenario: callable-region 覆盖不足
- **WHEN** `callable_coverage` is below the policy `min_callable_fraction`
- **THEN** the decision is `INCONCLUSIVE`
- **AND** `reason_codes` contains `LOW_CALLABLE_COVERAGE`

### Requirement: 污染信号路径 dormant 留痕

While ① does not emit a coverage-anomaly signal and no validated contaminant screen exists, `CONTAMINATION_SUSPECTED` SHALL remain defined in `reason_codes.yaml` but SHALL NOT be emitted by `DECISION_ENGINE`. The design.md for this change MUST record the two empirical facts that justify dormancy.

#### Scenario: 当前不触发 CONTAMINATION_SUSPECTED
- **WHEN** a sample with cross-kingdom contamination is processed by the current ①/② flow
- **THEN** the contamination is not detected
- **AND** `DECISION_ENGINE` does not emit `CONTAMINATION_SUSPECTED`
- **AND** the gap is documented in the change design and linked to the future Kraken2 self-built DB change
