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

