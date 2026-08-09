# Tasks: animal-short-read-assembly-evidence (M2-①)

## 1. 动物路由 + 组装子流程 ANIMAL_SR_ASSEMBLY

- [x] 1.1 自建本地 `mitofinder` 模块（Docker 容器、`versions.yml`、stub）——遵循 §12.3 local module 规范；`registries/tools.yaml` 中 `mitofinder_mitoz` 条目填 `container_digest`（admission 保持 CONDITIONAL）
- [x] 1.2 多参考诱饵提取步骤：`minimap2 -x sr` 对 bundled 多参考线粒体集提取候选 reads（决策 2/3；参考集 provenance 记录 accession + 校验和）
- [x] 1.3 本地输出适配模块 `animal_result_adapter`：CANDIDATE/DRAFT 分级、接口合同路径命名、收集注释与组装图（决策 5）
- [x] 1.4 组装 `ANIMAL_SR_ASSEMBLY` subworkflow（bait 提取 → MitoFinder 组装+注释 → 输出适配），复用 `QC_SHORT`/`ASSEMBLY_QC`

## 2. NUMT 风险筛查（最小版）

- [x] 2.1 本地 `numt_risk_screen` 模块：覆盖异质性（洼地 vs 中位数×policy 系数）+ 多重比对/异常深度信号（决策 6）
- [x] 2.2 `assets/reason_codes.yaml` 新增 `NUMT_RISK_SUSPECTED`（WARN 类别），version 递增
- [x] 2.3 NUMT 信号接入 `assembly_qc` 状态：检出 → `status=WARN` + `reason_codes=[NUMT_RISK_SUSPECTED]`，无信号不 emit

## 3. 状态输出（stage = assembly_qc）

- [x] 3.1 动物样本走复用 `ASSEMBLY_QC`，read-back 证据（BAM/depth/flagstat）产出
- [x] 3.2 动物 `assembly_qc` 状态发射：按 design "①→② 接口合同" 第 1/2/3 节逐字段冻结（`decision=NOT_APPLICABLE`、`evidence_files` 非空、动物与植物路径隔离）

## 4. 路由接入 ORGANELLEAUTH workflow

- [x] 4.1 新增动物 filter：`taxon_group=='animal' && has_short_reads && targets.contains('mitome')`（§3.3 / DATA-006）
- [x] 4.2 确认植物分支零改动、回归无损（植物 filter 原样保留）

## 5. 测试（T1–T3）

- [x] 5.1 T1：`mitofinder` 模块 nf-test（正常输入 + 失败/边界输入）
- [x] 5.2 T1：`numt_risk_screen` 模块 nf-test（检出信号 → WARN；无信号 → 不 emit）
- [x] 5.3 T1：`animal_result_adapter` 模块 nf-test（CANDIDATE/DRAFT 两分支 + 命名）
- [x] 5.4 T2：动物路由分支测试（animal → ANIMAL_SR_ASSEMBLY → assembly_qc 状态传播）
- [x] 5.5 T3：动物端到端微型数据 stub smoke（CI），含状态 JSON schema 校验
- [x] 5.6 植物 T3 回归确认（stub smoke 仍绿）

## 6. 真实数据验证（本地，留记录）

- [x] 6.1 准备 bait 多参考集（下载 ≥5 条 *W. acranulata* 完整线粒体，如 `NC_023928`/`KC688271`/`MK347500`/`CM084263`/`OQ076773`；记录 provenance + 来源凭证可信度 metadata——考据 (b)）
- [x] 6.2 正常场景：`SRR27841063` 抽稀 ~2 Gb 端到端（`-profile engineering_test,docker` 或对应 experimental），组装 + read-back + NUMT 筛查
- [x] 6.3 低覆盖场景：~0.5 Gb（proportion ~0.25, seed 固定）端到端，记录组装分级与 NUMT 信号
- [x] 6.4 一致性 vs 独立研究参考 `NC_023928`：mash / dnadiff；**预期 <100%（个体变异为真实生物学，考据 (a)）**；若 <95% → STOP 并报告，不得自动重跑调参
- [x] 6.5 写 `VALIDATION-animal.md`（镜像 M1-① `VALIDATION-7.1.md` 格式：Run / 结果 / 一致性 / 覆盖 / 分级与 NUMT 信号 / **两条参考考据 (a)(b) 全文** / 已知局限）

## 7. 归档与提交

- [x] 7.1 `openspec validate --all` 全绿（含新 spec 域）
- [x] 7.2 归档 change（`openspec archive animal-short-read-assembly-evidence`），spec 并入 `openspec/specs/animal-short-read-analysis/spec.md`
- [x] 7.3 提交（descriptive message 以 `Co-Authored-By: Claude <noreply@anthropic.com>` 结尾）
