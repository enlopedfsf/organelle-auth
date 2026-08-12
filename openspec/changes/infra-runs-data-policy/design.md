# Design: canonical run roots

## Path contract

The repository root is resolved from the launcher location, never from the caller's
current directory. Defaults are `runs/input`, `runs/output`, and `runs/work`; explicit
`ORG_AUTH_INPUT`, `ORG_AUTH_WORK`, `--input`, `--outdir`, and `-work-dir` remain supported.
The launcher must fail before Nextflow starts when the selected samplesheet is absent or
empty.

## Provenance and collision control

Pipeline reports use stable names under `runs/output/pipeline_info/` and overwrite only
the named report files. Run parameters, commit, tool versions, and Nextflow history remain
the provenance source; stable filenames are not treated as scientific identity.

## Local-data policy

Large FASTQ/BAM/work products remain local and are never added by a bulk Git command.
Versioned manifests and reports may be force-added explicitly. The repository `.gitignore`
will contain the canonical `runs/output/` and `runs/work/` exclusions and the narrowly
scoped evidence exceptions. Because nf-core lint normally compares `.gitignore` with its
template, the intentional project policy must be declared explicitly in `.nf-core.yml`
(`files_unchanged: .gitignore`) and documented in the PR. This is a deliberate, reviewable
template deviation, not a silent lint bypass; the full nf-core lint job must remain green.

No task deletes or moves existing data. A setup/check command reports path collisions and
requires explicit confirmation before any migration, which is outside this change.

## Validation

Tests will assert: launcher path resolution from another directory, non-empty input
preflight, explicit override behavior, stable report paths, and preservation of existing
work directories. Nextflow config/schema and strict OpenSpec validation must pass.
