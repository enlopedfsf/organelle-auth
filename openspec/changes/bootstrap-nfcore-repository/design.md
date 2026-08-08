## Context

当前 `~/Project/organelle-auth` 仅含 `openspec/`（已 `openspec init --tools claude`）、`docs/inputs`、`docs/specification`、`.claude/`，尚无 nf-core 工程模板、版本控制、CI 与治理模板。经实测，该目录及其所有父目录均**非 git 仓库**，因此可在原地 `git init` 而不违反 §12.1"禁止在上层混合 Git 工作区中直接初始化"。动机见 `proposal.md - Why`；行为契约见 `specs/`。总方案 v1.1.1 已由用户预先置于 `docs/specification/`，本 change 据 §0.2 冻结记录其校验和后保留不动。

外部约束：工作站已具备 Nextflow；`nf-core` CLI 尚未安装，须按机房规则用 `~/miniconda3/bin/mamba`（禁 `defaults` channel、扁平 env）安装。§12.1 要求"用当前稳定 `nf-core pipelines create` 生成全新模板，保留初始 vanilla commit，便于后续 `nf-core pipelines sync`"。

## Goals / Non-Goals

**Goals:**
- 得到一个**单一 git 仓库**，其第一个 commit 是 nf-core vanilla 基线，OpenSpec 与既有规范文档在其之上叠加——使 `nf-core pipelines sync` 可对未来模板升级做可读 diff。
- 让"空 pipeline 能通过 lint、OpenSpec validate 和 schema tests"（§18 M0 完成定义）在 T0 CI 上可复现。
- 让任何未经验证的工具/阈值/假设，从仓库第一刻起就**无路可走**进入 production 默认值。
- 建立可被 CI 校验的初始 Requirement 追踪矩阵，覆盖 SCI/DATA/ENG-POL/TEST/REL/HYP 全部 34 个 ID，使每个 Requirement ID 从规范域可追溯到实现、测试、验证与 release。

**Non-Goals:**
- 不在本 change 实现任何生信模块、subworkflow、真实数据或真实测试集（M1 起）。
- 不固化 `schema_input.json`/`schema_status.json`/`registries`/`policies`/compatibility 的内容——属下一个 change `define-core-contracts`（§23 顺序 2）。
- 不寻求加入 nf-core 官方组织（§1 工程蓝图明确"即使不申请入 nf-core"）——本仓库仅借用模板脚手架，所有权归本项目。

## Decisions

### 决策 1：模板生成策略——staging 生成 + vanilla commit + 原地合并

用 `nf-core pipelines create` 在**临时 staging 目录**生成完整 vanilla 模板（含其自带 `git init` 与 vanilla commit），再把生成内容合并进现有 `~/Project/organelle-auth`，保留既有 `openspec/`、`docs/inputs`、`docs/specification`、`.claude/`。

**为何不直接在原地跑 `nf-core pipelines create`**：该命令会自行 `git init` 并按非空目录行为不可控地提示/覆盖，且会生成自己的 `docs/`、`README.md`、`.gitignore`，可能与既有内容冲突或吞掉既有文件。staging 法让 vanilla 基线 commit 干净可追溯，合并步骤完全可控。

**为何不手写 nf-core 风格骨架**：会丧失 `nf-core pipelines sync` 的模板同步能力与社区 lint 一致性，违背 §12.1 明确要求。

**`docs/` 冲突处理**：nf-core 模板生成 `docs/usage.md`、`docs/output.md` 等；本项目既有 `docs/inputs/`、`docs/specification/`。两者文件名不重叠，共存即可；不删除既有规范文档。

**合并载体**：staging 的 `.git` 也一并迁移，使 vanilla commit 成为该仓库的第一个 commit；既有 OpenSpec/docs 作为第二个 commit 叠加。

### 决策 2：Lean M0 CI 裁剪——只留 3 个 workflow

nf-core 模板自带一整套 GitHub Actions（lint、nf-test、pipeline smoke、AWS full 等）。按 §12.7 / §14.1，M0 **只保留 3 个**：`spec-and-schema.yml`（OpenSpec validate + JSON/YAML schema + 追踪矩阵）、`lint.yml`（nf-core lint + format + 基础 Markdown/link）、最小模板检查（template 结构自检）。其余 workflow 随 milestone 启用：nf-test-changed 与 pipeline-smoke 于 M1、scheduled-regression 于 M3、release 系列于 M5。

被裁掉的 workflow 不删除其文件而是**记录于 milestone 门禁表**，避免遗忘后续启用。

### 决策 3：`spec-and-schema` 是新增的自定义 workflow

nf-core 模板没有"OpenSpec validate"workflow，需自建：在 PR/push 上运行 `openspec validate`、校验 `assets/` 下 schema 与 `registries/`/`policies/`/`openspec/specs` 的 YAML 结构，并检查 Requirement 追踪矩阵无断链（矩阵结构在 `define-core-contracts` 填充，本 change 先建 workflow 骨架与空检查）。

### 决策 4：证据优先的"零默认值"擦洗

合并后立即检查：`nextflow.config`/`nextflow_schema.json`/`conf/*.config` 中**不得出现**任何本项目科学阈值作为有效默认值（CycloneSEQ Q 值、ITS2 杂合度、灰区、覆盖洼地比例、`insert_size<200` 跳 Polypolish 等）。未标定值一律 `null`，由 policy pack 在 production 启动时 fail-fast（ENG-POL-001/002）。模板自带的通用结构参数（如 `publish_dir`、`validateParams`、容器引擎开关）保留，因其不构成科学判定。

这同时把工程蓝图（`docs/inputs/Nextflow流程开发蓝图...`）里被总方案 §20 否决的写死阈值挡在仓库之外——蓝图仅作参考输入，不作为代码事实来源。

### 决策 5：Nextflow 版本由 manifest 固定，不写"24.x LTS"文字

按 §12.5，最低兼容版本写入 `manifest.nextflowVersion`，CI 覆盖最低支持版本与当前稳定版；不在文档/配置里写死易过期的"24.x LTS"描述。版本升级走独立 OpenSpec change。

### 决策 6：5 个规范域作为"已冻结基线"登记

把 v1.1.1 已冻结的 Requirement ID（SCI/DATA/ENG-POL/REL 等）在 M0 即登记进 5 个 spec 域，作为可追溯的设计基线（§0.1 闭环、§19 追踪矩阵）。各 Requirement 的**实现与测试状态**跨 M1–M5 推进，由追踪矩阵跟踪，不在本 change 的 spec 里声明"已实现"。这区别于 §11.2"不提前冻结依赖未验证证据的设计"——本 change 登记的是已通过评审的治理契约，非未验证科学数值。

### 决策 7：CODEOWNERS 为职责分区而非人数

按 §17.2，CODEOWNERS 划分 Nextflow/modules、methods/policies、reference schemas、GitHub Actions/security、reports/docs 五区；1–3 人可兼任，但科学行为变化与代码实现至少一次交叉审阅（PR 模板强制字段落实此约束）。

### 决策 8：Requirement 追踪矩阵的位置与形态

按 §19"完整矩阵在 M0 中转为结构化文件并由 CI 检查"，初始矩阵置于 `openspec/traceability.yaml`（与 `specs/` 同域，便于 CI 交叉校验）。覆盖 SCI-001..010、DATA-001..007、ENG-POL-001..005、TEST-001..007、REL-001..004、HYP-DNA-001 共 34 个 ID；每条含 spec 域、实现区域、工程测试层级、科学验证、Release 证据、status（`planned`/`in_progress`/`validated`/`n/a`）、目标 milestone。M0 初始矩阵中绝大多数项为 `planned`（未实现），不伪造已验证状态。

`spec-and-schema` CI 做双向校验：每个 spec 中出现的 Requirement ID 必须在矩阵中存在；矩阵中每个 ID 必须唯一归属 5 个 spec 域之一。

**为何不放 `registries/`**：`registries/` 的 `tools.yaml`/`hypotheses.yaml` 内容属 `define-core-contracts`；矩阵是跨域治理对象，放 `openspec/` 更自然，且不与下一个 change 的 registry 内容耦合。矩阵中对 HYP-DNA-001 仅以一行引用其状态与验证里程碑，不创建 `hypotheses.yaml` 文件内容。

## Risks / Trade-offs

- **[nf-core lint 对本地化仓库报偏离]** → 用 `.nf-core.yml` 配置放宽与本项目无关的社区规则（如 name prefix、特定文档段），接受"owned locally"定位；lint 失败项须逐条标注是"配置放宽"还是"真实问题"。
- **[`nf-core pipelines create` 交互式提示]** → apply 时用非交互参数（`--name`、`--author` 等）或预填答案；若版本交互不可绕过则在 staging 用 `script`/期望输入喂入，并固定所用 `nf-core` tools 版本写入 CHANGELOG。
- **[模板自带 workflow 被裁后遗忘后续启用]** → 维护 milestone→workflow 启用表（见决策 2），并在 `docs/decisions/` 留档。
- **[模板版本漂移导致 sync 困惑]** → 固定生成所用 `nf-core` tools 版本，vanilla commit 信息记录模板版本；后续升级走 `nf-core pipelines sync` + OpenSpec change。
- **[staging 合并误删既有 openspec/docs]** → 合并为显式白名单拷贝（保留 `openspec/`、`docs/inputs`、`docs/specification`、`.claude/`），合并前对既有内容做校验和留底。
- **[mamba 安装 nf-core 装错 channel/env]** → 严格 `~/miniconda3/bin/mamba`、无 `defaults`、扁平 `envs/toolname`；记录到 CHANGELOG。

## Migration Plan

本 change 为 greenfield（无前序 release）。部署 = 完成上述合并与 CI 配置。**回滚**：因 vanilla commit 为第一 commit，回滚等于 `git reset --hard <vanilla-commit>` 并恢复 staging 前的 `openspec/`+`docs/`+`.claude/` 备份；不涉及任何对外发布或数据迁移。

## Open Questions

- 生成模板所用的具体 `nf-core` tools 版本号与模板版本（影响可复现性，但不改变 specs/策略/任务结构）→ apply 时确定并写入 CHANGELOG。
- 是否保留 nf-core 模板自带的 `test`/`test_full` profile 骨架（M0 不执行，M1 起填充）→ 倾向保留骨架并标注"M0 不运行"，apply 时确认。
