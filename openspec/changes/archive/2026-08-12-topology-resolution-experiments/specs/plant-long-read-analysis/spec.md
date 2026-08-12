## ADDED Requirements

### Requirement: Frozen-input exploratory topology grid

The plant long-read capability SHALL support an isolated exploratory grid using exactly the archived M3 recruited subset identified by its recorded SHA-256, and SHALL run no more than six independently identified Flye parameter combinations. Each combination SHALL vary only the declared `--asm-coverage` and `--min-overlap` values, preserve ONT labelling, and emit commands, tool versions, input/output checksums, contig metrics, GFA, junction evidence, circularity state, runtime, and resource metadata. Experimental values MUST NOT become production defaults (HYP-DNA-001, ENG-POL-001, TEST-004).

#### Scenario: Input checksum matches

- **WHEN** the archived subset is present, non-empty, and its checksum matches the M3 record
- **THEN** the grid may run and each combination receives an independent output directory and manifest

#### Scenario: Input checksum does not match

- **WHEN** the subset is missing, empty, or has a different checksum
- **THEN** the experiment fails before assembly and names the mismatch without substituting another input

### Requirement: MAPQ-0 copy-aware junction recount

The plant long-read capability SHALL support recomputing junction support while retaining MAPQ-0, MAPQ-10, secondary, and supplementary alignments. It SHALL deduplicate by read identity and apply an explicitly documented IR-copy-aware evidence weighting; raw counts and weighted counts SHALL be reported beside the prior high-quality-only count (SCI-001, SCI-005, TEST-004).

#### Scenario: Low-MAPQ IR reads are present

- **WHEN** MAPQ-0 or MAPQ-10 reads align to both IR copies and span the candidate junction
- **THEN** they remain auditable, are not counted as independent unique reads twice, and contribute through the declared copy-aware weighting

#### Scenario: No eligible low-MAPQ support

- **WHEN** no retained alignment spans both junction flanks after identity deduplication
- **THEN** the report records zero additional support and preserves the prior count for comparison

### Requirement: Topology experiment conclusion and channel isolation

Regardless of experiment results, outputs SHALL be written only to the standalone topology experiment appendix and SHALL retain `decision=NOT_APPLICABLE`. The archived pilot files, `VALIDATION-plant-lr.md`, the plant main route, IDENTIFY, and DECISION_ENGINE MUST NOT be modified. A topology revision MAY only be proposed by a separate governed change after explicit comparison against the `6.5 independent_alignment_support` definition (SCI-003, SCI-005, REL-001).

#### Scenario: Grid or recount is informative

- **WHEN** either experiment produces interpretable evidence
- **THEN** the appendix answers its corresponding question and leaves the formal topology state `INCONCLUSIVE`

#### Scenario: Evidence remains insufficient

- **WHEN** results are ambiguous, parameter-sensitive, or fail the independent-support definition
- **THEN** the appendix records `INCONCLUSIVE` with reason codes and does not infer a circle from contig labels or reference concordance
