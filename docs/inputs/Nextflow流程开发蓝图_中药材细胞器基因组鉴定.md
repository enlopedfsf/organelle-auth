# Nextflow 流程开发蓝图：中药材细胞器基因组鉴定系统

**版本**：v1.0 ｜ **日期**：2026-08-07 ｜ **配套文档**：《中药材细胞器基因组鉴定方法学技术方案（生信部分）v1.0》
**本文档定位**：把技术方案翻译成可执行的 Nextflow（DSL2）工程设计。模块可用性均经 nf-core/modules 官方仓库与 Bioconda 实测核验（2026-08-07）。

---

## 1. 总体技术选型

| 决策点 | 结论 | 理由 |
|---|---|---|
| 语言版本 | **Nextflow DSL2**（≥23.10，建议 24.x LTS） | 模块化/subworkflow 是 DSL2 原生能力 |
| 工程模板 | **`nf-core pipelines create` 脚手架**（即使不申请入 nf-core 官方组织） | 白得 nf-test 测试框架、GitHub Actions CI、参数校验（schema_input）、MultiQC 集成、版本追踪 |
| 运行环境 | **容器优先**（Docker/Singularity profile），conda 仅作开发兜底 | 方法学可审计性要求版本锁定；biocontainers 自动镜像 |
| 数据分流 | **samplesheet 驱动的单入口三分支** | 不按样本来源建三条 pipeline，一份 samplesheet 按数据列自动路由场景 A/B/C |
| 阈值管理 | 方案中全部【待验证】阈值 → **集中在 `nextflow.config` 的 params** | 前置实验标定后只改 config，不改代码 |

---

## 2. 单入口三分支架构（核心设计）

### 2.1 samplesheet 设计（唯一输入）

`samplesheet.csv`：

```csv
sample,sr1,sr2,lr,group
S001,/data/S001_R1.fq.gz,/data/S001_R2.fq.gz,,leaf
S002,,,/data/S002_cyclone.fq.gz,root
S003,/data/S003_R1.fq.gz,/data/S003_R2.fq.gz,/data/S003_cyclone.fq.gz,voucher
```

路由规则（写在 main workflow 里，一目了然）：

| sr1+sr2 | lr | 路由 |
|---|---|---|
| 有 | 无 | **场景 A**（仅二代） |
| 无 | 有 | **场景 B**（仅三代） |
| 有 | 有 | **场景 C**（混合，参考级） |

### 2.2 顶层流程骨架（`main.nf` 的分流逻辑）

```groovy
workflow {
    ch_input = Channel.fromList(samplesheetToList(params.input, "assets/schema_input.json"))

    // 按数据可得性分流
    ch_input.branch { meta, sr1, sr2, lr ->
        hybrid : sr1 && lr          // 场景 C
        sr_only: sr1 && !lr         // 场景 A
        lr_only: !sr1 && lr         // 场景 B
    }.set { ch_branched }

    // 公共层：质控与预检（第 2 章）
    QC_SHORT ( ch_branched.sr_only.mix(ch_branched.hybrid) )   // fastp
    QC_LONG  ( ch_branched.lr_only.mix(ch_branched.hybrid) )   // nanoplot+chopper
    SCREEN_CONTAM ( ch_all_clean )                              // kraken2 自建库

    // 三场景子工作流
    ORGANELLE_SR ( QC_SHORT.out.sr_only )                       // 场景 A
    ORGANELLE_LR ( QC_LONG.out.lr_only )                        // 场景 B
    ORGANELLE_HYBRID ( QC_SHORT.out.hybrid, QC_LONG.out.hybrid )// 场景 C

    // 共用判定层
    IDENTIFY ( ch_assemblies.mix(ch_sr, ch_lr, ch_hybrid) )
    MULTIQC_REPORT ( ch_all_qc.collect() )
}
```

**设计要点**：场景 C 不是 A+B 的简单叠加——它多出"三代骨架→二代抛光→分区域验收→归档"四个独有模块（5.3 节）；但 QC 层完全复用。

---

## 3. 模块盘点（实测，2026-08-07）

### 3.1 直接安装现成的 nf-core 模块

```bash
nf-core modules install fastp
nf-core modules install kraken2/kraken2
nf-core modules install minimap2/align
nf-core modules install nanoplot
nf-core modules install nanocomp
nf-core modules install chopper
nf-core modules install filtlong
nf-core modules install flye
nf-core modules install racon
nf-core modules install canu
nf-core modules install bcftools/call
nf-core modules install bcftools/consensus
nf-core modules install bandage/image
nf-core modules install samtools/depth
nf-core modules install samtools/faidx
nf-core modules install samtools/flagstat
nf-core modules install seqkit/seq
nf-core modules install iqtree
nf-core modules install multiqc
nf-core modules install custom/dumpsoftwareversions
```

### 3.2 需要自研的本地模块（bioconda 均有包 → 容器可自动生成）

| 模块 | Bioconda 包 | 开发量 | 说明 |
|---|---|---|---|
| `getorganelle` | ✅ getorganelle | 小 | 叶绿体 + nrDNA 两个 `-F` 模式各封装一次 |
| `novoplasty` | ✅ novoplasty | 小 | 场景 A 互验用 |
| `mitofinder` | ✅ mitofinder | 小 | 动物线粒体；也接收 contig 输入（场景 B/C 复用） |
| `pmat2` | ✅ pmat2 | 中 | 三代核心模块，注意内部要装 nextdenovo/canu 依赖（见 4.2） |
| `polypolish` | ✅ polypolish | 小 | 抛光候选路线 P1 |
| `coverage_check` | —（Python/awk 脚本） | 小 | 覆盖洼地检测（质控三件套之一，自写） |
| `numt_screen` | —（脚本 + blast） | 中 | NUMT/NUPT/MTPT 筛查 |
| `diagnostic_sites` | —（脚本） | 中 | 诊断位点提取与判定打分（判定层核心，自写） |
| `annotate_plastome` | agora/mfannot 可选 | 中 | 见 4.3 注释的本地化处理 |

> **容器生成提示**：bioconda 有包的工具，可用 Seqera Wave（`wave.seqera.io`）直接生成 Singularity/Docker 镜像，写进 module 的 `container` 指令，无需自己维护 Dockerfile。

---

## 4. 自研模块开发要点

### 4.1 模块骨架示例（`modules/local/pmat2/main.nf`）

```groovy
process PMAT2_AUTOMITO {
    tag "$meta.id"
    label 'process_high'

    conda "bioconda::pmat2=latest bioconda::nextdenovo bioconda::canu"
    container "oras://community.wave.seqera.io/library/pmat2_nextdenovo_canu:latest"

    input:
    tuple val(meta), path(lr)
    val taxo   // 0=plant, 1=animal, 2=fungi —— 来自 params 或 meta

    output:
    tuple val(meta), path("*/assembly_result/*.fa"), emit: assembly
    tuple val(meta), path("*/*.gfa"), optional: true, emit: gfa
    path "versions.yml", emit: versions

    script:
    """
    PMAT autoMito -i $lr -o ${meta.id}_pmat2 \\
        -t ont -x $taxo \\
        -S nextdenovo -C canu -N nextdenovo \\
        -T $task.cpus
    """
}
```

**注意**：PMAT2 的 `-x`（类群）参数建议放进 samplesheet 的 `group` 列映射（leaf/root/animal → 0/0/1），让每个样本自带路由信息。

### 4.2 覆盖洼地检测（`modules/local/coverage_check`）

方案 3.5 的质控三件套之一，核心逻辑（嵌入模块的 Python 脚本）：

```python
# 输入: samtools depth 输出；规则: 局部深度 < 全序列深度中位数 × params.coverage_valley_ratio (默认0.2)
# 输出: valley_regions.bed + qc_status.json (PASS/WARN/FAIL)
# FAIL → 该样本组装降级为草稿级（写入 meta.assembly_grade = "draft"）
```

**关键**：判定结果写进 `meta`（如 `meta.assembly_grade`），下游判定层模块根据 meta 决定报告中如何标注——这是 Nextflow 里"质控路由"的标准做法。

### 4.3 注释的本地化处理（重要提醒）

方案里的 PlastidHub/GeSeq 是**在线服务**，不能直接进 Nextflow 生产流程。处理策略：

- **自动化层**：本地注释工具封装（AGORA 或 MFannot，动物线粒体直接用 MitoFinder 自带注释）；
- **人工复核层**：参考级序列（场景 C 产物）出流程后人工提交 PlastidHub 复核——写入操作规程而非 pipeline；
- 叶绿体注释结果须带证据标记，注释争议区（如 IR 内基因边界）在报告中标注。

---

## 5. 子工作流与方案的章节映射

| 子工作流（`subworkflows/local/`） | 对应方案章节 | 组成模块 |
|---|---|---|
| `QC_SHORT` | 2.1 | fastp |
| `QC_LONG` | 2.2 | nanoplot → chopper/filtlong（阈值读 params，不写死） |
| `SCREEN_CONTAM` | 2.3 | kraken2/kraken2（自建库路径走 params） |
| `ORGANELLE_SR` | 3.1–3.6 | getorganelle(×2模式) → novoplasty 互验 → mitofinder → minimap2/align 回贴 → samtools/depth → coverage_check → bandage/image |
| `ORGANELLE_LR` | 4.2–4.5 | 植物: pmat2 ∥ (minimap2 提取→flye)；动物: minimap2 多参考提取 → flye → mitofinder + numt_screen；racon 抛光 + 同聚物标记脚本 |
| `ORGANELLE_HYBRID` | 5.2–5.5 | 三代骨架（复用 LR 模块）→ 双抛光路线（polypolish ∥ bcftools/call+consensus）→ 修改留痕脚本 → 分区域验收 → 归档打包 |
| `IDENTIFY` | 6.1–6.4 | minimap2 比对参考库 → diagnostic_sites → seqkit/seq 提取共有区 → iqtree → 判定汇总（正品/非正品/无法判定） |
| `REPORT` | 全文 | multiqc + custom/dumpsoftwareversions + 判定结果 JSON/PDF 汇总 |

---

## 6. 配置体系（params 与 profiles）

### 6.1 方案中的【待验证】阈值 → 全部进 params

```groovy
// nextflow.config —— 前置实验标定后只需改这里
params {
    // —— 公共层 ——
    kraken_db              = null      // 自建中药专用库路径（强制必填）
    reference_lib          = null      // 自建参考库（强制必填，版本化管理）
    // —— 三代（第 8.1 节标定）——
    lr_min_qscore          = 7         // 【待验证：按实测 Q 值分布定】
    lr_min_length          = 1000
    // —— 质控（第 3.5 节）——
    coverage_valley_ratio  = 0.2       // 覆盖洼地判定系数
    // —— 判定层（第 8.3 节标定）——
    its2_heterozygosity_max= 0.02      // 疑似杂交阈值【待验证】
    uncertain_zone_delta   = null      // 判定灰区阈值【待验证】
    blind_accuracy_gate    = 0.95      // Phase 0 筛选阈值
    // —— 抛光（第 5.3 节）——
    polish_routes          = 'both'    // both|polypolish|consensus（首轮对照后定终选）
    min_insert_size_polypolish = 200   // 小插入文库自动跳过 Polypolish
}
```

### 6.2 profiles

```groovy
profiles {
    docker      { docker.enabled = true }
    singularity { singularity.enabled = true; singularity.autoMounts = true }
    test        { includeConfig 'conf/test.config' }        // 微型测试数据
    test_full   { includeConfig 'conf/test_full.config' }   // 8.1 转移验证数据集
    slurm       { includeConfig 'conf/slurm.config' }
}
```

---

## 7. 参考库与数据库的版本化管理

| 资产 | 管理方式 |
|---|---|
| 自建正品-伪品参考库（fasta + 元数据） | **独立 git 仓库 + 版本标签**（如 reflib-v0.1），pipeline 只读引用路径；参考级序列按方案 5.5 归档清单配套存储 |
| Kraken2 自建库 | 独立 utility pipeline 从参考库自动构建，与参考库同版本号 |
| 近缘参考（场景 B 提取诱饵） | `assets/references/` 固定副本，随 pipeline 仓库分发（git-lfs） |
| 判定阈值 | `nextflow.config` + `params.json` 模板随版本发布，阈值变更即发新版 |

**纪律**：参考库、Kraken 库、阈值三者**同版本号发布**——任何一次鉴定报告都能凭版本号完整复现。

---

## 8. 测试与 CI

1. **nf-test**：每个自研模块至少一个正向测试 + 一个边界测试（如低覆盖样本触发 coverage_check FAIL 的路由）；
2. **test profile**：KB 级模拟数据（可用公共叶绿体 fasta 切 reads 模拟），`nextflow run . -profile test,docker` 三分钟跑完全流程冒烟测试；
3. **test_full profile**：对应方案 8.1 的 2–3 个转移验证样本，作为每次发版前的回归测试；
4. **GitHub Actions**（nf-core 模板自带骨架）：PR 触发 nf-test + test profile；release 触发 test_full。

---

## 9. 开发路线图（与前置验证实验对齐）

| 阶段 | 内容 | 出口标准 |
|---|---|---|
| **M1（2–3 周）** | 脚手架 + 公共层 + 场景 A（ORGANELLE_SR + IDENTIFY 简版） | test profile 通过；真实二代样本产出叶绿体+nrDNA |
| **M2（2–3 周）** | 场景 B（PMAT2 模块、动物提取子集路线、racon、同聚物标记） | 配合方案 8.1 转移验证跑通，产出错误谱报告 |
| **M3（2–3 周）** | 场景 C（双抛光路线、分区域验收、归档打包） | 凭证样本产出参考级序列 + 完整归档包 |
| **M4（与 8.2/8.3 并行）** | 下采样曲线脚本集成、判定层阈值标定、增益试点数据回流 | params 终值定稿，判定层转正 |
| **M5** | nf-test 补全、文档、v1.0 发版 | CI 全绿，版本三件套（参考库/库/阈值）同号发布 |

---

## 10. 风险提示（开发期）

1. **PMAT2 的容器**：bioconda 有包，但其内部调用 nextdenovo/canu——容器需用 Wave 把三个包打在一起并实测（4.1 骨架已体现）；
2. **GetOrganelle 的默认数据库**：首次运行会联网下载种子库，生产环境须预先 `curl` 到本地并参数化指向，避免计算节点无外网时失败；
3. **Kraken2 内存**：自建库若做大（含真菌+污染物）注意内存档位 `label 'process_high_memory'`；
4. **判定层不要过早自动化**：M1–M3 阶段 diagnostic_sites 输出建议人工复核后再写报告，阈值标定（M4）完成前全自动判定有合规风险；
5. nf-core 模板会带 lint 规则（`nf-core lint`），自研模块按规范写（meta map、versions.yml 输出）可一次过审，也为将来贡献回社区留路。

---

**下一步建议**：确认路线图后，我可以直接为您生成 M1 阶段的完整可运行工程骨架（脚手架文件 + 公共层与场景 A 的全部模块/subworkflow 代码 + test profile 的模拟数据脚本），您在本地 `nextflow run` 即可开始迭代。
