## 1. Inventory and classification

- [ ] 1.1 Record the complete CI lint failure list and baseline commit.
- [ ] 1.2 Classify all 18 reported TODOs as pure template placeholders or genuine follow-up work; record genuine items as issues or retained documentation.

## 2. Minimal metadata repair

- [ ] 2.1 Add metadata-only `meta.yml` files for the nine named subworkflows using existing interfaces.
- [ ] 2.2 Resolve the nf-core version warning with the smallest compatible metadata change.
- [ ] 2.3 Remove only classified pure template TODOs; preserve policy/scientific TODOs.

## 3. Verification

- [ ] 3.1 Verify no Nextflow process, parameter, module wiring, container, or evidence file changed.
- [ ] 3.2 Run nf-core lint with the CI tool version and capture the result.
- [ ] 3.3 Run schema checks and the full nf-test matrix; confirm no behavioral regression.

## 4. Review handoff

- [ ] 4.1 Commit only the infrastructure lint changes on `infra-nfcore-lint-fix`.
- [ ] 4.2 Open an independent PR with included/excluded scope and baseline comparison.
- [ ] 4.3 Wait for user acceptance before merge; do not modify PR #12 or C1/C2/C3.
