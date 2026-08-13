## Context

The archived M4-① evaluation aligned the same frozen held-out plant reads independently to B0, R1, P0, C0, R1P1, and R1C1. It retained per-arm depth, normalized residual ledgers, candidate-to-B0 PAF projections, lifted region BEDs, and an experimental evaluation policy. Because callable bases differed across arms, its validation text explicitly deferred a fair-denominator check to a separately pre-registered analysis. See `proposal.md` and the added `hybrid-reference-build` requirement.

## Goals / Non-Goals

**Goals:**

- Freeze and checksum the exact parent artifacts before computation.
- Express all six arms in the frozen plant B0 coordinate frame without remapping reads or changing candidates.
- Intersect six arm-specific uniquely projected, held-out-callable base sets.
- Emit the requested arm×region denominator table and a bounded R1P1 residual-lead classification.

**Non-Goals:**

- Re-running polishing, alignments, variant calling, or the animal matrix.
- Re-selecting any M4-① evaluation threshold or reinterpreting its full three-part dominance rule.
- Resolving IR copy number, adjacency, circularity, authentication, production admission, PMAT2, mitoVGP, or CycloneSEQ transfer.

## Decisions

### 1. Freeze the parent evidence before reading result values

The input manifest contains SHA256 and absolute read-only paths for the six candidate-to-B0 PAFs, six held-out depth TSVs, six held-out residual ledgers, the B0-coordinate plant region BED, and the archived evaluation policy. The implementation validates every path and checksum before analysis. Historical FASTQ/BAM/VCF files are neither modified nor copied into Git.

Alternative: regenerate alignments or calls. Rejected because that would mix reproducibility drift with the denominator question and would no longer be an addendum to the frozen M4-① run.

### 2. Use B0 base coordinates as the sole intersection frame

For each arm, parse primary PAF alignments at MAPQ 60 carrying a CIGAR (`cg`) and map only one-to-one `M`, `=`, or `X` query/target base pairs into B0 coordinates. Query-only insertions and target-only deletions are not projected bases. A B0 position is retained for an arm only when exactly one candidate base projects there; ambiguous or multiply projected positions are excluded with a reason. Reverse-strand coordinates are handled explicitly.

Alternative: intersect candidate BED coordinates directly. Rejected because indels make nominal coordinates non-comparable across arms.

### 3. Keep the archived callability policy unchanged

An arm-specific B0 position is callable when its uniquely projected candidate base has held-out depth at or above the archived `minimum_callable_depth`; mapping/base-quality filtering is inherited from the frozen depth artifact generation. The six-arm common-callable set is the exact intersection of the six arm-specific callable B0 sets. The script verifies that the common set is non-empty.

No new scientific threshold is introduced. The addendum consumes the archived experimental policy and cannot promote it to production.

### 4. Assign regions in B0 and report a transparent denominator

The archived `plant-regions.bed` is the only region authority. For each arm×region row:

- `projected_bases`: B0 region bases with exactly one base-to-base projection into that arm.
- `callable_bases`: B0 region bases in the six-arm common-callable set; therefore identical across arms for a region.
- `callable_fraction`: `callable_bases / projected_bases`, or null only when projected bases are zero.
- `residual_loci`: residual ledger events whose candidate-coordinate VCF anchor uniquely projects to a B0 base inside the common-callable set and that region.
- `residual_rate_per_10kb`: `residual_loci / callable_bases × 10,000`, or null only when callable bases are zero.

An additional `all_regions` row is the registered comparison row. Residual rows whose anchor lacks a unique base-to-base B0 projection are excluded from ranking and listed with a machine-readable reason; they are not silently reassigned to a nearby base.

### 5. Pre-register the only conclusion rule

Using only the `all_regions` rows, R1P1 is:

- `RETAINS_SOLE_LEAD` when its residual rate is strictly lower than every other arm;
- `TIED_LOWEST` when it equals the minimum with at least one other arm;
- `DOES_NOT_LEAD` otherwise.

Because all arms share the same callable denominator, the rate comparison is equivalent to a residual-count comparison. This classification answers only the fair-denominator residual question. It cannot revise M4-①, claim full dominance, or select a production route.

### 6. Keep outputs lightweight and independently auditable

The committed evidence comprises the frozen input manifest, common-callable BED, arm×region TSV, residual projection/exclusion audit, summary JSON, command/provenance record, `MANIFEST.sha256`, and `VALIDATION-plant-common-callability.md`. No FASTQ, BAM, VCF, candidate FASTA, or `runs/` directory is committed.

## Risks / Trade-offs

- [Risk] PAF ambiguity or structural rearrangement could create false coordinate equivalence. → Retain only exactly-one base-to-base projections and report exclusions.
- [Risk] Excluding unprojectable indel anchors may undercount route-specific residuals. → Report every exclusion by arm/reason and constrain the conclusion to the common projected base denominator.
- [Risk] A common intersection can be much smaller than any arm-specific callable set. → Report both projected and common-callable bases/fractions by region; do not generalize outside the intersection.
- [Risk] The analysis is post-M4 and already motivated by observed denominator spread. → Freeze the algorithm and conclusion rule before computing the intersection; do not add thresholds or alternative rankings after results.
- [Risk] Historical evidence paths are local. → Record absolute paths and checksums plus public/reproducible parent provenance; fail closed if artifacts no longer match.

## Migration Plan

1. Add and validate the standalone change artifacts.
2. Freeze the parent evidence manifest.
3. Run the deterministic summarizer once and validate its semantic assertions.
4. Commit lightweight evidence and tests, then complete PR/CI/merge.
5. Archive the change only after merge; sync the added requirement into `hybrid-reference-build` without modifying archived M4-①.

Rollback removes only this addendum and its new requirement. It never touches the parent run or historical `runs/` data.
