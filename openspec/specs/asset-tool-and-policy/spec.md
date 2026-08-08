# asset-tool-and-policy Specification

## Purpose
定义数据资产输入合同、工具准入分级、policy pack 与 hypothesis registry 的治理规则，使未经验证的工具、阈值与假设永远无法以 production 默认值的身份进入正式鉴定结论。
## Requirements
### Requirement: 正式资产输入合同

每次正式运行 SHALL 加载并校验以下资产：`reference_pack`、`policy_pack`、`tool_registry`、`hypothesis_registry`、`compatibility_manifest`、`container_lock`（§4.3）。每项资产 MUST 具有唯一 ID、版本、创建时间、维护者、校验和、来源、许可、适用范围与废弃状态。

#### Scenario: 缺失或不兼容资产快速失败

- **WHEN** a required asset is missing or a `reference_pack` version is incompatible
- **THEN** the run fails fast
- **AND** MUST NOT silently fall back to a default public database（DATA-005）

### Requirement: 工具准入五级制

工具准入 SHALL 使用五级制：`APPROVED`、`CONDITIONAL`、`EXPERIMENTAL`、`DEFERRED`、`PROHIBITED`（§8.1）。正式结论 SHALL 仅由 `APPROVED` 工具或满足声明条件的 `CONDITIONAL` 工具支撑；`EXPERIMENTAL` 工具的输出 MUST NOT 作为唯一判定依据；`DEFERRED`/`PROHIBITED` 工具 MUST NOT 进入首版生产流程。当 `container_digest` 或 `validation_record` 为空时，production profile MUST 拒绝使用该工具。

#### Scenario: 未验证工具不作唯一依据

- **WHEN** a tool has admission_status `EXPERIMENTAL`（例如 PMAT2 用于 CycloneSEQ、Flye、Racon、Polypolish、NOVOPlasty、bcftools 共识路线）
- **THEN** its output MUST NOT be the sole basis for a formal authentication decision

#### Scenario: 禁入工具不被使用

- **WHEN** a tool is `PROHIBITED`（例如绑定 ONT 模型的 medaka、依赖 fast5 信号的 Nanopolish、Clair3-ONT 预训练模型、HiFi 专用工具 Oatk/TIPPo/MitoHiFi/hifiasm 用于 CycloneSEQ）
- **THEN** it MUST NOT appear in any production module for CycloneSEQ data

### Requirement: 未验证阈值与 policy pack 治理

未经验证的阈值 MUST NOT 出现在 production profile 的有效默认值中（ENG-POL-001）；未标定值在 schema 中 SHALL 使用 `null`，production 启动时执行完整性检查并 fail-fast（ENG-POL-002）。experimental policy MUST 在输出中显著标识，MUST NOT 伪装成 production（ENG-POL-003）。判定阈值、QC 阈值与运行资源参数 MUST 分开管理，CPU/内存调整 MUST NOT 触发科学 policy 版本变化（ENG-POL-005）。

#### Scenario: production 拒绝未标定阈值

- **WHEN** a production run loads a policy_pack in which a rule-referenced threshold is `null` or uncalibrated（例如 callable_site、junction_support、uncertainty_zone、ITS2 杂合度、CycloneSEQ Q 值过滤阈值）
- **THEN** the run fails before producing a formal conclusion

#### Scenario: experimental policy 显著标识

- **WHEN** an experimental policy_pack is used
- **THEN** every output it produces is visibly marked experimental
- **AND** is not presented as a production result

### Requirement: hypothesis registry 状态机

凡"有依据但未验证、且影响流程行为"的科学假设 SHALL 登记于 hypothesis registry，与 tool registry 平行（§9.4）。每条假设 MUST 具有 ID、陈述、依据、适用范围、验证协议引用、状态与审阅日期，并沿状态机迁移：`proposed → under_validation → validated | rejected → superseded`。流程 MUST NOT 依赖处于 `proposed` 或 `rejected` 状态的假设作为已验证参数。

#### Scenario: 假设状态驱动可用性

- **WHEN** a hypothesis（例如 HYP-DNA-001 提取 DNA 片段档位）处于 `proposed` 或 `rejected` 状态
- **THEN** the pipeline MUST NOT use it as a validated routing or qualification parameter
- **AND** any manual `dna_integrity` value carries a `manual` provenance marker until a validated derivation rule is frozen

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

