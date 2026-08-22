## Why

The project needs a bounded proof that the CycloneSEQ engineering path can ingest public data and exercise its contracts before real paired project data arrive. This smoke test must remain explicitly separate from scientific validation so a successful run cannot be mistaken for transfer qualification or an authentication result.

## What Changes

- Add a public-bacterial-data engineering smoke using the registered candidate projects `CNP0006129` and `PRJNA1194773`, with accession/run metadata, download provenance, file integrity, sizes, and SHA256 frozen before execution.
- Title every human-facing report **“CycloneSEQ 工程冒烟，非科学结论 / CycloneSEQ engineering smoke, not a scientific conclusion”**.
- Exercise ingestion, manifest validation, QC parsing, workflow routing, output isolation, failure semantics, and audit packaging; emit `decision=NOT_APPLICABLE` throughout.
- Treat the reported Q10–Q11 interval as a descriptive expected band for this engineering fixture, not a calibrated QC threshold, pass gate, platform claim, or production default.
- Register Rosa data only as queued follow-up input; do not download, execute, compare, or infer from Rosa in this change.
- Out of scope: plant/animal organelle assembly, authentication, blind validation, Go/No-Go, scientific accuracy or transfer claims, threshold calibration, real project CycloneSEQ data, and Rosa execution.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `validation-and-go-no-go`: add an explicit public-data engineering-smoke contract that cannot satisfy scientific validation or CycloneSEQ Go/No-Go.

## Impact

- OpenSpec delta: `validation-and-go-no-go`.
- Apply-stage assets: accession manifest, deterministic bounded download/subsample policy if required, smoke workflow/fixtures, QC and routing assertions, status/evidence schema checks, audit report, and tests.
- External data remain public engineering inputs; large reads and work directories remain outside Git with manifest/checksum references.
- `IDENTIFY`, `DECISION`, production policies, and real-data state are unchanged.
