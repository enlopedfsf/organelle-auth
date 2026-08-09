## Why

M1-② `plant-short-read-identify` 的五场景真实数据验证（`VALIDATION-identify.md`）暴露了三个 honest divergences：
1. `LOW_COVERAGE` 被同时用于"测序深度不足"和"callable-region 覆盖不足（组装完整度）"，导致 1079× 深度的正常样本被标为 `LOW_COVERAGE`，语义误导且与预钉期望冲突。
2. 工程测试 policy 的 `callable_site.min_callable_fraction=0.9` 是占位阈值，真实 DRAFT 叶绿体（含 IR 结构缺口）实测 callable_cov 在 0.888–0.900 之间，0.9 把正常样本判为 `INCONCLUSIVE`。
3. `CONTAMINATION_SUSPECTED` 门径当前 unreachable：① 不 emit `COVERAGE_ANOMALY`，动物×植物混合夹具对质体招募无鉴别力，继续假装该路径有效会掩盖真实 gap。

本 change 做 M1 收尾修正：拆分 reason code、用实测证据修订占位阈值并留痕、将污染门径登记为 dormant。修正后正常样本应在工程测试 policy 下达到 `AUTHENTIC + WARN[INCOMPLETE_ASSEMBLY]`，同时保持 production-null 的 `THRESHOLD_NOT_CONFIGURED` 行为不变。

## What Changes

- **BREAKING** `assets/reason_codes.yaml`：移除 `LOW_COVERAGE` 的模糊语义，新增 `LOW_SEQUENCING_DEPTH`（深度不足，warn）与 `LOW_CALLABLE_COVERAGE`（callable-region 覆盖不足 / 组装完整度问题，scientific_inconclusive 或 warn 待设计文档定）。更新版本号。
- `modules/local/decision_engine/main.nf`：按 depth 与 callable_cov 分别触发新 reason code；保留 `THRESHOLD_NOT_CONFIGURED`、`IDENTITY_BELOW_THRESHOLD`、`INCOMPLETE_ASSEMBLY`、`DIAGNOSTIC_SITES_NOT_CALLABLE` 路径。
- `policies/tcm-plant-engineering-test.json`：将 `callable_site.min_callable_fraction` 从 `0.9` 下调至基于实测的证据值（约 0.88–0.89 区间，具体值由 design 文档论证），文件头增加注释记录本次修订依据（`VALIDATION-identify.md` 五场景、IR 缺口 DRAFT 实测范围）并标注“未经 M3 独立标定，M3 后替换”。
- `openspec/changes/archive/2026-08-09-plant-short-read-identify/VALIDATION-identify.md`：新增“预期状态修订表”，列明每场景的原预期、实际结果、修订后预期及理由；禁止静默调参。
- `openspec/specs/evidence-decision-and-status/spec.md`：将 `LOW_COVERAGE` 语义拆分要求写入 spec；把 `CONTAMINATION_SUSPECTED` 标注为 dormant 并说明复活条件（Kraken2 自建库落地、近缘植物混合夹具验证）。
- `openspec/specs/asset-tool-and-policy/spec.md`：增补 policy pack 占位阈值修订必须留痕的要求（依据、版本、待替换声明）。
- `openspec/specs/plant-short-read-analysis/spec.md`：调整 identify 阶段 scenario 预期（正常 DRAFT 样本 → `AUTHENTIC + WARN[INCOMPLETE_ASSEMBLY]`；污染信号路径 dormant）。
- `modules/local/decision_engine/tests/main.nf.test` 与相关 nf-test：更新 reason code 断言与阈值 fixture，确保 nf-test 全绿。
- 复跑五场景真实数据验证，确认修订后 policy 下正常样本 → `AUTHENTIC + WARN[INCOMPLETE_ASSEMBLY]`，production-null 仍 → `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]`。

## Capabilities

### New Capabilities

None. This is an honesty close-out revision of existing M1-② behavior, not a new feature.

### Modified Capabilities

- `evidence-decision-and-status`: Split the overloaded `LOW_COVERAGE` reason code into depth-driven and callable-coverage-driven codes. Mark `CONTAMINATION_SUSPECTED` as dormant until Kraken2 self-built DB validation lands.
- `asset-tool-and-policy`: Require that placeholder threshold revisions in policy packs carry provenance comments citing the empirical evidence, the version, and a "replace after M3 calibration" disclaimer.
- `plant-short-read-analysis`: Update the identify-stage scenarios for normal DRAFT samples and contamination handling to match the honest validation outcomes.

## Impact

- **Code**: `decision_engine` module, `reason_codes.yaml`, policy JSON, nf-test fixtures.
- **Specs**: three spec files receive delta requirements.
- **Validation artifact**: `VALIDATION-identify.md` gains an expectation-revision table.
- **Reference data / databases**: No DB downloads; contamination resurrection depends on a future Kraken2 self-built DB change.
- **Backward compatibility**: BREAKING for downstream report generators that hard-coded `LOW_COVERAGE`; they must handle `LOW_SEQUENCING_DEPTH` / `LOW_CALLABLE_COVERAGE`. The change keeps `CONTAMINATION_SUSPECTED` in the dictionary so dormant code does not break existing parsers.
