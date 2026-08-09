## Context

M1 (§18) delivered the plant short-read route end-to-end; its frozen ①→② interface contract lives in the M1-① archive design (reference for the pattern, NOT reused verbatim — animal has its own contract below). M2 extends to animal. Per the agreed split, this change is **M2-①** (data-production half): animal short-read mitogenome assembly + read-back evidence + NUMT risk screening + `stage=assembly_qc` status. M2-② (`animal-short-read-identify`, next session) consumes the frozen contract below. Scientific anchors: methods §3.3 (MitoFinder + NUMT 排检), §3.5 (read-back), §3.6 (no forced circularization / low-coverage), §4.3 (multi-reference bait, D-loop risk), §7.2 tool admission (`mitofinder_mitoz` CONDITIONAL, dnbseq); 总方案 §2.3 (animal default target = complete mitogenome; NUMT/异常覆盖/提前终止/基因缺失/结构一致性检查), §18-M2. Real data at `/mnt/ssd_pool/home/iris-hp/zhongyao/whitmania_test/` (`SRR27841063`, *Whitmania acranulata* 柳叶蚂蟥).

## Goals / Non-Goals

Goals (design-level, beyond proposal):
- Freeze the **animal ①→② output contract** (paths + status fields) exactly like M1-①, so ② is purely read-only.
- Keep the plant route byte-identical (routing is additive; plant filter untouched).
- NUMT risk screening is a **WARN-level signal**, never a decision input that forces a call.

Non-Goals (design-level boundaries, in addition to proposal's out-of-scope list):
- No NUMT confirmation (nuclear-flank / premature-stop / frameshift checks + long-read evidence → future change; recorded in known limitations below).
- No MitoFinder annotation deep-verification (annotation is produced and stored; independent MITOS2 cross-check is a future validation item).
- No Kraken2 self-built DB; no 3rd-gen/hybrid (M3/M4); no threshold calibration.

## Decisions

### 决策 1: 动物路由显式化,plant 分支不动
`ORGANELLEAUTH` adds a parallel filter (mirroring the plant one, §3.3/DATA-006): `taxon_group=='animal' && meta.has_short_reads && meta.targets.contains('mitome')`. Animal samples then flow `QC_SHORT` (same fastp module — 决策共用,identical params + experimental-only rule as plant) → `ANIMAL_SR_ASSEMBLY` → `ASSEMBLY_QC` → status emission. The existing plant filter is **not modified**; regression is verified by the plant T3 stub + real-data smoke remaining green.

### 决策 2: 多参考诱饵提取(方法学 §4.3 的短读长适配)
Before MitoFinder, `minimap2 -x sr` against a **multi-reference mitogenome set** extracts candidate mitochondrial reads. Rationale: a single reference can drop the hypervariable control region (D-loop) — the high-discrimination region for animal authentication (§4.3). Alternatives considered: (a) single-reference bait (rejected — D-loop dropout), (b) MitoFinder's own bundled-database seeding (rejected — not circumscribed to the target taxon; introduces unwanted reference bias), (c) MitoFinder on all clean reads with no bait (rejected — wastes compute on nuclear reads and weakens assembly focus for skimming data). Bait set = bundled tool-level resource (see 决策 3).

### 决策 3: bait 参考集 = bundled 工具级资源;判定 reference pack 归 ②
The multi-reference bait set ships with the pipeline as a **tool-level resource** (bundled FASTA of circumscribed mitogenomes, e.g. the 5 complete *W. acranulata* mitogenomes on GenBank + a close congener), NOT as a scientific decision asset. Rationale: ① must be independently validatable before ② exists; the decision-time reference pack (diagnostic sites, conflict rules) is ②'s deliverable. This mirrors M1-① using a pinned `--config-dir` GetOrganelle db (tool-level) while ② carries the scientific reference pack. The bait set's provenance (accessions, date, checksums) is recorded in the asset.

### 决策 4: MitoFinder = 自建 local module(容器化 + versions.yml)
MitoFinder is not an nf-core module; per §12.3 local-module rules we build a **local `mitofinder` module** (meta / stub / nf-test / `versions.yml`) wrapping the MitoFinder container. Scientific parameters follow methods §3.3 verbatim; runtime knobs (threads, memory, `--assembly-method`, annotation options) are tool algorithm parameters (§9.3, registered in tools.yaml as CONDITIONAL), NOT acceptance thresholds. `container_digest` is populated at apply; admission stays CONDITIONAL until project validation. (MitoZ remains the documented fallback, NOT wired this change.)

### 决策 5: 输出适配 + CANDIDATE/DRAFT 分级(镜像植物 getorganelle_result_adapter)
A local `animal_result_adapter` mirrors the plant adapter: detect a single circular contig → `CANDIDATE` (`<sample_id>_mitogenome.fasta`); otherwise scaffold/linear → `DRAFT` (`<sample_id>_mitogenome.scaffold.fasta`). Collects the annotation output, the assembly graph (Bandage-ready), and `versions.yml`. No forced circularization (§3.6/SCI-005).

### 决策 6: NUMT 风险筛查最小版 = 覆盖异质性 + 多重比对信号
`numt_risk_screen` re-maps reads (reuses the read-back BAM) and computes: (a) **coverage heterogeneity** — valley regions below `median × coefficient` (coefficient from policy, `null` in experimental → flagged, never hardcoded; mirrors ASSEMBLY_QC), (b) **multi-mapping / abnormal-depth signals** on the mitogenome assembly. Any signal → `status=WARN` + `reason_codes=[NUMT_RISK_SUSPECTED]` at `assembly_qc`. This is the first step of methods §3.3 NUMT 排检. Alternatives: full NUMT confirmation now (rejected — out of scope, needs nuclear-flank checks + long reads). **Known limitation (recorded for future change):** nuclear-flank / premature-stop-codon / frameshift checks and long-read NUMT confirmation are NOT implemented here; this version is a screening signal only.

## 参考选择考据与验证诚实性(用户批准附加约束,2026-08-09)

> 两项考据必须进入本 design 与 `VALIDATION-animal.md`,禁止为追求高一致性而调参。

### 考据 (a):NC_023928 为独立研究参考,预期一致性 < 100%
bait 集与验证参考选用 `NC_023928`(同种 *Whitmania acranulata*)。该参考**来自独立研究**,不是 M1 那样的"循环性参考"——样本与参考没有共享的建库/测序来源。因此:
- **验证强度高于 M1**(M1 的参考与样本来源存在循环性,一致性 99.95% 部分是来源重合的体现);
- **个体间变异是真实生物学**,预期一致性 < 100%(mash/dnadiff),落在合理区间(如 95–99.9%)均属正常;
- **MUST NOT 为把一致性调高而改动参数/参考选择**——验证记录的是"组装质量 + 与独立同种参考的吻合度",不是"调参刷分"。

### 考据 (b):*Whitmania* 属公共库记录的物种错误鉴定风险
文献证实 *Whitmania* 属公共数据库记录存在**物种错误鉴定**(Ye et al. 2015, *Belgian Journal of Zoology*)。因此:
- reference pack 的每条序列 MUST 记录**来源凭证可信度 metadata**(accession、发表文献/凭证标本、提交者信息、鉴定依据),v0.1 可仅记录 metadata 不判优劣;
- **v1.0 前 MUST 建立序列准入审查**(独立凭证核验),在此之前所有基于公共库序列的判定视为"参考待准入"状态;
- 本变更(①)与 M2-② 的 reference pack 均须把该 metadata 字段写入资产结构与 status,不静默依赖公共库 accession 的自称物种名。

### 验证停-报规则
真实数据验证时若**一致性落在意外区间(如 < 95%)**:STOP 验证流程并**报告**,不得自动重跑调参。报告内容:原始比对数字、可能的生物学/技术原因假设、是否需要更换参考或补做独立样本。

## ①→② 接口合同(冻结;② 必须引用,不得重新发明)

> 与 M1-① 相同的拆分代价:动物 ① 的产出物路径、格式与 `stage=assembly_qc` 状态字段取值**逐字段冻结**,作为 M2-②(`animal-short-read-identify`)的输入依据。② 的 proposal MUST 引用本节;若需变更接口,须新开 change,不得在 ② 内擅改。

### 1. 产出目录与 FASTA 路径约定
根:`${params.outdir}/animal_sr_assembly/<sample_id>/`

| 产物 | 路径 | 说明 |
|---|---|---|
| 环化线粒体 | `.../<sample_id>_mitogenome.fasta` | MitoFinder 单环状 contig 时产出;`assembly_grade=CANDIDATE` |
| 线粒体 scaffold | `.../<sample_id>_mitogenome.scaffold.fasta` | 未环化时产出;`assembly_grade=DRAFT` |
| 注释 | `.../annotation/<sample_id>_annotation.*` | MitoFinder 注释输出(含基因表/结构) |
| 组装图 | `.../mitofinder/<sample_id>_assembly_graph.fastg` | 供 ② 结构审查/Bandage |

约定:同一样本**仅产出 `*_mitogenome.fasta` 或 `*_mitogenome.scaffold.fasta` 之一**(据环化结果)。文件名 `<sample_id>` 与 samplesheet `sample_id` 一致、安全字符。

### 2. evidence_files(写入 status JSON 的 `evidence_files` 数组,outdir 相对路径)
1. 选中的线粒体序列(`*_mitogenome.fasta` 或 `*_mitogenome.scaffold.fasta`)
2. 注释(annotation 目录内主产物)
3. read-back BAM:`.../readback/<sample_id>.sorted.bam`
4. depth:`.../readback/<sample_id>.depth.tsv`
5. flagstat:`.../readback/<sample_id>.flagstat.txt`
6. 组装图:`.../mitofinder/<sample_id>_assembly_graph.fastg`

### 3. `stage = assembly_qc` 状态 JSON 字段取值规则(逐字段)

| 字段 | 取值 | 规则 |
|---|---|---|
| `sample_id` | <sample_id> | 与 samplesheet 一致 |
| `stage` | `"assembly_qc"` | 字面量 |
| `status` | `PASS` \| `WARN` \| `FAIL` \| `INCONCLUSIVE` | PASS=环化成功且覆盖可用;WARN=scaffold(DRAFT)或 NUMT 风险信号但可用;FAIL=组装失败(无 contig/工具错误);INCONCLUSIVE=低覆盖无法产出可信组装(禁止强判) |
| `assembly_grade` | `CANDIDATE` \| `DRAFT` \| `NOT_APPLICABLE` | CANDIDATE=环化线粒体;DRAFT=scaffold/部分;NOT_APPLICABLE=组装失败(status=FAIL)。**① 永不产出 `REFERENCE`** |
| `decision` | `"NOT_APPLICABLE"` | 字面量(① 不判定;② 在 `stage=identify` 填 decision) |
| `reason_codes` | `[]` \| `[NO_CIRCULARIZATION]` \| `[NUMT_RISK_SUSPECTED]` \| `[ASSEMBLY_FAILED]` | 来自 `reason_codes.yaml`(本变更新增 `NUMT_RISK_SUSPECTED`)。可组合 |
| `policy_pack_id` | <experimental policy id> | 如 `tcm-animal-experimental-0.1.0`(② 提供 pack;① 仅透传字段) |
| `evidence_files` | 见第 2 节清单 | 非空 |

### 4. ② 的消费契约(摘要,详见 ② proposal)
② 读入:① 选中的线粒体 FASTA + read-back 证据(BAM/depth/flagstat)+ 本 `assembly_qc` status(尤其 `assembly_grade`、`reason_codes` 含 `NUMT_RISK_SUSPECTED` 信号)→ 产出 `stage=identify` 的新 status,`decision` 填充。② **不得**修改 ① 的路径/格式;`assembly_grade=NOT_APPLICABLE` 或 `status=FAIL` 时 ② 应直通 INCONCLUSIVE/不判定。

## Risks / Trade-offs

- **[MitoFinder 非 nf-core 模块,需自建]** → 遵循 §12.3 local module 规范(meta/versions/stub/nf-test),最小封装;MitoZ 留作文档化备选。
- **[bait 参考集绑定引入参考偏差?]** → 多参考集是"提取诱饵"而非"判定参考",判定参考归 ②;记录 provenance 防静默换库。
- **[NUMT 筛查可能假阳性/假阴性]** → 明确标注为筛查(非确证);WARN 级、不强制判定;确证方法列入 known limitations。
- **[D-loop 高变区仍可能漏]** → 多参考提取降低概率但不消除;② 的 reference pack 若诊断位点落 D-loop,判定时按 DIAGNOSTIC_SITES_NOT_CALLABLE 处理(② 决策,非本变更)。
- **[植物路线回归]** → 植物 filter/子流程零改动;回归由既有 T3 + 真实数据 smoke 验证。

## Migration Plan

No production deployment (pipeline in dev). Rollout: implement → T1/T2/T3 green → local real-data validation recorded → `openspec validate` → archive → ② next session. Rollback: `dev` history (single branch, no release).

## Open Questions

- MitoFinder 注释的产出格式细节(Bed/GB 等)与后续 ② 消费字段的精确对应 —— ② 起步时按冻结路径定稿,不改变 ① 的行为。
- bait 参考集的具体 accession 清单与校验和 —— apply 期下载并在 asset 中记录 provenance(非科学阈值,不触发 spec 变更)。
- 覆盖洼地系数、多重比对阈值的默认行为 —— 均为 policy 注入(`null` → 仅标注),不硬编码,无需在 ① 冻结数值。
