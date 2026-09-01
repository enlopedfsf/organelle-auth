## ADDED Requirements

### Requirement: Candidate audit packages are independently reproducible
Each taxon package SHALL include immutable source identifiers, SHA256 manifests, route rationale, evaluable-region definitions, unresolved-locus ledger, topology exclusions, tool/container identities, and explicit release blockers. The package MUST NOT be publishable as a production reference when any required provenance or blocker record is absent (REL-001, REL-003).

#### Scenario: Source evidence is complete
- **WHEN** a package is assembled from M4-① artifacts
- **THEN** all source paths and checksums resolve within the repository or its manifest contract

#### Scenario: A blocker is present
- **WHEN** topology, unresolved regions, or evidence provenance prevents reference-grade release
- **THEN** the blocker is machine-readable and the package remains CANDIDATE/INCONCLUSIVE
