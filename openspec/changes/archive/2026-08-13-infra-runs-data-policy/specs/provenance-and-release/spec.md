## ADDED Requirements

### Requirement: Stable run report locations

The local pipeline SHALL publish execution reports and parameter provenance under
`runs/output/pipeline_info/` using stable, documented report filenames. The nf-core-owned
parameter dump MAY retain a timestamped filename, provided it remains in that directory and
run identity is retained in its content and Nextflow history.

#### Scenario: Repeated local launch

- **WHEN** compatible runs are launched through the canonical launcher
- **THEN** report locations remain under the canonical report directory and no timestamp-based report tree is created

### Requirement: Non-destructive work-directory policy

The run policy SHALL keep Nextflow task work under `runs/work/` by default, document
explicit legacy-cache resume behavior, and SHALL NOT delete or move existing work or
output data as part of normal setup or launch.

#### Scenario: Legacy resume

- **WHEN** a user explicitly supplies a legacy work directory with `-resume`
- **THEN** the pipeline attempts compatible task reuse without moving or deleting that directory
