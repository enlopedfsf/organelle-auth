# validation-and-go-no-go Specification

## Purpose
定义工程验证与科学验证的分离原则、CycloneSEQ 转移验证与盲样 Go/No-Go 框架，确保工具与阈值的准入始终由独立证据驱动，且验证集绝不反向污染被验证对象。
## Requirements
### Requirement: 工程测试与科学验证分离

工程测试（证明代码按合同运行）与科学验证（证明方法在声明适用范围内可接受）MUST 分离（§13.1）。nf-test MUST NOT 替代盲样正确率、错误谱、诊断位点验证或正交实验。

#### Scenario: 工程绿不等于方法通过

- **WHEN** all engineering tests pass
- **THEN** this alone MUST NOT be reported as scientific method validation

### Requirement: VALIDATE 不得反向调阈值

VALIDATE workflow SHALL 在揭示完整测试结果前把通过标准写入版本化 validation protocol。VALIDATE MUST NOT 用验证集结果反向调整阈值后仍报告为独立验证（§3.2 禁止行为）。新诊断位点、关键结构连接与争议结论 SHALL 按风险用独立方法（如 PCR/Sanger）正交验证，正交验证的样本选择、成功标准与不一致处理 MUST 写入 validation protocol（SCI-010 / §15.5）。

#### Scenario: 阈值冻结先于揭盲

- **WHEN** VALIDATE evaluates blind samples
- **THEN** the pass thresholds are frozen in a versioned protocol before unblinding
- **AND** the validation set is not used to re-tune thresholds that are then reported as independently validated

### Requirement: Go/No-Go 增益门槛

Go/No-Go 评价 SHALL 覆盖正确判定率、假阳性率、假阴性率、`INCONCLUSIVE` 率、诊断位点可重复性、结构假阳性率、跨批次一致性、单样本失败率、计算资源与人工复核负担、以及三代相对纯二代的经验证增益（§15.4）。若 CycloneSEQ 或混合路线未产生预定义的独立增益，长读长分支 SHALL 降为研究层，不进入正式鉴定 SOP。

#### Scenario: 无增益则降级

- **WHEN** a Go/No-Go evaluation finds no predefined independent long-read/hybrid gain
- **THEN** the long-read branch is downgraded to research-only
- **AND** excluded from the formal authentication SOP
