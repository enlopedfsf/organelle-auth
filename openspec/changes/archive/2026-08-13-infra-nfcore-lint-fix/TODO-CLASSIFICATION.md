# CI lint TODO classification

Baseline: `origin/dev` at `be1c71eda2cdd76705de8d460770036c5b7b6f19`.

The 18 TODO findings reported by the CI nf-core lint run are classified below.

## Template placeholders (remove)

- `CHANGELOG.md`: unreleased-date marker
- `main.nf`: optional FASTA-file marker
- `nextflow.config`: command-line-flags marker
- `nextflow.config`: optional pipeline-specific config marker
- `README.md`: documentation, figure, default-steps, execution, minimal-example, contributor, citation, and bibliography markers (8)
- `tests/nextflow.config`: additional-parameters marker
- `conf/base.config`: process-defaults and process-requirements markers (2)

## Genuine pending work (retain and track as issues)

- `nextflow.config`: nf-core modules issue #6694 compatibility note; retained because it tracks an external dependency decision.
- `nextflow.config`: contributor metadata marker; retained until authorship is confirmed.

The CI display reports 18 findings after grouping repeated marker text; the source inventory above is the auditable file-level classification. No policy threshold, tool-admission, routing, or decision TODO is deleted.
