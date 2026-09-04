## ADDED Requirements

### Requirement: CycloneSEQ transfer protocol is frozen before outcome access

CycloneSEQ transfer validation SHALL use a versioned, owner-approved protocol frozen before analysts can access scientific outcomes. It MUST identify the declared plant and animal applicability scope, matched specimen/DNA relationships, comparison routes, discovery versus validation roles, metrics, missing-data handling, orthogonal-evidence policy, outcome rules, software/reference/policy versions, and checksums. Unapproved or null scientific thresholds MUST remain null and MUST NOT be inferred from the validation data (SCI-003, SCI-010, ENG-POL-001, ENG-POL-002, ENG-POL-004).

#### Scenario: Real data have not arrived

- **WHEN** the required matched real CycloneSEQ evidence has not passed the arrival gate
- **THEN** transfer and Go/No-Go remain `PENDING_REAL_DATA`
- **AND** engineering fixtures, ONT evidence, public data, or protocol completion cannot satisfy the scientific gate

#### Scenario: Protocol is frozen before execution

- **WHEN** all required real inputs have passed arrival validation but scientific execution has not begun
- **THEN** an owner-approved protocol freezes the declared scope, arms, metrics, thresholds or explicit nulls, outcome branches, versions, and SHA256 values
- **AND** subsequent changes are versioned deviations that invalidate confirmatory status unless independently revalidated

### Requirement: CycloneSEQ data arrival is machine-validated and fail-closed

Every real-data delivery SHALL enter a quarantine/arrival stage before channel creation or scientific inspection. The stage MUST validate an allow-listed path manifest, expected specimen and platform identities, non-empty files, format/compression integrity, checksums, paired-read synchronization where applicable, sample-ID uniqueness, matched-DNA relationship or documented comparability, sequencing/library/basecalling provenance, batch metadata, and required HMW/QC metadata or explicit missing reason. File names alone MUST NOT establish identity (DATA-001, DATA-002, DATA-004, DATA-006).

#### Scenario: Arrival package passes

- **WHEN** every required file and metadata record matches the signed delivery manifest and all machine checks pass
- **THEN** the package receives an immutable arrival-manifest SHA256 and may proceed to protocol freeze
- **AND** the original delivery remains read-only with no silent replacement

#### Scenario: Arrival package fails or is incomplete

- **WHEN** any required identity, integrity, checksum, pairing, provenance, matched-DNA, or metadata check fails or is unresolved
- **THEN** scientific analysis is blocked with a specific reason code
- **AND** transfer remains `PENDING_REAL_DATA` or `INCONCLUSIVE_NOT_EVALUABLE` as pre-registered
- **AND** the failure is not interpreted as biological or platform underperformance

### Requirement: Blind-sample truth remains inaccessible until result freeze

Transfer validation SHALL separate analysis identities from expected truth. Analysis samplesheets MUST use coded sample IDs and coded allow-listed data paths, and MUST NOT contain truth-bearing columns, path components, filenames, directory names, reference labels, or free text. A designated truth custodian who does not run or tune the analysis SHALL hold the access-controlled truthset; analysts SHALL freeze per-sample outputs, exclusions, deviations, aggregate metrics that do not require truth, commands, and SHA256 values before an authorized unblinding event (DATA-003, SCI-010).

#### Scenario: Blinded analysis proceeds

- **WHEN** a validation sample enters analysis
- **THEN** the analyst receives only the coded input package and the frozen protocol
- **AND** truth access is denied and auditable until every required sample result is frozen

#### Scenario: Unblinding is authorized

- **WHEN** the result-freeze manifest is complete and signed by the validation/evidence owner
- **THEN** the evaluator loads truth from the separate truthset and records custodian, timestamp, truthset SHA256, result-manifest SHA256, and evaluation command
- **AND** no post-unblinding retuning can be reported as confirmatory validation

#### Scenario: Blind integrity is breached

- **WHEN** truth leaks through a file, metadata field, communication, access log, or result-driven protocol change before freeze
- **THEN** the affected evaluation is marked `BLINDING_INVALIDATED`
- **AND** it cannot support GO, tool admission, or production thresholds

### Requirement: Transfer evidence distinguishes platform quality, structural gain, and decision gain

The protocol SHALL compare the pre-declared short-read baseline, CycloneSEQ-only research route, and hybrid route on the same eligible sample scope. It SHALL separately report read length/Q calibration, substitution/insertion/deletion/homopolymer error spectra, callable coverage, assembly completeness, independently supported junctions and structural false positives, diagnostic-site recovery, result stability, single-sample failure, computational resources, manual review, and incremental gain relative to the short-read baseline. Pure CycloneSEQ MUST remain outside terminal authentication decisions (SCI-003, SCI-004, SCI-005, TEST-003, TEST-005).

#### Scenario: Engineering smoke checks pass

- **WHEN** synthetic or public fixtures prove that arrival, routing, schemas, and evidence outputs execute correctly
- **THEN** engineering status may be PASS
- **AND** scientific transfer status remains `PENDING_REAL_DATA`

#### Scenario: Real transfer evidence is evaluated

- **WHEN** a blind, arrival-valid, protocol-frozen real-data set completes all declared routes
- **THEN** route-level results use the same registered sample inclusion rules and denominator definitions
- **AND** unsupported or non-callable bases and structures remain explicit rather than being forced into a favorable metric

### Requirement: Negative and non-GO branches are pre-written

Before unblinding, the protocol SHALL define a deterministic `transfer_outcome` table covering at least: `PENDING_REAL_DATA`, `ARRIVAL_BLOCKED`, `INCONCLUSIVE_NOT_EVALUABLE`, `NO_GO_CONTROL_FAILURE`, `NO_GO_NO_INDEPENDENT_GAIN`, `NO_GO_HARM_OR_FALSE_STRUCTURE`, `CONDITIONAL_MIXED_EVIDENCE`, `INSUFFICIENT_SCOPE_FOR_GO`, and eligibility for a later `GO_REVIEW`. These are outcome/reason codes: machine `status` MUST remain within `PASS|WARN|FAIL|INCONCLUSIVE`, and `decision` remains `NOT_APPLICABLE`. Only `ELIGIBLE_FOR_GO_REVIEW` may be submitted for a separate owner Go/No-Go decision; no analysis run may self-approve production admission (SCI-003, SCI-005, REL-001).

#### Scenario: No independent gain is observed

- **WHEN** CycloneSEQ/hybrid routes do not meet the pre-frozen independent-gain conditions over the short-read baseline
- **THEN** the outcome is `NO_GO_NO_INDEPENDENT_GAIN`
- **AND** long-read outputs remain research-only and outside the formal authentication SOP

#### Scenario: Error or false structure regresses

- **WHEN** a declared route exceeds a pre-frozen harm boundary or introduces unsupported structural claims
- **THEN** the outcome is `NO_GO_HARM_OR_FALSE_STRUCTURE`
- **AND** favorable metrics elsewhere cannot override that branch unless the frozen protocol explicitly defined the exception

#### Scenario: Negative or contamination control fails

- **WHEN** a pre-declared extraction, library, sequencing, or blind negative control violates its frozen evidence boundary
- **THEN** the outcome is `NO_GO_CONTROL_FAILURE`
- **AND** affected sample results cannot support transfer eligibility even if positive samples appear favorable

#### Scenario: Evidence is mixed or scope is insufficient

- **WHEN** gains and regressions coexist without a pre-frozen dominant outcome, or validation lacks the declared taxa/samples/batches/orthogonal evidence
- **THEN** the outcome is `CONDITIONAL_MIXED_EVIDENCE` or `INSUFFICIENT_SCOPE_FOR_GO`
- **AND** thresholds and production admission remain unchanged

#### Scenario: Evidence is eligible for human GO review

- **WHEN** all arrival, blinding, scope, metric, gain, harm, reproducibility, and orthogonal-evidence gates in the frozen protocol pass
- **THEN** the machine outcome may be `ELIGIBLE_FOR_GO_REVIEW`
- **AND** final GO requires a separate owner-reviewed change and cannot be emitted by this validation run

### Requirement: Optional tools cannot block or contaminate the core transfer study

The core transfer protocol SHALL remain executable without PMAT2 or mitoVGP. PMAT2 MUST remain gated by Issue #10 and mitoVGP MUST remain outside scope unless each completes its own admission change. Missing optional comparators SHALL be recorded as governance state, not as biological or platform evidence (ENG-POL-003, REL-001).

#### Scenario: PMAT2 or mitoVGP is unavailable

- **WHEN** Issue #10 is unresolved or mitoVGP has no completed admission
- **THEN** the core baseline/CycloneSEQ/hybrid comparison proceeds without that optional comparator once real inputs are otherwise eligible
- **AND** the omission cannot cause scientific PASS or FAIL
