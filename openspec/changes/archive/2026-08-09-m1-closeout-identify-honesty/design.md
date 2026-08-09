## Context

See `proposal.md - Why`. The M1-② real-data validation (`VALIDATION-identify.md`) revealed that:
- `LOW_COVERAGE` conflates two different failure modes, producing misleading labels.
- The `0.9` placeholder `min_callable_fraction` sits on a razor's edge for the Corydalis DRAFT plastome.
- `CONTAMINATION_SUSPECTED` is currently unreachable because ① never emits `COVERAGE_ANOMALY`.

This change is a **spec-honesty close-out**: it updates reason codes, revises the engineering-test policy with documented provenance, and records the contamination gap as dormant rather than silently pretending it works.

## Goals / Non-Goals

**Goals:**
- Replace the ambiguous `LOW_COVERAGE` code with `LOW_SEQUENCING_DEPTH` and `LOW_CALLABLE_COVERAGE`.
- Revise `tcm-plant-engineering-test.json`'s `min_callable_fraction` to an evidence-based placeholder so the normal Corydalis sample reaches `AUTHENTIC + WARN[INCOMPLETE_ASSEMBLY]`.
- Document the threshold revision provenance in the policy file header and in `VALIDATION-identify.md`.
- Mark `CONTAMINATION_SUSPECTED` as dormant in `reason_codes.yaml` and record why.
- Update nf-test fixtures and re-run all five real-data scenarios under the revised policy.

**Non-Goals:**
- Implement a real Kraken2 self-built DB contaminant screen (M2 change).
- Change production-null behavior; it must still yield `THRESHOLD_NOT_CONFIGURED`.
- Calibrate thresholds scientifically; this change only moves the placeholder to an empirically justified placeholder pending M3.
- Modify ① assembly logic; we only change ② decision/reason-code handling.

## Decisions

### 1. Reason-code split: `LOW_SEQUENCING_DEPTH` vs `LOW_CALLABLE_COVERAGE`

**Decision:** Remove `LOW_COVERAGE`; add `LOW_SEQUENCING_DEPTH` (depth below `min_mean_depth`) and `LOW_CALLABLE_COVERAGE` (callable-region fraction below `min_callable_fraction`).

**Rationale:** Depth is a sequencing/input quantity; callable coverage is an assembly-contiguity quantity. Conflating them made a 1079× sample appear “low coverage” when the real issue was the DRAFT's structural incompleteness. Separate codes let reports and operators act correctly.

**Alternative considered:** Keep `LOW_COVERAGE` as a generic umbrella and add sub-codes. Rejected: the umbrella code is already overloaded and report generators would continue to use it ambiguously.

### 2. Threshold value for `min_callable_fraction`

**Decision:** Set `min_callable_fraction` to a value between the measured normal-sample `callable_coverage` (0.888206) and the low-cov sample (0.900144), leaning slightly below the normal value to ensure the normal 2 Gb run reaches `AUTHENTIC`. A concrete candidate is `0.885` or `0.88`, chosen after re-running with the exact value and confirming `AUTHENTIC + WARN[INCOMPLETE_ASSEMBLY]`.

**Rationale:** The DRAFT plastome spans ~88.8% of the callable regions because of a known IR-region short-read structural gap. A threshold below this measured floor acknowledges the gap without pretending it is calibrated. The low-cov sample (0.900144) proves that slightly better contiguity pushes it above any threshold in this range, so the gate remains meaningful.

**Alternative considered:** Keep `0.9` and accept that normal samples stay `INCONCLUSIVE`. Rejected: it contradicts the accepted gate that DRAFT+all-callable+identity → AUTHENTIC+WARN, and masks the pipeline's utility for real DRAFT-grade samples.

**Alternative considered:** Set to exactly `0.888` (just below normal). Rejected: too close to measurement noise and GetOrganelle non-determinism; a small margin (`0.88`–`0.885`) is safer for reproducibility.

### 3. `CONTAMINATION_SUSPECTED` dormancy

**Decision:** Keep the code in `reason_codes.yaml` but add a `dormant: true` marker and explanatory note. Do not emit it from `DECISION_ENGINE`. Document two facts in `design.md` and `VALIDATION-identify.md`:
- ① `emit_assembly_qc_status` binds the coverage-valley coefficient to `_`, so no `COVERAGE_ANOMALY` is ever produced.
- The 50:50 animal×plant (Corydalis + 柳叶蚂蟥) mixture did not change `callable_coverage` or `mean_readback_depth`, proving cross-kingdom contamination is invisible to plastome recruitment alone.

**Rationale:** Removing the code would silently erase a known gap. Dormancy makes the gap explicit and ties reactivation to a future, testable deliverable.

**Alternative considered:** Emit `CONTAMINATION_SUSPECTED` anyway for documentation. Rejected: emitting a code that is not backed by a validated signal is exactly the kind of “forced judgment” the project rejects.

### 4. Where to record threshold provenance

**Decision:** Add a multi-line comment block at the top of `tcm-plant-engineering-test.json` and append a new “预期状态修订表” section to `VALIDATION-identify.md`.

**Rationale:** The policy file is the runtime artifact operators inspect; it must carry its own justification. The validation markdown is the authoritative record of the five scenarios and the reasoning chain.

## Risks / Trade-offs

- **[Risk] Non-deterministic `callable_coverage` around the threshold.** → Mitigation: choose a threshold with margin (~0.88–0.885) and re-run the full five-scenario suite to confirm stability. Note the non-determinism source (GetOrganelle 500× internal subsampling) in `VALIDATION-identify.md`.
- **[Risk] Downstream report generators still expect `LOW_COVERAGE`.** → Mitigation: this is a BREAKING change per `proposal.md`. Report generators must be updated; `LOW_COVERAGE` is removed from `reason_codes.yaml`.
- **[Risk] Future M3 calibration may reject the `0.88` placeholder.** → Mitigation: policy header and validation doc explicitly state the value is uncalibrated and MUST be replaced after M3 independent validation. The placeholder is experimental-only.
- **[Risk] Dormancy label is ignored and someone re-uses `CONTAMINATION_SUSPECTED` prematurely.** → Mitigation: code does not emit it; `reason_codes.yaml` carries `dormant: true`; design.md records the exact reactivation conditions.

## Open Questions

None. The scope is bounded to the three honesty corrections identified in `VALIDATION-identify.md`.
