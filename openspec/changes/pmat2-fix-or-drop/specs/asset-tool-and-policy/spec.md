## ADDED Requirements

### Requirement: PMAT2 has a bounded fix-or-drop disposition
The PMAT2 candidate SHALL have exactly one runtime-repair attempt. The repair SHALL verify that the rebuilt image contains an executable PMAT2 entry point before any biological input is used. A successful repair SHALL produce one comparison record against the checksum-frozen plant long-read result; a failed repair, failed execution, or uninterpretable comparison SHALL produce a terminal `DROP` record and remove PMAT2 from the active candidate registry. Exit 127 SHALL be recorded as runtime unavailability, not as biological evidence (ENG-POL-002, TEST-003).

#### Scenario: Repair succeeds and comparator is interpretable
- **WHEN** the single image rebuild passes executable preflight and the frozen plant comparison satisfies the registered evidence contract
- **THEN** the registry records the pinned runtime and comparator evidence while PMAT2 remains non-production and outside `IDENTIFY`/`DECISION`

#### Scenario: Repair or comparator fails
- **WHEN** the rebuild, executable preflight, comparator run, or interpretation contract fails
- **THEN** the registry records `DROP` with immutable logs and the issue closeout cites the failure without biological claims

#### Scenario: No repeated attempt is requested
- **WHEN** a second repair, parameter search, animal run, or M4 dependency is proposed
- **THEN** the change rejects it as out of scope and leaves animal and M4 work unblocked
