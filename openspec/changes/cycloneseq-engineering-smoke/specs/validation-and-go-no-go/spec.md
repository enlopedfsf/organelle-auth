## ADDED Requirements

### Requirement: CycloneSEQ engineering smoke is isolated from scientific validation
The workflow SHALL support a bounded engineering smoke using public bacterial inputs `CNP0006129` and `PRJNA1194773`, with frozen accession/file checksums and audit metadata. Every report title SHALL contain “CycloneSEQ 工程冒烟，非科学结论”. The smoke SHALL emit `decision=NOT_APPLICABLE`, SHALL NOT satisfy transfer validation or Go/No-Go, and SHALL leave real CycloneSEQ state `PENDING_REAL_DATA` (SCI-003, TEST-003).

#### Scenario: Engineering fixture passes
- **WHEN** ingestion, manifest, QC, routing, and output-isolation assertions pass on the public fixture
- **THEN** the report records engineering PASS/WARN evidence only and retains `decision=NOT_APPLICABLE`

#### Scenario: Q10–Q11 is observed
- **WHEN** the fixture produces a value in the expected Q10–Q11 band
- **THEN** the band is reported descriptively and is not promoted to a calibrated threshold or production gate

#### Scenario: Rosa is referenced
- **WHEN** Rosa is mentioned during planning
- **THEN** it is recorded as queued follow-up only and is not downloaded, run, or compared

#### Scenario: Public smoke is mistaken for transfer validation
- **WHEN** a consumer attempts to use the smoke as scientific, transfer, authentication, or Go/No-Go evidence
- **THEN** the status contract rejects that use and keeps CycloneSEQ `PENDING_REAL_DATA`
