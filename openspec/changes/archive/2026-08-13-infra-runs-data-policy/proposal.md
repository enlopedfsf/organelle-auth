# Proposal: Fixed runs input/output/work policy

## Why

Previous runs were launched from multiple working directories and reused unrelated
Nextflow caches. This made valid results difficult to locate and weakened provenance.

## What changes

Introduce one canonical local layout rooted at the repository:

```text
runs/input/   staged inputs and samplesheet
runs/output/  published outputs and pipeline reports
runs/work/    Nextflow task work and resume cache
```

The launcher, Nextflow defaults, schema, and documentation will use these paths while
retaining explicit override support for deliberate isolated runs. The policy also records
how old work directories may be used with `-resume` without moving or deleting them.

## Scope

In scope: launcher and path defaults, report naming, input preflight, output/work
documentation, local data-policy markers, and tests for path determinism.

Out of scope: scientific thresholds, routing/decision logic, reference data, existing
results, deletion or movement of any `runs/` data, and C2/C3 archival changes.

## Spec domain

The spec delta belongs to the existing `scope-routing-and-input` and
`provenance-and-release` capability domains. No new experiment-named spec domain is
created.
