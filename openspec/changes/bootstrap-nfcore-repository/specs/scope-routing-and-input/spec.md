## Purpose

定义中药材细胞器基因组鉴定系统的鉴定范围、显式路由原则与输入数据合同，确保分析意图、生物学目标与数据可得性三者不被样本描述或文件扩展名隐式推断。

## ADDED Requirements

### Requirement: 三 entry workflow 范围与明确非目标

The system SHALL declare exactly three analysis entry workflows — `REFERENCE_BUILD`, `IDENTIFY`, `VALIDATE`. 首版核心实现 MUST NOT 包含炮制品 mini-barcode、复方、metabarcoding、靶向捕获或 qPCR/dPCR 定量的可执行生产模块（§1.2）。任何保留的扩展接口 MUST 标注其准入须经独立 OpenSpec change。

#### Scenario: 首版范围不含扩展层

- **WHEN** 检查首版核心实现
- **THEN** 不存在 metabarcoding / 靶向捕获 / qPCR 定量的生产模块
- **AND** 任何扩展接口占位都明确标注准入条件

### Requirement: 路由仅依据显式字段

The system SHALL route each sample exclusively from explicitly declared routing fields — `analysis_mode`, `taxon_group`, `targets`, short-read availability, long-read availability, `specimen_role`, `reference_pack` compatibility, and `policy_pack` status（§3.3）。The system MUST NOT infer `taxon_group` from specimen descriptions, MUST NOT infer reference-grade qualification from the presence of dual-platform data, and MUST NOT infer sequencing platform from file extensions（DATA-006）。

#### Scenario: 禁止从样本描述推断分类群

- **WHEN** a sample description or `specimen_role` reads `leaf`, `root`, or `voucher`
- **THEN** `taxon_group` is taken only from the explicit `taxon_group` field, never from the description

#### Scenario: 禁止从数据组合推断参考级资格

- **WHEN** a sample has both DNBSEQ and CycloneSEQ data
- **THEN** the sample is not automatically granted reference-grade qualification; qualification follows `REFERENCE_BUILD` acceptance rules

### Requirement: 真值与样本数据隔离

Analysis samplesheets MUST NOT carry expected taxonomic truth. The `VALIDATE` unblinding evaluation SHALL load truth exclusively from a separate, access-controlled `truthset.csv`, and only after every sample-level result is frozen with a checksum（DATA-003）。

#### Scenario: 分析输入不含真值

- **WHEN** an analysis samplesheet is constructed for any entry workflow
- **THEN** it contains no expected-truth column
- **AND** `truthset.csv` is loaded only by the unblinding evaluation step after result freeze
