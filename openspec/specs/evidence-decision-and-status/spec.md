# evidence-decision-and-status Specification

## Purpose
定义证据类别、判定规则来源与机器可读状态输出模型，使鉴定结论始终建立在预定义证据组合规则上，并使"无法判定"成为合法的质量输出而非流程失败。
## Requirements
### Requirement: 证据组合判定而非单一阈值

鉴定结论 SHALL 建立在预定义的证据组合规则上，MUST NOT 仅凭单一距离阈值或单个组装结果强制判定（SCI-001）。判定引擎 SHALL 从 reference pack 读取规则（`required_evidence`、`supporting_evidence`、`conflict_rules`、`callable_regions`、`diagnostic_sites`、`uncertainty_rules`、`known_exceptions`、`nuclear_evidence_requirement`，§7.2），MUST NOT 把"正品四要素全部一致"等自然语言硬编码进流程。

#### Scenario: 判定读取版本化规则

- **WHEN** the decision engine evaluates a sample
- **THEN** it applies rules loaded from the `reference_pack`
- **AND** does not apply hardcoded natural-language decision logic

### Requirement: 细胞器证据的科学边界

纯 CycloneSEQ 序列 MUST NOT 单独升级为正式鉴定终序列，其定位为结构证据、候选骨架或研究证据（SCI-003）。证据不足时系统 MUST 保留不确定位点或输出 `INCONCLUSIVE`，MUST NOT 为获得完整结果而强制补碱基、强制环化或强制归属（SCI-005）。植物线粒体首版 MUST 限定为研究性证据层，不进入日常判定（SCI-006）。动物核标记 MUST NOT 统一硬编码为 ITS2，而由分类群专用 marker panel 声明（SCI-007）。reads 比例 MUST NOT 直接解释为混合药材质量比例（SCI-008）。DNA 阴性 MUST NOT 直接推断原料从未存在（SCI-009）。

#### Scenario: 纯三代不作终判

- **WHEN** only CycloneSEQ evidence is available for a sample
- **THEN** no `AUTHENTIC` or `NON_AUTHENTIC` conclusion is issued on that basis alone
- **AND** the result is reported as structural evidence or candidate skeleton

#### Scenario: 证据不足输出 INCONCLUSIVE

- **WHEN** coverage is insufficient, evidence conflicts, or the reference is missing
- **THEN** the system outputs `INCONCLUSIVE` rather than forcing a call

### Requirement: 机器可读状态输出模型

每个关键 subworkflow SHALL 输出机器可读状态文件（§5.5），包含 `sample_id`、`stage`、`status`、`assembly_grade`、`decision`、`reason_codes`、`policy_pack_id`、`evidence_files`。允许值：`status ∈ {PASS,WARN,FAIL,INCONCLUSIVE}`；`assembly_grade ∈ {REFERENCE,DRAFT,CANDIDATE,NOT_APPLICABLE}`；`decision ∈ {AUTHENTIC,NON_AUTHENTIC,INCONCLUSIVE,NOT_APPLICABLE}`。`reason_codes` MUST 来自版本化字典；报告生成器只负责解释，不重新判断。pipeline failure 与 scientific `INCONCLUSIVE` MUST 分开编码。

#### Scenario: 状态文件可机器解析且 reason code 受控

- **WHEN** any key subworkflow completes
- **THEN** it emits a status JSON whose fields conform to the allowed enumerations
- **AND** whose `reason_codes` reference a versioned dictionary rather than free text

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
