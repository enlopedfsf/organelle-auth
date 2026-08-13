## Purpose

Defines an evidence-first hybrid reference-build capability that combines a frozen long-read structural candidate with parallel short-read polishing/evidence routes while preserving experimental status and authentication decision boundaries.

## ADDED Requirements

### Requirement: Frozen hybrid inputs and provenance

Each hybrid evaluation SHALL freeze the plant or animal taxon route, specimen identity, B0/R1 backbones, recruited long reads, deterministic 80/20 paired-short-read split products, reference/policy/tool versions, command parameters, split rule and salt, input sizes, and SHA256 checksums before polishing begins. Mates SHALL remain together, and the held-out set SHALL NOT be used for polishing, mask construction, or parameter tuning. A run MUST fail before polishing when required files are missing, empty, unreadable, unpaired, overlapping across split sets, or checksum-inconsistent (DATA-001, DATA-002, DATA-004, REL-001).

#### Scenario: Input manifest is complete

- **WHEN** a hybrid evaluation starts
- **THEN** it records reproducible manifests for B0/R1, recruited long reads, and both mates of the training and held-out splits
- **AND** the manifest records whether the data are public evaluation data or real CycloneSEQ transfer data

#### Scenario: Deterministic held-out split is frozen

- **WHEN** paired short reads are prepared
- **THEN** canonical pair IDs are assigned by SHA256 with salt `m4-hybrid-v1`, residues 0-1 are held out, and residues 2-9 are training data
- **AND** split rule text, pair counts, products, and SHA256 checksums are frozen with the backbone

#### Scenario: Invalid input is rejected

- **WHEN** a required input is absent, empty, unpaired, or fails its recorded checksum
- **THEN** the evaluation fails before assembly or polishing

### Requirement: Long-read structural candidate is separated from authentication

The capability SHALL construct or consume a long-read structural candidate using only tools in the `EXPERIMENTAL` evidence/tool tier. `EXPERIMENTAL` SHALL NOT be used as the result status. Every candidate produced by this capability SHALL record `status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE` (SCI-003, SCI-005, ENG-POL-003).

#### Scenario: Long-read-only evidence remains non-decision evidence

- **WHEN** only the long-read backbone or its Racon-polished candidate is available
- **THEN** no `AUTHENTIC` or `NON_AUTHENTIC` decision is emitted
- **AND** the result remains outside `IDENTIFY` and `DECISION`

### Requirement: Parallel polishing from an identical backbone

The capability SHALL pre-register exactly six arms per taxon: unpolished backbone (B0), Racon-only (R1), B0→Polypolish (P0), B0→bcftools call/consensus (C0), R1→Polypolish (R1→P1), and R1→bcftools call/consensus (R1→C1). The paired short-read routes SHALL use identical declared reads within each backbone stratum, and no additional arm, polishing round, or alternate read type SHALL be introduced during execution without a change revision (SCI-004, ENG-POL-004).

R1 SHALL consist of exactly two Racon rounds. Each round SHALL align the same frozen taxon-specific recruited long-read set to the current candidate with minimap2 `-x map-ont`, then run `racon -w 500 -q 10.0 -e 0.3 -m 3 -x -5 -g -4 -t 4` without `-u`, `--no-trimming`, or CUDA flags. Round two SHALL remap the same reads to the round-one candidate and stop; result-driven extra rounds are forbidden. The selected Racon version and container SHALL be frozen under the tool-admission contract before execution.

#### Scenario: Routes are comparable

- **WHEN** both polishing routes run for the same sample
- **THEN** their input backbone checksum and short-read manifest identifiers are identical
- **AND** each route emits an independent candidate and evidence bundle

#### Scenario: Matrix scope is capped

- **WHEN** execution begins for plant and animal routes
- **THEN** exactly twelve arm/taxon combinations are registered
- **AND** an unregistered combination fails review as out of scope

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

### Requirement: Proxy-reference metrics and pre-registered ranking

The capability SHALL label reference-comparison metrics as proxy evidence: disagreement with a reference MUST NOT be treated as an assembly error without this sample's read-level support. The same frozen held-out reads SHALL be independently aligned to every final arm. Within the frozen evaluable core, every arm SHALL report `residual_unsupported_loci`, defined as callable candidate positions unsupported by held-out read-backed allele evidence, plus held-out core concordance, held-out-supported evaluable homopolymer discordances, SNVs, indels, and regional residuals. `introduced_edits` SHALL be reported separately as step-local and cumulative provenance and SHALL NOT replace the uniform residual metric. A route SHALL be called dominant only if it has fewer residual unsupported loci and fewer held-out-supported evaluable homopolymer discordances than every competitor while held-out core concordance does not decrease relative to B0; otherwise the scientific result SHALL retain multiple routes as `CONDITIONAL` and the machine status SHALL remain `INCONCLUSIVE`.

#### Scenario: Reference disagreement is adjudicated by reads

- **WHEN** a candidate differs from a reference at a reported site
- **THEN** the report labels the reference comparison as proxy evidence
- **AND** adjudication uses this sample's read-level evidence rather than reference authority

#### Scenario: No dominant route

- **WHEN** no arm satisfies all three dominance conditions
- **THEN** the result is reported as `CONDITIONAL` with multiple routes
- **AND** no post hoc winner is selected

### Requirement: Animal unresolved-repeat exclusion

Animal polishing MAY run across the full candidate backbone, but route-ranking metrics SHALL be restricted to a pre-run frozen Flye/Raven-consensus core. Before any of the twelve evaluations, the validation/evidence owner SHALL freeze a BED in the B0/Flye coordinate frame containing only same-orientation collinear intervals represented exactly once in both assemblers and callable from training reads, after excluding non-unique sequence, unresolved AT-rich/D-loop repeats, ambiguous graph edges, and unresolved junctions. The manifest SHALL record exact coordinates, callability/uniqueness rules, coordinate/liftover rule, owner, and BED SHA256. Held-out reads SHALL NOT define or revise this mask. Edits outside the mask SHALL be counted separately, labeled `NOT_EVALUABLE`, and excluded from ranking and any reference-grade claim.

#### Scenario: Repeat edits are isolated

- **WHEN** an animal polishing arm edits an unresolved AT-rich repeat
- **THEN** the edit is retained in the ledger as `NOT_EVALUABLE`
- **AND** it is excluded from arm comparison and topology qualification

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
