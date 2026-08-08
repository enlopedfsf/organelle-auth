## 1. 输入 schema + 测试夹具

- [x] 1.1 `assets/schema_input.json` — 12 个 §4.1 字段 + 枚举 + 条件必填；强制 DATA-001(schema 校验)+ DATA-003(`additionalProperties:false` 禁真值列)
- [x] 1.2 `tests/fixtures/samplesheet_valid.csv` — 合法样本(identify + reference_build 两行),通过 schema
- [x] 1.3 `tests/fixtures/samplesheet_with_truth.csv` — 含 `expected_species` 真值列,被 schema 拒绝(DATA-003)
- [x] 1.4 DATA-005(fail-fast)/DATA-006(禁隐式推断)/DATA-007(对照作正式样本)—— CI 断言 + 设计说明(决策 2;运行时 loader 随 M1)

## 2. 状态 schema + reason codes

- [x] 2.1 `assets/schema_status.json` — 完整 §5.5 状态对象 + 三组枚举(status/assembly_grade/decision)
- [x] 2.2 `assets/reason_codes.yaml` — 空框架 + 3 个示例码(scientific-INCONCLUSIVE / WARN / engineering-FAIL)

## 3. 工具注册表

- [x] 3.1 `registries/tools.yaml` — §8.3 的 13 个候选,§8.2 条目结构,`container_digest`/`validation_record` 为 null
- [x] 3.2 PROHIBITED 区 7 条(medaka/Nanopolish/Clair3-ONT + Oatk/TIPPo/MitoHiFi/hifiasm),每条 `reason`(§7.2)+ `re_evaluation_trigger`
- [x] 3.3 文件头注释:PROHIBITED vs DEFERRED 语义区分

## 4. 假设注册表

- [x] 4.1 `registries/hypotheses.yaml` — §9.4 状态机 + 5 个状态含义
- [x] 4.2 HYP-DNA-001 完整誊抄 §9.4(statement/basis/scope_notes/metric_definitions 双指标/derived_fields/status proposed/validation_protocol null)

## 5. policy + compatibility manifest

- [x] 5.1 `policies/` 空框架(tcm-plant-experimental.yaml 为示例)
- [x] 5.2 `policies/tcm-plant-experimental.yaml` — §9.2 experimental 示例,阈值全 `null`
- [x] 5.3 production-null 拒绝设计说明(ENG-POL-002)+ `tests/fixtures/policy_all_null.yaml` + check 脚本校验 experimental 阈值全 null(loader 代码随 M1)
- [x] 5.4 `assets/compatibility_manifest.yaml` 空框架(§10.3:compatibility_id + 6 个独立版本字段)

## 6. CI 扩展(spec-and-schema / check_schema_traceability.py)

- [x] 6.1 用 `jsonschema` 校验 `schema_input.json` 合法 + 两份 samplesheet 夹具(valid 通过 / truth 被拒)
- [x] 6.2 校验 `schema_status.json` 合法 + 三组枚举闭合
- [x] 6.3 PROHIBITED 工具 grep:扫描 `modules/` + `conf/`,7 个禁入工具名出现即失败
- [x] 6.4 结构校验 `reason_codes.yaml` / `tools.yaml`(13+7,每条 reason+trigger)/ `hypotheses.yaml`(状态机 + HYP-DNA-001)/ `policies/` + compatibility manifest

## 7. 验证

- [x] 7.1 `openspec validate define-core-contracts --strict` 通过
- [x] 7.2 全部 YAML/JSON 语法有效、schema 自洽(check 脚本通过)
- [x] 7.3 本地 `/usr/bin/python3 .github/scripts/check_schema_traceability.py` → ALL T0 CONTRACT CHECKS PASSED
- [x] 7.4 契约文件无任何标定阈值数字(科学阈值全 `null`);无任何分析模块代码(hypotheses.yaml 的结构长度值属 §9.4 假设依据,非阈值)

---

### 收尾(apply 之后,与 bootstrap 同规矩)
- [ ] 8.1 feature 分支 `feat/define-core-contracts` 提交 + push + 开 PR(→ dev)
- [ ] 8.2 三个 T0 CI 变绿(spec-and-schema 含新增 schema/PROHIBITED 检查 / linting / template-check;lint 仍 advisory,见 m0-lint-advisory-deviations.md)
- [ ] 8.3 逐条核对验收标准(4 条)
- [ ] 8.4 merge → `/opsx:archive define-core-contracts`
