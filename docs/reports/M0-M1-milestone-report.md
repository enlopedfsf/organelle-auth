# organelle-auth — M0 & M1 里程碑报告 / Milestone Report

> Pipeline: `enlopedfsf/organelle-auth` (内部名 `organelleauth`, 主干 `dev`)
> 总方案 / master spec: v1.1.1 (`docs/specification/`)
> 报告日期 / Date: 2026-08-09
> 证据优先级 / Evidence-first: 本文所有判定均锚定 OpenSpec 归档 change 与实测数据，不锚"能不能跑" / Every verdict is anchored to archived OpenSpec changes and measured data, not to "does it run".

---

## 0. 里程碑地图 / Milestone map

| 里程碑      | OpenSpec 归档 change                            | 性质 / Nature                              | 状态                       |
| ----------- | ----------------------------------------------- | ------------------------------------------ | -------------------------- |
| **M0-1**    | `2026-08-08-bootstrap-nfcore-repository`        | 工程骨架 / Engineering skeleton            | ✅ 归档 (dbbb430)          |
| **M0-2**    | `2026-08-08-define-core-contracts`              | 可执行合同 / Executable contracts          | ✅ 归档 (83b48a7)          |
| **M1-①**    | `2026-08-09-plant-short-read-assembly-evidence` | 数据生产半 / Assembly + read-back evidence | ✅ 归档 (ab4a1a9)          |
| **M1-②**    | `2026-08-09-plant-short-read-identify`          | 判定半 / Reference-first identify          | ✅ 归档 (2a49c2f)          |
| **M1 收尾** | `2026-08-09-m1-closeout-identify-honesty`       | 诚实性修正 / Honesty close-out             | ✅ 归档 (5514e15, 729c81b) |

判定阶梯总览 / Decision ladder at a glance (M1 最终态):

```
rung1 ① 不可用 passthrough ──→ INCONCLUSIVE (透传 ① reason)
rung2 污染门径 (COVERAGE_ANOMALY) ──→ CONTAMINATION_SUSPECTED   【DORMANT】
rung3 null 阈值 ──→ THRESHOLD_NOT_CONFIGURED
rung4 诊断位点不可判 ──→ DIAGNOSTIC_SITES_NOT_CALLABLE
rung5a callable_coverage < min ──→ LOW_CALLABLE_COVERAGE
rung5b mean_readback_depth < min ──→ LOW_SEQUENCING_DEPTH
identity ladders ──→ NON_AUTHENTIC / 灰区 / AUTHENTIC(+WARN[INCOMPLETE_ASSEMBLY] for DRAFT)
```

---

# 第一部分 · M0 — 工程骨架与可执行合同 / Part I · M0 — Skeleton & Contracts

> **M0 的本质 / What M0 actually is**: 在写任何一行分析逻辑之前，先把**科学方法的不可变约束**翻译成机器可校验的合同，并用 CI 守住它。M0 产出 **0 个分析模块、0 个科学阈值**——这是它的设计目标，不是缺陷。零分析逻辑、全 `null` 阈值，是"证据优先"纪律的第一道防线。
>
> **The essence of M0**: before any analysis logic is written, the **immutable constraints of the scientific method** are translated into machine-checkable contracts and guarded by CI. M0 ships **zero analysis modules and zero scientific thresholds** — that is its design goal, not a gap. Zero logic + all-`null` thresholds is the first line of "evidence-first" discipline.

## M0-1 · bootstrap-nfcore-repository — nf-core 骨架与治理 / Skeleton & governance

### 产出物 / Deliverables

1. **nf-core 模板 / template** (`nf-core pipelines create --name organelleauth`)
   - nf-core tools 4.1.0, Nextflow 26.04.6; `manifest.nextflowVersion = '!>=25.10.4'`。
   - 原始 vanilla 提交 `b543f3d`,内部名 `organelleauth`(nf-core 禁连字符；repo 名 `organelle-auth`,**命名坑**,详见 [[project_organelle_auth]])。

2. **5 个 spec 域 / 5 spec domains** (OpenSpec) — 这是 M0 最关键的设计资产 / the single most important M0 design asset:

   | 域 / Domain                    | 职责 / Responsibility                                               |
   | ------------------------------ | ------------------------------------------------------------------- |
   | `scope-routing-and-input`      | 样本路由、samplesheet 真值禁入、preflight fail-fast (DATA-001..007) |
   | `asset-tool-and-policy`        | 工具准入、假设状态机、policy null 纪律 (ENG-POL-001..005, HYP)      |
   | `evidence-decision-and-status` | 状态模型、reason-code 字典、证据组合判定 (SCI-001..009)             |
   | `validation-and-go-no-go`      | 诊断位点独立发现/验证、测试矩阵 (SCI-010, TEST-001..007)            |
   | `provenance-and-release`       | 兼容性清单独立版本化、审计包 (REL)                                  |

3. **可追溯性矩阵 / Traceability matrix** — `openspec/traceability.yaml`,**34 个 Requirement ID**(SCI×10, DATA×7, ENG-POL×5, TEST×7, REL×4, HYP×1),每个 ReqID 唯一映射到一个 spec 域,并标注 `implementation_area / engineering_test / scientific_validation / release_evidence` 四阶段。**M0 中每条都是 `planned`,不标 `validated` 无证据**——CI (`spec-and-schema.yml`) 双向交叉校验:本文每个 ID 都出现在某 spec delta 中,spec 引用的每个 ID 都在此矩阵中。

4. **精益 M0 CI / Lean CI** — 3 个 workflow:`spec-and-schema`(OpenSpec + JSON Schema 校验)、`linting`、`template-check`。注意:**刻意不放 nf-core lint 全量门**(本地 `nf-core pipelines lint` 会 hang,改用 CI 验证;[[project_organelle_auth]])。

5. **治理模板 / Governance** — `CODEOWNERS`、PR 模板(7 字段)、6 个 issue 模板。

### M0-1 真正做了什么 / What M0-1 actually does

把"方法学 §2.1 的科学约束"从自然语言**升级为工程可执行物**:不再是写在文档里靠人遵守,而是**一个 ReqID 漏进 spec、CI 就红**。这把后续每个里程碑(M1~M5)锁死在同一条主干道上——任何 change 都必须经过 propose → spec-delta → tasks → archive 闭环。

---

## M0-2 · define-core-contracts — 合同的具体内容 / The concrete contracts

M0-1 是骨架,M0-2 把骨架引用的**占位合同填成可校验文件**。仍 **0 分析逻辑、全 `null` 阈值**(ENG-POL-001/002)。

### ① samplesheet schema — `assets/schema_input.json`

12 个字段(§4.1),enum + 条件必填。关键守则:

- **DATA-001**:所有字段过 JSON Schema 才能创建分析 channel。
- **DATA-003**:**分析 samplesheet 禁含真值**;truthset.csv 只在揭盲评价时加载。这是防"训练/验证数据泄漏进判定"的硬合同。
- **DATA-005**:缺 reference pack / 版本不兼容 → fail-fast,**不得静默回退任何公共数据库**。

### ② status schema — `assets/schema_status.json` (§5.5)

逐样本机器可读状态对象:

```
status ∈ {PASS, WARN, FAIL, INCONCLUSIVE}
assembly_grade ∈ {REFERENCE, DRAFT, CANDIDATE, NOT_APPLICABLE}
decision ∈ {AUTHENTIC, NON_AUTHENTIC, INCONCLUSIVE, NOT_APPLICABLE}
reason_codes: array  (来自版本化字典,非自由文本)
evidence_files: array
```

**关键设计**:pipeline failure(工程失败)与 scientific INCONCLUSIVE(科学灰区)**分开编码**——一个机器崩了 ≠ 一个样本无法判定。这是 SCI-005 的工程体现。

### ③ reason-code 字典框架 — `assets/reason_codes.yaml`

版本化(M0: `0.1.0` 框架 + 3 示例码)。四类别:`scientific_inconclusive` / `warn` / `engineering_fail` / `non_authentic`。**报告生成器只解释码、不重新判定**——判定只发生在 decision engine 一处。

### ④ 工具准入注册表 — `registries/tools.yaml` (§8.3)

13 个首版候选工具 + **PROHIBITED 区**:

| 准入层 / Tier          | 工具 / Tools                                                                                                          |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------- |
| APPROVED (仅描述性 QC) | NanoPlot                                                                                                              |
| CONDITIONAL            | fastp, Kraken2(+自建库), GetOrganelle, MitoFinder/MitoZ                                                               |
| EXPERIMENTAL           | NOVOPlasty, Flye, PMAT2, Racon, Polypolish, bcftools-consensus                                                        |
| DEFERRED               | NextPolish2, GeSeq/PlastidHub                                                                                         |
| **PROHIBITED**         | **medaka, Nanopolish, Clair3-ONT**(ONT 模型绑定,无 CycloneSEQ 兼容模型);**Oatk, TIPPo, MitoHiFi, hifiasm**(HiFi-only) |

> PROHIBITED ≠ DEFERRED:前者是**当前因科学理由禁止**(方法学 §7.2 模型绑定档),后者是**暂不可评估、有证据即可激活**。CI grep 断言 PROHIBITED 工具不出现在 `modules/` + `conf/`。

### ⑤ 假设注册表 — `registries/hypotheses.yaml` (§9.4)

状态机 `proposed → under_validation → validated|rejected → superseded`。转录 HYP-DNA-001 完整条目:**按提取 DNA 片段分布划分长读长适用档(≥25kb / 10–<25kb / <10kb),且区分"片段分布"与"read N50"**。这是后续 M3 CycloneSEQ 路由的依据。

### ⑥ policy 框架 + production-null 夹具

- 框架 + 一个 experimental 示例 `policies/tcm-plant-experimental.yaml`(所有阈值 `null`)。
- **production-null 拒绝 (ENG-POL-002)**:production 启动配置门遇 null → fail-fast;模块层遇 null → `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]`。**两层防御,互不替代**。

### M0 交付小结 / M0 deliverables summary

| 维度           | 产出                                                                           |
| -------------- | ------------------------------------------------------------------------------ |
| 分析模块       | **0** (设计如此 / by design)                                                   |
| 科学阈值       | **0** (全 `null`)                                                              |
| spec 域        | 5                                                                              |
| 可追溯 ReqID   | 34                                                                             |
| 可执行合同文件 | schema_input / schema_status / reason_codes / tools / hypotheses / policy 框架 |
| CI 门          | 3 workflow + PROHIBITED grep + schema 双向校验                                 |

---

# 第二部分 · M1 — 植物短读长组装证据与身份判定 / Part II · M1 — Plant Short-Read Evidence & Identify

> **M1 的两半结构**:① 生产**证据**(组装 + 回贴),只到 `stage=assembly_qc`,**不做身份判定**(`decision=NOT_APPLICABLE`);② 消费 ① 冻结产出做 **reference-first 判定**,填 `decision`。② **不得修改 ① 的产出路径或格式**——这是冻结的接口合同,保证判定逻辑可独立审计/重跑。
>
> **Why split ①/②**: 把"数据生产"(可缓存、可复算)与"身份判定"(随 reference/policy 变化)解耦,判定层永远可基于冻结证据重算,不必重跑组装。

## M1-① · plant-short-read-assembly-evidence — 组装 + 回贴证据

### 数据流 / Data flow (3 个子流程)

```
QC_SHORT (fastp)  ──→  PLANT_SR_ASSEMBLY (GetOrganelle)  ──→  ASSEMBLY_QC (minimap2 + samtools)
  清洗 reads            叶绿体 embplant_pt / nrDNA embplant_nr     回贴组装 → 覆盖度/均一度
                                                                    → stage=assembly_qc 状态 JSON
```

### 真实数据实测 / Real-data evidence — 刻叶紫堇 _Corydalis ophiocarpa_ SRR38978846

| 项 / Item | 值 / Value                                                                                                    |
| --------- | ------------------------------------------------------------------------------------------------------------- |
| 样本      | `SRR38978846` (DNBSEQ 短读长)                                                                                 |
| 抽稀      | ~~2.0 Gb, seed 11 → 6,671,740 PE reads (输入一律抽稀~~2Gb,见 [[feedback_organelle_auth_subsample_input]])     |
| 参考      | `PZ405204.1` (200,540 bp,同种完整环状叶绿体)                                                                  |
| Profile   | `experimental`, Docker, `-work-dir` 在 `$HOME`(snap Docker 不能挂 /tmp,见 [[feedback_snap_docker_tmp_mount]]) |

#### 组装结果 / Assembly result

| 目标                | 结果                               | 细节                                          |
| ------------------- | ---------------------------------- | --------------------------------------------- |
| **叶绿体 plastome** | **DRAFT, 6 scaffolds, 139,697 bp** | 5089 / 70326 / 9892 / 29021 / 9169 / 16200 bp |
| **nrDNA**           | 1 scaffold, 6,931 bp               | 干净组装                                      |

**为何是 DRAFT 而非环状 / Why DRAFT, not circular**:
GetOrganelle 日志:`Disentangling unsuccessful: "Complicated graph: please check around EDGE_18389_7049!# tags: {'petL'}"`,`Result status of embplant_pt: 6 scaffold(s)`。**petL IR 连接区的 de Bruijn 图纠缠**阻止环化→走 scaffold 路径(`scaffolds.graph1.1.path_sequence.fasta`,GetOrganelle 自己 WARNING "Assembly based on scaffolding may not be as accurate")。流程 **MUST NOT 强行选择闭环路径**(SCI-005 / 方法 §5.2),故诚实标 `DRAFT / WARN / [NO_CIRCULARIZATION]`。

#### 一致性 vs PZ405204(组装到的部分)/ Identity where assembled — 决定性通过

| 指标                 | 值                         | 工具                      |
| -------------------- | -------------------------- | ------------------------- |
| mash distance        | **0.000881** (≈99.91% ANI) | `mash dist`               |
| AvgIdentity (1-to-1) | **99.95%**                 | `dnadiff`                 |
| mismatches           | **0** (error rate 0.0)     | `minimap2 -ax asm5 --eqx` |

**序列保真度极好,但这是"组装到的部分"的一致性,不等于完整度**——见下。

#### 覆盖度 / 完整度 / Coverage vs completeness — 组装是部分的

- 1-to-1 覆盖:139,523 / 200,540 = **69.6%**;M-to-M(允许重复/IR):184,446 / 200,540 = **91.97%**。
- 约 **16 kb 参考序列无对应组装**(含一个 IR 拷贝的一部分)。
- 结论:**序列保真度高(0 SNP),但组装部分 / DRAFT 级(6 scaffolds, ~92% 完整),非干净单 contig 环**。37.8M PE 全量数据复跑确认——**碎片化是结构性的,不是覆盖不足导致的**。

#### ① → ② 接口合同产物 / Frozen interface artifacts (6 件,精确路径)

`${outdir}/plant_sr_assembly/<sample>/`:
`*_plastome.scaffold.fasta` / `*_nrdna.fasta` / `readback/{sorted.bam,depth.tsv,flagstat.txt}` / `getorganelle/<sample>_assembly_graph.fastg` / status JSON。

### M1-① 关键 bug 修复 / Key bug fix

**BUG #6 — 组装分级语义 bug**:旧适配器把任何 `*graph1.1*path_sequence*` 都判 `CANDIDATE`(status=PASS)。固定后:6-scaffold = **DRAFT**(status=WARN)。修正已验证。这正是不诚实分级的典型——M1 收尾专门为此设了诚实性修正 change。

---

## M1-② · plant-short-read-identify — reference-first 判定引擎

### 判定引擎六级阶梯 / 6-rung precedence ladder (`modules/local/decision_engine/main.nf`)

| rung     | 条件 / Condition                                   | 输出                                                                       |
| -------- | -------------------------------------------------- | -------------------------------------------------------------------------- |
| 1        | ① `assembly_grade=NOT_APPLICABLE` 或 `status=FAIL` | INCONCLUSIVE(透传 ① reason)                                                |
| 2        | ① emit `COVERAGE_ANOMALY`(污染/覆盖异常)           | CONTAMINATION_SUSPECTED (**DORMANT**)                                      |
| 3        | policy 阈值为 null                                 | THRESHOLD_NOT_CONFIGURED                                                   |
| 4        | 诊断位点落在缺失/不可判区                          | DIAGNOSTIC_SITES_NOT_CALLABLE                                              |
| 5a       | `callable_coverage < min_callable_fraction`        | LOW_CALLABLE_COVERAGE                                                      |
| 5b       | `mean_readback_depth < min_mean_depth`             | LOW_SEQUENCING_DEPTH                                                       |
| identity | 位点级一致性阶梯                                   | NON_AUTHENTIC / 灰区 / **AUTHENTIC(+WARN[INCOMPLETE_ASSEMBLY] for DRAFT)** |

**核心原则 (SCI-001)**:判定建立在 **callable-region 覆盖 + diagnostic-site 一致性**的证据组合上,**禁止仅凭单一 mash/ANI 距离阈值或单个组装强判**。

### 关键工程 bug 修复 / Key engineering fix

**Docker `val` → `path` staging bug**:一个持有宿主路径的 `val` 输入**不会**挂载进容器;`path` 输入才会 stage 进 work dir。修正:`DECISION_ENGINE` 的 policy 输入 + `LOAD_REFERENCE_PACK` 模式从 `val` 改 `path`。修正前正常样本错误返回 `policy_pack_id=null` → `THRESHOLD_NOT_CONFIGURED`(策略没加载进去)。

---

## M1 收尾 · m1-closeout-identify-honesty — 诚实性三连修正

五场景实测暴露了**预期与实际的三处系统性偏离**。本 change 不掩盖、不强行凑通过,而是**修订合同并留痕**。

### 偏离一 / Divergence 1 — reason code 语义模糊

**现象**:1079× 深度的样本被标 `LOW_COVERAGE`,语义误导(深度其实爆表)。`LOW_COVERAGE` 同时指"深度不足"和"callable-region 覆盖不足",两个根因混为一码。
**修正**:拆为 `LOW_SEQUENCING_DEPTH`(warn,深度不足)与 `LOW_CALLABLE_COVERAGE`(scientific_inconclusive,组装完整度不足)。

### 偏离二 / Divergence 2 — 占位阈值 0.9 不合理

**现象**:`min_callable_fraction=0.9` 是占位值,但含已知 IR 结构缺口的 DRAFT 叶绿体实测 callable_cov 范围 **0.888–0.900**——正常样本 0.888206 也过不了门 → `AUTHENTIC` 路径**不可达**。
**修正**:`0.9 → 0.885`(实测 floor 0.888206 下方留 ~0.003 margin),policy 文件头 `_comment_2/3/4` 记录实测依据 + **"M3 后必须以统计标定值替换"** 声明。**禁止静默调参**——VALIDATION-identify.md 新增"预期状态修订表"。

### 偏离三 / Divergence 3 — 污染门径是死的

**现象**:50:50 动物×植物混合 → 期望 `CONTAMINATION_SUSPECTED`,实际走 normal 同路径(`callable_cov` 与深度**不变**)。两个事实:① 当前 ① 不 emit `COVERAGE_ANOMALY`(Kraken2 自建库缺口);② 动物×植物混合对质体招募**无鉴别力**。
**修正**:`CONTAMINATION_SUSPECTED` 保留但标 `dormant: true` + `dormant_note`。正式污染验证改用**近缘植物混合夹具**,随 Kraken2 自建库 change 一并实装并移除 dormant。

---

## 五场景实测 / Five-scenario validation

### 修订前(暴露偏离)/ Pre-revision (divergences exposed)

| #   | 场景          | policy    | decision     | reason                   | callable_cov | depth   | 匹配?                      |
| --- | ------------- | --------- | ------------ | ------------------------ | ------------ | ------- | -------------------------- |
| 1   | Normal 2Gb    | eng-test  | INCONCLUSIVE | LOW_COVERAGE             | 0.888206     | 1079.6  | ✗(pin: AUTHENTIC)          |
| 2   | Low-cov 0.5Gb | eng-test  | AUTHENTIC    | INCOMPLETE_ASSEMBLY      | 0.900144     | 269.88  | ✗(predicted: LOW_COVERAGE) |
| 3   | Contam 50:50  | eng-test  | INCONCLUSIVE | LOW_COVERAGE             | 0.888206     | 1079.78 | ✗(pin: CONTAM; ① silent)   |
| 4   | No ref        | —         | —            | DATA-005 fail-fast       | —            | —       | ✓                          |
| 5   | Prod-null     | prod-null | INCONCLUSIVE | THRESHOLD_NOT_CONFIGURED | 0.888206     | 1079.6  | ✓                          |

> **场景 2 的反直觉发现 / The counter-intuitive finding in scenario 2**: 0.5Gb 反而比 2Gb 组装得更好(`callable_cov 0.900144 > 0.888206`)。机制:GetOrganelle 内部 500× subsampling,2Gb 时丢弃了部分 bridging reads;0.5Gb 用了全部 reads,contiguity 反而略优。**→ 更多输入在内部 subsampling 激活时不一定更好**(支撑"输入一律抽稀~2Gb"策略)。

### 修订后(从缓存复跑)/ Post-revision (cached re-run)

复跑方式:从原始五场景 session `54010c65`(curious_kare)`-resume`,① 全部 cache-hit(`cached=15`),仅 `DECISION_ENGINE`+`EMIT_IDENTIFY_STATUS` 重算(`completed=3`)。① metrics 不变。

| #   | 场景         | 修订后 decision  | reason                         | callable_cov | depth   | 说明                                                                          |
| --- | ------------ | ---------------- | ------------------------------ | ------------ | ------- | ----------------------------------------------------------------------------- |
| 1   | Normal       | **AUTHENTIC**    | **WARN[INCOMPLETE_ASSEMBLY]**  | 0.888206     | 1079.6  | 0.888>0.885 通过覆盖门,identity=1.0 → AUTHENTIC                               |
| 2   | Low-cov      | **AUTHENTIC**    | **WARN[INCOMPLETE_ASSEMBLY]**  | 0.900144     | 269.88  | 同上                                                                          |
| 3   | Contam 50:50 | AUTHENTIC        | WARN[INCOMPLETE_ASSEMBLY]      | 0.888206     | 1079.78 | 污染 dormant,走 normal 同路径(**诚实记录:50:50 动物×植物混合被当作植物正品**) |
| 4   | No ref       | —                | DATA-005 fail-fast             | —            | —       | EXIT=1, cached=11                                                             |
| 5   | Prod-null    | **INCONCLUSIVE** | **[THRESHOLD_NOT_CONFIGURED]** | 0.888206     | 1079.6  | thr_cf=null,模块层 null 防御优先                                              |

### 验收三条件 / Three acceptance gates — 全满足

1. ✅ 正常样本 → `AUTHENTIC + WARN[INCOMPLETE_ASSEMBLY]`
2. ✅ production-null 仍 `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]`
3. ✅ nf-test **7/7 PASS**(含新 `LOW_CALLABLE_COVERAGE` / `LOW_SEQUENCING_DEPTH` 码);OpenSpec validate **6/6 PASS**

---

## M1 交付的 8 个 local 模块 / The 8 local modules M1 ships

```
QC_SHORT(外部 fastp) · getorganelle_result_adapter · touch_readback_markers
align_assembly_to_reference · evaluate_callable_regions · evaluate_diagnostic_sites
load_reference_pack · decision_engine · emit_assembly_qc_status · emit_identify_status
```

判定证据链 / Evidence chain: 组装 → 回贴 → callable-region 评估 → diagnostic-site 评估 → reference-pack 加载 → 判定引擎 → 状态输出。

---

# 总结 · M0+M1 建立了什么、没建立什么 / Summary — what is and isn't established

## 已建立 / Established

- **可治理的工程主干**:5 spec 域 + 34 可追溯 ReqID + OpenSpec 闭环 + CI 守门。
- **可执行的合同**:samplesheet 真值禁入、status 模型、reason-code 字典、工具 PROHIBITED 区、policy null 双层防御。
- **植物短读长端到端**:组装 → 回贴 → reference-first 判定,**真实刻叶紫堇数据验证**,身份确认(AUTHENTIC)与组装不完整(WARN)诚实分离。
- **诚实性纪律的实证**:三处系统性偏离被记录、合同被修订并留痕,**没有为凑通过而改科学方法**(见 [[feedback_gsd_closed_loop_discipline]])。

## 未建立 / 明确留待后续 / Not yet — explicitly deferred

- **科学阈值标定**:所有 policy 阈值仍是 placeholder(0.885 等),M3 独立统计标定后替换。
- **污染检测**:`CONTAMINATION_SUSPECTED` dormant,需 Kraken2 自建库 + 近缘植物混合夹具(M2 起)。
- **动物线粒体**:M2(animal DNBSEQ mitogenome,总方案 §18),**不是 M3/M5**。
- **诊断位点的独立发现/验证集**:SCI-010,M5。
- **参考级终序列(REGRADE 到 REFERENCE)**:需 M4 hybrid 证据。

> **下一步 / Next**: M2 — animal DNBSEQ 线粒体基因组。

---

_本报告锚定 OpenSpec 归档 changes 与 `~/corydalis_validation/` 实测数据。任何数字与判定可在上述归档 change 的 VALIDATION 文档中复核。_
