## 1. 预检与工具准备

- [x] 1.1 `nf-core` tools 已存在（env `nf-core`，版本 **4.1.0**，免安装）；Nextflow **26.04.6**——版本号待 `CHANGELOG.md` 创建后记入（见 §3）
- [x] 1.2 确认 Nextflow 可用并记录版本（**26.04.6**，作为 CI 最低支持版本的依据）
- [x] 1.3 对现有 `openspec/`、`docs/inputs`、`docs/specification`、`.claude/` 计算校验和并留底（25 文件 → `~/Project/organelle-auth-prebootstrap-checksums.txt`）

## 2. nf-core vanilla 模板生成（staging）

- [x] 2.1 在临时 staging 目录用 `nf-core pipelines create` 生成全新模板（`--name organelleauth` —— nf-core 禁连字符，pipeline 内部名用 `organelleauth`，仓库仍为 `organelle-auth`）
- [x] 2.2 staging 内已 `git init` 并存在 vanilla commit（`b543f3d`，nf-core tools 4.1.0）；版本已记录
- [x] 2.3 模板结构与 §12.2 推荐目录一致

## 3. 合并到项目仓库（目标 = 当前目录）

- [x] 3.1 staging 的 `.git` 与全部生成文件已迁入 `~/Project/organelle-auth`，vanilla commit `b543f3d` 为第一个 commit
- [x] 3.2 既有 `openspec/`、`docs/inputs`、`docs/specification`、`.claude/` 经校验和验证未改动（24/25 字节一致；第 25 个为本会话编辑的 tasks.md）
- [x] 3.3 `docs/` 共存：nf-core `docs/*.md` 与既有 `docs/inputs`、`docs/specification` 共存（未提交——见下方"待决策：提交"）

## 4. 证据优先配置擦洗

- [x] 4.1 扫描确认 `nextflow.config`/`nextflow_schema.json`/`conf/*.config` 无本项目科学阈值作默认值（模板均为通用 nf-core 参数，未标定值已为 `null`）
- [x] 4.2 `manifest.nextflowVersion = '!>=25.10.4'`（pinned 最低版本，无"24.x LTS"文字）
- [x] 4.3 `.nf-core.yml` 已调整：移除 `PULL_REQUEST_TEMPLATE.md` 的 files_unchanged、移除 `manifest.homePage` 的 nextflow_config 检查（适配 organelle-auth 仓库 URL）。**完整 lint 绿尚依赖下方决策 + CI 网络**

## 5. OpenSpec 结构与上下文

- [x] 5.1 `openspec/config.yaml` 项目上下文已填充（tech stack、领域、规范来源 v1.1.1、证据优先、命名约定、版本化、测试层级、按 ID 引用）
- [x] 5.2 `openspec/specs/` 下仅 5 个规范域（本 change 的 delta），无其他空目录；`openspec validate --strict` 通过

## 6. 总方案纳入与 Requirement 追踪矩阵

- [x] 6.1 总方案 v1.1.1 确认位于 `docs/specification/`（合并校验和验证未改动）
- [x] 6.2 `openspec/traceability.yaml` 已创建，覆盖 34 个 ID（SCI×10、DATA×7、ENG-POL×5、TEST×7、REL×4、HYP×1）
- [x] 6.3 未实现项均 `status: planned` + 目标 milestone，无伪造已验证
- [x] 6.4 双向一致：矩阵 34 ID 唯一归属 5 域；specs 中引用的 20 个 ID 全部在矩阵中（`check_schema_traceability.py` 通过）

## 7. 协作治理模板

- [x] 7.1 `.github/CODEOWNERS` 已创建（5 区职责，允许兼任；@enlopedfsf 为占位待替换）
- [x] 7.2 `.github/PULL_REQUEST_TEMPLATE.md` 已覆盖为 7 必填字段版（OpenSpec change ID / 受影响 ReqID / 科学行为是否变更 / 测试 / 验证证据 / breaking / rollback）
- [x] 7.3 `.github/ISSUE_TEMPLATE/` 6 类齐备：bug、feature（保留模板）+ scientific-discrepancy、tool-admission-request、hypothesis-status-change、reference-policy-update（新增）

## 8. Lean M0 CI（仅三个 T0 workflow）

- [x] 8.1 `.github/workflows/spec-and-schema.yml`：`openspec validate --changes` + JSON/YAML 校验 + 追踪矩阵完整性（`check_schema_traceability.py`）
- [x] 8.2 `linting.yml`（模板自带，SHA-pinned）运行 `nf-core pipelines lint`
- [x] 8.3 `.github/workflows/template-check.yml`：最小模板结构自检
- [x] 8.4 决策 **Option K**：保留 nf-core 标准 workflow（`nf-core pipelines lint` 合规所需），3 个 T0 门禁（spec-and-schema/linting/template-check）为 M0 活跃检查；milestone→workflow 启用表与决策历史见 `docs/decisions/milestone-ci-workflows.md`

## 9. M0 完成验证

- [ ] 9.1 `nf-core pipelines lint` —— **本地无法完成**（hang 于 nf-core/modules 仓库拉取，需代理/CI 网络）；待 GitHub-hosted runner 验证
- [x] 9.2 `openspec validate --changes` 通过
- [x] 9.3 空 pipeline 解析通过（`NXF_OFFLINE=1 nextflow run . -profile test --help` exit 0）；schema 加载通过
- [x] 9.4 `openspec/` 下仅 5 规范域、无多余空目录；`modules/nf-core/` 为空（无生信模块代码）
- [x] 9.5 追踪矩阵 34 ID 完整且与 specs 双向一致
- [x] 9.6 引用总方案一律使用 Requirement ID（specs/config/矩阵/模板均按 ID 引用）
- [ ] 9.7 三条 T0 CI 在 GitHub-hosted runner 通过（需 push 到 GitHub）
- [ ] 9.8 PR 审阅（交叉审阅）——需人工

---

### 决策结果（apply 暂停点已解决）

1. **CI vs lint**：采 **Option K**——恢复 nf-core 标准 workflow 以满足"通过 nf-core lint"；3 个 T0 门禁（spec-and-schema/linting/template-check）为 M0 活跃检查（详见 `docs/decisions/milestone-ci-workflows.md`）。
2. **提交**：采"逻辑拆分提交"——在 feature 分支 `feat/bootstrap-nfcore-repository` 上按主题分多个 commit，**不 push**。
