## 1. Fixture and provenance

- [x] 1.1 Create the accession manifest for CNP0006129 and PRJNA1194773 with source metadata, sizes, and SHA256 fields.
- [x] 1.2 Implement deterministic bounded acquisition/integrity checks without downloading Rosa.

## 2. Engineering assertions

- [x] 2.1 Add ingestion, manifest, QC, routing, and output-isolation fixtures.
- [x] 2.2 Record Q10–Q11 as an uncalibrated expected band and reject use as a threshold or scientific conclusion.
- [x] 2.3 Emit the report title containing “CycloneSEQ 工程冒烟，非科学结论” and machine status `decision=NOT_APPLICABLE`.
- [x] 2.4 Assert smoke outputs cannot flow to `IDENTIFY`/`DECISION`; keep real CycloneSEQ `PENDING_REAL_DATA`.

## 3. Audit and validation

- [x] 3.1 Register Rosa as queued-only metadata.
- [x] 3.2 Commit audit manifest/checksums while excluding large data/work directories.
- [x] 3.3 Run focused tests and `openspec validate --all --strict`; stop at review without executing the smoke.

## 4. Download and engineering run

- [ ] 4.1 Resolve and freeze the CNP0006129 CNGB direct URL and SHA256; if unavailable, record `INFRASTRUCTURE_BLOCKED` without substituting data.
- [ ] 4.2 Download `SRR31850014` with resume-safe SRA acquisition, verify checksum, and record file metadata outside Git.
- [ ] 4.3 Run the bounded engineering smoke in CI, emit only the non-scientific status contract, and upload the audit artifact.
- [ ] 4.4 On network failure, preserve logs and classify infrastructure blockage; do not reinterpret it as a scientific result.
