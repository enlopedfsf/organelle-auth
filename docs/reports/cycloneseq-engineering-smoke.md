# CycloneSEQ 工程冒烟，非科学结论

This report is an engineering-fixture contract only. It does not report a biological result, transfer validation, authentication result, or Go/No-Go decision.

## Frozen scope

The planned public bacterial fixtures are `CNP0006129` and `PRJNA1194773` (resolved NCBI run `SRR31850014`). Acquisition, file sizes, and SHA256 values must be frozen before execution. `CNP0006129` requires a configured CNGB direct URL and checksum; no substitute accession is permitted. Rosa remains `QUEUED` and is not executed by this change.

## Status contract

- `decision=NOT_APPLICABLE`
- real CycloneSEQ state: `PENDING_REAL_DATA`
- Q10–Q11 is an uncalibrated descriptive expected band, never a threshold or gate
- outputs are prohibited from `IDENTIFY` and `DECISION`

## Execution boundary

Download uses resume-safe `prefetch`/`aria2c` and fails closed on checksum mismatch. `SRR31850014` downloaded and passed SRA validation with SHA256 `7a9108b9821decd5fa1e20fe9790b766681b2aedaa438daf3b7ff049a896e085`; both installed SRA conversion tools then exited with SIGSEGV, so the run is `INFRASTRUCTURE_BLOCKED`. A missing CNGB URL or network failure is also infrastructure-only. The engineering run may emit only the non-scientific status contract above.
