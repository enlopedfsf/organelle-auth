## Context

This is an engineering-only fixture for validating workflow plumbing before real paired CycloneSEQ data arrive.

## Goals / Non-Goals

**Goals:** prove accession manifest handling, deterministic acquisition/integrity checks, routing, QC parsing, isolation, and audit packaging.

**Non-Goals:** scientific accuracy, transfer validation, threshold calibration, authentication, Go/No-Go, plant/animal assembly, or Rosa execution.

## Decisions

1. Use only public bacterial accessions `CNP0006129` and `PRJNA1194773`; freeze metadata and checksums before execution.
2. Treat Q10–Q11 as an expected descriptive band in the fixture report, explicitly marked uncalibrated and non-gating.
3. Emit machine-readable status with `decision=NOT_APPLICABLE`; real data state remains `PENDING_REAL_DATA`.
4. Keep all smoke outputs in an engineering namespace and assert they cannot enter `IDENTIFY` or `DECISION`.
5. Register Rosa as `QUEUED` only. Any execution requires a later change.

## Risks / Trade-offs

- [Public accession changes] → checksum and metadata freeze fails closed.
- [Engineering green is over-interpreted] → title, status, and routing assertions repeat the non-scientific boundary.
- [Large fixture files] → keep them outside Git and commit manifests/checksums only.

## Migration Plan

Apply will create fixtures, schemas, and tests only after review. No production policy or real-data status is migrated.
