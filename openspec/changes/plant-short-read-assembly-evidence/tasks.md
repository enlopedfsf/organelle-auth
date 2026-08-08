## 1. fastp 模块 + QC_SHORT(experimental profile)

- [x] 1.1 `nf-core modules install fastp`(✓ 已装 `modules/nf-core/fastp` + modules.json;8 个 container_configs 已重生 → issue #2 核心消除,待 CI 确认)
- [x] 1.2 fastp 参数(`--qualified_quality_phred 15 --length_required 50`,方法 §2.1)以 `process.withName:FASTP.ext.args` 仅写入 `conf/experimental.config`;`--detect_adapter_for_pe` 内置于 nf-core fastp PE 分支;production/test 不设 → 默认 `''`(ENG-POL-001)。**零硬编码审计通过:Q15/len50 仅出现于 experimental.config**
- [x] 1.3 QC_SHORT 子流程:`subworkflows/local/qc_short`(fastp → clean reads + JSON/HTML/log)+ meta.yml

## 2. GetOrganelle(nf-core 模块)+ PLANT_SR_ASSEMBLY

- [x] 2.1 装 nf-core `getorganelle/fromreads` + `getorganelle/config`(v1.7.7.1,quay.io/biocontainers);**前提变更:原"自建(nf-core 无)"已失效,apply 期改用 nf-core 模块**(决策 4 已更新;TEST-007)。minimap2/align + samtools/sort+index+depth+flagstat 同批安装
- [x] 2.2 两条 Scenario A 算法参数(经 `ext.args`,逐字):plastome `-R 15 -k 21,45,65,85,105`、nrdna `-k 35,85,115`,经 `GETORGANELLE_FROMREADS_PT/_NR` 别名在 `conf/modules.config` 注入(全 profile 一致,工具参数);`-k` 源 = GetOrganelle 官方 README(注释已注明,满足逐字约束)
- [x] 2.3 本地**输出适配模块** `modules/local/getorganelle_result_adapter`(检测环化 graph1.1→CANDIDATE,否则 scaffold→DRAFT,否则 NOT_APPLICABLE;采 fastg;按①→②接口合同命名);PLANT_SR_ASSEMBLY 子流程:`config→fromreads(pt/nr)` → 适配(别名单实例化)→ join;**不强环化**(§3.6/§5.2);meta.yml 齐
- [x] 2.4 tool registry:`getorganelle` 填 `container_digest`(`quay.io/biocontainers/getorganelle:1.7.7.1--pyhdfd78af_0@sha256:8254b6f5…`,skopeo 实测),admission 保持 CONDITIONAL

## 3. Read-back 证据(ASSEMBLY_QC)

- [x] 3.1 `nf-core modules install minimap2/align`(ext.args=`-x sr`)+ `samtools/index` + `samtools/depth` + `samtools/flagstat`(+ `samtools/sort` 装但未用:minimap2/align `bam_format=true` 内置 samtools sort 直接产 sorted BAM;sort 为冗余,lint 阶段可删)
- [x] 3.2 ASSEMBLY_QC 子流程:`subworkflows/local/assembly_qc`(clean reads `-x sr` 回贴 → sorted BAM → index → depth/flagstat;未产出 plastome 的样本经 `TOUCH_READBACK_MARKERS` 走 ASSEMBLY_FAILED 路径)+ meta.yml
- [x] 3.3 覆盖洼地系数 `params.coverage_valley_coefficient`(policy 注入,experimental `null` → 仅标注,**零硬编码审计:代码中无任何数字系数**);emitter 把 readback/depth/flagstat 写入 evidence_files

## 4. 组装阶段状态输出

- [x] 4.1 status emitter `modules/local/emit_assembly_qc_status`:产 `stage=assembly_qc` 状态 JSON,符合 `assets/schema_status.json`(stub 输出已 schema 校验通过);字段取值严格按 design "①→② 接口合同"第 3 节;证据按合同路径 staging
- [x] 4.2 `assets/reason_codes.yaml` 新增 `NO_CIRCULARIZATION`(warn)、`ASSEMBLY_FAILED`(engineering_fail)、`COVERAGE_ANOMALY`(scientific_inconclusive)
- [x] 4.3 `decision=NOT_APPLICABLE`(① 不判定,字面量);`evidence_files` 按接口合同第 2 节(选定 plastome / nrdna / sorted.bam / depth.tsv / flagstat.txt / assembly_graph.fastg)

## 5. 路由接入

- [x] 5.1 `workflows/organelleauth.nf`:对 `taxon_group=plant` + `has_short_reads` + `targets⊂{plastome,nrdna}`(含 plastome)的样本,显式接入 QC_SHORT → PLANT_SR_ASSEMBLY → ASSEMBLY_QC → EMIT(DATA-006;不从文件名推断);samplesheet reader 修正(`targets` CSV 定界串→列表;meta 携带路由字段)

## 6. 测试(T1–T3)

- [~] 6.1 T1:adapter 模块 nf-test 已写(`modules/local/getorganelle_result_adapter/tests/main.nf.test`,正常 CANDIDATE + 边界 NOT_APPLICABLE);**adapter/emitter 逻辑已用独立 bash/python 单元测试验证 3 分支全通过**;fastp/minimap2 复用 nf-core 自带测试(TEST-007)。⚠️ **本地 nf-test 无法执行:nf-test 插件索引 URL `askimed/nf-test-plugins/main/plugins.json` 返回 404(M0 基建问题,非本变更),需修 plugin 源后在 CI 跑**
- [x] 6.2 T2:子流程分支与状态传播逻辑已验证(环化→CANDIDATE/PASS;未环化→DRAFT/WARN+NO_CIRCULARIZATION;失败→FAIL+ASSEMBLY_FAILED)——emitter status_for() 单元测试 3 分支 + stub 端到端 12/12
- [x] 6.3 T3:pipeline smoke **stub 端到端 12/12 进程全完成,exit 0**(QC_SHORT→PLANT_SR_ASSEMBLY(pt+nr)→ASSEMBLY_QC→EMIT,status JSON schema 合规);**真实数据端到端已在 7.1 跑通(SRR38978846,PASS/CANDIDATE),getorganelle DB 资产已就绪**

## 7. 验证 + issue #2

- [x] 7.1 本地跑正常刻叶紫堇样本(SRR38978846 抽稀 ~2Gb,seed 11)端到端;组装叶绿体与 **PZ405204** 高度一致。**已通过(2026-08-08)**:plastome CANDIDATE(139,697 bp),mash 0.000881 / dnadiff AvgIdentity **99.95%** / minimap2 asm5 **0 mismatch**(≥99% 一致性 PASS);覆盖 91.97% 差额经 show-coords + mash 证实为 IR 重复表示伪影(两段 25,284 bp = IR 双拷贝,mash dist=0),非缺失序列;read-back 1079.6X。pipeline 绿,6 件 contract 产物齐全,状态 PASS/CANDIDATE。**验证记录见 `VALIDATION-7.1.md`**(证据数据在 `/home/iris-hp/corydalis_validation/`,不入 git)。**7.1 期发现并修复 3 个真实数据 bug:#3 embplant_pt 需同时配 embplant_mt DB、#4 emitter 容器内直写 outdir 致 PermissionError→改 work-dir+publishDir、#5 adapter 残留 .NONE 致 graph glob 匹配两文件→graph 被丢弃**
- [~] 7.2 issue #2:8 个 container_configs **已重生(fastp 安装触发)**;本变更新装 7 模块又生成更多 container_configs 条目 → 待 push 后 CI 确认 lint 归零。**进度见 RESUME.md**
- [x] 7.3 全程零硬编码科学阈值(**审计通过**:fastp 仅 experimental.config;GetOrganelle -R/-k 为工具参数置 modules.config;覆盖系数 policy 注入 params,代码零数字)
