## ADDED Requirements

### Requirement: Canonical run roots

The local pipeline launcher SHALL resolve paths from the repository root and SHALL default
to `runs/input`, `runs/output`, and `runs/work`. It MUST preserve explicit path overrides
for deliberate isolated runs and MUST NOT infer a different root from the caller's current
working directory.

#### Scenario: Launch from another directory

- **WHEN** the repository launcher is invoked from outside the repository
- **THEN** the selected input, published output, and task work paths resolve under the repository's `runs/` root

### Requirement: Fail-fast input preflight

The launcher SHALL verify that the selected samplesheet exists and is non-empty before
starting Nextflow, and SHALL return a non-zero status with the path when the check fails.

#### Scenario: Missing samplesheet

- **WHEN** the default or explicitly selected samplesheet is absent or empty
- **THEN** Nextflow is not started and the launcher reports the failing path
