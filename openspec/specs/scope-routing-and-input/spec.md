# scope-routing-and-input Specification

## Purpose
定义中药材细胞器基因组鉴定系统的鉴定范围、显式路由原则与输入数据合同，确保分析意图、生物学目标与数据可得性三者不被样本描述或文件扩展名隐式推断。
## Requirements
### Requirement: 三 entry workflow 范围与明确非目标

The system SHALL declare exactly three analysis entry workflows — `REFERENCE_BUILD`, `IDENTIFY`, `VALIDATE`. 首版核心实现 MUST NOT 包含炮制品 mini-barcode、复方、metabarcoding、靶向捕获或 qPCR/dPCR 定量的可执行生产模块（§1.2）。任何保留的扩展接口 MUST 标注其准入须经独立 OpenSpec change。

#### Scenario: 首版范围不含扩展层

- **WHEN** 检查首版核心实现
- **THEN** 不存在 metabarcoding / 靶向捕获 / qPCR 定量的生产模块
- **AND** 任何扩展接口占位都明确标注准入条件

### Requirement: 路由仅依据显式字段

The system SHALL route each sample exclusively from explicitly declared routing fields — `analysis_mode`, `taxon_group`, `targets`, short-read availability, long-read availability, `specimen_role`, `reference_pack` compatibility, and `policy_pack` status（§3.3）。The system MUST NOT infer `taxon_group` from specimen descriptions, MUST NOT infer reference-grade qualification from the presence of dual-platform data, and MUST NOT infer sequencing platform from file extensions（DATA-006）。

#### Scenario: 禁止从样本描述推断分类群

- **WHEN** a sample description or `specimen_role` reads `leaf`, `root`, or `voucher`
- **THEN** `taxon_group` is taken only from the explicit `taxon_group` field, never from the description

#### Scenario: 禁止从数据组合推断参考级资格

- **WHEN** a sample has both DNBSEQ and CycloneSEQ data
- **THEN** the sample is not automatically granted reference-grade qualification; qualification follows `REFERENCE_BUILD` acceptance rules

### Requirement: 真值与样本数据隔离

Analysis samplesheets MUST NOT carry expected taxonomic truth. The `VALIDATE` unblinding evaluation SHALL load truth exclusively from a separate, access-controlled `truthset.csv`, and only after every sample-level result is frozen with a checksum（DATA-003）。

#### Scenario: 分析输入不含真值

- **WHEN** an analysis samplesheet is constructed for any entry workflow
- **THEN** it contains no expected-truth column
- **AND** `truthset.csv` is loaded only by the unblinding evaluation step after result freeze

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

### Requirement: Canonical run roots

The local pipeline launcher SHALL resolve paths from the repository root and SHALL default
to `runs/input`, `runs/output`, and `runs/work`. It MUST preserve explicit path overrides
for deliberate isolated runs and MUST NOT infer a different root from the caller's current
working directory.

#### Scenario: Launch from another directory

- **WHEN** the repository launcher is invoked from outside the repository
- **THEN** the selected input, published output, and task work paths resolve under the repository's `runs/` root

### Requirement: Fail-fast input preflight

The launcher SHALL verify that the selected samplesheet exists and is non-empty before
starting Nextflow, and SHALL return a non-zero status with the path when the check fails.

#### Scenario: Missing samplesheet

- **WHEN** the default or explicitly selected samplesheet is absent or empty
- **THEN** Nextflow is not started and the launcher reports the failing path

