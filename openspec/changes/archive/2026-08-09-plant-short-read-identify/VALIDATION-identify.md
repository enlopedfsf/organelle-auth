# VALIDATION-identify.md — M1-② plant-short-read-identify

Record of the four(+null) validation scenarios from `tasks.md §5`. Per `tasks.md 5.6`, the raw
validation **evidence** (real FASTQs, `work/` dirs, real ① assembly outputs) lives **outside git** at
`~/corydalis_validation/`; this file is the in-repo summary. "No forced judgment" is asserted at the end.

Validation spans two tiers:
- **CI-proven** (logic): exercised by committed nf-test cases on nf-test 0.9.4 (CI version) + the
  full-chain stub smoke. These are gating.
- **Real-data** (science): real ① assembly of the Corydalis sample `SRR38978846` (刻叶紫堇), end-to-end
  through IDENTIFY, one run per scenario, engineering-test policy (scenario 5 excepted). **Executed
  2026-08-09.** Expected-vs-actual recorded below; two scenarios **diverged from the pre-pinned
  expectation** — both are honest findings, not forced calls.

---

## CI-proven (gating)

### 5.4 Reference-missing → DATA-005 fail-fast ✔
`load_reference_pack` nf-test case *"DATA-005: missing reference_pack_id → fail-fast"* — a pack root
with no `nonexistent/` subdir → `sys.exit(1)` with `DATA-005: reference pack not found`. No public-DB
fallback. **GREEN on nf-test 0.9.4.** (Also confirmed end-to-end on real data — see Real-data 5.4.)

### 5.5 Production null-threshold → INCONCLUSIVE [THRESHOLD_NOT_CONFIGURED] ✔ (决策 2)
`decision_engine` nf-test case *"null policy threshold → INCONCLUSIVE [THRESHOLD_NOT_CONFIGURED]"* —
a `production`-status policy with `callable_site:null, uncertainty_zone:null` → the module-layer null
defense returns `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]`, **no crash, no forced call**. This
complements (does not replace) the ENG-POL-002 startup gate that blocks `production + all-null policy`
at launch. **GREEN on nf-test 0.9.4.** (Also confirmed end-to-end on real data — see Real-data 5.5.)

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

## Real-data (executed 2026-08-09)

All scenarios reuse the same ① subsampled input (`SRR38978846` → ~2 Gb, 6,671,740 PE reads), the
`corydalis-test-0.1` reference pack, and (except 5.5) the `tcm-plant-engineering-test-0.1.0` policy
(experimental; `min_callable_fraction 0.9`, `min_mean_depth 20`, `uncertainty_zone [0.9, 0.99]`,
`non_authentic_identity 0.9`). ① assembly is CPU-bound (GetOrganelle; runs of tens of minutes are
normal and were allowed to complete). Runs share one work-dir under `-resume`; cached ① outputs are
reused across scenarios.

### Bug surfaced by the real run (transparency)
The scenario-1 real run first returned `THRESHOLD_NOT_CONFIGURED` with `policy_pack_id=null` *despite*
the engineering-test policy being supplied — a Docker-only bug invisible to CI: the policy pack was
passed as a **host-path `val`**, which Nextflow does **not** mount into the container, so
`DECISION_ENGINE` silently read `policy={}`. Fixed by staging the policy as a **`path`** (staged into
the work dir, container-visible) in three places — `decision_engine/main.nf` (input decl + script
template), `subworkflows/local/identify/main.nf` (`channel.value(file(params.policy_pack_file ?: ...))`),
and the `decision_engine` nf-test inputs — the same `val`→`path` fix already used by
`LOAD_REFERENCE_PACK`. CI did not catch this because nf-test runs host-side (host paths resolve). After
the fix, scenario 1 loads the policy correctly (`policy_pack_id="tcm-plant-engineering-test-0.1.0"`).
nf-test 5/5 still GREEN.

### 5.1 Normal — Corydalis SRR38978846, engineering-test policy
- **Input:** `SRR38978846` sub ~2 Gb (6,671,740 PE reads), reused from ①. `specimen_role=routine_test`.
- **Output status:** `INCONCLUSIVE + [LOW_COVERAGE]`; `assembly_grade=DRAFT`;
  `callable_coverage=0.888206`; `mean_readback_depth=1079.6354`; `diagnostic_identity=1.0`;
  `n_diagnostic_callable=5/5`; `uncallable_sites=[]`.
- **Expected (pre-pinned):** `AUTHENTIC + WARN[INCOMPLETE_ASSEMBLY]` *if all diagnostic sites callable
  on the assembled region*, else `INCONCLUSIVE + [DIAGNOSTIC_SITES_NOT_CALLABLE]`.
- **Actual vs expected:** **DIVERGED** — neither pinned branch. All 5 diagnostic sites ARE callable and
  identity is a perfect 1.0, so absent the coverage gate this would reach `AUTHENTIC`. But the DRAFT
  (6-scaffold, uncircularized) plastome spans only 88.8% of the pack's `callable_regions`, just below
  the placeholder `min_callable_fraction=0.9`, so rung 5 (`LOW_COVERAGE`) fires *before* the identity
  ladders. **Finding:** the v0.1 placeholder `min_callable_fraction=0.9` is too strict for a DRAFT
  plastome — the `AUTHENTIC` path is **unreachable** with this pack+threshold. This is calibration
  feedback for M3 (the real `callable_site` threshold must be derived from DRAFT-grade reference
  assemblies, not a round placeholder).

### 5.2 Low-coverage — deep subsample, engineering-test policy
- **Input:** `SRR38978846` deep-sub ~0.5 Gb (1,667,947 PE reads, ~270× plastome), `seqkit sample -p 0.25
  -s 42` (fixed seed; same seed on R1/R2 preserves pairing).
- **Note on depth:** an 11× (0.02 Gb) subsample was tried first to exercise *depth-driven*
  `LOW_COVERAGE` (`mean_readback_depth < 20`), but **GetOrganelle's nrDNA (`embplant_nr`) assembly
  hangs at ~11×** (98% CPU, no I/O, 20+ min — a documented GetOrganelle low-coverage behavior; PT
  assembles fine at 11×, only nrDNA spins). The plant_sr_assembly subworkflow runs NR **unconditionally**
  (method §2.3: default plastome + nrDNA), so `targets=plastome` does not skip it. The user-suggested
  0.2–0.5 Gb range was therefore used: enough for NR to assemble, still genuinely reduced input.
- **Output status:** `AUTHENTIC + WARN[INCOMPLETE_ASSEMBLY]`; `assembly_grade=DRAFT`;
  `callable_coverage=0.900144`; `mean_readback_depth=269.8844`; `diagnostic_identity=1.0`;
  `n_diagnostic_callable=5/5`; `uncallable_sites=[]`.
- **Expected vs actual:** **DIVERGED from code prediction.** I predicted `INCONCLUSIVE + [LOW_COVERAGE]`
  via `callable_coverage` (≈0.888, the same DRAFT). Instead the reduced-input run produced a **slightly
  better assembly** (`callable_coverage=0.900144`, just above the 0.9 threshold), so the coverage gate
  **passed** and the identity ladder reached `AUTHENTIC`. The likely mechanism: at 2 Gb, GetOrganelle
  internally subsamples to ~500× (random draw), which happened to discard bridging reads and left
  `callable_coverage=0.888`; at 0.5 Gb it used **all** reads, producing marginally better contiguity
  that pushed coverage just above the threshold. **Finding:** the `min_callable_fraction=0.9` threshold
  is on a razor's edge for this DRAFT plastome — tiny assembly differences flip the decision, and
  more input can be worse when internal subsampling is active. Depth-driven `LOW_COVERAGE` (<20×) is
  still unreachable because nrDNA hangs at ~11×; that is a separate M2/M3 hardening item.

### 5.3 Contamination — spike 柳叶蚂蟥 SRR27841063, engineering-test policy
- **Input:** Corydalis sub (6.67 M PE reads) + 柳叶蚂蟥 `SRR27841063` (6.7 M PE reads), **50:50 mix**
  (13.37 M PE reads, ~4 Gb), `specimen_role=mixture_control`. Fixed by construction (equal read counts).
- **Output status:** `INCONCLUSIVE + [LOW_COVERAGE]`; `assembly_grade=DRAFT`;
  `callable_coverage=0.888206`; `mean_readback_depth=1079.783`; `diagnostic_identity=1.0`;
  `n_diagnostic_callable=5/5`; `uncallable_sites=[]`.
- **Expected (pre-pinned):** `INCONCLUSIVE + [CONTAMINATION_SUSPECTED]` — ① was to emit
  `COVERAGE_ANOMALY` → ② rung 2 (before any identity check).
- **Actual vs expected:** **DIVERGED by construction of ①.** `emit_assembly_qc_status` (①) binds the
  coverage-valley coefficient to a no-op (`_ = coverage_coeff`, line ~117); ① therefore **never emits
  `COVERAGE_ANOMALY`**, so ②'s contamination rung (rung 2) is **unreachable**. The 50:50 leech spike is
  **invisible** to the pipeline: the contam sample walks the same path as normal and resolves to
  `LOW_COVERAGE` (`callable_coverage ≈ 0.888`). **Finding:** ②'s contamination guard is dead because ①
  does not produce the upstream signal. Candidate fix: either wire ①'​s coverage-anomaly metric, or add
  a ②-level (host/contaminant) screen. **Honest assessment: ② does not detect cross-kingdom
  contamination in its current form** — recorded as a gap, not papered over.

### 5.4 Reference-missing → DATA-005 fail-fast ✔ (real)
- **Input:** `COR_NORMAL` with `reference_pack_dir` → an empty pack root
  (`empty_packs/corydalis-test-0.1/`, no `manifest.json`).
- **Output:** `LOAD_REFERENCE_PACK` exits 1 — `DATA-005: reference pack not found:
  empty_packs/corydalis-test-0.1/manifest.json`. Pipeline fails fast (`completed=2 failed=1 cached=11`,
  EXIT 1) before any alignment/identity work. No public-DB fallback. **Confirmed end-to-end on real
  data**, matching the nf-test case.

### 5.5 Production-null — COR_NORMAL, all-null production policy ✔ (real)
- **Input:** same cached `COR_NORMAL` ① outputs. Policy switched to
  `tcm-plant-production-null-0.1.0` (status `production`; **all thresholds null**).
- **Output status:** `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]`; `policy_status=production`;
  `thresholds_used` all `null`; `callable_coverage=0.888206`, `mean_readback_depth=1079.6354` (same
  ① assembly as 5.1).
- **Expected vs actual:** MATCHES. With null thresholds, rung 3 (`THRESHOLD_NOT_CONFIGURED`) fires
  *before* rung 5, so the `LOW_COVERAGE` reason that dominated 5.1 is **superseded** by
  `THRESHOLD_NOT_CONFIGURED`. No crash (module-layer null defense, 决策 2). Confirms null→
  `THRESHOLD_NOT_CONFIGURED` precedence over the coverage checks — a production pipeline with an
  unconfigured threshold degrades to `INCONCLUSIVE`, never to a forced `AUTHENTIC`.

---

## Summary table (real-data)

| # | Scenario | Policy | Status | Reason | callable_cov | depth | identity | Matches pin? |
|---|----------|--------|--------|--------|--------------|-------|----------|--------------|
| 1 | Normal | eng-test | INCONCLUSIVE | LOW_COVERAGE | 0.888206 | 1079.6 | 1.0 | ✗ (pin: AUTHENTIC) |
| 2 | Low-cov 0.5 Gb | eng-test | AUTHENTIC | INCOMPLETE_ASSEMBLY | 0.900144 | 269.88 | 1.0 | ✗ (predicted: LOW_COVERAGE) |
| 3 | Contam 50:50 | eng-test | INCONCLUSIVE | LOW_COVERAGE | 0.888206 | 1079.78 | 1.0 | ✗ (pin: CONTAM_SUSPECTED; ① silent) |
| 4 | No ref | eng-test | — (fail-fast) | DATA-005 | — | — | — | ✓ |
| 5 | Prod-null | prod-null | INCONCLUSIVE | THRESHOLD_NOT_CONFIGURED | 0.888206 | 1079.6 | 1.0 | ✓ |

---

## Assertion — no forced judgment
Across every executed and CI-proven scenario, an unmeasurable / missing-threshold / uncallable-site /
low-coverage condition degrades to **`INCONCLUSIVE` with an explicit reason code** (decision_engine
precedence ladder, `decision_engine/main.nf:87-119`). There is no code path that upgrades a
non-authentic or ambiguous condition to `AUTHENTIC`. The `AUTHENTIC` branch is reachable **only** after
callable diagnostic sites + adequate coverage + identity ≥ `uncertainty_zone.upper`.

Two honest divergences from the pre-pinned expectations are recorded above (5.1 `AUTHENTIC`
unreachable under the placeholder threshold; 5.2 the same threshold sits on a razor's edge — a 0.5 Gb
run reaches `AUTHENTIC` while the 2 Gb run fails coverage; 5.3 contamination rung dead because ① emits
no `COVERAGE_ANOMALY`). None were massaged to match the pin; all are forwarded as calibration /
hardening items for M3 / the contamination-detection redesign.
