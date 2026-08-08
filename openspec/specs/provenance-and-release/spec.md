# provenance-and-release Specification

## Purpose
定义每次运行的最小审计包、参考级序列归档清单与发布门禁，使任何正式结论都能从 Requirement ID 追溯到代码、测试、验证记录与 release 资产，并禁止无痕覆盖已发布版本。
## Requirements
### Requirement: 每次运行最小审计包

每次正式运行 SHALL 产出最小审计包，至少包含 input samplesheet、normalized samplesheet、params/configs、pipeline version 与 commit、Nextflow version、tool versions、container digests、reference/policy/compatibility IDs、checksums、trace/timeline/report/DAG、per-sample status JSON、evidence bundle、final report（§16.3）。

#### Scenario: 审计包支持复现与问责

- **WHEN** a formal run completes
- **THEN** the audit bundle contains every artifact required to reproduce and account for the run

### Requirement: 独立版本对象与 Pipeline SemVer

Pipeline、method specification、reference pack、policy pack、Kraken DB、validation dataset/protocol、hypothesis registry、container lock SHALL 各自独立版本化（§16.1）。Pipeline SemVer 规则：MAJOR 对应输入/输出合同或判定含义的不兼容变更，MINOR 对应向后兼容的新路线/报告/工具准入，PATCH 仅限不改科学行为的修复（§16.2）。阈值、诊断位点与判定规则变化 MUST NOT 仅作 PATCH 隐式发布，MUST 升级对应 policy/reference 版本并更新 compatibility manifest（§10.3 / §16.2）。

#### Scenario: 科学变化不隐式 PATCH

- **WHEN** a threshold, diagnostic site, or decision rule changes
- **THEN** the corresponding policy/reference version is bumped
- **AND** the compatibility manifest is updated, rather than shipping as a silent PATCH

### Requirement: 发布门禁与禁止无痕覆盖

正式 release SHALL 仅在受保护的 release qualification workflow 通过且所有强制门禁满足后发布（REL-001）。release tag SHALL 能唯一解析 pipeline commit、OpenSpec baseline、container lock 与 compatibility manifest（REL-002）。科学行为发生变化时，release notes MUST 列出受影响 Requirement ID、policy/reference 版本与迁移影响（REL-003）。发现发布后科学性缺陷时，MUST 保留原 release、发布撤回或警示说明，并通过新版本修正；MUST NOT 无痕覆盖（REL-004）。

#### Scenario: 缺陷发布不可抹除

- **WHEN** a post-release scientific defect is discovered
- **THEN** the original release is retained with a retraction or warning
- **AND** the fix ships as a new version
