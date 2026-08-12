## Purpose

Defines auditable animal ONT recruitment diagnostics, experimental assembly comparison, repeat-copy evidence review, and closeout governance while preserving strict separation from authentication decisions.

## ADDED Requirements

### Requirement: Animal recruitment diagnostics are evidence-first and taxon-specific

The animal long-read route SHALL audit the frozen bounded input and existing recruitment evidence before changing any parameter or rerunning assembly. Diagnostic results MUST report MAPQ-0, read-identity deduplication, alignment spans, sequence complexity, and comparison with the frozen M2-① anchor. Plant recruitment parameters MUST NOT be reused as animal defaults without a separately evidenced decision (SCI-001, SCI-005, ENG-POL-001).

#### Scenario: Diagnostic input is complete

- **WHEN** the user-verified subsample, recruitment PAF, reference rotations, and M2 anchor are non-empty and checksum-recorded
- **THEN** the route emits A/B JSON, TSV, and appendix evidence before any repair stage
- **AND** the route remains `EXPERIMENTAL` with `decision=NOT_APPLICABLE`

#### Scenario: Recruitment is dominated by ambiguous evidence

- **WHEN** MAPQ-0 or duplicated read identities dominate recruitment records
- **THEN** the report quantifies that dominance and preserves the ambiguous records
- **AND** it does not treat them as independent unique mitochondrial support

#### Scenario: Plant parameters lack animal evidence

- **WHEN** a proposed animal parameter is inherited only from the plant route
- **THEN** the route rejects it as an animal default pending diagnostic evidence
- **AND** parameter selection is deferred to a separately reviewed repair stage

### Requirement: Animal Flye evidence is runtime-complete and variance-governed

Animal Flye execution SHALL use a pinned complete runtime containing `flye`, `flye-minimap2`, and `flye-samtools`, SHALL fail before assembly if any required executable is absent, and SHALL record versions, executable paths, input checksum, requested threads, deterministic mode, and graph properties. Authoritative runs SHALL enable Flye `--deterministic` as a variance-reduction measure, while explicitly recording that it does not guarantee full determinism. Validation MUST use property-based scientific assertions and MUST NOT require an exact assembly hash, exact contig length, or one fixed circularity outcome.

#### Scenario: Flye helper executable is absent

- **WHEN** the selected Flye runtime lacks `flye-minimap2` or `flye-samtools`
- **THEN** the assembly fails before producing scientific output
- **AND** no empty consensus is interpreted as biological evidence

#### Scenario: Identical or reordered reads yield divergent graphs

- **WHEN** repeated or read-order-controlled Flye runs produce different contig structures or repeat paths
- **THEN** the divergence is reported as run/order sensitivity
- **AND** no single traversal is promoted to a topology conclusion

### Requirement: Animal topology promotion uses the project evidence gate

This project SHALL permit promotion of animal topology from `INCONCLUSIVE` only when unique-flank reads, end-to-start junction reads, short-read consistency, and agreement between two independent assembler families all qualify under their governed audits. Repeated runs of Flye do not count as independent-assembler agreement. If any element is absent or unresolved, topology SHALL remain `INCONCLUSIVE`, ONT evidence SHALL remain outside `IDENTIFY` and `DECISION`, and PMAT2 SHALL remain gated by Issue #10.

#### Scenario: An assembler emits a circular contig without all evidence classes

- **WHEN** Flye, Raven, or another experimental assembler emits a circular contig but one or more project evidence-gate elements are absent
- **THEN** topology remains `INCONCLUSIVE`
- **AND** the circular contig is retained only as experimental structural evidence

### Requirement: Independent animal assembler evidence is comparator-only

The animal long-read route SHALL govern Raven as an `EXPERIMENTAL` independent assembler-family comparator. It SHALL compare one original-order coherent input and one fixed-seed shuffled ordering, report assembly properties and M2-① anchor agreement, and keep every Raven output outside `IDENTIFY` and `DECISION`. Byte-identical recruitment branches MUST NOT be rerun merely under different labels or counted as independent evidence.

#### Scenario: Raven and Flye agree on a core sequence

- **WHEN** Raven and Flye outputs agree across the M2-① anchored core
- **THEN** the agreement is recorded as independent-assembler core evidence
- **AND** it does not by itself establish repeat adjacency, copy number, or circular topology

### Requirement: Excluded ultra-long reads receive direct evidence classification

Every recruited read of at least 30 kb that was excluded by the coherent single-alignment filter SHALL be audited directly with self-alignment, per-copy anchor alignment, anchor coverage, and flank evidence. The audit SHALL distinguish `TRUE_MULTIMER`, `NUMT_FLANK_CHIMERA`, `CHIMERIC_JUNK`, and unresolved evidence without inferring contamination from exclusion alone. HYP-DNA-002 strength SHALL be reported as `CONFIRMED`, `SUGGESTIVE`, or `REJECTED` independently of per-read class.

#### Scenario: An excluded read contains repeated anchor-scale units

- **WHEN** self-alignment and copy-wise anchor alignments support repeated mitochondrial-scale units but unique flanks or junction evidence remain incomplete
- **THEN** the read is retained as suggestive multimer/repeat evidence
- **AND** animal topology remains `INCONCLUSIVE`
