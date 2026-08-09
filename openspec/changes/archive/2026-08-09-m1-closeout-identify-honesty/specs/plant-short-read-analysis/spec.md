## MODIFIED Requirements

### Requirement: assembly_grade ↔ decision 门控（锚定 SCI-001/SCI-005）

`IDENTIFY` SHALL gate `decision` by `assembly_grade` and evidence strength. `DRAFT +` all reference-pack `diagnostic_sites` callable and consistent `+` adequate `callable_coverage` `+` adequate `mean_readback_depth` `→ AUTHENTIC + WARN [INCOMPLETE_ASSEMBLY]`. If the only failing condition is `callable_coverage < min_callable_fraction`, the reason code SHALL be `LOW_CALLABLE_COVERAGE`. If the only failing condition is `mean_readback_depth < min_mean_depth`, the reason code SHALL be `LOW_SEQUENCING_DEPTH`.

#### Scenario: DRAFT + 诊断位点全部 callable + 充足覆盖 → AUTHENTIC + WARN
- **WHEN** ① outputs `assembly_grade = DRAFT`, all diagnostic sites are callable and consistent, `callable_coverage` meets the policy threshold, and `mean_readback_depth` meets the policy threshold
- **THEN** `decision = AUTHENTIC`, `status = WARN`, `reason_codes` contains `INCOMPLETE_ASSEMBLY`
- **AND** the report honestly notes “identity confirmed but assembly structure incomplete”

#### Scenario: 诊断位点落缺失区 → INCONCLUSIVE（即使全局一致性高）
- **WHEN** 全局一致性高，但参考 pack 的诊断位点落在组装缺失/不可判区
- **THEN** `decision = INCONCLUSIVE`，`reason_codes` 含 `DIAGNOSTIC_SITES_NOT_CALLABLE`
- **AND** MUST NOT 仅凭已组装部分的全局一致性输出 `AUTHENTIC`

#### Scenario: 一致性低于阈值 → NON_AUTHENTIC
- **WHEN** 诊断位点一致性明显低于 reference-pack `conflict_rules` 阈值
- **THEN** `decision = NON_AUTHENTIC`，`reason_codes` 含 `IDENTITY_BELOW_THRESHOLD`

#### Scenario: ① 不可用 → 直通 INCONCLUSIVE
- **WHEN** ① `assembly_grade = NOT_APPLICABLE` 或 `status = FAIL`
- **THEN** `decision = INCONCLUSIVE`，`IDENTIFY` 不进行身份判定

#### Scenario: callable 覆盖不足 → INCONCLUSIVE + LOW_CALLABLE_COVERAGE
- **WHEN** `callable_coverage` is below the policy `min_callable_fraction`
- **THEN** `decision = INCONCLUSIVE`
- **AND** `reason_codes` contains `LOW_CALLABLE_COVERAGE`
- **AND** `reason_codes` does NOT contain `LOW_COVERAGE`

#### Scenario: 测序深度不足 → INCONCLUSIVE + LOW_SEQUENCING_DEPTH
- **WHEN** `mean_readback_depth` is below the policy `min_mean_depth`
- **THEN** `decision = INCONCLUSIVE`
- **AND** `reason_codes` contains `LOW_SEQUENCING_DEPTH`
- **AND** `reason_codes` does NOT contain `LOW_COVERAGE`

### Requirement: 污染信号不强判 AUTHENTIC

When ① emits a validated contamination or coverage-anomaly signal, `IDENTIFY` SHALL output `INCONCLUSIVE + [CONTAMINATION_SUSPECTED]`, MUST NOT force `AUTHENTIC`. Until such a signal is implemented and validated, `CONTAMINATION_SUSPECTED` is dormant: the current ①/② flow does not detect cross-kingdom animal×plant mixtures at the plastome-recruitment level, and formal contamination validation MUST use close-relative plant mixtures together with the Kraken2 self-built DB change.

#### Scenario: 污染信号 → INCONCLUSIVE，不得强判
- **WHEN** ① emits a validated contamination or coverage-anomaly signal
- **THEN** `decision = INCONCLUSIVE`, `reason_codes` contains `CONTAMINATION_SUSPECTED`
- **AND** MUST NOT output `AUTHENTIC` even if single-reference identity is high

#### Scenario: 当前污染路径 dormant
- **WHEN** a cross-kingdom animal×plant mixture is processed by the current flow
- **THEN** the contamination is not detected at the plastome-recruitment step
- **AND** `CONTAMINATION_SUSPECTED` is not emitted
- **AND** the dormancy and reactivation plan are documented in the change design
