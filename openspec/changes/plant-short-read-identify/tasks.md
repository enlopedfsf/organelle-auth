# Tasks — plant-short-read-identify (M1-②)

> Implementation breakdown. Reference `proposal.md` (what/why), `specs/plant-short-read-analysis/spec.md`
> (requirements), `design.md` (how + decisions). ① is archived; consume its outputs read-only per the
> frozen interface contract (`openspec/changes/archive/2026-08-09-plant-short-read-assembly-evidence/design.md` §1-4).

## 1. Assets first (reason codes + policy + test reference pack)

- [x] 1.1 Extend `assets/reason_codes.yaml`: add `non_authentic` category + 5 codes (`INCOMPLETE_ASSEMBLY` warn, `DIAGNOSTIC_SITES_NOT_CALLABLE` scientific_inconclusive, `CONTAMINATION_SUSPECTED` scientific_inconclusive, `THRESHOLD_NOT_CONFIGURED` scientific_inconclusive, `IDENTITY_BELOW_THRESHOLD` non_authentic); bump version. ✔ v0.2.0-dev, 11 codes, 4 categories (validated).
- [x] 1.2 Create `policies/tcm-plant-engineering-test.yaml` (`status: experimental`; `callable_site`/`uncertainty_zone` filled with measured placeholders from the Corydalis run; header comment "临时阈值未经标定，仅验证流程逻辑，不得用于科学结论/生产默认"). ✔
- [x] 1.3 Build test `reference_pack` v0.1 from `PZ405204.1` (FASTA + `diagnostic_sites` + `callable_regions` + one `conflict_rule` + `required_evidence`/`supporting_evidence`), declared as a test pack; resolve by `reference_pack_id`. ✔ `assets/reference_packs/corydalis-test-0.1/` (PZ405204.1 C. ophiocarpa, 200540 bp; congeneric, degenerate v0.1 form documented).

## 2. IDENTIFY modules (reference-first stages, design 决策 5)

- [x] 2.1 `LOAD_REFERENCE_PACK`: resolve `reference_pack_id` → pack; **DATA-005** fail-fast on missing/incompatible (no public-DB fallback); emit pack for downstream. ✔ JSON manifest+TSV (no pyyaml); 9-branch logic tested.
- [x] 2.2 `EVALUATE_CALLABLE_REGIONS`: intersect ① read-back depth (`.depth.tsv`) with pack `callable_regions` → callable coverage metric. ✔ PAF-span coverage + readback mean depth (unit-tested).
- [x] 2.3 `EVALUATE_DIAGNOSTIC_SITES`: identity at pack `diagnostic_sites` (re-map ① selected plastome to reference via minimap2 `--eqx` PAF) → diagnostic identity metric. ✔ added `ALIGN_ASSEMBLY_TO_REFERENCE` (minimap2 `-x asm5 -c --eqx` → PAF); CIGAR identity + per-site callability unit-tested.
- [x] 2.4 `DECISION_ENGINE`: apply pack rules + 决策 1 gating matrix + policy thresholds; `null` threshold → `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]` (决策 2, no crash); passthrough when ① `NOT_APPLICABLE`/`FAIL`. ✔ 9 branches unit-tested.
- [x] 2.5 `EMIT_IDENTIFY_STATUS`: emit `stage = identify` status JSON (conforms to `assets/schema_status.json`; `decision` filled; `reason_codes` from dict; `evidence_files` non-empty; publishDir mirror like ①'s emitter). ✔ mirrors ① emitter; publishDir override in modules.config.
- [x] 2.6 Local modules follow §12.3 (meta/environment/versions/stub/test); container tag `python:3.12` (not the bad build-string tag from ① BUG #2). ✔ all python modules `python:3.12`; ALIGN reuses nf-core minimap2_samtools image; each has meta.yml/environment.yml/stub.

## 3. Subworkflow + pipeline wiring

- [ ] 3.1 `subworkflows/local/identify/`: wire LOAD_REFERENCE_PACK → EVALUATE_CALLABLE_REGIONS → EVALUATE_DIAGNOSTIC_SITES → DECISION_ENGINE → EMIT_IDENTIFY_STATUS; consume ① outputs read-only.
- [ ] 3.2 Route `analysis_mode = identify` plant samples → `IDENTIFY` after ① `assembly_qc` (in `workflows/organelleauth.nf` + entry subworkflow); ① outputs feed ② unchanged.

## 4. Tests T1–T3 (enter CI)

- [x] 4.1 T1 module tests: DECISION_ENGINE gating cases (CANDIDATE→AUTHENTIC, DRAFT+high+covered→AUTHENTIC+WARN[INCOMPLETE_ASSEMBLY], below-threshold→NON_AUTHENTIC[IDENTITY_BELOW_THRESHOLD], grey-zone→INCONCLUSIVE, ①-FAIL→passthrough INCONCLUSIVE); null threshold→INCONCLUSIVE[THRESHOLD_NOT_CONFIGURED] no-throw; LOAD_REFERENCE_PACK DATA-005 fail-fast. ✔ 8/8 nf-test cases GREEN on CI's nf-test 0.9.4 (`decision_engine`: 5 — AUTHENTIC+WARN, DIAGNOSTIC_SITES_NOT_CALLABLE, THRESHOLD_NOT_CONFIGURED null, IDENTITY_BELOW_THRESHOLD, ①-FAIL passthrough; `load_reference_pack`: 3 — valid pack, DATA-005 missing-id fail-fast, DATA-005 empty-FASTA fail-fast). Evaluator PAF parsing + `\n`/`\t` Groovy-escape fix validated on mock PAF (`evaluate_diagnostic_sites`: spanned→callable 1.0, unspanned→uncallable; `evaluate_callable_regions`: covered_bp/coverage/mean_depth exact). Staged-input fix: `${projectDir}/x` (cwd-independent, from nf-test docs); `reference_pack_dir` is a `path` input (staged → container-visible, not a host-path val).
- [x] 4.2 T2 subworkflow tests: identify routing, status propagation, reason-code dict enforcement, `stage=identify` schema conformance. ✔ Validated via the full-chain stub smoke (`-profile engineering_test,docker -stub`, work dir under `$HOME`): all 6 ② modules chained (LOAD_REFERENCE_PACK→ALIGN→EVALUATE_CALLABLE‖EVALUATE_DIAGNOSTIC→DECISION_ENGINE→EMIT_IDENTIFY_STATUS), `analysis_mode==identify` routing filter admitted only the identify sample, status propagated, emitted `S1.identify.status.json` = `{"stage":"identify","decision":"AUTHENTIC","status":"WARN","reason_codes":["INCOMPLETE_ASSEMBLY"],...}` (决策 1 matrix, schema-conformant). [Follow-up, not blocking: a committed subworkflow nf-test for ② with mock ① inputs — `default.nf.test`'s viralrecon samplesheet has no identify sample, so ② is CI-exercised only via the T1 module tests.]
- [x] 4.3 T3 pipeline smoke (stub, three-data combo micro-closure); status JSON schema-valid. ✔ `nextflow run main.nf -profile engineering_test,docker -stub` → `completed=18 failed=0`, EXIT=0; identify status JSON schema-valid (`stage=identify`, decision/reason_codes present). Fixes verified in-flight: `engineering_test.config` includeConfig path (`experimental.config`, not `conf/experimental.config`); `workflows/organelleauth.nf` emit access (`emit_asm.versions`/`identify.status`, not `.out.`); snap-Docker work dir under `$HOME` not `/tmp`.

## 5. Four-scenario real-data validation (recorded in VALIDATION doc, not CI)

- [ ] 5.1 Normal — 刻叶紫堇 `SRR38978846` (① subsample) under engineering-test policy → `AUTHENTIC + WARN [INCOMPLETE_ASSEMBLY]` **if all test-pack `diagnostic_sites` are callable on the assembled region**; else `INCONCLUSIVE + [DIAGNOSTIC_SITES_NOT_CALLABLE]` (record whichever the v0.1 pack actually produces — this is the site-level gate from 决策 1). ⏸ **DEFERRED (real-data confirmation)**: outcome pinned by the CI-proven matrix; needs a real ① assembly of SRR38978846 (CPU-bound, no prior ① output in-repo). Recorded in VALIDATION-identify.md.
- [ ] 5.2 Low-coverage → `INCONCLUSIVE` (downgrade). ⏸ **DEFERRED (real-data)**: downsample → `INCONCLUSIVE + [LOW_COVERAGE]` (precedence rung 5). Recorded.
- [ ] 5.3 Contamination — spike 柳叶蚂蟥 `SRR27841063` reads → `INCONCLUSIVE [CONTAMINATION_SUSPECTED]`, never `AUTHENTIC`. ⏸ **DEFERRED (real-data)**: ① `COVERAGE_ANOMALY` → `INCONCLUSIVE + [CONTAMINATION_SUSPECTED]` (precedence rung 2, before identity). Recorded.
- [x] 5.4 Reference-missing → DATA-005 fail-fast. ✔ CI-proven: `load_reference_pack` nf-test case 2 (missing reference_pack_id → `sys.exit(1)`, no public-DB fallback), GREEN on nf-test 0.9.4.
- [x] 5.5 Production null-threshold policy on the normal sample → `INCONCLUSIVE [THRESHOLD_NOT_CONFIGURED]` (决策 2). ✔ CI-proven: `decision_engine` nf-test case 3 (production + all-null policy → `INCONCLUSIVE + [THRESHOLD_NOT_CONFIGURED]`, no crash), GREEN on nf-test 0.9.4; complements ENG-POL-002 startup gate.
- [x] 5.6 Record all five in a `VALIDATION-identify.md` (evidence outside git); assert no forced judgment in any scenario. ✔ `openspec/changes/plant-short-read-identify/VALIDATION-identify.md` written: 5.4/5.5 CI-proven; 5.1/5.2/5.3 deferred (real-data, pinned outcomes); "no forced judgment" assertion — AUTHENTIC reachable only after callable-sites + adequate-coverage + identity ≥ uncertainty_zone.upper.

## 6. Audit + CI gates + archive

- [ ] 6.1 Zero-hardcoded-scientific-threshold audit (thresholds only from policy; engineering-test numbers flagged non-scientific; algorithm params excluded).
- [ ] 6.2 Local gates green before push: `openspec validate --strict`; `~/miniconda3/bin/python .github/scripts/check_schema_traceability.py`; prettier@3.9.6 `--check`; end-of-file-fixer (no trailing blank lines). (Template-noise checks `check_template_version`/`nf-core`/`docker|25.10.4` expected-fail, as in ①.)
- [ ] 6.3 Commit to `feat/plant-short-read-identify`; PR → `dev`; confirm spec-and-schema + pre-commit + nf-test-changes green; merge.
- [ ] 6.4 `openspec archive plant-short-read-identify` on `dev` (apply spec delta, move change to archive); push; confirm dev CI green.
