## 1. Governance and contracts

- [x] 1.1 Register recruitment, target-gate, assembly, comparator, and fallback reason codes with stage and non-decision semantics.
- [x] 1.2 Add versioned experimental reference-recruitment and target-evidence policy fixtures while leaving production scientific thresholds null.
- [x] 1.3 Extend parameter/schema documentation for raw processing budget, reference metadata, mapper policy, rescue-pass switch, gate policy, Flye options, and PMAT2 comparator options.
- [x] 1.4 Mark `plant-long-read-pmat2-pilot` as superseded by this corrective change without deleting its artifacts or preserved run evidence.

## 2. Reference preparation and whole-read recruitment

- [x] 2.1 Implement a deterministic reference-metadata validator that rejects missing, empty, malformed, incompatible, or quarantined entries.
- [x] 2.2 Implement circular-reference rotation generation with canonical coordinate mapping and streaming checksums.
- [x] 2.3 Add a minimap2 long-read mapping module that emits PAF with CIGAR/`cs`, command provenance, versions, and a stub contract.
- [x] 2.4 Implement policy-driven PAF evidence selection that retains primary, secondary, and supplementary evidence and never filters by MAPQ alone.
- [x] 2.5 Add a whole-read extraction module that deduplicates selected identifiers, extracts complete FASTQ records, and records counts, bases, and checksums.
- [x] 2.6 Implement deterministic union of pass-one/pass-two identifiers with per-pass provenance and a hard maximum of two passes.

## 3. Target evidence and subset assembly

- [x] 3.1 Implement canonical interval lifting/deduplication and calculate recruited yield, aligned target bases/depth, breadth, alignment distributions, and declared junction support.
- [x] 3.2 Implement the policy gate with experimental eligibility, metric-specific `INCONCLUSIVE` codes, and production-null `THRESHOLD_NOT_CONFIGURED` behavior.
- [x] 3.3 Add a Flye subset-assembly module with validated FASTQ input, policy-supplied arguments, assembly/graph/log outputs, resource provenance, versions, and stub behavior.
- [x] 3.4 Refactor PMAT2 into a subset comparator module that enforces `-p 0`, labels output `EXPERIMENTAL_COMPARATOR`, and preserves structured failure independently from Flye.
- [x] 3.5 Implement the full-background PMAT2 routing guard so it remains disabled unless no usable reference, explicit strategy, and separately eligible high-coverage policy all agree.
- [x] 3.6 Verify Flye and PMAT2 comparator execution records carry the identical recruited-subset checksum.

## 4. Structural and error evidence

- [x] 4.1 Add assembly-to-reference and assembly-to-M1-anchor alignment modules with exact command/version records and stub contracts.
- [x] 4.2 Implement candidate read remapping for circular-origin, IR-boundary, and other declared junction support.
- [x] 4.3 Implement the structural evidence report with candidate length/contigs, aligned span, identity, gaps/conflicts, canonical coordinates, and Flye-versus-PMAT2 disagreements.
- [x] 4.4 Implement the M1 38 kb IR-gap outcome as `closed`, `not_closed`, or `not_assessable` with independent spanning-read identifiers.
- [x] 4.5 Replace positional homopolymer comparison with anchor-run discovery, fixed-alignment coordinate lifting, callable denominators, run-length deltas, and unliftable intervals.

## 5. Nextflow integration and provenance

- [x] 5.1 Create a `plant_long_read_reference_first` subworkflow that orders validation, bounded QC, pass-one recruitment/gate, preliminary Flye, optional one-pass rescue, final gate, and assembly fan-out.
- [x] 5.2 Redirect only the experimental `long_read_pilot` route to the corrected subworkflow and prove no IDENTIFY/DECISION channel receives its outputs.
- [x] 5.3 Publish all evidence/status/version/resource artifacts under an isolated plant long-read evaluation tree with explicit optional-comparator statuses.
- [x] 5.4 Remove whole-file in-memory hashing from the long-read path and use streaming checksum/counting for large FASTQ/FASTA inputs.
- [x] 5.5 Update `VALIDATION-plant-lr.md` methodology to distinguish the historical whole-background failure, corrected route, observed facts, and pending CycloneSEQ/Go-No-Go fields.

## 6. Tests and validation gates

- [x] 6.1 Add T1 tests for reference validation/rotation, repeated PAF evidence, MAPQ-independent selection, whole-read extraction, union/deduplication, and empty/corrupt inputs.
- [x] 6.2 Add T1 tests for target metrics/gates, null production policy, Flye failure, PMAT2 comparator failure, structural evidence, IR outcomes, and homopolymer lifting.
- [x] 6.3 Add T2 tests for reference-first ordering, two-pass maximum, identical subset checksums, full-background fallback guard, comparator isolation, and zero decision-channel coupling.
- [x] 6.4 Add a bounded non-stub T3 synthetic circular-organelle test with background, repeat/multi-map, and junction-spanning reads; record T4 real data separately.
- [x] 6.5 Run formatting/lint, Nextflow validation, affected nf-tests, and `openspec validate --strict`; resolve every failure without counting stubs or skips as biological success.
- [x] 6.6 Run the corrected route on the bounded paired ONT/DNBSEQ fixture after verifying every reference/input is non-empty, and record commands, policy, status JSON, checksums, resources, and structural results.
- [x] 6.7 Confirm ONT results remain platform-labeled, CycloneSEQ and Go/No-Go remain `PENDING_REAL_DATA`, and no terminal authentication call is emitted.
