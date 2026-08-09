## ADDED Requirements

### Requirement: 工程测试 policy 占位阈值修订必须留痕

Any revision to a placeholder threshold in an `experimental` policy pack SHALL be recorded in the policy file header comment. The comment MUST cite the empirical evidence, the sample(s) and version of the validation artifact, the measured range, the selected value and a rationale for the selection within that range, and an explicit statement that the value remains uncalibrated and MUST be replaced after M3 independent calibration.

#### Scenario: 阈值修订文件头留痕
- **WHEN** an `experimental` policy pack's threshold is revised
- **THEN** the policy file contains a header comment documenting the empirical basis
- **AND** it names the validation artifact and version (e.g., `VALIDATION-identify.md`)
- **AND** it states the measured range and the selected value
- **AND** it includes a "replace after M3 calibration" disclaimer
- **AND** the change adds a corresponding "预期状态修订表" to the validation artifact showing original expectation, actual result, revised expectation, and rationale per scenario

#### Scenario: 禁止静默调参
- **WHEN** a threshold in a policy pack is changed
- **THEN** the change is accompanied by the validation-artifact revision table
- **AND** the reason for the new value is traceable to a validation run, not an undocumented round number
