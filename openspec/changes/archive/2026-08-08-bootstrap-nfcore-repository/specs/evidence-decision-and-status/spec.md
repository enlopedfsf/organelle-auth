## Purpose

定义证据类别、判定规则来源与机器可读状态输出模型，使鉴定结论始终建立在预定义证据组合规则上，并使"无法判定"成为合法的质量输出而非流程失败。

## ADDED Requirements

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
