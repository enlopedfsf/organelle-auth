## Context

M0 + `define-core-contracts` 提供了骨架与可执行契约。本变更是 **M1-①**(植物短读长组装 + read-back 证据 + 组装阶段状态),按已确认拆分:M1 = ①(本变更,数据生产半)+ ②(`plant-short-read-identify`,判定半,下一会话)。① 到 `stage=assembly_qc`、`decision=NOT_APPLICABLE` 为止;判定逻辑、测试 reference pack、四场景决策验证归 ②。依据:总方案 §4/5.1/5.2/5.5/6/8/12/13/18-M1 + 方法学生信部分 Scenario A。真实数据在 `/mnt/ssd_pool/home/iris-hp/zhongyao/corydalis_test`(刻叶紫堇 SRR38978846;参考 PZ405204)。

## Goals / Non-Goals

**Goals**
- samplesheet → 植物 plastome(+nrDNA)组装 + read-back 证据 + 组装阶段 status,正常样本组装与 PZ405204 高度一致。
- 装 fastp 真模块(消除 issue #2 的 8 个 container_configs);启用 T1–T3。
- 冻结 ①→② 输出接口(本 design 的专门章节)。

**Non-Goals(显式排除)**
- reference-first 判定逻辑、decision 字段填充、测试 reference pack 接入、四场景决策验证 → ②。
- Kraken2 自建库(独立 change);M1 污染由覆盖度/组装信号承担,缺口在 Risks 说明。
- NOVOPlasty 交叉验证(EXPERIMENTAL,独立评估 change)、动物分支(M2)、三代/混合(M3/M4)、植物线粒体、完整判定引擎(M5)。

## Decisions

### 决策 1:fastp 参数 = 方法 §2.1,仅 experimental profile
`--detect_adapter_for_pe --qualified_quality_phred 15 --length_required 50`。这些是**未标定的 QC 阈值**,按 §5.1/ENG-POL-001 仅进 `conf/experimental.config`(或 experimental profile params);production profile 中为 `null`,由批准的 policy pack 注入。**绝不写进 production 默认值。**

### 决策 2:GetOrganelle `-R`/`-k` = 工具算法参数,非科学阈值
`-F embplant_pt -R 15 -k 21,45,65,85,105` 与 `-F embplant_nr -k 35,85,115`(方法 §3.1/3.2 逐字)。`-R`(word coverage)、`-k`(k-mer)是 GetOrganelle 算法参数(§9.3 → tool registry + design,CONDITIONAL),**不是**科学验收阈值。科学阈值(覆盖洼地系数等)仍从 policy 读、`null` 时不硬编码。此区分是"零硬编码科学阈值"与"照抄 Scenario A 命令"并存的关键。

### 决策 3:read-back 用 minimap2 `-ax sr`(已批准)
理由:方法 §3.5 明确 minimap2 回贴;且 minimap2 同时支持短读长与未来长读长,bwa 仅短读长——为 M3/M4 一致性预留。clean reads `-ax sr` 回贴组装 FASTA → sorted BAM → samtools depth/flagstat。

### 决策 4:GetOrganelle 自建模块(nf-core 无)
bioconda `getorganelle`;容器用 Wave/biocontainer 生成并固定 tag+digest;模块输出 `versions.yml`;两个 `-F` 目标作为同一模块的两次调用(或 mode 输入),由 `targets` 路由(plastome/nrdna)。登记到 tool registry,admission CONDITIONAL,`container_digest` 在容器构建后填入。

### 决策 5:低覆盖不强环化(§3.6/§5.2)
GetOrganelle 未环化 → 输出 scaffold,`assembly_grade = DRAFT`,status WARN;数据严重不足 → INCONCLUSIVE + `LOW_COVERAGE`,**禁止强行闭环/强判**。

### 决策 6:污染检测缺口(M1 临时方案)
本变更不建 Kraken2 自建库(独立 change)。M1 污染信号由 read-back 覆盖度异常(双峰/异常低覆盖)+ 组装图异常分支承担,命中时输出 reason code(如 `COVERAGE_ANOMALY`,待加入 reason_codes.yaml)并标 INCONCLUSIVE/WARN。**此为已知缺口**,Kraken2 自建库 change 落地后补齐;design 在此明示,不在 spec 里假装已实现。

### 决策 7:issue #2 消除
fastp 首个真模块安装 → `nf-core modules install` 重新生成 8 个 `conf/containers_*.config` → 8 个 container_configs lint 偏差消失。按 issue #2 恢复判据:CI lint 0 failure 后,把 nf-core/linting 设为 required、更新 `docs/decisions/m0-lint-advisory-deviations.md` 状态、关 issue #2(注:PR 模板那 1 项仍 advisory,见该 issue)。

---

## ①→② 接口合同(冻结;② 必须引用,不得重新发明)

> 本节是拆分的代价所在:① 的产出物路径、格式与 `stage=assembly_qc` 状态字段取值**逐字段冻结**,作为 ②(`plant-short-read-identify`)的输入依据。② 的 proposal MUST 引用本节;若需变更接口,须新开 change,不得在 ② 内擅改。

### 1. 产出目录与 FASTA 路径约定
根:`${params.outdir}/plant_sr_assembly/<sample_id>/`

| 产物 | 路径 | 说明 |
|---|---|---|
| 环化叶绿体 | `.../<sample_id>_plastome.fasta` | GetOrganelle 环化成功时产出;`assembly_grade=CANDIDATE` |
| 叶绿体 scaffold | `.../<sample_id>_plastome.scaffold.fasta` | 未环化时产出;`assembly_grade=DRAFT` |
| nrDNA 一致性单元 | `.../<sample_id>_nrdna.fasta` | `targets` 含 `nrdna` 时产出(~5.8 kb) |
| 组装图 | `.../getorganelle/<sample_id>_assembly_graph.fastg` | 供 ② 结构审查/Bandage |

约定:同一样本**仅产出 `*_plastome.fasta` 或 `*_plastome.scaffold.fasta` 之一**(据环化结果)。文件名 `<sample_id>` 与 samplesheet `sample_id` 一致、安全字符。

### 2. evidence_files(写入 status JSON 的 `evidence_files` 数组,outdir 相对路径)
1. 选中的叶绿体序列(`*_plastome.fasta` 或 `*_plastome.scaffold.fasta`)
2. nrDNA FASTA(`*_nrdna.fasta`,若产出)
3. read-back BAM:`.../readback/<sample_id>.sorted.bam`
4. depth:`.../readback/<sample_id>.depth.tsv`
5. flagstat:`.../readback/<sample_id>.flagstat.txt`
6. 组装图:`.../getorganelle/<sample_id>_assembly_graph.fastg`

### 3. `stage = assembly_qc` 状态 JSON 字段取值规则(逐字段)

| 字段 | 取值 | 规则 |
|---|---|---|
| `sample_id` | <sample_id> | 与 samplesheet 一致 |
| `stage` | `"assembly_qc"` | 字面量 |
| `status` | `PASS` \| `WARN` \| `FAIL` \| `INCONCLUSIVE` | PASS=环化成功且覆盖可用;WARN=scaffold(DRAFT)但可用;FAIL=组装失败(无 contig/工具错误);INCONCLUSIVE=低覆盖无法产出可信组装(禁止强判) |
| `assembly_grade` | `CANDIDATE` \| `DRAFT` \| `NOT_APPLICABLE` | CANDIDATE=环化叶绿体;DRAFT=scaffold/部分;NOT_APPLICABLE=组装失败(status=FAIL)。**① 永不产出 `REFERENCE`** |
| `decision` | `"NOT_APPLICABLE"` | 字面量(① 不判定;② 在 `stage=identify` 填 decision) |
| `reason_codes` | `[]` \| `[NO_CIRCULARIZATION]` \| `[LOW_COVERAGE]` \| `[ASSEMBLY_FAILED]` \| `[COVERAGE_ANOMALY]` | 来自 `reason_codes.yaml`(本变更新增 `NO_CIRCULARIZATION`/`ASSEMBLY_FAILED`/`COVERAGE_ANOMALY`)。可组合 |
| `policy_pack_id` | <experimental policy id> | 如 `tcm-plant-experimental-0.1.0` |
| `evidence_files` | 见第 2 节清单 | 非空 |

### 4. ② 的消费契约(摘要,详见 ② proposal)
② 读入:① 选中的叶绿体 FASTA + read-back 证据(BAM/depth/flagstat)+ 本 `assembly_qc` status(尤其 `assembly_grade`、`reason_codes`)→ 产出 `stage=identify` 的新 status,`decision` 填充。② **不得**修改 ① 的路径/格式;`assembly_grade=NOT_APPLICABLE` 或 `status=FAIL` 时 ② 应直通 INCONCLUSIVE/不判定。

## Risks / Trade-offs

- **[污染检测缺口]** → 决策 6:用覆盖度/组装信号临时承担,明示为缺口,Kraken2 自建库 change 补齐。
- **[GetOrganelle 容器化]** → bioconda 包 + Wave 生成镜像;首次构建实测;失败则降级 conda 兜底(仅开发,非 production 可重复性唯一来源)。
- **[接口冻结过早?]** → 接口合同已尽量贴近 §5.5 既有 status 模型,变动面小;若 ② 发现需扩展,走新 change 而非擅改。
- **[`-R 15` 边界定性]** → 决策 2 明确其为工具算法参数;若审阅认定属科学阈值,则改为 policy 注入(目前按工具参数)。

## Migration Plan

Greenfield(首次真实模块)。回滚 = 移除 fastp/getorganelle/minimap2/samtools 模块 + 回退 subworkflow 改动;vanilla 组装空骨架恢复。issue #2 状态随之回退(advisory)。

## Open Questions

- GetOrganelle 容器构建的具体 Wave 镜像 tag/digest(apply 时定,填入 tool registry)。
- `COVERAGE_ANOMALY` reason code 的精确触发逻辑(M1 临时:read-back 双峰/异常低覆盖;Kraken2 落地后细化)——可在 apply 时收敛。
