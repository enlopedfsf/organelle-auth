## 1. fastp 模块 + QC_SHORT(experimental profile)

- [x] 1.1 `nf-core modules install fastp`(✓ 已装 `modules/nf-core/fastp` + modules.json;8 个 container_configs 已重生 → issue #2 核心消除,待 CI 确认)
- [ ] 1.2 fastp 参数(`--detect_adapter_for_pe --qualified_quality_phred 15 --length_required 50`,方法 §2.1)仅写入 `conf/experimental.config`;production 中为 `null`(ENG-POL-001)
- [ ] 1.3 QC_SHORT 子流程:fastp → clean reads + fastp HTML/JSON 报告

## 2. 自建 GetOrganelle 模块 + PLANT_SR_ASSEMBLY

- [ ] 2.1 自建 `modules/local/getorganelle`(bioconda;Wave/biocontainer 镜像,固定 tag+digest;输出 `versions.yml`)
- [ ] 2.2 两条命令(方法 Scenario A):`-F embplant_pt -R 15 -k 21,45,65,85,105` 与 `-F embplant_nr -k 35,85,115`,由 `targets` 路由
- [ ] 2.3 PLANT_SR_ASSEMBLY 子流程:按接口合同产出 `*_plastome.fasta`(环化,CANDIDATE)或 `*_plastome.scaffold.fasta`(DRAFT)+ `*_nrdna.fasta` + 组装图;**不强环化**(§3.6/§5.2)
- [ ] 2.4 tool registry:getorganelle 填 `container_digest`,admission 保持 CONDITIONAL

## 3. Read-back 证据(ASSEMBLY_QC)

- [ ] 3.1 `nf-core modules install minimap2/align`(用 `-ax sr`)+ `samtools/depth` + `samtools/flagstat`
- [ ] 3.2 ASSEMBLY_QC 子流程:clean reads `-ax sr` 回贴组装 → sorted BAM → depth/flagstat
- [ ] 3.3 覆盖洼地系数从 policy 读(experimental `null` → 仅标注,不硬编码);写入 `evidence_files`

## 4. 组装阶段状态输出

- [ ] 4.1 status emitter:产 `stage=assembly_qc` 状态 JSON,符合 `assets/schema_status.json`,字段取值严格按 design "①→② 接口合同"第 3 节
- [ ] 4.2 `reason_codes.yaml` 新增 `NO_CIRCULARIZATION`、`ASSEMBLY_FAILED`、`COVERAGE_ANOMALY`(各附 category+meaning)
- [ ] 4.3 `decision=NOT_APPLICABLE`(① 不判定);`evidence_files` 按接口合同第 2 节

## 5. 路由接入

- [ ] 5.1 `ORGANELLEAUTH` 工作流:对 `taxon_group=plant` + 短读长可得 + `targets⊂{plastome,nrdna}` 的样本,接入 QC_SHORT → PLANT_SR_ASSEMBLY → ASSEMBLY_QC(显式路由,DATA-006)

## 6. 测试(T1–T3)

- [ ] 6.1 T1:getorganelle / fastp / minimap2 模块 nf-test(正常 + 边界)
- [ ] 6.2 T2:子流程分支与状态传播(环化→CANDIDATE/PASS;未环化→DRAFT/WARN+NO_CIRCULARIZATION;失败→FAIL+ASSEMBLY_FAILED)
- [ ] 6.3 T3:微型数据 pipeline smoke(进 CI);nf-test.yml 启用

## 7. 验证 + issue #2

- [ ] 7.1 本地跑正常刻叶紫堇样本(`corydalis_test/`,SRR38978846 抽稀 ~2Gb)端到端;组装叶绿体与 **PZ405204** 高度一致(记录一致性证据,留验证记录,不进 CI)
- [~] 7.2 issue #2:8 个 container_configs **已重生(fastp 安装触发,本地可见)** → 待 push 后 CI 确认 lint 这 8 项归零;再按恢复判据处理(PR 模板那 1 项仍 advisory,另议)。**进度见 RESUME.md**
- [ ] 7.3 全程零硬编码科学阈值(fastp 仅 experimental;GetOrganelle -R/-k 为工具参数;覆盖系数 policy 注入)
