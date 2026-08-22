## ADDED Requirements

### Requirement: M4 reference-grade audit is a bounded candidate packaging step
The audit SHALL consume immutable M4-① evidence, register plant `R1P1` as the primary route, and retain the animal result as `CONDITIONAL` when no pre-registered dominant route exists. Every produced package SHALL be capped at `assembly_grade=CANDIDATE`, `status=INCONCLUSIVE`, and `decision=NOT_APPLICABLE`. Plant and animal topology SHALL remain `INCONCLUSIVE`; this change MUST NOT revise topology, authentication routing, or CycloneSEQ transfer status (SCI-003, SCI-005, ENG-POL-003).

#### Scenario: Plant route is packaged
- **WHEN** immutable common-callability evidence identifies R1P1 as the registered primary route
- **THEN** the audit package records R1P1 with provenance and caveats, without promoting it to REFERENCE

#### Scenario: Animal routes are tied or conditional
- **WHEN** no route satisfies the pre-registered dominance rule
- **THEN** the package retains the eligible routes as `CONDITIONAL` and does not choose a single winner post hoc

#### Scenario: Topology appears circular
- **WHEN** a source candidate contains circular-looking or unresolved repeat structure
- **THEN** topology remains `INCONCLUSIVE` and the audit records the exclusion from grade promotion

#### Scenario: Package status is emitted
- **WHEN** a plant or animal candidate package is generated
- **THEN** its machine-readable status is `INCONCLUSIVE`, grade is `CANDIDATE`, and decision is `NOT_APPLICABLE`
