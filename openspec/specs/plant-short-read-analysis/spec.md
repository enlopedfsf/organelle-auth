# plant-short-read-analysis Specification

## Purpose
定义植物短读长（DNBSEQ）样本的细胞器组装与 read-back 证据子流程及其组装阶段状态输出，作为 M1 的数据生产半（M1-①）。判定逻辑（reference-first identify）由 M1-② 在本域追加；本变更只到 `stage = assembly_qc`，`decision = NOT_APPLICABLE`。
## Requirements
### Requirement: 短读长 QC 子流程（QC_SHORT）

植物短读长样本 SHALL 经 nf-core `fastp` 清洗。fastp 参数（`--detect_adapter_for_pe`、`--qualified_quality_phred 15`、`--length_required 50`，按方法学 §2.1）SHALL 仅存在于 **`experimental` profile**；production profile MUST NOT 把这些未标定的 Q 值/长度/接头阈值作为默认值（ENG-POL-001/002，§5.1）。子流程 SHALL 同时保留原始与清洗后统计。

#### Scenario: fastp 阈值仅在 experimental profile

- **WHEN** 检查 fastp 的 Q 值/长度/接头阈值
- **THEN** 它们只出现在 experimental profile 配置；production profile 中为 `null`，由批准的 policy pack 注入

### Requirement: 植物细胞器组装（PLANT_SR_ASSEMBLY，GetOrganelle 模块）

植物样本 SHALL 用 nf-core `getorganelle/fromreads` 模块(配合 `getorganelle/config` 构建种子库)组装,执行方法学 Scenario A 的两条算法参数集:`-F embplant_pt -R 15 -k 21,45,65,85,105`(叶绿体)与 `-F embplant_nr -k 35,85,115`(nrDNA),由 `targets` 路由。`-R`/`-k` 为 GetOrganelle 算法参数(§9.3 工具算法参数,登记于 tool registry 为 CONDITIONAL),不是科学验收阈值。**科学参数(`-F`/`-R`/`-k`)逐字对齐 Scenario A;仅参考库交付改为预构建固定 db(`--config-dir`),非科学方法改变。** 模块 SHALL 输出叶绿体 FASTA、nrDNA FASTA 与 `versions.yml`,并经本地输出适配模块产出①→②接口合同约定的路径与环化判定。系统 MUST NOT 因期望叶绿体为圆形而强行闭环——未环化时输出 scaffold 并标 `DRAFT`(§5.2)。

#### Scenario: GetOrganelle 双目标算法参数与 Scenario A 一致

- **WHEN** 植物样本进入 PLANT_SR_ASSEMBLY
- **THEN** 对叶绿体执行 `-F embplant_pt -R 15 -k 21,45,65,85,105`、对 nrDNA 执行 `-F embplant_nr -k 35,85,115`(经 `ext.args` 注入,逐字),并输出 `versions.yml`

#### Scenario: 低覆盖不强环化

- **WHEN** 组装未能环化(数据量不足/降解)
- **THEN** 输出 scaffold 并标 `assembly_grade = DRAFT`,MUST NOT 强行选择闭环路径

### Requirement: Read-back 证据（ASSEMBLY_QC）

clean reads SHALL 用 `minimap2 -ax sr` 回贴组装结果(§3.5;且与未来长读长路线保持一致),随后 `samtools depth`/`flagstat` 产出覆盖度与均一度指标。覆盖洼地判定系数(局部深度 < 全序列中位数 × 系数)是**科学阈值,从 policy pack 读取**;experimental profile 下为 `null` 时 SHALL 仅标注、不得硬编码数字。产出(BAM、depth、flagstat、组装 FASTA、GetOrganelle 组装图)SHALL 写入状态输出的 `evidence_files`。

#### Scenario: 覆盖阈值来自 policy 而非硬编码

- **WHEN** 进行覆盖洼地判定
- **THEN** 系数从 policy pack 读取;experimental profile 下为 `null` 时该区域标注草稿级,代码与配置中不存在硬编码科学阈值

### Requirement: 组装阶段状态输出（stage = assembly_qc）

PLANT_SR_ASSEMBLY + ASSEMBLY_QC 完成后 SHALL 输出符合 `assets/schema_status.json`(§5.5)的状态 JSON:`stage = assembly_qc`;`status ∈ {PASS, WARN, FAIL, INCONCLUSIVE}`;`assembly_grade ∈ {CANDIDATE, DRAFT, NOT_APPLICABLE}`(本变更不产出 `REFERENCE`);`decision = NOT_APPLICABLE`(判定逻辑在 M1-②);`reason_codes` 来自版本化字典(如 `NO_CIRCULARIZATION`、`ASSEMBLY_FAILED`);`evidence_files` 列出本阶段产物。`stage = assembly_qc` 时的字段取值规则在 design.md "①→② 接口合同"中逐字段冻结,作为 M1-② 的输入依据。

#### Scenario: 组装阶段状态符合 schema 且 decision 留空

- **WHEN** 组装 + read-back 完成
- **THEN** 输出的状态 JSON 通过 `schema_status.json` 校验,`stage = assembly_qc`,`decision = NOT_APPLICABLE`,`reason_codes` 引用版本化字典,`evidence_files` 非空

### Requirement: 植物短读长判定子流程（IDENTIFY，reference-first）

`analysis_mode = identify` 的植物样本 SHALL 进入 `IDENTIFY` 子流程：消费 ① 的冻结产出（选中的叶绿体 FASTA `*_plastome.fasta` / `*_plastome.scaffold.fasta`、read-back 证据 `readback/*.{sorted.bam,depth.tsv,flagstat.txt}`、`getorganelle/<sample_id>_assembly_graph.fastg`、以及 `stage = assembly_qc` 状态中的 `assembly_grade` 与 `reason_codes`），对照已加载的 `reference_pack` 完成 reference-first 判定，产出 `stage = identify` 的新状态并填充 `decision`。判定 SHALL 按 §5.3 的 reference-first 顺序：参考映射/检索 → callable-region 评估 → diagnostic-site 证据 → 分类/似然证据 → 判定引擎；de novo 回退仅在四个条件全部满足时启动且标 `candidate/inconclusive`。② MUST NOT 修改 ① 的产出路径或格式（冻结接口合同）。

#### Scenario: IDENTIFY 消费 ① 冻结产出且不改其路径

- **WHEN** 一个 `identify` 植物样本完成 ① 的 `assembly_qc`
- **THEN** `IDENTIFY` 读取 ① 选中的叶绿体 FASTA、read-back 证据与 `assembly_qc` 状态
- **AND** 不修改 ① 产出物的路径或格式
- **AND** 产出 `stage = identify` 状态，`decision` 非 `NOT_APPLICABLE`（除非直通场景）

#### Scenario: reference-first 顺序，单一距离阈值不强判

- **WHEN** 判定引擎评估一个样本
- **THEN** 结论建立在 callable-region 覆盖 + diagnostic-site 一致性的证据组合上（SCI-001）
- **AND** MUST NOT 仅凭单一 mash/ANI 距离阈值或单个组装结果强制判定

### Requirement: assembly_grade ↔ decision 门控（锚定 SCI-001/SCI-005）

`IDENTIFY` SHALL gate `decision` by `assembly_grade` and evidence strength. `DRAFT +` all reference-pack `diagnostic_sites` callable and consistent `+` adequate `callable_coverage` `+` adequate `mean_readback_depth` `→ AUTHENTIC + WARN [INCOMPLETE_ASSEMBLY]`. If the only failing condition is `callable_coverage < min_callable_fraction`, the reason code SHALL be `LOW_CALLABLE_COVERAGE`. If the only failing condition is `mean_readback_depth < min_mean_depth`, the reason code SHALL be `LOW_SEQUENCING_DEPTH`.

#### Scenario: DRAFT + 诊断位点全部 callable + 充足覆盖 → AUTHENTIC + WARN
- **WHEN** ① outputs `assembly_grade = DRAFT`, all diagnostic sites are callable and consistent, `callable_coverage` meets the policy threshold, and `mean_readback_depth` meets the policy threshold
- **THEN** `decision = AUTHENTIC`, `status = WARN`, `reason_codes` contains `INCOMPLETE_ASSEMBLY`
- **AND** the report honestly notes “identity confirmed but assembly structure incomplete”

#### Scenario: 诊断位点落缺失区 → INCONCLUSIVE（即使全局一致性高）
- **WHEN** 全局一致性高，但参考 pack 的诊断位点落在组装缺失/不可判区
- **THEN** `decision = INCONCLUSIVE`，`reason_codes` 含 `DIAGNOSTIC_SITES_NOT_CALLABLE`
- **AND** MUST NOT 仅凭已组装部分的全局一致性输出 `AUTHENTIC`

#### Scenario: 一致性低于阈值 → NON_AUTHENTIC
- **WHEN** 诊断位点一致性明显低于 reference-pack `conflict_rules` 阈值
- **THEN** `decision = NON_AUTHENTIC`，`reason_codes` 含 `IDENTITY_BELOW_THRESHOLD`

#### Scenario: ① 不可用 → 直通 INCONCLUSIVE
- **WHEN** ① `assembly_grade = NOT_APPLICABLE` 或 `status = FAIL`
- **THEN** `decision = INCONCLUSIVE`，`IDENTIFY` 不进行身份判定

#### Scenario: callable 覆盖不足 → INCONCLUSIVE + LOW_CALLABLE_COVERAGE
- **WHEN** `callable_coverage` is below the policy `min_callable_fraction`
- **THEN** `decision = INCONCLUSIVE`
- **AND** `reason_codes` contains `LOW_CALLABLE_COVERAGE`
- **AND** `reason_codes` does NOT contain `LOW_COVERAGE`

#### Scenario: 测序深度不足 → INCONCLUSIVE + LOW_SEQUENCING_DEPTH
- **WHEN** `mean_readback_depth` is below the policy `min_mean_depth`
- **THEN** `decision = INCONCLUSIVE`
- **AND** `reason_codes` contains `LOW_SEQUENCING_DEPTH`
- **AND** `reason_codes` does NOT contain `LOW_COVERAGE`

### Requirement: 判定阈值来自 policy（null → INCONCLUSIVE，模块层不崩溃）

`IDENTIFY` 的判定阈值（`callable_site`、`uncertainty_zone`）SHALL 从 policy pack 读取，MUST NOT 硬编码科学阈值。当 identify 模块在运行时遇到 `null`/未标定阈值时，SHALL 输出 `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]` 且 **MUST NOT 崩溃或强制判定**（SCI-005 防御层）。此模块层行为与 `ENG-POL-002`（production 启动配置门对 null 阈值 fail-fast）并存：启动门在 production launch 时拒绝 null policy；模块层在运行时遇 null 输出 `INCONCLUSIVE` 而非抛错——两层防御，互不替代。

#### Scenario: null 阈值 → INCONCLUSIVE + reason code，不崩溃

- **WHEN** identify 模块运行时加载的 policy 含 `null` 判定阈值（如 experimental / production 配置失误）
- **THEN** 输出 `decision = INCONCLUSIVE`，`reason_codes` 含 `THRESHOLD_NOT_CONFIGURED`
- **AND** 流程不抛未捕获异常、不强制产出 AUTHENTIC/NON_AUTHENTIC

#### Scenario: 阈值从 policy 读取而非硬编码

- **WHEN** 检查 identify 判定代码与配置
- **THEN** `callable_site`/`uncertainty_zone` 取值来自 policy pack，代码中不存在硬编码科学阈值数字

### Requirement: reference pack 加载与缺失快速失败（DATA-005）

`IDENTIFY` SHALL 按 samplesheet 的 `reference_pack_id` 加载 `reference_pack`；缺失或版本不兼容时 SHALL 快速失败，MUST NOT 静默回退到任何公共数据库（DATA-005）。判定规则（`required_evidence`/`supporting_evidence`/`conflict_rules`/`callable_regions`/`diagnostic_sites`/`uncertainty_rules`/`known_exceptions`/`nuclear_evidence_requirement`，§7.2）SHALL 从 reference pack 读取，MUST NOT 把“正品四要素全部一致”等自然语言硬编码进流程（SCI-001）。

#### Scenario: 缺/不兼容 reference pack 快速失败

- **WHEN** `identify` 请求的 `reference_pack_id` 缺失或版本不兼容
- **THEN** 运行快速失败
- **AND** MUST NOT 回退到默认公共数据库

#### Scenario: 判定规则读取自 reference pack

- **WHEN** 判定引擎应用规则
- **THEN** 规则来自已加载的 `reference_pack`，而非流程内硬编码的自然语言规则

### Requirement: 污染信号不强判 AUTHENTIC

When ① emits a validated contamination or coverage-anomaly signal, `IDENTIFY` SHALL output `INCONCLUSIVE + [CONTAMINATION_SUSPECTED]`, MUST NOT force `AUTHENTIC`. Until such a signal is implemented and validated, `CONTAMINATION_SUSPECTED` is dormant: the current ①/② flow does not detect cross-kingdom animal×plant mixtures at the plastome-recruitment level, and formal contamination validation MUST use close-relative plant mixtures together with the Kraken2 self-built DB change.

#### Scenario: 污染信号 → INCONCLUSIVE，不得强判
- **WHEN** ① emits a validated contamination or coverage-anomaly signal
- **THEN** `decision = INCONCLUSIVE`, `reason_codes` contains `CONTAMINATION_SUSPECTED`
- **AND** MUST NOT output `AUTHENTIC` even if single-reference identity is high

#### Scenario: 当前污染路径 dormant
- **WHEN** a cross-kingdom animal×plant mixture is processed by the current flow
- **THEN** the contamination is not detected at the plastome-recruitment step
- **AND** `CONTAMINATION_SUSPECTED` is not emitted
- **AND** the dormancy and reactivation plan are documented in the change design

### Requirement: 判定阶段状态输出（stage = identify）

`IDENTIFY` 完成后 SHALL 输出符合 `assets/schema_status.json` 的状态 JSON：`stage = identify`；`status ∈ {PASS, WARN, FAIL, INCONCLUSIVE}`；`decision ∈ {AUTHENTIC, NON_AUTHENTIC, INCONCLUSIVE, NOT_APPLICABLE}`（`NOT_APPLICABLE` 仅用于直通场景）；`assembly_grade` 透传 ① 的取值；`reason_codes` 来自版本化字典（本变更新增 `THRESHOLD_NOT_CONFIGURED`/`IDENTITY_BELOW_THRESHOLD`/`CONTAMINATION_SUSPECTED`/`INCOMPLETE_ASSEMBLY`/`DIAGNOSTIC_SITES_NOT_CALLABLE`）；`evidence_files` 列出本阶段产物（含 ① 证据与判定证据）。pipeline failure 与 scientific `INCONCLUSIVE` MUST 分开编码。

#### Scenario: 判定阶段状态符合 schema 且 decision 已填

- **WHEN** `IDENTIFY` 完成
- **THEN** 输出的状态 JSON 通过 `schema_status.json` 校验，`stage = identify`，`decision` 已填充（非 `NOT_APPLICABLE`，除非直通）
- **AND** `reason_codes` 引用版本化字典（含本变更新增码），`evidence_files` 非空

#### Scenario: reason code 来自受控字典且新增码登记

- **WHEN** `IDENTIFY` 发出 reason code
- **THEN** 该码定义于版本化 `reason_codes.yaml`（含 `THRESHOLD_NOT_CONFIGURED`/`IDENTITY_BELOW_THRESHOLD`/`CONTAMINATION_SUSPECTED`/`INCOMPLETE_ASSEMBLY`/`DIAGNOSTIC_SITES_NOT_CALLABLE`），非自由文本
