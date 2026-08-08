# M0 lint advisory — recorded deviations

> **状态 / Status**: 在 M0,`nf-core pipelines lint` 是 **advisory(非阻塞)**。这是有意决策(choice B,见 `milestone-ci-workflows.md`),不是疏漏。本文件逐条记录 9 个偏差及其预期消除方式,确保"M1 自动消失"的承诺落到纸面。
>
> **追踪 issue**: <https://github.com/enlopedfsf/organelle-auth/issues/2> —— "M1: 恢复 nf-core lint 为阻塞性门禁"。

## 背景

M0 验收要求"仓库中不存在任何生信工具模块代码",据此剥离了 nf-core 模板自带的 demo 模块 fastqc/multiqc;另定制了 7 字段 PR 模板。这两项 M0 定制是 `nf-core pipelines lint` 报出下列 9 个偏差的**唯一原因**——它们不是代码缺陷,而是模板一致性类规则与 M0 定制的必然冲突。M0 的 3 个 T0 门禁(`spec-and-schema`、`template-check`、`pre-commit`)均通过。

## 9 个偏差及消除方式

| #   | lint 规则           | 对象                                                                                                           | 原因                                                                                                                                 | 消除方式                                                                                                                                                                                       |
| --- | ------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1–8 | `container_configs` | `conf/containers_{conda_lock_files,docker,singularity_https,singularity_oras}_{amd64,arm64}.config`(共 8 文件) | M0 剥离 fastqc/multiqc 后 `modules.json` 的 nf-core 模块为空,但这 8 个容器配置仍引用已删除模块 → 要求按 `modules.json` 重新生成      | **M1 自动消失**:加入第一个真实模块时 `nf-core modules install` 重新生成这 8 个文件。或现在在 PR 评论 `/fix-linting` 触发 `nf-core pipelines lint --fix` 立即重生(代价:同时回退 PR 模板,需重做) |
| 9   | `files_unchanged`   | `.github/PULL_REQUEST_TEMPLATE.md`                                                                             | 本项目 7 字段 PR 模板(OpenSpec change ID / 受影响 ReqID / 科学行为 / 测试 / 验证证据 / breaking / rollback)与 nf-core 默认模板不一致 | **M1 决策**: (a) 保留 7 字段模板 → 本项持续 advisory;或 (b) 回退 nf-core 默认模板 → 全绿,7 字段纪律改放 CONTRIBUTING/checklist                                                                 |

## 恢复 lint 为阻塞门禁的判据

当 `nf-core pipelines lint` 在 PR CI 上 **0 failure**:

1. GitHub branch protection 把 `nf-core` / `linting` check 设为 **required**;
2. 在本文件顶部把状态从 advisory 改为 blocking;
3. 关闭追踪 issue #2。

## 关联

- 决策历史:`docs/decisions/milestone-ci-workflows.md`(Option K)
- 追踪 issue:<https://github.com/enlopedfsf/organelle-auth/issues/2>
- 验收依据:总方案 v1.1.1 §18 M0 完成定义
