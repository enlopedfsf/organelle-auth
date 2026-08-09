# VALIDATION — M2-① animal short-read assembly evidence (真实数据)

> 证据数据在 git 外 `/home/iris-hp/whitmania_validation/`(reads、参考、组装、一致性)。本文记录判定、bug 修复与参考考据。抽稀 seed:normal 11、lowcov 42。

## 运行 / Run

| item | value |
|---|---|
| Sample | `SRR27841063` (柳叶蚂蟥 *Whitmania acranulata*, DNBSEQ short-read) |
| Normal subsample | ~2.0 Gb, seed 11 → 6,659,067 PE reads (`reads/WTM_NORMAL_*`) |
| Low-cov subsample | ~0.5 Gb, seed 42 → ~1,660,000 PE reads (`reads/WTM_LOWCOV_*`) |
| Bait set | `assets/bait_references/mitofinder-bait-v0.1/multi_ref.fasta` — 5 条 *W. acranulata* 完整线粒体(NC_023928/KC688271/MK347500/CM084263/OQ076773),provenance 见该目录 |
| MitoFinder annotation ref | `NC_023928.gb` (唯一可解析的带基因 *W. acranulata* .gb 记录) |
| Identity validation ref | **`CM084263.1`** (jianxi01 谱系;样本 100% 匹配) |
| Profile | `-profile experimental,docker`, `-work-dir` 在 `$HOME` |

## 结果 — 流水线绿,诚实输出(正常样本)

```
completed=7 failed=0 cached=5  (exit 0)
status = WARN, assembly_grade = DRAFT, decision = NOT_APPLICABLE,
reason_codes = [NO_CIRCULARIZATION]
```

**Mitogenome**: `WTM_NORMAL_mitogenome.scaffold.fasta` — **14,393 bp, 1 contig**, GC 27.24%;回贴 read-back **mean_depth 391.2×**。MitoFinder 注释 **15 个基因**(protein-coding + rRNA + tRNA,`tRNA annotation with MitFi run well`),`Circularization: Not found` → 诚实标 `DRAFT`(不强环化,§3.6/SCI-005)。

## 身份一致性 / Identity vs published mitogenome

| 比对 | dnadiff AvgIdentity | 对齐 | 结论 |
|---|---|---|---|
| 组装 vs **CM084263.1** (W. acranulata jianxi01) | **100.00%** | 14,399/14,393 bp | 组装 = jianxi01 谱系,决定性通过 |
| 组装 vs **NC_023928** (W. acranulata, RefSeq) | **87.62%** | 10,122/14,393 bp | 参考分歧 |
| **NC_023928 vs CM084263.1** (两"同种"参考互比) | **87.62%** | — | 两参考彼此 12% 分歧 → 误鉴定信号 |

## 参考考据 (用户批准约束 1,2026-08-09)

### 考据 (a):参考为独立研究来源,预期一致性 < 100%
`NC_023928` 来自独立研究(RefSeq, BioProject PRJNA927338)。与 M1 的"循环性参考"不同,个体间变异是真实生物学,预期 < 100%。**实际发现更强的信号**:样本与 jianxi01 谱系(`CM084263`)100% 一致——说明参考选择的"独立性"不是单向的:公共库同种记录之间就存在 12% 分歧(见考据 b)。**禁止为追求高一致性调参**(全程未调)。

### 考据 (b):*Whitmania* 公共库物种错误鉴定(Ye et al. 2015)——**本验证的实证**
文献(Ye et al. 2015, *Belgian Journal of Zoology*)证实 *Whitmania* 属公共库存在物种误鉴定。**本验证提供了直接实证**:
- 样本组装与 `CM084263.1`(W. acranulata jianxi01)**100% 一致**;
- 但与同标为 *W. acranulata* 的 `NC_023928`(RefSeq)仅 **87.62%** 一致;
- 两条"同种"参考彼此也仅 87.62% —— 属内(可能跨种)分歧。
- 旁证:Frontiers in Genetics 2025 (10.3389/fgene.2025.1548006) *"Comparative genomics of three non-hematophagous leeches (Whitmania spp.)"* 覆盖 3 个 *Whitmania* 物种,其中至少一条记录的物种标签与样本谱系不符。

**处置(用户批准选项 1)**:身份验证参考改用 `CM084263.1`(样本 100% 匹配的已发表 W. acranulata);`NC_023928` 分歧留作考据 (b) 实证。MitoFinder **注释参考**仍用 `NC_023928.gb`(jianxi01 无独立注释 .gb,`CM084263` 为 WGS master 无内嵌序列)——注释是参考引导的,与样本谱系 87.6% 分歧,注释质量作为已知局限记录,深度注释 QA 属 M2-②/后续。**每参考序列的来源凭证可信度 metadata 待 v1.0 前准入审查(考据 b 要求)**。

## 停-报记录 (约束 2) / STOP & REPORT

初测以 `NC_023928` 为验证参考时,一致性 **87.62% < 95%** → **按用户约束 2 停止,未自动重跑调参**,报告后用户批准改用 `CM084263.1`。停-报内容:组装质量无问题(与 CM084263 100%),分歧源于参考记录本身(Ye 2015 误鉴定)。

## 三场景实测 / Three-scenario results

| # | 场景 | 状态 | 组装 | 深度 | 身份 vs CM084263 |
|---|---|---|---|---|---|
| 1 | Normal 2 Gb | `WARN / DRAFT / [NO_CIRCULARIZATION]` | 14,393 bp, 1 contig | 391× | **100.00%** |
| 2 | Low-cov 0.5 Gb | `WARN / DRAFT / [NO_CIRCULARIZATION]` | 14,383 bp, 1 contig | 98× | **100.00%** |
| 3 | No-ref (参考缺失) | **fail-fast**(pipeline failed,exit≠0) | — | — | — |

- **低覆盖稳健**:0.5 Gb 组装仅比 2 Gb 短 10 bp(14,383 vs 14,393),两者互比 **100% 一致**,覆盖 98× 仍能组装完整线粒体。→ 该数据量下线粒体组装对覆盖不敏感(与 GetOrganelle 500× 内部抽稀的"更多输入未必更好"互为印证)。
- **参考缺失 fail-fast**:`--animal_annotation_reference_gb` 指向不存在文件 → MITOFINDER 输入缺失 → pipeline failed,未静默回退、未产出伪结果(ENG-POL-002 防御层之外的第二层:输入文件缺失即失败)。
- 两场景 `decision=NOT_APPLICABLE`(① 不判定),`policy_pack_id=tcm-animal-experimental-0.1.0`。

## 已知局限 / Known limitations

- **NUMT**:风险筛查(覆盖异质性 + 多重比对)已执行且报告,`numt_coverage_coefficient`/`numt_multimap_fraction` 在 experimental 为 null → 仅标注不判;确证(核侧翼/提前终止/移码 + 长读长)属后续 change。
- **注释参考分歧**:MitoFinder 注释以 `NC_023928.gb` 为参考(与样本谱系 87.6% 分歧),注释结果含不确定性;深度注释 QA 与独立 MITOS2 复核留 M2-②。
- **低覆盖 / 参考缺失**场景见下方(在本文补记)。
- **圆环化**:MitoFinder 未确认环化 → DRAFT;14,393 vs 参考 14,462–14,505 bp 差约 70 bp,可能为线性化连接点或小缺口,② 结构审查时核。
