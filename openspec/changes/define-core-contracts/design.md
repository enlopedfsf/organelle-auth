## Context

M0 (`bootstrap-nfcore-repository`) 已归档,5 个规范域生效(16 条 requirement)。本 change(§23 #2)填充这些规范域所**引用但仍为占位**的可执行契约文件:concrete samplesheet schema、status schema + reason-code 字典、tool/hypothesis 注册表、policy/compatibility 框架。设计受总方案 §4.1/4.2/5.5/8.2/8.3/9.2/9.4/10.3 + 已商定的差异修正(D1.x–D5.x、D-AC、D-C、D3.4)约束。不引入任何流程逻辑、任何阈值数字(全 `null`)。

## Goals / Non-Goals

**Goals**
- 产出 `schema_input.json`、`schema_status.json`、`reason_codes.yaml`、`tools.yaml`(13 候选 + 7 PROHIBITED)、`hypotheses.yaml`(状态机 + 完整 HYP-DNA-001)、`policies/` 框架 + experimental 示例、compatibility manifest。
- 扩展 `spec-and-schema` CI:真实 schema 校验 + 两份 samplesheet 夹具断言 + PROHIBITED 工具 grep。
- production-null 拒绝(ENG-POL-002)以设计说明 + fixture 落地。

**Non-Goals**
- 不写任何 Nextflow module/subworkflow、不写 policy-loader 代码(M0 仅设计说明 + fixture)。
- 不填任何标定阈值(全 `null`)、不放参考 FASTA。
- 不改 `validation-and-go-no-go` 规范域(本轮无新要求)。

## Decisions

### 决策 1:ADDED(非 MODIFIED)requirements
向 4 个既有域**追加**可执行契约要求,不重写既有行为要求。既有要求(DATA-003 真值隔离、工具准入五级制、状态模型…)含义不变;本 change 追加让它们机器可校验的 schema/registry 契约。

### 决策 2:DATA 分层 —— schema 可表达 vs 需测试/设计
`schema_input.json` 完全表达 DATA-001(schema 校验)+ DATA-003(禁真值列)+ 部分 DATA-002/004。**DATA-005(运行时 fail-fast)、DATA-006(禁隐式推断)、DATA-007(对照作正式样本)** 是运行时/preflight 行为 → CI 测试断言 + 设计说明,而非列 schema 单独能实现。避免"一个 schema 覆盖 7 条 DATA"的陷阱。

### 决策 3:tools.yaml PROHIBITED 区(用户 D3.4)
7 条(medaka / Nanopolish / Clair3-ONT + Oatk / TIPPo / MitoHiFi / hifiasm),每条带 `reason`(方法学 §7.2 模型绑定层:无 CycloneSEQ 兼容模型)+ `re_evaluation_trigger`。头部注释区分:**PROHIBITED** = 当前有明确科学理由禁用;**DEFERRED** = 暂无条件评估、证据到位可激活。

### 决策 4:PROHIBITED CI 强制 —— 便宜 T0 grep
在 `check_schema_traceability.py` 增加一个 grep,扫描 `modules/` + `conf/` 是否出现 7 个 PROHIBITED 工具名(作为 process/container),命中即失败。**代价小 → 现在实现**(不过度工程)。

### 决策 5:production-null 拒绝(ENG-POL-002)—— 设计说明 + fixture,不写 loader
M0 不写 policy-loader 代码(无分析模块)。提供:(a) §9.2 experimental 示例(阈值全 null);(b) 设计说明:production loader 行为(任何规则引用的阈值为 null 即 fail-fast);(c) `tests/fixtures/policy_all_null.yaml` + 测试桩断言"未来 loader 必须拒绝"。loader 代码随 M1 第一个消费 policy 的模块落地。

### 决策 6:HYP-DNA-001 逐字誊抄 §9.4
含 `metric_definitions` 双指标区分(提取 DNA 片段分布 vs 测序 read N50)。`status: proposed`,`validation_protocol: null`。

### 决策 7:reason_codes.yaml 空框架 + 3 示例
3 个示例码覆盖三类:`INSUFFICIENT_JUNCTION_SUPPORT`(scientific INCONCLUSIVE)、`LOW_COVERAGE`(WARN)、`TOOL_MISSING_DIGEST`(engineering FAIL)。框架可扩展;pipeline failure 与 scientific INCONCLUSIVE 分开编码。

### 决策 8:JSON Schema 选型
`schema_input.json` / `schema_status.json` 用 JSON Schema **Draft 2020-12**(若 nf-schema 运行期校验有更窄约束,以 nf-schema 为准并在此注明)。字段命名与 §4.1/§5.5、既有规范域术语一致。

## Risks / Trade-offs

- **[schema 越界声称覆盖 DATA]** → 决策 2 把 DATA-005/006/007 明确归到测试/设计,不在 schema 里假声称。
- **[PROHIBITED grep 误报/漏报]** → grep 仅匹配 process/container 行的工具名 token;范围写在脚本注释。
- **[production-null 在 M0 无 loader 兜底]** → 设计说明 + fixture + M1 loader 追踪(见决策 5)。
- **[JSON Schema 方言]** → 决策 8 选 Draft 2020-12,若与 nf-schema 冲突以 nf-schema 为准。

## Migration Plan

Greenfield 契约(无前序版本)。回滚 = 删除新增文件 + 回退 `spec-and-schema`/`check_schema_traceability.py` 扩展。

## Open Questions

- 3 个示例 reason code 的最终命名(可延后;决策 7 已给代表样)。
- JSON Schema draft 与 nf-schema 运行期校验的最终对齐(可延后;决策 8 已给默认)。
