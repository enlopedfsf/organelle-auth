## Context

The active animal pilot has a verified bounded ONT input, a rotated CM084263 recruitment PAF, and a Flye failure with one 41,025 bp disjointig and empty consensus. This diagnostic change must preserve those artifacts and separate measured evidence from any later repair.

## Goals / Non-Goals

**Goals:**

- Make input size/provenance and recruitment purity auditable.
- Quantify MAPQ-0, identity, alignment-span, complexity, and M2-anchor overlap by read identity.
- Quantify Flye run-to-run and read-order sensitivity before treating a repeat-graph traversal as biological structure.

**Non-Goals:**

- No PMAT2, authentication decision, or automatic topology promotion from an assembler output.
- No authentication decision or promotion of ONT evidence.

## Decisions

- Use the user-verified subsample as the frozen A input; record its existing checksum rather than regenerate it.
- Parse the existing PAF without filtering away MAPQ-0 records; deduplicate by query read ID for support estimates.
- Align the recruited reads to the frozen M2-① scaffold with the same auditable minimap2 provenance, while keeping this diagnostic comparison separate from production paths.
- Compute complexity with a transparent fixed-window entropy/DUST-like metric and report distributions; do not turn cutoffs into policy.
- Write JSON/TSV plus a human-readable appendix containing commands, versions, checksums, and explicit limitations.

### Flye reproducibility governance

- Authoritative Flye executions use a pinned complete runtime and `--deterministic` as a variance-reduction control. In Flye 2.9.6 this makes disjointig assembly single-threaded; it does not guarantee full determinism because upstream Issue #640 documents other random sources.
- Record the requested thread count, deterministic mode, command, runtime paths, input checksum, graph paths, and assembly properties.
- CI and nf-test use property-based assertions for Flye scientific outputs, such as non-empty output, reference breadth/identity ranges, and governed topology status. Exact assembly hashes, exact contig lengths, and one specific circularity outcome are not pass/fail contracts.
- Multiple Flye runs are sensitivity evidence, not independent algorithm-family corroboration. Topology promotion still requires separately governed read-level evidence and an independent assembler comparison.

### Independent assembler comparison

- Raven is admitted as `EXPERIMENTAL` for independent OLC-family comparison only and cannot feed `IDENTIFY` or `DECISION`.
- Because the coherent 25 kb and 30 kb inputs are byte-identical, Raven is run once on the original order and once on one fixed-seed shuffled order. Duplicate execution of identical files is not treated as additional evidence.
- Raven reports contig count, lengths, circularity annotation, M2-① anchor identity/breadth, and core-region agreement with the Flye sensitivity set. A Raven circular contig does not override the project topology evidence gate.

### HYP-DNA-002 long-read audit

- Audit each of the 13 excluded reads of at least 30 kb directly rather than treating coherent-filter exclusion as evidence of contamination.
- Preserve self-alignment coordinates, dotplots, per-copy anchor alignments, anchor breadth, aligned fraction, and non-anchor flanks for each read.
- Classify each read as `TRUE_MULTIMER`, `NUMT_FLANK_CHIMERA`, or `CHIMERIC_JUNK` only when evidence is sufficient; otherwise use `UNRESOLVED`. Assign hypothesis strength separately as `CONFIRMED`, `SUGGESTIVE`, or `REJECTED`.
- HYP-DNA-002 tests AT-rich repeat adjacency and copy number. It cannot promote topology without the full project evidence gate.

### Closeout

- The main validation narrative records the five-link attribution: incomplete system Flye runtime, incoherent recruitment aggregation, disproved upper-length-filter repair, Flye run/order sensitivity, and unresolved AT-rich micro-edge traversal.
- Final animal ONT status remains `EXPERIMENTAL`, topology `INCONCLUSIVE`, and `decision=NOT_APPLICABLE` regardless of any single assembler output.

## Risks / Trade-offs

- [Subsample provenance ambiguity] → preserve the user-verified manifest and mark any unavailable original shell history as unverifiable rather than infer it.
- [Low-complexity metric sensitivity] → report descriptive distributions and method parameters, not a biological pass/fail threshold.
- [M2 anchor is not independent biological truth] → label comparison as an engineering evidence anchor.
- [Flye is not fully deterministic] → use `--deterministic` to reduce variance, retain property assertions, and never interpret one repeat-graph traversal as a topology decision.
