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

PLANT_SR_ASSEMBLY + ASSEMBLY_QC 完成后 SHALL 输出符合 `assets/schema_status.json`(§5.5)的状态 JSON:`stage = assembly_qc`;`status ∈ {PASS, WARN, FAIL, INCONCLUSIVE}`;`assembly_grade ∈ {CANDIDATE, DRAFT, NOT_APPLICABLE}`(本变更不产出 `REFERENCE`);`decision = NOT_APPLICABLE`(判定逻辑在 M1-②);`reason_codes` 来自版本化字典(如 `NO_CIRCULARIZATION`、`LOW_COVERAGE`、`ASSEMBLY_FAILED`);`evidence_files` 列出本阶段产物。`stage = assembly_qc` 时的字段取值规则在 design.md "①→② 接口合同"中逐字段冻结,作为 M1-② 的输入依据。

#### Scenario: 组装阶段状态符合 schema 且 decision 留空

- **WHEN** 组装 + read-back 完成
- **THEN** 输出的状态 JSON 通过 `schema_status.json` 校验,`stage = assembly_qc`,`decision = NOT_APPLICABLE`,`reason_codes` 引用版本化字典,`evidence_files` 非空
