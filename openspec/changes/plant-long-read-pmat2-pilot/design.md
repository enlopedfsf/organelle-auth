## Context

See `proposal.md` for motivation. M1 already provides a plant short-read assembly/read-back
contract under `plant_sr_assembly/<sample_id>/`; the Corydalis anchor is the SRR38978846 DNBSEQ
assembly and the `corydalis-test-0.1` pack built around PZ405204.1. M1 recorded a 6-scaffold
plastome with high local identity but an unresolved approximately 38 kb IR-region representation
gap. The available long-read fixture is `/mnt/ssd_pool/home/iris-hp/zhongyao/corydalis_test/
SRR38978847-long.fastq.gz`, an ONT public run, paired to `SRR38978846_1/2.fastq.gz` for evaluation
only.

The capability contract is the new `plant-long-read-analysis` domain; the change name remains
`plant-long-read-pmat2-pilot` so future plant long-read changes do not accumulate under a
pilot-named capability domain.

## Goals / Non-Goals

**Goals:**

- Add an explicitly opt-in long-read pilot subworkflow that cannot feed the existing IDENTIFY or
  DECISION channels.
- Make QC, PMAT2 arguments, assembly outputs, comparisons, error summaries, and resource usage
  reproducible and reviewable.
- Use the M1 short-read evidence and PZ405204 as comparison anchors while preserving the distinction
  between an evidence anchor and an independently validated truth set.
- Produce an ONT-only M3 Go/No-Go record with CycloneSEQ fields reserved for a later change.

**Non-Goals:**

- No PMAT2 production admission, decision threshold, or identify integration.
- No CycloneSEQ claim, animal long-read route, hybrid assembly, or mixed-platform authentication.
- No threshold calibration from this same ONT/SR pair and no forced circularization or gap filling.

## Decisions

### 1. Explicit pilot routing and output isolation

Add a distinct analysis mode (for example `long_read_pilot`) and a dedicated subworkflow whose
outputs are published below a pilot-specific root. The main workflow may validate the input contract
and launch the pilot, but it MUST NOT connect PMAT2 output to `IDENTIFY`, `DECISION_ENGINE`, or any
status field that represents a terminal authentication result. This is safer than reusing the
M1/M2 identify channel because pure long-read evidence is explicitly research-only.

### 2. Select filtlong for read filtering

Use filtlong rather than chopper: filtlong is a mature bioconda/containerized streaming filter,
fits a single local module, and avoids introducing a signal-model dependency. The filter receives
all quality/length/retention settings from the experimental profile or an evaluation policy record;
the design does not choose scientific cutoff numbers. NanoPlot is used before and after filtering
for descriptive metrics only.

### 3. PMAT2 module and tool arguments

Create a local `PMAT2` process with a pinned bioconda/container recipe, explicit `versions.yml`,
resource trace, deterministic output staging, and an nf-test stub. Pass `-t ont -x 0` exactly as
method/tool parameters. Container digest and PMAT2 version are recorded at apply time and linked
to `registries/tools.yaml`; the registry remains `EXPERIMENTAL` and no production profile loads it.

Alternatives considered: an nf-core PMAT2 module was not assumed because the requirement is a local
module and PMAT2 availability/CLI details need direct verification; Flye or a hybrid assembler is
not substituted because that would change the pilot question and violate the scope.

### 4. Comparison anchors and structural closure

The evaluation subworkflow consumes:

1. PMAT2 assembly FASTA/graph and its metadata;
2. the M1 `plant_sr_assembly` scaffold/read-back evidence, read-only;
3. PZ405204.1 from `assets/reference_packs/corydalis-test-0.1/`.

Use versioned alignment/assembly-comparison tools already accepted by the repository for sequence
identity and aligned span. For the IR test, encode the M1 recorded gap coordinates/interval and
report `closed`, `not_closed`, or `not_assessable` only when the alignment and contiguity evidence
supports it. No output may fill or circularize a gap merely to satisfy the expected structure.

### 5. Error-spectrum and resource accounting

Derive homopolymer runs from the aligned PMAT2 and short-read-anchor sequences using one fixed,
reusable procedure: (1) scan the short-read anchor for maximal homopolymer runs and record reference
contig, 1-based start/end, base, and run length; (2) lift each interval through the same alignment
used for sequence concordance, retaining only intervals with an unambiguous aligned span; (3)
compare PMAT2 and short-read sequence inside each interval, counting substitutions, insertions,
deletions, and run-length delta (`LR_length - SR_length`) separately by reference run length; and
(4) summarize counts, rates per callable homopolymer base, length-stratified distributions, and
uncallable/ambiguous run coordinates. The exact alignment tool/version, scoring and ambiguity
policy, callable denominator, and TSV/JSON schema are recorded so the procedure can be rerun
unchanged on CycloneSEQ data. The M1 short-read sequence is a truth proxy for this pilot, not an
independent truth set. Capture wall time, CPU, peak memory, disk, input/output bytes, tool versions,
container digest, and command arguments through Nextflow trace plus a normalized evaluation JSON.

### 6. Validation and Go/No-Go artifacts

Write `VALIDATION-plant-lr.md` in the change artifact during apply. It must include input checks,
ONT platform disclaimer, QC metrics, PMAT2 output status, IR closure evidence, sequence comparison,
homopolymer report, resource table, and limitations. A separate M3 Go/No-Go skeleton records ONT
evidence and leaves CycloneSEQ transfer fields explicitly `PENDING_REAL_DATA`; it cannot promote
PMAT2 or authorize production use.

### 7. Testing strategy

T1 covers PMAT2 process contract, versions/stub, empty-output failure, and QC parameter provenance.
T2 covers pilot routing isolation, M1 read-only consumption, IR closure states, error/resource JSON,
and failure propagation. T3 is deliberately not run: the public ONT fixture is too large for a
lightweight smoke; the real end-to-end command and rationale are recorded in the validation doc.

## Risks / Trade-offs

- **[ONT-to-CycloneSEQ transfer risk]** → Label every result ONT-only and leave transfer Go/No-Go
  fields pending real CycloneSEQ paired DNA.
- **[Short-read anchor is not independent truth]** → Call it an evidence anchor/truth proxy and
  prohibit threshold calibration or production claims from this pair.
- **[PMAT2 CLI/container drift]** → Pin version/digest, capture `versions.yml`, and fail closed on
  unknown CLI/output layout.
- **[IR repeat ambiguity]** → Require coordinate-level alignment and contiguity evidence; permit
  `not_assessable` and never force closure.
- **[Long-read homopolymer errors]** → Report an observed error spectrum with callable span and
  sequencing-platform label, not a generalized accuracy claim.
- **[Large ONT resource cost]** → Keep T3 out of routine CI, use local real-data validation, and
  record resource consumption for the Go/No-Go decision.

## Migration Plan

No production migration. Apply adds the pilot modules/configuration and tests behind an explicit
experimental route. Rollback removes the pilot route and its artifacts; existing plant/animal
short-read identify behavior and M1/M2 output contracts remain unchanged.

## Open Questions

- The exact PMAT2 package version/container digest and the final resource envelope are to be pinned
  during apply after the installed CLI is probed.
- The M1 IR gap's precise coordinate representation must be copied from the archived validation
  artifact into the evaluation manifest before running the pilot; if coordinates cannot be mapped
  unambiguously, the result is `not_assessable`, not an inferred closure.
