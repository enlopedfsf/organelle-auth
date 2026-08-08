## ADDED Requirements

### Requirement: 机器可读状态 schema（assets/schema_status.json + assets/reason_codes.yaml）

The system SHALL provide `assets/schema_status.json` as a JSON Schema encoding the full §5.5 status object — `sample_id`, `stage`, `status` (∈ `PASS` | `WARN` | `FAIL` | `INCONCLUSIVE`), `assembly_grade` (∈ `REFERENCE` | `DRAFT` | `CANDIDATE` | `NOT_APPLICABLE`), `decision` (∈ `AUTHENTIC` | `NON_AUTHENTIC` | `INCONCLUSIVE` | `NOT_APPLICABLE`), `reason_codes`, `policy_pack_id`, `evidence_files`.

The system SHALL provide `assets/reason_codes.yaml` as a versioned reason-code dictionary with an **empty framework seeded by 3 example codes**; report generators only interpret codes, never re-judge, and pipeline failure MUST be encoded separately from scientific `INCONCLUSIVE`.

#### Scenario: status object 符合三组枚举

- **WHEN** a status JSON is validated against `schema_status.json`
- **THEN** `status`, `assembly_grade`, and `decision` each fall within their allowed enumerations

#### Scenario: reason code 来自受控字典

- **WHEN** a subworkflow emits a reason code
- **THEN** it references a code defined in the versioned `reason_codes.yaml`, not free text
