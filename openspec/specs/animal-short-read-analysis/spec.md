# animal-short-read-analysis Specification

## Purpose
定义动物短读长（DNBSEQ）样本的线粒体组装、read-back 证据与 NUMT 风险筛查子流程及其组装阶段状态输出，作为 M2 的数据生产半（M2-①）。判定逻辑（reference-first identify）由 M2-② 在本域追加；本变更只到 `stage = assembly_qc`，`decision = NOT_APPLICABLE`。M2-① maximally 复用 M1 植物分支（QC_SHORT 的 fastp、ASSEMBLY_QC 的 read-back、status 模型），只新增动物特有部分。
## Requirements
### Requirement: 动物短读长组装（ANIMAL_SR_ASSEMBLY，MitoFinder 路线）

`taxon_group = animal` 且有短读长、`targets ⊇ {mitome}` 的样本 SHALL 经显式路由（§3.3 / DATA-006）进入与植物相同的 `QC_SHORT`（nf-core `fastp`，参数与 experimental-only 规则同植物）清洗，然后进入 `ANIMAL_SR_ASSEMBLY`。组装 SHALL 按方法学 §3.3/§4.3 适配短读长执行：先用 `minimap2 -x sr` 对一组 circumscribed 线粒体参考（多参考）提取候选线粒体 reads——单一参考可能漏掉高度分化的控制区 D-loop，而 D-loop 恰是动物药鉴定的高变区（§4.3），再以 MitoFinder（工具准入 `mitofinder_mitoz`，CONDITIONAL，dnbseq）组装 + 注释 + 基因排序标准化（§3.3）。MitoFinder 的算法/运行参数是工具算法参数（§9.3，登记于 tool registry），不是科学验收阈值；科学参数逐字对齐方法学。本地输出适配模块 SHALL 按 ①→② 接口合同路径命名并判定环化：单环状 contig → `CANDIDATE`，scaffold/线性 → `DRAFT`。系统 MUST NOT 因期望线粒体为环状而强行闭环——未环化时输出 scaffold 并标 `DRAFT`（§3.6 / SCI-005）。模块 SHALL 输出线粒体 FASTA、注释、组装图与 `versions.yml`。

#### Scenario: 动物样本路由到 MitoFinder 分支

- **WHEN** 一个样本 `taxon_group=animal`、有短读长、`targets` 含 `mitome`
- **THEN** 样本经与植物相同的 `QC_SHORT` 清洗，进入 `ANIMAL_SR_ASSEMBLY` 的 MitoFinder 路线，输出 `versions.yml`
- **AND** 路由仅依据显式字段，不从文件名/样本描述推断（DATA-006）

#### Scenario: 多参考提取避免 D-loop 漏检

- **WHEN** 组装前提取候选线粒体 reads
- **THEN** 使用多参考（circumscribed 线粒体参考集）而非单一参考做 `minimap2 -x sr` 诱饵提取
- **AND** 单一参考可能漏掉的高变控制区（D-loop）不作为流程静默丢弃理由

#### Scenario: 低覆盖不强环化

- **WHEN** 组装未能环化（数据量不足/降解）
- **THEN** 输出 scaffold 并标 `assembly_grade = DRAFT`，MUST NOT 强行选择闭环路径

### Requirement: Read-back 证据（ASSEMBLY_QC，复用植物路线）

动物组装结果 SHALL 用与植物相同的 read-back 子流程：clean reads 用 `minimap2 -ax sr` 回贴组装结果（§3.5），随后 `samtools depth`/`flagstat` 产出覆盖度与均一度指标。覆盖洼地判定系数（局部深度 < 全序列中位数 × 系数）是**科学阈值，从 policy pack 读取**；experimental profile 下为 `null` 时 SHALL 仅标注、不得硬编码数字。产出（BAM、depth、flagstat、组装 FASTA、组装图）SHALL 写入状态输出的 `evidence_files`。

#### Scenario: 覆盖阈值来自 policy 而非硬编码

- **WHEN** 进行动物组装结果的覆盖洼地判定
- **THEN** 系数从 policy pack 读取；experimental profile 下为 `null` 时该区域标注草稿级，代码与配置中不存在硬编码科学阈值

### Requirement: NUMT 风险筛查（最小版）

`ANIMAL_SR_ASSEMBLY` + read-back 完成后 SHALL 对线粒体组装结果执行**最小版 NUMT 风险筛查**（方法学 §3.3 NUMT 排检的首步）：基于回贴 reads 检查**覆盖异质性**（覆盖洼地区域 vs 全序列中位数）与**多重比对/异常深度信号**。筛查检出信号时 SHALL 在 `assembly_qc` 状态输出 **WARN 级 reason code**（如 `NUMT_RISK_SUSPECTED`），MUST NOT 因此强制判定。本版筛查 SHALL 明确标注为**风险筛查而非 NUMT 确证**；确证方法（核基因组侧翼序列检查、蛋白编码基因提前终止密码子/移码检查、长读长证据，方法学 §3.3）在 change design 的 known limitations 中记录，属后续 change 范围。

#### Scenario: 覆盖/多重比对信号 → WARN reason code

- **WHEN** NUMT 风险筛查在组装结果的覆盖洼地或多重比对信号中发现异常
- **THEN** `assembly_qc` 状态 `status = WARN`，`reason_codes` 含 `NUMT_RISK_SUSPECTED`
- **AND** 不产出 `AUTHENTIC`/`NON_AUTHENTIC`（本阶段 `decision = NOT_APPLICABLE`）

#### Scenario: 无信号不 emit

- **WHEN** 回贴覆盖均一、多重比对信号正常
- **THEN** `NUMT_RISK_SUSPECTED` 不出现于 `reason_codes`，状态不受影响

### Requirement: 组装阶段状态输出（stage = assembly_qc）

`ANIMAL_SR_ASSEMBLY` + read-back + NUMT 风险筛查完成后 SHALL 输出符合 `assets/schema_status.json`（§5.5）的状态 JSON：`stage = assembly_qc`；`status ∈ {PASS, WARN, FAIL, INCONCLUSIVE}`；`assembly_grade ∈ {CANDIDATE, DRAFT, NOT_APPLICABLE}`（本变更不产出 `REFERENCE`）；`decision = NOT_APPLICABLE`（判定逻辑在 M2-②）；`reason_codes` 来自版本化字典（如 `NO_CIRCULARIZATION`、`NUMT_RISK_SUSPECTED`、`ASSEMBLY_FAILED`）；`evidence_files` 列出本阶段产物。`stage = assembly_qc` 时的动物字段取值规则在 design.md "①→② 接口合同"中逐字段冻结，作为 M2-② 的输入依据。动物与植物输出在 `outdir` 下路径 MUST NOT 冲突（按样本/目标隔离）。

#### Scenario: 组装阶段状态符合 schema 且 decision 留空

- **WHEN** 动物组装 + read-back + NUMT 筛查完成
- **THEN** 输出的状态 JSON 通过 `schema_status.json` 校验，`stage = assembly_qc`，`decision = NOT_APPLICABLE`，`reason_codes` 引用版本化字典，`evidence_files` 非空

#### Scenario: 动物与植物输出路径隔离

- **WHEN** 同一运行同时含植物与动物短读长样本
- **THEN** 两组产出路径不冲突、各自独立可寻址，任一分支失败不影响另一分支的状态输出

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

