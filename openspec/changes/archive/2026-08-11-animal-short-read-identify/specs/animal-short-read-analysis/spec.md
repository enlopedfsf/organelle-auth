## ADDED Requirements

### Requirement: 动物 reference pack v0.1 参考治理

动物 `identify` SHALL 使用版本化的 animal reference pack v0.1，并以 `CM084263` 线粒体作为当前判定参考。pack 元数据 MUST 包含：(a) 循环性声明——CM084263 与本次验证数据来自同一 BioProject 派生，一致性结果证明流程可复现性而非独立生物学验证；(b) `NC_023928` 的 `QUARANTINED` 条目，记录 87.6% 分歧、M2-① 的 STOP/REPORT 记录及 Ye et al. (2015) 公共库误鉴定文献依据。QUARANTINED 序列 MUST NOT 进入判定。诊断窗口 MUST 避开 D-loop 高变区与 M2-① 实测组装缺口；每条序列仍需记录 accession、校验和、来源、凭证/文献与 provenance-confidence metadata（DATA-005、SCI-001）。

#### Scenario: CM084263 的循环性被显式披露

- **WHEN** reference pack 被加载或写入 validation record
- **THEN** pack 与记录同时声明 CM084263 和验证数据的 BioProject 派生关系
- **AND** 一致性结论被标注为流程可复现性证据，而不是独立生物学验证

#### Scenario: NC_023928 隔离且不可判定

- **WHEN** 判定引擎解析 animal reference pack
- **THEN** `NC_023928` 的状态为 `QUARANTINED`，并保留 87.6% 分歧与误鉴定考据
- **AND** `NC_023928` 不得作为 mapping、diagnostic-site 或 conflict-rule 的判定输入

#### Scenario: 诊断窗口避开已知风险区

- **WHEN** pack 生成或校验 diagnostic windows
- **THEN** 窗口不落在 D-loop 高变区或 M2-① 记录的 assembly gap
- **AND** 若无法提供足够的非风险可调用窗口，运行输出 `INCONCLUSIVE`，不得扩展到隔离参考或静默改窗

### Requirement: 动物 policy pack 与 production-null 行为

动物 policy pack v0.1 SHALL 独立版本化并声明适用 reference pack。engineering-test policy 的占位阈值 SHALL 按同数据参考的高一致性预期设置，并在文件头记录样本、验证记录、测量范围、选定值、选择理由及“未标定、M3 后替换”的声明。production policy 的规则引用阈值 SHALL 保持 `null`；production 运行 SHALL 在入口 fail-fast，运行时若 null 穿透则输出 `INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED`，不得使用硬编码替代值（ENG-POL-001/002/003/004/005）。

#### Scenario: engineering-test 占位阈值留痕

- **WHEN** engineering-test policy 被加载
- **THEN** 文件头记录其同数据高一致性依据、验证 artifact、测量范围、选定值和未标定状态
- **AND** 输出显著标记为 experimental，不得伪装成 production

#### Scenario: production-null fail-fast

- **WHEN** production policy 的规则引用阈值为 `null`
- **THEN** 运行在产生正式结论前 fail-fast
- **AND** 不得用代码常量、经验数字或 engineering-test 值替换该 `null`

#### Scenario: runtime null 防御

- **WHEN** 任意非 production profile 中单个必需阈值以 `null` 进入 DECISION_ENGINE
- **THEN** 输出 `decision = INCONCLUSIVE` 且 `reason_codes` 含 `THRESHOLD_NOT_CONFIGURED`
- **AND** 不得崩溃或强制输出身份结论

### Requirement: 复用判定骨架与动物门控矩阵

动物 `identify` SHALL 复用 `LOAD_REFERENCE_PACK` / `DECISION_ENGINE` 骨架，并按动物门控矩阵组合 `assembly_grade`、callable diagnostic windows、policy threshold、参考一致性、核 marker 状态和 M2-① 的 NUMT WARN。`DRAFT` 不得被无条件判为不确定：当非风险诊断窗口全部 callable 且 engineering-test policy 规则满足时允许 `AUTHENTIC + WARN + INCOMPLETE_ASSEMBLY`；若 callable 不足、规则冲突、缺少核 marker 输入或阈值为 null，则为 `INCONCLUSIVE`。M2-① `NUMT_RISK_SUSPECTED` 是风险信号，不得单独导出 `NON_AUTHENTIC`。单一距离、单一组装结果或纯 CycloneSEQ 不得终判（SCI-001、SCI-003、SCI-005）。

#### Scenario: DRAFT 但诊断证据可判

- **WHEN** 输入 `assembly_grade = DRAFT`，非风险诊断窗口全部 callable，且 policy/reference 规则满足
- **THEN** 输出允许为 `decision = AUTHENTIC`、`status = WARN`
- **AND** `reason_codes` 含 `INCOMPLETE_ASSEMBLY`，不隐藏结构不完整性

#### Scenario: DRAFT 或 CANDIDATE 证据不足

- **WHEN** 诊断窗口不可调用、证据冲突、核 marker 输入缺失或 policy 阈值为 null
- **THEN** 输出 `decision = INCONCLUSIVE`
- **AND** 不得以全局一致性或 assembly grade 绕过门控

#### Scenario: NUMT WARN 传播

- **WHEN** M2-① `assembly_qc.reason_codes` 含 `NUMT_RISK_SUSPECTED`
- **THEN** identify 保留该风险证据并按 policy 降级或输出 WARN/INCONCLUSIVE
- **AND** 不得仅凭 NUMT WARN 输出 `NON_AUTHENTIC`

#### Scenario: 明确冲突

- **WHEN** 非隔离参考的可调用 diagnostic evidence 按 reference pack conflict rules 明确不一致
- **THEN** 输出 `decision = NON_AUTHENTIC` 及版本化冲突 reason code
- **AND** 该结论不得由单一距离或缺失证据触发

### Requirement: SCI-007 核 marker 输入与状态传播接口

系统 SHALL 提供分类群专用 nuclear-marker panel 的输入契约与状态传播接口：样本显式声明 `taxon_group`、panel identifier/version、输入证据路径、callable 状态、结果摘要与 provenance。M2-② 仅提供空 panel 占位与接口位，MUST NOT 虚构 marker、序列、阈值或判定结果；未声明、空占位或不匹配 panel SHALL 传播为缺失核证据并按门控输出 `INCONCLUSIVE`（SCI-007）。

#### Scenario: 空 panel 不被虚构

- **WHEN** animal sample 没有已批准的 marker panel
- **THEN** 输出中记录 panel 缺失/占位状态
- **AND** 决策引擎不得自动回退 ITS2 或生成虚构 marker 证据

#### Scenario: 核 marker 状态可追踪

- **WHEN** 上游或未来 marker workflow 提供 panel 输入
- **THEN** identify status 传播 panel id/version、callable 状态、证据路径和 provenance
- **AND** panel 证据参与与 reference pack 一致的证据组合规则

### Requirement: `stage = identify` 输出保持 M2-① 接口零偏离

动物 identify SHALL 只读消费 M2-① 冻结的 `animal_sr_assembly/<sample_id>/` FASTA/scaffold、annotation、read-back BAM/depth/flagstat、assembly graph 与 `stage = assembly_qc` status；不得修改其路径、格式、`assembly_grade`、`reason_codes` 或证据文件。identify SHALL 在独立路径输出机器可读 status，设置 `stage = identify`，保留 assembly evidence 并填充 `decision`、identify reason codes、`policy_pack_id` 和 reference/panel provenance（§5.5、DATA-005）。

#### Scenario: 正常识别 status

- **WHEN** M2-① assembly status 可用且 CM084263 pack、policy 与接口输入完整
- **THEN** 输出通过 `assets/schema_status.json` 的 `stage = identify` status
- **AND** `decision` 由组合证据填充，`evidence_files` 非空且可追溯

#### Scenario: 组装失败或低覆盖

- **WHEN** assembly status 为 `FAIL`/`NOT_APPLICABLE`，或低覆盖导致诊断窗口不可调用
- **THEN** 输出 `INCONCLUSIVE` 或明确降级状态并透传上游 reason code
- **AND** 不得将失败、低覆盖或 DRAFT 自动升级为 `NON_AUTHENTIC`

#### Scenario: 参考缺失

- **WHEN** `reference_pack_id` 缺失、不兼容或 pack 文件不存在
- **THEN** 运行在 DECISION_ENGINE 前 fail-fast
- **AND** 不得静默回退公共数据库、QUARANTINED NC_023928 或 de novo 结果（DATA-005）

### Requirement: 三场景验证、reason codes 与 CI 归档硬门

M2-② SHALL 记录 `VALIDATION-animal-identify.md`，覆盖本地真实数据 normal、low-coverage 与 missing-reference 三场景，逐场记录输入、reference/policy、status JSON、预期与实际结果。normal 在 engineering-test policy 下可判定；low-coverage 输出 `INCONCLUSIVE` 或降级；missing-reference fail-fast。新逻辑必须有 T1、动物判定分支 T2、端到端 T3；新增 reason codes 必须入册。**M2-② 归档前 T1–T3 CI 必须全绿（含 M2-① 遗留的镜像问题已解决）**，任一 job 失败、跳过、缺失或镜像不可追溯 SHALL 阻止归档（TEST-001/002/005/006、REL）。

#### Scenario: 三场景预期状态全对

- **WHEN** normal、low-coverage 与 missing-reference 场景按固定输入运行
- **THEN** 实际状态分别符合工程测试可判定、低覆盖不确定/降级、参考缺失 fail-fast 的预期
- **AND** 三场景均无强判越权或静默 fallback

#### Scenario: production-null 复跑

- **WHEN** normal 样本用 production all-null policy 复跑
- **THEN** 结果为 `INCONCLUSIVE` 且含 `THRESHOLD_NOT_CONFIGURED`
- **AND** 不得沿用 engineering-test 占位阈值

#### Scenario: 归档前 CI 门禁

- **WHEN** 用户请求归档 M2-② change
- **THEN** T1、T2、T3 CI 均为 green，M2-① 镜像问题已解决且镜像 digest/日志可追溯
- **AND** `openspec validate --strict` 通过，否则 SHALL 阻止归档
