## 1. Reason-code semantics split

- [x] 1.1 Update `assets/reason_codes.yaml`: bump version, remove `LOW_COVERAGE`, add `LOW_SEQUENCING_DEPTH` (warn) and `LOW_CALLABLE_COVERAGE` (scientific_inconclusive), mark `CONTAMINATION_SUSPECTED` as dormant with reactivation trigger.
- [x] 1.2 Update `modules/local/decision_engine/main.nf` to emit `LOW_SEQUENCING_DEPTH` when `mean_readback_depth < min_mean_depth` and `LOW_CALLABLE_COVERAGE` when `callable_coverage < min_callable_fraction`; keep `THRESHOLD_NOT_CONFIGURED` / `IDENTITY_BELOW_THRESHOLD` / `INCOMPLETE_ASSEMBLY` / `DIAGNOSTIC_SITES_NOT_CALLABLE` paths unchanged.
- [x] 1.3 Update `modules/local/decision_engine/tests/main.nf.test` fixtures and assertions to use the new reason codes where previously `LOW_COVERAGE` was expected.
- [x] 1.4 Search the repo for any remaining references to `LOW_COVERAGE` in code/tests/config and update or remove them.

## 2. Engineering-test policy threshold revision with provenance

- [x] 2.1 Select the revised `min_callable_fraction` value using the measured range (normal 0.888206, low-cov 0.900144); candidate values 0.88–0.885, final choice documented.
- [x] 2.2 Update `policies/tcm-plant-engineering-test.json`: set the new `min_callable_fraction`, add a header comment citing `VALIDATION-identify.md`, the Corydalis DRAFT IR-gap evidence, the measured range, the selected value, and the "replace after M3 calibration" disclaimer.
- [x] 2.3 Verify `policies/tcm-plant-production-null.json` remains all-null and is not affected by the threshold revision.

## 3. VALIDATION-identify.md honesty revision table

- [x] 3.1 Append an "预期状态修订表" section to `openspec/changes/archive/2026-08-09-plant-short-read-identify/VALIDATION-identify.md` with columns: scenario, original expectation, actual result, revised expectation, rationale.
- [x] 3.2 Fill the table for all five scenarios, explicitly stating why the threshold and reason-code changes alter the expected outcome.

## 4. nf-test and static validation

- [x] 4.1 Run `nf-test modules/local/decision_engine/tests/main.nf.test --profile docker` and ensure 5/5 PASS.
- [x] 4.2 Run `openspec validate --all` and resolve any spec/delta errors.
- [x] 4.3 Run T2/T3 stub smoke (`-profile engineering_test,docker -stub`) to confirm full chain still emits the expected status schema.

## 5. Real-data re-validation under revised policy

- [x] 5.1 Re-run scenario 1 (normal 2 Gb) with the revised engineering-test policy and confirm `AUTHENTIC + WARN[INCOMPLETE_ASSEMBLY]`.
- [x] 5.2 Re-run scenario 2 (low-cov 0.5 Gb) and record the new `callable_coverage` / `mean_readback_depth` and decision.
- [x] 5.3 Re-run scenario 3 (contam 50:50) and confirm it now resolves to `INCONCLUSIVE + [LOW_CALLABLE_COVERAGE]` (or other honest reason code, documented).
- [x] 5.4 Re-run scenario 4 (reference missing) and confirm `DATA-005` fail-fast unchanged.
- [x] 5.5 Re-run scenario 5 (production-null) and confirm `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]` unchanged.
- [x] 5.6 Update `VALIDATION-identify.md` with the final post-revision numbers and cross-reference the policy revision.

## 6. Archive and commit

- [x] 6.1 Archive this change into the main specs (`openspec archive m1-closeout-identify-honesty`) once the implementation is verified.
- [ ] 6.2 Commit all changes (reason_codes.yaml, decision_engine, policy file, tests, VALIDATION-identify.md, archived specs) with a descriptive message ending in `Co-Authored-By: Claude <noreply@anthropic.com>`.
