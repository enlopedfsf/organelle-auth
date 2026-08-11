## Context

See `proposal.md` for the motivation. The active `plant-long-read-pmat2-pilot` change introduced an isolated M3 route but its implementation currently performs QC/filtering and then sends all filtered ONT reads to PMAT2 whole-background correction/assembly. The 2 GB real-data trial stopped at PMAT2/NextDenovo's approximately 10x seed-depth precondition, while the frozen method contract requires reference-first extraction and subset assembly for M3 (SCI-001, TEST-004).

The route must remain an evidence producer: ONT evidence is not CycloneSEQ validation, EXPERIMENTAL values cannot become production defaults, and no output can enter IDENTIFY or DECISION. The implementation must also remain practical for shallow WGS from taxa whose nuclear genome sizes differ by orders of magnitude; therefore nuclear coverage and raw gigabytes are not valid universal eligibility measures.

## Goals / Non-Goals

**Goals:**

- Introduce explicit, testable module boundaries for reference preparation, mapping, whole-read recruitment, target-evidence summarization/gating, subset assembly, comparator assembly, and structural validation.
- Preserve reads spanning divergent or repeated organelle structures without allowing indiscriminate off-target recruitment.
- Make target-organelle evidence and every scientific threshold policy-controlled, versioned, and machine-readable.
- Produce a Flye primary candidate and an independently labeled PMAT2 `-p 0` comparator from the exact same final subset.
- Answer the 38 kb IR-gap question with alignments and independent spanning-read evidence.
- Keep bounded synthetic T3 CI practical while reserving T4 claims for actual real-data execution.

**Non-Goals:**

- Calibrating production recruitment, depth, breadth, or junction thresholds.
- Claiming transfer from ONT to CycloneSEQ.
- Providing reference-free assembly for low-depth data.
- Integrating the pilot with production IDENTIFY/DECISION.
- Implementing polishing, variant interpretation, nuclear marker panels, or animal long-read routing.

## Decisions

### 1. Use a reference-first subworkflow with narrow module contracts

The corrected route is composed as:

```text
validated bundle
  -> deterministic raw budget + descriptive QC/filter
  -> prepare circular reference rotations
  -> minimap2 mapping pass 1
  -> policy-based read-id selection
  -> whole-read extraction
  -> target evidence + gate
  -> Flye preliminary assembly
  -> optional minimap2 rescue pass against preliminary candidates
  -> union/deduplicate complete read ids + extract final subset
  -> final target evidence + gate
  -> Flye final primary assembly
  -> PMAT2 -p 0 comparator on the identical final subset
  -> reference/anchor alignments + IR/junction/homopolymer evidence
```

Each process owns one external tool or one deterministic in-repository evidence script. Mapping, selecting identifiers, extracting reads, gating, assembling, and summarizing structure are separate processes so failures and provenance are attributable. The subworkflow, not a monolithic shell block, controls the optional second pass and assembly fan-out.

Alternative considered: add a minimap2 command inside the existing `PLANT_LONG_READ_PILOT` process. Rejected because it would retain a multi-tool process, hide intermediate evidence, prevent independent T1 tests, and make resume/resource behavior opaque.

### 2. Make circular-reference rotations explicit reference-pack data

Reference metadata declares topology, canonical sequence identifier, reference-pack version, allowed status, and rotation offsets. A deterministic preparation script emits rotated FASTA records plus a mapping table back to canonical coordinates. Offsets must be integers within the reference length and are never invented from sample data during execution.

Multiple rotations reduce false loss of reads spanning the arbitrary FASTA origin. The canonical unrotated sequence remains present for coordinate reporting. Quarantined or empty references fail before mapping.

Alternative considered: concatenate the reference to itself and map to a doubled sequence. Rejected because duplicated coordinate space makes depth/breadth double counting and canonical interval lifting easier to get wrong.

### 3. Recruit complete molecules using multi-field alignment evidence

Pass-one mapping uses the platform-appropriate sensitive preset (ONT currently uses `map-ont`) and emits PAF with CIGAR and `cs` evidence. Experimental mapper heuristics such as secondary-hit count and minimum secondary-to-primary score ratio live in the policy/config record, not module code. The current exploratory profile may supply `--secondary=yes`, `-N 20`, and `-p 0.5`; these are recorded mapper settings, not validated production acceptance thresholds.

Selection evaluates configurable fields such as aligned query bases, query-aligned fraction, divergence/identity evidence, chain score, and alignment class. Mapping quality is recorded but cannot be the sole exclusion field. If any alignment for a read is eligible, the identifier is retained once and the entire original FASTQ record is extracted. Primary, secondary, and supplementary evidence remain in the alignment table so inverted-repeat mappings are not silently lost.

For paired short reads in future symmetry work, either mate recruiting will retain both mates; that is not implemented by this plant long-read change.

Alternative considered: retain only aligned read segments. Rejected because clipped sequence can contain the structural junction needed for circularization or IR-boundary evidence.

Alternative considered: `MAPQ >= X` alone. Rejected because true organelle reads in long repeats can be multi-mapping and receive low MAPQ.

### 4. Permit one candidate-guided rescue pass, never an unbounded loop

If pass one is experimentally eligible and the policy enables rescue, Flye creates preliminary candidates. All bounded input reads are mapped once to those candidates. Eligible pass-two identifiers are unioned with pass one, deduplicated, and re-extracted as complete reads. The route then recomputes evidence and performs the final assembly. The maximum pass count is two by contract.

Pass-two candidates can recover structurally divergent molecules whose alignments to the original reference were too weak. Bounding the loop prevents data-dependent nontermination and makes resume semantics deterministic. Per-pass manifests include candidate checksum, mapper parameters, selected IDs, and counts.

Alternative considered: repeatedly recruit until no new reads appear. Rejected because convergence depends on noisy/off-target candidates and is difficult to reproduce or budget.

### 5. Separate processing budget from target-organelle eligibility

The experimental profile may default to an approximately 2 GB raw-read budget with a fixed seed. That value limits compute and supports repeatability; it does not establish biological sufficiency. If input is smaller, all input is used. The manifest records requested bases, observed bases, selected reads, and hashes using streaming checksum tools rather than loading large FASTQ files into memory.

When reference recruitment yields extreme organelle depth, Flye's initial disjointig workload is capped through its policy-controlled `--asm-coverage` option. The experimental value is 50x, chosen as a conservative processing cap above Flye's documented typical 40x recommendation; it is not a production biological threshold, remains null in production policy, and does not replace full recruited-read evidence or downstream read remapping.

Target evidence is computed from canonicalized alignment coordinates:

- `recruited_reads` and `recruited_bases`: unique complete molecules selected;
- `aligned_target_bases`: per-read eligible aligned query intervals merged before summing, avoiding duplicate rotations/hits;
- `estimated_target_depth`: `aligned_target_bases / canonical_reference_length`;
- `reference_breadth`: union of eligible canonical reference intervals divided by reference length;
- alignment span, divergence, and multi-hit distributions;
- reads crossing the canonical circular-origin interval and declared IR/junction intervals;
- off-target warning indicators, including extreme recruited-to-aligned-base ratios.

Gate values are read from a versioned policy JSON. The evidence script calculates metrics but contains no pass/fail constants. Required null values in production return `INCONCLUSIVE` plus `THRESHOLD_NOT_CONFIGURED`. Experimental values must carry a rationale such as `exploratory_same_specimen_reference` and cannot be imported by the production profile.

Alternative considered: infer nuclear depth from a nominal genome size and require PMAT2's whole-genome seed depth. Rejected because genome size varies greatly, the target is an enriched multicopy compartment, and the observed 2 GB failure demonstrates that nuclear-depth eligibility answers the wrong question.

### 6. Use an explicit assembly route matrix

| Reference state | Target-evidence state | Strategy flag | Flye subset | PMAT2 `-p 0` subset | Full-background PMAT2 | Status |
|---|---|---|---:|---:|---:|---|
| usable | eligible experimental | reference-first | primary | comparator | no | continue as EXPERIMENTAL evidence |
| usable | insufficient/unassessable | any | no | no | no | `INCONCLUSIVE` with metric-specific reasons |
| missing/inadequate | any | reference-first | no | no | no | fail-fast or `INCONCLUSIVE`, according to input contract |
| missing/inadequate | separately eligible high-coverage de novo | explicit de novo fallback | no | no | permitted experimental fallback | evidence only |
| missing/inadequate | de novo policy null/false | explicit de novo fallback | no | no | no | `FULL_BACKGROUND_DE_NOVO_NOT_APPLICABLE` |

Flye is primary because it can assemble the small target-enriched long-read subset without PMAT2's whole-background NextDenovo correction prerequisite. PMAT2 is retained on the identical subset with `-p 0` to compare its organelle graph/candidate behavior while bypassing whole-genome correction. The subset checksum is included in both execution records to prove input equivalence.

Full-background PMAT2 is not the automatic fallback for poor recruitment. It is a distinct experimental branch whose high-coverage policy remains null until validated; this correction may implement the guard and reason code without activating that branch.

Alternative considered: PMAT2 `-p 1`/default as primary. Rejected for shallow WGS because it invokes whole-background correction and reproduced the observed seed-depth failure/resource expansion.

### 7. Validate structure with alignments and independent reads

Each non-empty candidate is aligned independently to the canonical reference and M1 short-read anchor using assembly-to-reference alignment settings. Evidence scripts consume those alignments plus the read-to-candidate mappings; they do not compare sequences by array position.

The structural record includes:

- candidate length and contig count;
- aligned span, identity/divergence, gaps, conflicts, and orientation;
- circular-origin and reference-declared junction support;
- IR boundary coordinates on reference, M1 anchor, and candidate where liftable;
- independent read IDs spanning each junction with flanking alignment on both sides;
- M1 38 kb gap result: `closed`, `not_closed`, or `not_assessable`;
- disagreements between Flye and PMAT2 candidates.

Homopolymer analysis scans maximal runs on the chosen anchor, lifts positions through a fixed alignment, and reports substitutions, indels, run-length deltas, callable denominators, and ambiguous/unliftable intervals. The method is platform-neutral; results remain platform-labeled.

Alternative considered: infer closure from a circular/contig label or successful tool exit. Rejected because neither proves that a biological junction is assembled and independently supported.

### 8. Define channel and artifact contracts

Every module input begins with `meta` and every output preserves it. Required tuple contracts are:

| Stage | Required inputs | Principal outputs |
|---|---|---|
| reference preparation | `meta`, reference FASTA, reference metadata JSON | rotated FASTA, coordinate map TSV, validation JSON |
| mapping | `meta`, bounded/filter FASTQ, target FASTA, mapper-policy JSON | PAF, command/version record |
| selection | `meta`, PAF, recruitment-policy JSON | selected IDs, alignment evidence TSV/JSON, status JSON |
| extraction | `meta`, source FASTQ, selected IDs | recruited FASTQ, counts/checksum JSON |
| target evidence/gate | `meta`, canonical reference, coordinate map, PAF, selected IDs, target-policy JSON | metrics JSON/TSV, gate status JSON |
| Flye assembly | `meta`, eligible recruited FASTQ, assembly-policy JSON | candidate FASTA, graph/logs, execution JSON, versions |
| PMAT2 comparator | same `meta` and recruited FASTQ checksum, comparator-policy JSON | candidate FASTA/graph/logs, execution JSON, versions |
| structural evidence | candidates, reference, M1 anchor, read mappings, structural-policy JSON | evidence JSON/TSV, alignment files, human-readable summary |

Empty or invalid required files fail at the owning boundary. Optional comparator artifacts are represented by an explicit status record, never by silently missing channels.

### 9. Register stage-specific status and reason codes

The route reuses common `PASS`, `WARN`, `INCONCLUSIVE`, and `FAIL` states but never emits an authentication class. New reason codes are registered with stage and meaning:

| Code | Stage | Meaning |
|---|---|---|
| `RECRUITMENT_COMPLETE` | recruitment | Pass completed with auditable selected identifiers |
| `LOW_TARGET_READ_YIELD` | gate | Recruited read/base evidence below selected experimental policy |
| `LOW_TARGET_COVERAGE` | gate | Estimated target depth below selected experimental policy |
| `LOW_REFERENCE_BREADTH` | gate | Canonical reference breadth below selected experimental policy |
| `REFERENCE_DIVERGENCE_SUSPECTED` | recruitment/gate | Alignment divergence distribution suggests reference mismatch |
| `OFFTARGET_RECRUITMENT_SUSPECTED` | recruitment/gate | Recruited/full-aligned evidence is inconsistent with target enrichment |
| `JUNCTION_SUPPORT_INSUFFICIENT` | gate/validation | Required circular/IR junction support is absent or unassessable |
| `SUBSET_ASSEMBLY_FAILED` | assembly | Primary subset assembly failed or emitted no valid FASTA |
| `COMPARATOR_ASSEMBLY_FAILED` | assembly | PMAT2 comparator failed while primary evidence is preserved |
| `THRESHOLD_NOT_CONFIGURED` | gate | Required production scientific policy value is null |
| `FULL_BACKGROUND_DE_NOVO_NOT_APPLICABLE` | routing | Full-background fallback eligibility is absent/false/unconfigured |

Codes never independently imply authenticity or non-authenticity.

### 10. Test the behavior at three engineering tiers

- T1 tests each module with tiny reference/read fixtures, including empty files, repeated alignments, complete-read extraction, null policy, tool failure, and stub outputs.
- T2 tests subworkflow routing: reference-first ordering, two-pass maximum, identical subset checksums for Flye/PMAT2, comparator failure isolation, production-null guard, and no decision-channel coupling.
- T3 runs a bounded synthetic circular organelle fixture with background reads, repeat/multi-map reads, and a junction-spanning molecule. Heavy real ONT data is not required for CI.
- T4 records the actual paired ONT/DNBSEQ run, resource use, structural findings, and unresolved CycloneSEQ fields. A skipped or blocked T4 remains pending.

The tool processes expose deterministic `stub` blocks so CI can validate contracts without pretending stubs are biological validation. At least one non-stub bounded path must exercise the evidence scripts and locally available lightweight tools.

## Risks / Trade-offs

- [Reference bias can exclude divergent or rearranged organelle molecules] → Use rotations, sensitive mapping evidence, complete-read retention, a bounded candidate-guided rescue pass, divergence warnings, and explicit `INCONCLUSIVE` rather than a forced negative.
- [Sensitive mapping can recruit NUMTs/NUPTs or other off-target sequence] → Gate on breadth/aligned depth/distributions, retain multi-hit evidence, report off-target suspicion, and require independent junction support; do not use recruitment alone as a decision.
- [Repeat preservation increases ambiguous mappings] → Canonicalize/deduplicate intervals for metrics while retaining all raw alignment classes for structure analysis.
- [Flye can fail on a very small or uneven subset] → Stop on target-evidence gates, preserve structured failure, and compare PMAT2 only as secondary evidence rather than silently switching to whole-background correction.
- [Two-pass recruitment can amplify an incorrect preliminary contig] → Require pass-one eligibility, limit rescue to one pass, preserve candidate checksums/per-pass deltas, and surface off-target warnings.
- [Experimental policy values may be mistaken for production thresholds] → Keep them in an experimental-only versioned policy; production values remain null and fail with `THRESHOLD_NOT_CONFIGURED`.
- [Synthetic CI does not establish real biological performance] → Separate T1-T3 engineering status from T4 real-data evidence and keep Go/No-Go pending.

## Migration Plan

1. Keep the existing `long_read_pilot` entry point disabled by default and isolated from IDENTIFY/DECISION.
2. Add the new modules and corrected subworkflow behind the experimental route without deleting preserved PMAT2 work directories or validation evidence.
3. Add experimental policy/schema fields; set all corresponding production scientific values to null.
4. Redirect the pilot workflow from the monolithic PMAT2-first module to the reference-first subworkflow. Preserve legacy outputs only as clearly labeled historical evidence where useful.
5. Mark `plant-long-read-pmat2-pilot` as superseded by this change and do not archive its conflicting capability delta independently.
6. Run strict OpenSpec validation, T0-T3 engineering tests, and a local bounded real-data dry run before updating `VALIDATION-plant-lr.md`.
7. Run the paired real ONT/DNBSEQ T4 route when compute and inputs are available; keep CycloneSEQ/Go-No-Go fields pending.

Rollback: restore the workflow include/call to the existing isolated pilot module while leaving the new modules unused. Because both routes are EXPERIMENTAL and disconnected from decision channels, rollback does not alter production authentication behavior. Do not delete generated work directories or evidence; label the reverted run and checksums in validation records.
