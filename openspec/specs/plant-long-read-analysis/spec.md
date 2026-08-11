# plant-long-read-analysis Specification

## Purpose

This capability evaluates plant long-read shallow-WGS data through reference-first organelle-read recruitment, coverage-aware subset assembly, and auditable structural evidence while remaining isolated from production authentication decisions.

## Requirements

### Requirement: Experimental-only scope and platform provenance

The plant long-read route SHALL remain explicitly `EXPERIMENTAL`, SHALL preserve the declared sequencing platform, and SHALL keep CycloneSEQ transferability and Go/No-Go status pending until paired real CycloneSEQ evidence exists. Its outputs MUST NOT enter `IDENTIFY`, `DECISION_ENGINE`, or a terminal authentication status (SCI-003, SCI-006, REL-001).

#### Scenario: Evaluation output remains isolated

- **WHEN** a plant sample completes any long-read pilot path
- **THEN** its reads, assemblies, and evidence are emitted only in the long-read evaluation output tree
- **AND** no identify or decision channel receives those artifacts

#### Scenario: ONT evidence is not relabeled

- **WHEN** the current ONT fixture contributes to validation or Go/No-Go records
- **THEN** the record labels it as ONT
- **AND** CycloneSEQ transfer remains `PENDING_REAL_DATA`

### Requirement: Paired evidence and usable reference contract

The route SHALL accept explicit long-read input, the paired M1 short-read evidence anchor, a non-empty organelle reference, and versioned reference metadata for the same specimen or declared taxonomic context. It MUST reject absent, empty, corrupt, or provenance-incompatible required inputs before recruitment (DATA-006, SCI-001).

#### Scenario: Valid evidence bundle is accepted

- **WHEN** non-empty long reads, the paired short-read anchor, and a usable organelle reference have compatible identifiers and provenance
- **THEN** the route proceeds to descriptive QC and reference recruitment
- **AND** it records the identifiers, checksums, reference version, and compatibility decision

#### Scenario: Invalid reference bundle fails fast

- **WHEN** the organelle reference is missing, empty, malformed, quarantined, or incompatible with the declared sample context
- **THEN** the reference-first path stops before mapping or assembly
- **AND** it emits a structured input/reference reason code without silently substituting another reference

### Requirement: Bounded raw input and descriptive long-read QC

The route SHALL support deterministic raw-read subsampling as a processing-budget control and SHALL distinguish that budget from biological sufficiency. The experimental default raw input budget MAY be approximately 2 GB, but no raw-GB value may act as a production biological threshold. Descriptive QC and filter values MUST be supplied by the experimental policy, with counts, bases, checksums, and tool versions recorded (ENG-POL-001, DATA-006, TEST-001).

#### Scenario: Deterministic bounded input is traceable

- **WHEN** the input exceeds the configured experimental processing budget
- **THEN** a fixed-seed procedure selects the bounded raw-read input
- **AND** the manifest records the seed, requested and observed bases, read count, and checksum

#### Scenario: Input size does not imply assembly eligibility

- **WHEN** the bounded input contains insufficient target-organelle evidence
- **THEN** the route reports the target-evidence deficiency
- **AND** it does not treat meeting the raw-input budget as permission to assemble or decide

### Requirement: Sensitive reference-first whole-read recruitment

The route SHALL map long reads sensitively against versioned circular-reference rotations and SHALL retain the complete source read when a policy-eligible alignment supports recruitment. Recruitment MUST preserve repeat-relevant primary, secondary, and supplementary evidence and MUST NOT use mapping quality alone as the exclusion rule. An optional rescue pass SHALL map all bounded input reads against preliminary organelle candidates, union complete read identifiers with pass one, and stop after at most two passes (SCI-001, SCI-005, TEST-004).

#### Scenario: Partial alignment retains the full molecule

- **WHEN** one interval of a long read satisfies the configured recruitment evidence policy
- **THEN** the complete read, not only its aligned interval, is written to the recruited subset
- **AND** the evidence table retains alignment class, coordinates, score fields, and recruitment reason

#### Scenario: Inverted-repeat mappings are not silently discarded

- **WHEN** a read has credible repeat-derived secondary or supplementary alignments
- **THEN** those alignments remain available to the recruitment and structural-evidence stages
- **AND** low mapping quality alone cannot remove the read

#### Scenario: Rescue recruitment is bounded and auditable

- **WHEN** pass-one evidence permits candidate assembly and the experimental policy enables rescue
- **THEN** all bounded input reads are remapped to the preliminary candidates exactly once
- **AND** the final subset is the deduplicated union of complete read identifiers from both passes with per-pass counts

### Requirement: Target-organelle evidence gate

Before each assembly path, the route SHALL emit machine-readable recruited yield, estimated target depth, reference breadth, alignment-span distribution, and junction-support evidence. Assembly eligibility SHALL depend on a versioned experimental policy over those target metrics rather than inferred nuclear-genome depth. Uncalibrated production thresholds SHALL remain null and yield `INCONCLUSIVE` with `THRESHOLD_NOT_CONFIGURED` (ENG-POL-001, ENG-POL-002, TEST-004).

#### Scenario: Experimentally eligible subset proceeds

- **WHEN** all required target-evidence values satisfy an explicitly selected experimental policy
- **THEN** the gate reports `ELIGIBLE_EXPERIMENTAL`
- **AND** the primary subset assembly may start with the exact policy and evidence JSON attached

#### Scenario: Low target evidence stops expensive assembly

- **WHEN** recruited yield, target depth, breadth, or required junction evidence is insufficient or unassessable
- **THEN** the gate reports `INCONCLUSIVE` with specific reason codes
- **AND** neither a larger assumed nuclear genome nor the raw input size overrides that outcome

#### Scenario: Production policy is unconfigured

- **WHEN** the production profile invokes the route while required biological thresholds are null
- **THEN** the route reports `INCONCLUSIVE` and `THRESHOLD_NOT_CONFIGURED`
- **AND** no experimental value is silently promoted to a production default

### Requirement: Subset assembly route matrix

For an eligible recruited subset, the route SHALL run Flye as the primary assembly and SHALL run PMAT2 with whole-genome correction disabled (`-p 0`) only as an EXPERIMENTAL comparator on the same subset. Full-background PMAT2 SHALL be disabled by default and may run only when no adequate reference exists, a separately versioned high-coverage de novo eligibility policy passes, and the experimental strategy explicitly enables it (SCI-001, SCI-006, ENG-POL-001).

#### Scenario: Reference-first primary and comparator consume the same subset

- **WHEN** the reference-first gate reports `ELIGIBLE_EXPERIMENTAL`
- **THEN** Flye receives the recruited complete-read subset as the primary assembly input
- **AND** PMAT2 `-p 0` receives the same subset and is labeled `EXPERIMENTAL_COMPARATOR`

#### Scenario: Comparator failure cannot erase primary evidence

- **WHEN** Flye produces a valid primary assembly but PMAT2 fails or emits no valid assembly
- **THEN** the record preserves the Flye result and reports a structured comparator failure
- **AND** no authentication decision is emitted

#### Scenario: Full-background de novo is not a shallow-data fallback

- **WHEN** a usable reference is absent or recruitment is inconclusive but high-coverage de novo eligibility is absent, false, or unconfigured
- **THEN** the route reports `FULL_BACKGROUND_DE_NOVO_NOT_APPLICABLE`
- **AND** it does not launch whole-background correction or assembly

### Requirement: Alignment-based structural and sequence evidence

The route SHALL align each candidate assembly to the versioned reference and M1 short-read anchor and SHALL report aligned span, identity, gaps, conflicts, circularization evidence, IR-boundary coordinates, and independent reads spanning expected junctions. The previous M1 38 kb IR-gap question MUST be reported as `closed`, `not_closed`, or `not_assessable` with coordinates and supporting read identifiers; positional sequence zipping or tool success alone is insufficient (SCI-005, TEST-004).

#### Scenario: IR closure is supported independently

- **WHEN** a candidate appears to bridge the M1 IR gap
- **THEN** the report includes assembly-to-anchor/reference alignments and independent junction-spanning read evidence
- **AND** it states one of the three explicit closure outcomes with reasons

#### Scenario: Reference concordance remains evidence

- **WHEN** a candidate is aligned to the reference and short-read anchor
- **THEN** identity, breadth, structural differences, ambiguous intervals, and tool/version provenance are recorded
- **AND** no unvalidated concordance cutoff becomes an authenticity threshold

### Requirement: Error, resource, status, and validation records

The route SHALL emit versioned JSON/TSV status and evidence records for every stage, including full commands, software/container versions, CPU, peak memory, wall time, disk, input/output sizes, pass counts, and reason codes. Homopolymer analysis SHALL locate maximal runs on the declared anchor, lift coordinates through a fixed alignment, and record substitutions, indels, run-length deltas, callable denominators, and unliftable intervals. `VALIDATION-plant-lr.md` SHALL distinguish observed results from pending real-data gates (REL-001, TEST-001, TEST-004, TEST-005).

#### Scenario: Failure is specific and non-terminal

- **WHEN** recruitment, gating, primary assembly, comparator assembly, or structural validation fails
- **THEN** the status names the failing stage and one or more registered reason codes
- **AND** the failure cannot become `AUTHENTIC` or `NON_AUTHENTIC`

#### Scenario: Test tiers are reported honestly

- **WHEN** the corrective change is validated in CI
- **THEN** T1 covers module contracts and failure modes, T2 covers routing and isolation, and T3 covers a bounded synthetic end-to-end path
- **AND** T4 real-data or CycloneSEQ work not actually run remains explicitly pending rather than counted as green

#### Scenario: Homopolymer method transfers unchanged

- **WHEN** ONT and later CycloneSEQ candidates are compared with the same anchor
- **THEN** the same coordinate-lift and denominator method is used
- **AND** platform-specific results remain separately labeled and traceable
