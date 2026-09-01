## 1. Freeze and ingest

- [x] 1.1 Verify M4-① and plant callability manifests and checksums without modifying source evidence.
- [x] 1.2 Create immutable per-taxon source and candidate manifests.

## 2. Audit and package

- [x] 2.1 Package plant R1P1 with route rationale, callable regions, unresolved loci, and topology exclusion.
- [x] 2.2 Package animal eligible routes as `CONDITIONAL` with unresolved-repeat and topology blockers.
- [x] 2.3 Emit status objects as `INCONCLUSIVE / CANDIDATE / NOT_APPLICABLE` and generate a release-blocker ledger.
- [x] 2.4 Assert no topology, authentication, IDENTIFY/DECISION, or CycloneSEQ state changes.

## 3. Verification

- [x] 3.1 Add schema/checksum/provenance tests for candidate packages.
- [x] 3.2 Run `openspec validate --all --strict` and focused tests; stop at review without publishing or promoting a reference.
