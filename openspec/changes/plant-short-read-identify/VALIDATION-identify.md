# VALIDATION-identify.md — M1-② plant-short-read-identify

Record of the four(+null) validation scenarios from `tasks.md §5`. Per `tasks.md 5.6`, the raw
validation **evidence** (real FASTQs, `work/` dirs, real ① assembly outputs) lives **outside git**;
this file is the in-repo summary. "No forced judgment" is asserted at the end.

Validation spans two tiers:
- **CI-proven** (logic): exercised by committed nf-test cases on nf-test 0.9.4 (CI version) + the
  full-chain stub smoke. These are gating.
- **Real-data** (science): require a real ① assembly of the Corydalis sample; **deferred** to a
  dedicated run (CPU-bound; no prior ① output is present in-repo to reuse). Expected outcomes are
  pinned below so the run is a confirmation, not an exploration.

---

## CI-proven (gating)

### 5.4 Reference-missing → DATA-005 fail-fast ✔
`load_reference_pack` nf-test case *"DATA-005: missing reference_pack_id → fail-fast"* — a pack root
with no `nonexistent/` subdir → `sys.exit(1)` with `DATA-005: reference pack not found`. No public-DB
fallback. **GREEN on nf-test 0.9.4.**

### 5.5 Production null-threshold → INCONCLUSIVE [THRESHOLD_NOT_CONFIGURED] ✔ (决策 2)
`decision_engine` nf-test case *"null policy threshold → INCONCLUSIVE [THRESHOLD_NOT_CONFIGURED]"* —
a `production`-status policy with `callable_site:null, uncertainty_zone:null` → the module-layer null
defense returns `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]`, **no crash, no forced call**. This
complements (does not replace) the ENG-POL-002 startup gate that blocks `production + all-null policy`
at launch. **GREEN on nf-test 0.9.4.**

Two-layer null defense (决策 4): **ENG-POL-002 startup gate** intercepts *production + all-null policy*;
**module-layer `THRESHOLD_NOT_CONFIGURED`** intercepts *any profile where a referenced threshold field
is null*.

### Decision-matrix coverage (决策 1) ✔
`decision_engine` nf-test (5 cases): AUTHENTIC+WARN[INCOMPLETE_ASSEMBLY] (DRAFT+callable+high);
INCONCLUSIVE[DIAGNOSTIC_SITES_NOT_CALLABLE] (global identity high but sites uncallable);
THRESHOLD_NOT_CONFIGURED (null); NON_AUTHENTIC[IDENTITY_BELOW_THRESHOLD] (below pack
`non_authentic_identity`); ①-FAIL passthrough INCONCLUSIVE (透传 ① reason). Evaluator site-level gate
+ coverage math validated on mock PAF (`evaluate_diagnostic_sites`: spanned→callable 1.0,
unspanned→uncallable; `evaluate_callable_regions`: covered_bp/coverage/mean_depth exact).

### End-to-end stub smoke (T2/T3) ✔
`-profile engineering_test,docker -stub`, work dir under `$HOME` → `completed=18 failed=0`, EXIT 0.
All 6 ② modules chained; emitted `S1.identify.status.json` =
`{"stage":"identify","decision":"AUTHENTIC","status":"WARN","reason_codes":["INCOMPLETE_ASSEMBLY"],...}`
(schema-conformant, 决策 1 matrix).

---

## Real-data (deferred — confirmation runs, not exploration)

These need a real ① assembly of `SRR38978846` (Corydalis / 刻叶紫堇). Re-running ① (GetOrganelle) is
CPU-bound and no prior ① output is in-repo. Outcomes are pinned by the CI-proven decision matrix, so a
real run only confirms which branch the v0.1 test pack's assembled region lands in.

### 5.1 Normal — Corydalis SRR38978846 under engineering-test policy
Expected: **`AUTHENTIC + WARN [INCOMPLETE_ASSEMBLY]`** *if all test-pack `diagnostic_sites` are
callable on the assembled region*; else **`INCONCLUSIVE + [DIAGNOSTIC_SITES_NOT_CALLABLE]`** — record
whichever the v0.1 pack actually produces. This is the 决策 1 site-level gate (high global identity does
NOT override uncallable diagnostic sites).

### 5.2 Low-coverage → INCONCLUSIVE
Downsample reads so `callable_coverage < min_callable_fraction` (0.90) OR `mean_readback_depth <
min_mean_depth` (20) → **`INCONCLUSIVE + [LOW_COVERAGE]`** (decision precedence rung 5).

### 5.3 Contamination — spike 柳叶蚂蟥 SRR27841063
① emits `COVERAGE_ANOMALY` → ② returns **`INCONCLUSIVE + [CONTAMINATION_SUSPECTED]`**, **never
AUTHENTIC** (decision precedence rung 2, before any identity check).

---

## Assertion — no forced judgment
Across every proven and every pinned-deferred scenario, an unmeasurable / missing-threshold /
uncallable-site / contamination condition degrades to **`INCONCLUSIVE` with an explicit reason code**
(decision_engine precedence ladder, `decision_engine/main.nf:87-119`). There is no code path that
upgrades a non-authentic or ambiguous condition to `AUTHENTIC`. The `AUTHENTIC` branch is reachable
**only** after callable diagnostic sites + adequate coverage + identity ≥ `uncertainty_zone.upper`.
