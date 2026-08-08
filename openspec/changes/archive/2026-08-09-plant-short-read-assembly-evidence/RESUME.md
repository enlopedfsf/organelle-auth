# RESUME — plant-short-read-assembly-evidence (M1-①) apply

> 会话暂停点。新会话从此文件续。change: `plant-short-read-assembly-evidence`(M1-①)。

## 已完成 / Completed
- **Propose 完成 + 校验通过**:proposal / specs(plant-short-read-analysis)/ design(含"①→② 接口合同")/ tasks 已写;`openspec validate --strict` 通过。
- **fastp 真模块已装**:`modules/nf-core/fastp/`(main.nf/meta.yml/environment.yml/tests)+ modules.json 登记。
- **issue #2 的 8 个 `container_configs` 已重生**:`conf/containers_*.config` 现含 fastp 条目(本地可见;待 push 后 CI 确认这 8 项 lint 归零)。issue #2 的第 9 项(PR 模板)仍 advisory。

## 下一步从哪续 / Resume from
建议顺序:**3.1**(装 `minimap2/align` + `samtools/depth` + `samtools/flagstat`,快速 nf-core 安装)→ **2.1**(自建 `modules/local/getorganelle`)→ 2.2/2.3(两条 `-F` 命令 + PLANT_SR_ASSEMBLY 子流程)→ 3.2/3.3(read-back ASSEMBLY_QC)→ 4(status emitter @ stage=assembly_qc)→ 5(路由接入 ORGANELLEAUTH)→ 6(T1–T3)→ 7.1(真实数据验收)→ 7.2/7.3 → push/CI → merge → archive。

**首个动作**:task 3.1 + 2.1(装 read-back 模块 + 起自建 GetOrganelle 模块)。

## 已知风险 / Known risks
- **Wave/biocontainer 构建自建 GetOrganelle**:bioconda `getorganelle 1.7.2`(noarch,依赖 spades/blast 等,镜像可能较大)→ Wave 构建;网络 + 构建时间,失败面不小。失败则降级 conda 兜底(**仅开发,非 production 可重复性唯一来源**)。
- **GetOrganelle 真实数据耗时**:`~2Gb 刻叶紫堇子样本上约 **30–90 分钟**(计算密集,在工作站跑,不进 CI)。
- **网络依赖**(走代理 `http://127.0.0.1:10808`):nf-core modules 仓库(装模块)、Wave registry(容器构建)、NCBI(下 PZ405204)。
- **PZ405204 参考尚未下载**:task 7.1 需先用 NCBI datasets/efetch 取 GenBank PZ405204(刻叶紫堇叶绿体)做一致性比对。
- **fastp 参数**:仅 experimental profile(ENG-POL-001),不得漏进 production 默认值。
- **GetOrganelle `-R`/`-k`**:工具算法参数(非科学阈值),模块内保持此定性。

## 数据 / Data
- 刻叶紫堇 reads:`/mnt/ssd_pool/home/iris-hp/zhongyao/corydalis_test/SRR38978846_{1,2}.fastq.gz`(~2.2GB ×2)。
- 参考(待取):GenBank **PZ405204**。
- 正常场景:抽稀 ~2Gb(task 7.1)。

## 关键引用 / Key refs(仓内)
- `design.md` "①→② 接口合同"——冻结的输出契约(② 必须消费,不得重发明)。
- 方法学 §2.1(fastp)、§3.1/§3.2(GetOrganelle 两命令,逐字)。
- issue #2(lint 恢复判据)+ `docs/decisions/m0-lint-advisory-deviations.md`。

## 分支 / Branch
`feat/plant-short-read-assembly-evidence`(本提交)。**尚未开 PR**(apply 未完成)。

## M1 全局提醒
M1 = ①(本变更)+ ②(`plant-short-read-identify`,新会话)。① 归档后再做 ②;两个都归档 = M1 完成。
