## 1. Reference pack, policy, and controlled evidence assets

- [x] 1.1 Create animal reference pack v0.1 under `assets/reference_packs/` with `CM084263.1` as `decision_reference`, immutable checksum/provenance fields, explicit same-BioProject circularity disclosure, and diagnostic/callable-region files that exclude D-loop and the M2-① assembly-gap mask (DATA-005, SCI-001).
- [x] 1.2 Add `NC_023928` as a `QUARANTINED` audit record in the pack metadata, including the 87.62% divergence, pointer to `VALIDATION-animal.md` STOP/REPORT evidence, and Ye et al. (2015) misidentification citation; make the loader reject it for all decision inputs.
- [x] 1.3 Add animal engineering-test and production-null policy packs. Put the same-data high-consistency placeholder values and full evidence/rationale/disclaimer in the engineering policy header; keep production rule thresholds all `null` and wire `THRESHOLD_NOT_CONFIGURED` behavior (ENG-POL-001/002/003/004/005).
- [x] 1.4 Define the SCI-007 empty nuclear-marker panel input/status contract and add all identify-stage reason codes to `assets/reason_codes.yaml`, including `INCOMPLETE_ASSEMBLY`, `DIAGNOSTIC_SITES_NOT_CALLABLE`, `THRESHOLD_NOT_CONFIGURED`, marker-missing, and controlled identity-conflict codes.
- [ ] 1.5 Update `assets/compatibility_manifest.yaml`, input/status schemas, and traceability metadata so the animal pack, policy, marker interface, and identify stage are versioned independently and linked to the applicable Requirement IDs.

## 2. Animal identify implementation and gate matrix

- [x] 2.1 Extend the existing `LOAD_REFERENCE_PACK` path to validate the animal pack metadata, CM084263 decision eligibility, NC_023928 quarantine, gap/D-loop exclusion, checksums, and DATA-005 fail-fast behavior with no public-DB fallback.
- [x] 2.2 Extend `DECISION_ENGINE` with the animal gate matrix: callable non-risk diagnostics are required; DRAFT may yield `AUTHENTIC + WARN + INCOMPLETE_ASSEMBLY`; M2-① `NUMT_RISK_SUSPECTED` propagates as a warning/downgrade only; conflicts can yield `NON_AUTHENTIC`; missing evidence/null thresholds yield `INCONCLUSIVE`.
- [ ] 2.3 Add the SCI-007 marker interface to the decision input and status output. Keep the panel empty/placeholder, propagate missing or mismatched panel state, and prohibit automatic ITS2 fallback or fabricated marker evidence.
- [ ] 2.4 Extend `IDENTIFY`/`ORGANELLEAUTH` routing for animal short-read samples to consume M2-① outputs read-only and emit an isolated `stage = identify` status without changing any M2-① path, file, assembly grade, or assembly-stage reason code.
- [ ] 2.5 Ensure production all-null policy is rejected at startup and that a runtime null reaching the module emits `INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED` without crashing or substituting a hardcoded value.

## 3. T1–T3 tests and local validation evidence

- [ ] 3.1 Add T1 module tests for pack quarantine/metadata, policy null behavior, animal DRAFT/NUMT gate outcomes, SCI-007 empty panel propagation, controlled reason codes, and schema-valid identify status.
- [ ] 3.2 Add T2 animal branch tests covering M2-① `CANDIDATE`/`DRAFT`/`FAIL`, callable versus missing diagnostic windows, NUMT WARN propagation, marker absence, and reference/policy fail-fast behavior.
- [ ] 3.3 Add T3 end-to-end stub smoke covering animal routing, assembly-to-identify state propagation, isolated output paths, and plant-route regression.
- [ ] 3.4 Run the local real-data normal scenario with CM084263 and engineering-test policy; record inputs, pack/policy IDs, status JSON, expected versus actual state, and the circularity limitation in `VALIDATION-animal-identify.md`.
- [ ] 3.5 Run and record the low-coverage scenario as `INCONCLUSIVE` or an explicit downgrade, with no forced call and complete evidence files.
- [ ] 3.6 Run and record the missing-reference scenario as fail-fast before `DECISION_ENGINE`, with no silent fallback or output masquerading as an identify result.
- [ ] 3.7 Re-run the normal scenario with production all-null policy and record `INCONCLUSIVE + THRESHOLD_NOT_CONFIGURED`; verify no engineering placeholder value leaked into production behavior.

## 4. CI, image, and release gate

- [ ] 4.1 Add or update GitHub Actions jobs so T1, T2, and T3 for animal identify run on the relevant PR/branch and publish traceable logs/artifacts; preserve T0 OpenSpec/schema/lint gates.
- [ ] 4.2 Resolve the M2-① GHCR image problem tracked by issue #6 via a verified local push or canonical CI build/push, pin the resulting image by immutable digest, and prove the image is pullable by CI.
- [ ] 4.3 Run the complete T1–T3 CI matrix after the image issue is resolved; do not mark skipped/missing jobs as green. Record the run URL, image digest, and artifact links in the validation/release record.
- [ ] 4.4 Enforce the hard gate: **M2-② 归档前 T1–T3 CI 必须全绿（含 M2-① 遗留的镜像问题已解决）**. M2-② archive is blocked until image publication, all T1–T3 jobs, and their traceable evidence are green.

## 5. Governance and completion checks

- [ ] 5.1 Update `openspec/traceability.yaml` for all added animal identify Requirement IDs and link implementation/tests/validation evidence without orphaned requirements.
- [ ] 5.2 Run `openspec validate --strict`, JSON/YAML schema checks, nf-core lint, and affected nf-test suites; resolve every failure before proposing archive.
- [ ] 5.3 Confirm M2-① assembly outputs and archived artifacts are unchanged, plant identify regression remains green, and the M2-② change remains unarchived until task 4.4 is satisfied.
