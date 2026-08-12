## ADDED Requirements

### Requirement: Independent-support conclusion review

Any proposed revision of an archived plant long-read topology conclusion SHALL audit each candidate junction read against the complete `6.5 independent_alignment_support` definition, including both-sided flanking alignment, unique-anchor status, read-identity deduplication, alignment class, MAPQ stratum, and IR-copy ambiguity. Aggregate MAPQ-inclusive or copy-weighted counts alone MUST NOT revise topology (SCI-001, SCI-005, REL-001).

#### Scenario: Candidate satisfies all support conditions

- **WHEN** a deduplicated read independently anchors both junction sides in unique sequence and passes every declared support condition
- **THEN** it is entered as qualifying support with coordinates, alignment class, and command provenance

#### Scenario: Candidate is copy-ambiguous

- **WHEN** a read supports the junction but its anchors are non-unique, MAPQ-zero, secondary, or unresolved across IR copies
- **THEN** it remains in the ambiguity ledger and cannot independently qualify the topology revision

### Requirement: Governed topology label revision

The review SHALL emit a standalone report comparing the archived conclusion with the audited ledger. Unless the qualifying support contract is satisfied, the formal topology SHALL remain `INCONCLUSIVE`; any upgrade SHALL state its evidence class and remain isolated from IDENTIFY and DECISION_ENGINE until separately approved.

#### Scenario: Evidence remains insufficient

- **WHEN** no sufficient independent-support set is established
- **THEN** the report records `INCONCLUSIVE` and leaves archived conclusions unchanged

#### Scenario: Evidence supports a revision

- **WHEN** the complete contract is satisfied and all excluded candidates are accounted for
- **THEN** the report proposes one explicit topology label and cites the qualifying read ledger without silently editing archived prose
