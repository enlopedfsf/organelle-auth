## Purpose

This capability evaluates a plant long-read assembly route as an experimental evidence producer.
It establishes reproducible ONT QC, PMAT2 execution, short-read-anchored structural/error analysis,
and a CycloneSEQ-pending Go/No-Go record without creating any production authentication path.

## ADDED Requirements

### Requirement: Experimental-only scope and platform provenance

The pilot SHALL be explicitly marked `EXPERIMENTAL`, SHALL identify `SRR38978847` as ONT data, and
SHALL state that CycloneSEQ transferability remains unvalidated until real paired CycloneSEQ data
are available. PMAT2 outputs MUST NOT be consumed by `IDENTIFY`, `DECISION_ENGINE`, or any terminal
authentication status. Pure long-read evidence MUST remain research/evaluation evidence (SCI-003,
SCI-006, REL).

#### Scenario: Long-read output is isolated from decision routing

- **WHEN** a plant sample is run through the pilot
- **THEN** PMAT2 results are emitted only into the pilot/evaluation output tree
- **AND** no identify or decision channel receives the long-read assembly

#### Scenario: ONT result is not mislabeled as CycloneSEQ evidence

- **WHEN** validation or Go/No-Go records are generated from `SRR38978847`
- **THEN** the record labels the platform as ONT
- **AND** CycloneSEQ transferability is recorded as pending rather than inferred (SCI-003)

### Requirement: Paired short-read and long-read input contract

The pilot SHALL accept explicit short-read and long-read inputs for the same plant specimen, with
the current fixture pairing `SRR38978846` (DNBSEQ/short-read) and `SRR38978847` (ONT/long-read) from
the project data directory. Routing MUST use explicit samplesheet fields and MUST reject missing,
empty, or mismatched input pairs before assembly (DATA-006).

#### Scenario: Valid paired inputs are accepted

- **WHEN** both non-empty read sets are declared for one sample and pass integrity checks
- **THEN** the pilot proceeds to long-read QC and PMAT2 evaluation
- **AND** the record preserves both input identifiers and independent provenance

#### Scenario: Missing or mismatched pair fails fast

- **WHEN** either read set is absent, empty, corrupt, or assigned to a different specimen
- **THEN** the pilot fails before PMAT2 execution
- **AND** it emits a structured input error without falling back to a single-platform result

### Requirement: Descriptive long-read QC

The pilot SHALL produce NanoPlot descriptive QC and SHALL apply exactly one approved/available
long-read filter (filtlong is selected because it is containerized, bioconda-available, and supports
deterministic streaming without signal-level models). Filter parameters MUST be supplied by the
experimental profile or policy record; no scientific quality, length, or yield threshold may be
hardcoded as a production default (ENG-POL-001, TEST-001).

#### Scenario: QC and filtering are traceable

- **WHEN** valid ONT reads enter the QC stage
- **THEN** NanoPlot metrics, filter parameters, read counts, and output checksums are recorded
- **AND** the filtered reads are the only reads passed to PMAT2

#### Scenario: Production configuration cannot silently activate pilot thresholds

- **WHEN** a production profile attempts to run this experimental pilot without explicit policy values
- **THEN** the run fails or remains disabled before execution
- **AND** it does not substitute QC thresholds from the experimental profile

### Requirement: Containerized PMAT2 execution and version evidence

The pilot SHALL execute PMAT2 in a containerized local module with a version report and stub path.
The method-specified ONT invocation parameters (`-t ont -x 0`) SHALL be represented as tool arguments,
not scientific acceptance thresholds. The module SHALL emit assembly FASTA, graph/metadata when
available, a versions record, and machine-readable execution status (TEST-001).

#### Scenario: PMAT2 completes on the ONT fixture

- **WHEN** filtered `SRR38978847` reads and the declared plant reference context are available
- **THEN** PMAT2 completes or reports a structured tool failure
- **AND** successful output includes an assembly, tool version, exact arguments, and resource trace

#### Scenario: PMAT2 failure does not become an authentication result

- **WHEN** PMAT2 exits non-zero, produces an empty assembly, or violates the input contract
- **THEN** the pilot status is `FAIL` or `INCONCLUSIVE`
- **AND** no identify/decision status is emitted from that failure

### Requirement: Short-read-anchored structural and sequence evaluation

The evaluation SHALL compare PMAT2 output against the existing M1 short-read evidence anchor and
PZ405204. It SHALL report circularity/closure, whether the M1-measured 38 kb IR gap is closed,
sequence concordance to PZ405204 and the short-read assembly, and unresolved discrepancies. These
comparisons are evidence reports, not authenticity calls (SCI-005, TEST-004).

#### Scenario: IR closure has an explicit conclusion

- **WHEN** PMAT2 output is compared to the M1 assembly and its recorded 38 kb IR gap
- **THEN** the report states `closed`, `not_closed`, or `not_assessable` with coordinates and evidence
- **AND** it does not infer closure from a single contig name or tool status alone

#### Scenario: Concordance is reported without a fabricated threshold

- **WHEN** PMAT2 sequence is aligned to PZ405204 and the M1 short-read assembly
- **THEN** identity, aligned span, gaps, and conflicts are recorded with tool/version provenance
- **AND** no unvalidated identity cutoff is promoted to a production decision threshold

### Requirement: Error-spectrum, resource, and Go/No-Go evidence record

The pilot SHALL scan maximal homopolymer runs in the short-read anchor, lift their coordinates
through the fixed alignment, and compare long-read versus anchor substitutions, indels, and
run-length deltas by reference run length. It SHALL record callable span, ambiguous/unliftable
intervals, alignment/tool policy, versioned TSV/JSON outputs, CPU, memory, wall time, disk, and
input/output sizes. It SHALL write `VALIDATION-plant-lr.md` plus an M3 Go/No-Go record with ONT
evidence populated and CycloneSEQ transfer fields explicitly pending. The PMAT2 registry entry MUST
link the validation record without changing its EXPERIMENTAL admission tier (REL, TEST-004/005).

#### Scenario: Homopolymer error report is reproducible

- **WHEN** aligned PMAT2 and short-read-anchor sequences contain homopolymer runs
- **THEN** run coordinates, reference run lengths, LR-vs-SR substitutions/indels, run-length deltas, callable denominator, and ambiguous intervals are recorded
- **AND** the same procedure can be rerun unchanged on CycloneSEQ data

#### Scenario: Go/No-Go remains CycloneSEQ-gated

- **WHEN** the ONT pilot validation is completed
- **THEN** the Go/No-Go record contains ONT structural, sequence, error, and resource evidence
- **AND** no PMAT2 admission promotion or production integration is recommended without CycloneSEQ transfer data

### Requirement: T1/T2 coverage and explicit T3 non-scope

The change SHALL add T1 module tests for QC/PMAT2 contracts and T2 evaluation/guardrail tests for
scope isolation, IR-gap reporting, error/resource JSON, and failure propagation. T3 long-read
end-to-end smoke is explicitly out of scope because the fixture is too large; the reason and the
replacement real-data validation command MUST be recorded (TEST-001/002/005).

#### Scenario: T1/T2 pass without decision-path coupling

- **WHEN** the affected module and evaluation tests run
- **THEN** T1/T2 verify outputs, metadata, errors, and isolation contracts
- **AND** tests fail if a PMAT2 result is routed into identify/decision

#### Scenario: T3 is not silently counted as green

- **WHEN** CI summarizes this change's test tiers
- **THEN** T3 is reported as not run with the large-fixture rationale
- **AND** real ONT end-to-end validation is linked separately in `VALIDATION-plant-lr.md`
