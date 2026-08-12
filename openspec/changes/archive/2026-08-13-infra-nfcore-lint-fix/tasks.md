## 1. Inventory and classification

- [x] 1.1 Record the complete CI lint failure list and baseline commit.
- [x] 1.2 Classify the 18 reported TODO findings at file/marker level; preserve the classification artifact and note that the complete cleanup was not applied.

## 2. Minimal metadata repair

- [x] 2.1 Add metadata-only `meta.yml` files for the nine named subworkflows using existing interfaces.
- [ ] 2.2 Resolve and record the nf-core version warning (not completed in PR #13/#14).
- [ ] 2.3 Remove only classified pure template TODOs; preserve policy/scientific TODOs (superseded).

## 3. Verification

- [ ] 3.1 Verify no Nextflow process, parameter, module wiring, container, or evidence file changed.
- [ ] 3.2 Run nf-core lint with the CI tool version and capture the result.
- [ ] 3.3 Run schema checks and the full nf-test matrix; confirm no behavioral regression.
- [ ] 3.4 Run the full nf-test matrix once on the baseline and once after the repair; verify identical result sets (no archived evidence).
- [ ] 3.5 Require the nf-core lint check to be fully green; no advisory/ignored lint result is acceptable.

## 4. Review handoff

- [ ] 4.1 Commit only the infrastructure lint changes on `infra-nfcore-lint-fix`.
- [ ] 4.2 Open an independent PR with included/excluded scope and baseline comparison.
- [ ] 4.3 Wait for user acceptance before merge; do not modify PR #12 or C1/C2/C3.

## Closeout

This change is archived as `PARTIAL/SUPERSEDED`. The merged metadata repair is evidenced by PRs #13/#14 and their green CI checks; unchecked tasks remain open for a separate follow-up change.
