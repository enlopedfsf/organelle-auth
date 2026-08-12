## Why

The repository-wide nf-core lint gate currently fails on template TODO placeholders, missing subworkflow metadata, and a version warning. This blocks otherwise scoped PRs, including the M3 animal closeout, and must be repaired as an independent infrastructure change.

## What Changes

- Add only the required `meta.yml` metadata for the nine named local subworkflows.
- Review each reported TODO; remove pure template placeholders and record genuine unresolved policy/tooling items as issues rather than silently deleting them.
- Resolve the reported nf-core version metadata warning without changing workflow behavior.
- Add regression checks proving workflow source and nf-test behavior are unchanged.
- Keep runs-data policy, full `.gitignore` policy, proxy normalization, and workflow logic changes out of scope.

## Capabilities

### New Capabilities

None; this is a tooling and repository-quality repair.

### Modified Capabilities

None; no scientific or runtime requirement changes.

## Impact

The change affects nf-core lint metadata, documentation placeholders, and CI validation only. It must not alter Nextflow process wiring, parameters, containers, evidence status, or decision routing. It is intentionally separate from PR #12 and from C1/C2/C3.
