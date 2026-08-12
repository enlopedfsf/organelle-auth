## Purpose

Defines an evidence-first hybrid reference-build capability that combines a frozen long-read structural candidate with parallel short-read polishing/evidence routes while preserving experimental status and authentication decision boundaries.

## ADDED Requirements

### Requirement: Frozen hybrid inputs and provenance

Each hybrid evaluation SHALL freeze the plant or animal taxon route, specimen identity, long-read backbone, paired short-read inputs, reference/policy/tool versions, command parameters, random seeds, input sizes, and SHA256 checksums before polishing begins. A run MUST fail before polishing when required files are missing, empty, unreadable, unpaired, or checksum-inconsistent (DATA-001, DATA-002, DATA-004, REL-001).

#### Scenario: Input manifest is complete

- **WHEN** a hybrid evaluation starts
- **THEN** it records a reproducible manifest for the frozen backbone and both short-read mates
- **AND** the manifest records whether the data are public evaluation data or real CycloneSEQ transfer data

#### Scenario: Invalid input is rejected

- **WHEN** a required input is absent, empty, unpaired, or fails its recorded checksum
- **THEN** the evaluation fails before assembly or polishing

### Requirement: Long-read structural candidate is separated from authentication

The capability SHALL construct or consume a long-read structural candidate using only admitted experimental tools and SHALL label its status `EXPERIMENTAL`, its assembly grade no higher than `CANDIDATE`, and its decision `NOT_APPLICABLE` unless an independent qualification protocol explicitly changes that state (SCI-003, SCI-005, ENG-POL-003).

#### Scenario: Long-read-only evidence remains non-decision evidence

- **WHEN** only the long-read backbone or its Racon-polished candidate is available
- **THEN** no `AUTHENTIC` or `NON_AUTHENTIC` decision is emitted
- **AND** the result remains outside `IDENTIFY` and `DECISION`

### Requirement: Parallel polishing from an identical backbone

The Polypolish route and the explicit alignment/variant-call/consensus route SHALL start from the identical frozen backbone and identical declared paired short-read input set. Their outputs MUST be produced as parallel candidates, with no route allowed to consume the other route's polished sequence as its input (SCI-004, ENG-POL-004).

#### Scenario: Routes are comparable

- **WHEN** both polishing routes run for the same sample
- **THEN** their input backbone checksum and short-read manifest identifiers are identical
- **AND** each route emits an independent candidate and evidence bundle

#### Scenario: Unsupported route is not silently used

- **WHEN** library metadata, multi-mapping behavior, or platform compatibility is insufficient to evaluate Polypolish
- **THEN** the Polypolish result is marked unavailable or experimental-inapplicable
- **AND** the consensus route is not presented as a validated replacement without its own evidence

### Requirement: Per-base edit and region-level evidence ledger

Every candidate-producing route SHALL emit an edit ledger recording the reference coordinate, original and proposed base, supporting read counts, depth, allele evidence, mapping ambiguity, filtering reason, and route identifier. Validation SHALL report separate evidence for unique sequence, IR/repeat sequence, animal D-loop/AT-rich sequence, homopolymers, and each claimed junction (SCI-004, SCI-005, SCI-010).

#### Scenario: Unsupported edits remain visible

- **WHEN** a polishing route changes a base without sufficient declared evidence
- **THEN** the edit is retained in the ledger with its reason and the affected region is downgraded or marked unresolved
- **AND** the pipeline does not silently force a consensus base

#### Scenario: Junction evidence is auditable

- **WHEN** a candidate claims a structural junction
- **THEN** the bundle records junction coordinates, read IDs, alignment length, direction, identity, both-side anchors, and repeat/chimera risk
- **AND** a circular-looking candidate alone cannot upgrade topology

### Requirement: Transfer and decision gates remain closed

Until real paired CycloneSEQ data and a separately frozen transfer/Go-No-Go protocol are available, the capability SHALL report CycloneSEQ transfer as `PENDING_REAL_DATA`, keep ONT/CycloneSEQ evidence outside `IDENTIFY` and `DECISION`, and exclude PMAT2 while Issue #10 is OPEN (SCI-003, TEST-003, ENG-POL-003).

#### Scenario: Public evaluation data are not transfer validation

- **WHEN** the evaluation uses public ONT and/or DNBSEQ data
- **THEN** it may produce experimental method evidence
- **AND** it MUST NOT mark CycloneSEQ transfer or Go/No-Go as complete

#### Scenario: PMAT2 remains gated

- **WHEN** Issue #10 is OPEN
- **THEN** PMAT2 is not executed or used as a comparator in this capability
- **AND** its absence is recorded as a governance gate, not a biological result
