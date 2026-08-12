# Tasks

- [x] 1. Add the canonical path contract to `nextflow.config` and `nextflow_schema.json`.
- [x] 2. Add or update the repository-root launcher with non-empty input preflight and explicit override support.
- [x] 3. Make execution reports use stable names under `runs/output/pipeline_info/`; retain the nf-core-owned timestamped parameter dump without changing scientific logic.
- [x] 4. Add the minimal `.gitignore` policy and explicit `.nf-core.yml` template-deviation declaration.
- [x] 5. Update `docs/usage.md` and `docs/output.md` with canonical paths, resume rules, and no-delete/no-move policy.
- [x] 6. Add path/preflight regression tests; prove behavior is unchanged outside path resolution and report naming.
- [x] 7. Run focused tests, nf-core lint, CI, and `openspec validate --strict`; inspect the changed-file list before commit.
