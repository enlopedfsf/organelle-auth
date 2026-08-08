## ADDED Requirements

### Requirement: 具体输入 schema 合同（assets/schema_input.json）

The system SHALL provide `assets/schema_input.json` as a JSON Schema encoding every §4.1 samplesheet field — `sample_id`; `analysis_mode` (∈ `reference_build` | `identify` | `validate`); `taxon_group` (∈ `plant` | `animal`); `targets` (subset of `plastome` | `mitome` | `nrdna`); `short_reads_1`, `short_reads_2`, `long_reads`; `specimen_role` (∈ `voucher` | `reference_candidate` | `routine_test` | `blind_control` | `negative_control` | `mixture_control`); `dna_integrity` (∈ `hmw_pass` | `fragmented` | `degraded` | `unknown`); `reference_pack_id`; `policy_pack_id`; `batch_id` — with conditional-required rules (e.g. `short_reads_2` required for paired-end; `reference_pack_id` required for `identify`; `dna_integrity` required for `reference_build`).

The schema SHALL enforce **DATA-001** (no analysis channel before JSON Schema validation) and **DATA-003** (the schema MUST reject any column that carries expected taxonomic truth, e.g. an `expected_species` / `truth_*` field). **DATA-002** (path/pairing/uniqueness) and **DATA-004** (reference_build metadata) SHALL be expressed as schema constraints where feasible and otherwise by CI assertions. **DATA-005** (incompatible/missing reference_pack fail-fast), **DATA-006** (no implicit inference from filenames/descriptions), and **DATA-007** (controls treated as formal samples) are runtime/preflight behaviours and SHALL be covered by CI test assertions + design notes, not by the column schema alone.

#### Scenario: 合法 samplesheet 通过校验

- **WHEN** a samplesheet carrying all required fields with valid enums is validated against `schema_input.json`
- **THEN** validation passes (DATA-001)

#### Scenario: 含真值字段的 samplesheet 被拒绝（DATA-003）

- **WHEN** a samplesheet contains an expected-taxonomic-truth column (e.g. `expected_species`)
- **THEN** `schema_input.json` validation rejects it

#### Scenario: 缺/不兼容 reference_pack 快速失败（DATA-005）

- **WHEN** `identify` mode is requested with a missing or incompatible `reference_pack_id`
- **THEN** the run fails fast (asserted by a CI test / documented preflight design), and MUST NOT silently fall back to a default public database
