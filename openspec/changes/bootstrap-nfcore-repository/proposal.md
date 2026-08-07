## Why

项目需要一个不会产生"多套真相"的工程骨架，作为后续所有科学模块（M1–M5）的地基。当前 `~/Project/organelle-auth` 仅有 OpenSpec 初始化结果与三份规范文档，尚无 nf-core 工程模板、版本控制、T0 CI 与协作治理模板。本 change 按《总方案 v1.1.1》§23 顺序 1，建立 Lean M0 的仓库基础：干净模板 + 最小门禁 + 规范域结构，确保"空 pipeline 能通过 lint、OpenSpec validate 和 schema tests"（§18 M0 完成定义）。

## What Changes

- 用当前稳定的 `nf-core pipelines create` 生成全新 vanilla 模板，**保留初始 vanilla commit** 以支持后续 `nf-core pipelines sync`（§12.1）；在现有 `~/Project/organelle-auth` 之上合并，保留既有 `openspec/`、`docs/inputs`、`docs/specification`、`.claude/`。
- 初始化**独立 git 仓库**：当前目录与所有父目录均非 git 仓库，无混合工作区问题（已实测），符合 §12.1"禁止在上层混合 Git 工作区中直接初始化本项目"。
- 建立 OpenSpec 首批 **5 个核心规范域**（§11.2）作为项目的需求分类轴，每个域写入 M0 级别的基础契约要求（来自 v1.1.1 已冻结条款，**不**含任何未经验证的科学细节或阈值）。
- **Lean M0 CI**：仅保留 3 个 GitHub Actions workflow（`spec-and-schema`、`lint`、最小模板检查），其余门禁随 milestone 启用（§12.7、§14.1）。
- **协作治理模板**：CODEOWNERS（职责分区，1–3 人团队可兼任，但科学行为变化与代码实现至少一次交叉审阅，§17.2）、PR 模板（含 OpenSpec change ID / 受影响 Requirement IDs / 科学行为是否变更 / breaking change / rollback，§17.3）、issue 模板（bug / scientific discrepancy / tool admission request / hypothesis status change / reference-policy update / feature request，§17.3）。
- 填充 `openspec/config.yaml` 的项目上下文（tech stack、规范来源、领域知识）。
- **纳入总方案并建立初始 Requirement 追踪矩阵**：确认并保留总方案 v1.1.1 于 `docs/specification/`（按 §0.2 冻结记录其校验和）；建立结构化追踪矩阵 `openspec/traceability.yaml`，覆盖 SCI-001..010、DATA-001..007、ENG-POL-001..005、TEST-001..007、REL-001..004、HYP-DNA-001 共 34 个 Requirement ID，每条映射 spec 域 / 实现区域 / 工程测试 / 科学验证 / Release 证据 / status / 目标 milestone（§19）；M0 初始矩阵中未实现项标记 `planned` 与目标 milestone，不伪造已验证。
- **不在本 change 范围（显式排除）**：`schema_input.json`/`schema_status.json` 内容、`registries/tools.yaml`、`hypotheses.yaml`（HYP-DNA-001 完整登记条目）、`policies/` 与 compatibility manifest 内容——这些属于下一个 change `define-core-contracts`（§23 顺序 2）。本 change 的追踪矩阵仅以一行引用 HYP-DNA-001 的状态与验证里程碑，不创建 `hypotheses.yaml` 文件内容。
- **不在本 change 范围**：任何生信模块、subworkflow、真实流水线逻辑（自 M1 起）、真实测试数据。
- **BREAKING**：无（首个仓库基线，无前序可破坏的对外契约）。

## Capabilities

### New Capabilities

按《总方案 v1.1.1》§11.2，首批只建立以下 5 个核心规范域，每个域本 change 仅承载 M0 级别的基础契约（已冻结的治理/合同/状态条款）：

- `scope-routing-and-input`：项目范围（三个 entry workflow + 明确非目标，§1.2）、显式路由原则（禁止从文件名/目录名/数据可得性隐式推断分析意图、分类群或参考级资格，§3.3 / DATA-006）、输入合同结构（samplesheet 最小字段与真值隔离 DATA-003）。具体 schema 字段约束留给 `define-core-contracts`。
- `asset-tool-and-policy`：资产输入合同（reference_pack/policy_pack/tool_registry/hypothesis_registry/compatibility_manifest/container_lock 各带 ID/版本/校验和等，§4.3/§10）、工具准入五级制（APPROVED/CONDITIONAL/EXPERIMENTAL/DEFERRED/PROHIBITED，§8.1）、policy pack 的 null 与未验证阈值禁止进 production（ENG-POL-001/002/003）、hypothesis registry 状态机（§9.4）、compatibility manifest 独立版本（§10.3）。具体工具条目与首条假设留给 `define-core-contracts`。
- `evidence-decision-and-status`：证据类别（E1–E6，§7.1）、判定规则从 reference pack 读取而非硬编码（§7.2）、状态输出模型（status=PASS/WARN/FAIL/INCONCLUSIVE；assembly_grade；decision；reason code 来自版本化字典，§5.5）、SCI 硬约束（SCI-003 纯 CycloneSEQ 不得单独终判、SCI-005 证据不足输出 INCONCLUSIVE、SCI-006 植物线粒体研究级、SCI-007 动物核 marker 不统一硬编码 ITS2、SCI-008 reads 比例≠质量比例等）。
- `validation-and-go-no-go`：工程测试与科学验证必须分离（§13.1）、CycloneSEQ 转移验证/下采样/盲样框架（§15）、Go/No-Go 指标（§15.4）、禁止用验证集反向调阈值后冒充独立验证（§3.2 禁止行为）、SCI-010 诊断位点须独立发现与独立验证集确认。
- `provenance-and-release`：每次运行最小审计包（§16.3）、参考级序列归档清单（§16.4）、版本对象与 Pipeline SemVer 规则（§16.1/16.2，阈值/位点/判定规则变化不得仅作 PATCH）、发布门禁（REL-001..004，REL-004 禁止无痕覆盖）、checksums/RO-Crate。

### Modified Capabilities

无（首个 change，尚无既有 spec 可修改）。

## Impact

- **新增仓库结构**：`main.nf`、`nextflow.config`、`nextflow_schema.json`、`conf/`、`modules/`、`subworkflows/`、`workflows/`、`.github/`、`lib/`、`assets/`、`tests/`、`nf-test.config`、`CHANGELOG.md`、`README.md`、`.gitignore`、`.gitattributes` 等 nf-core 模板文件。
- **新增/调整**：`openspec/specs/<5 个域>/spec.md`、`openspec/config.yaml`（项目上下文）、`openspec/traceability.yaml`（Requirement 追踪矩阵，34 个 ID）、`.github/workflows/{spec-and-schema,lint}.yml` 及最小模板检查 workflow、`.github/CODEOWNERS`、`.github/ISSUE_TEMPLATE/*`、`.github/PULL_REQUEST_TEMPLATE.md`。
- **工具依赖（apply 阶段）**：需安装 `nf-core` tools（按机房规则用 `~/miniconda3/bin/mamba`，禁用 `defaults` channel，扁平 env）；Nextflow 已具备（工作站既有）。
- **不影响**任何既有科学行为——本 change 只建工程骨架、契约域结构、CI 与治理模板；不引入任何工具容器、参考数据或可执行生信逻辑。
