# M4 Hybrid Backbone and Polish — Execution Validation

## State

`apply=APPROVED`; `planning_validation=PASS`; `freeze_gate=FROZEN`; `12-arm_execution=PASS`; `heldout_evaluation=COMPLETE`.

All three freeze artifacts below were present, non-empty, checksum-recorded, and listed in the signed freeze manifest before the arm run began.

## Freeze checklist

| Artifact | Required evidence | Status |
|---|---|---|
| Plant/animal B0 and R1 backbone FASTA | absolute path, non-empty check, SHA256, producing command and tool versions | FROZEN |
| Per-taxon train/held-out paired FASTQs | deterministic pair-preserving split, counts, source checksums, output checksums, manifest SHA256 | FROZEN |
| Animal core-mask BED | Flye/Raven/M2-anchor unique projection intersected with training-read callability; BED SHA256; owner | FROZEN |

## Registered execution parameters

- Paired split: canonical first whitespace-delimited read token, strip `@` and terminal `/1` or `/2`; SHA256 of `m4-hybrid-v1\t<canonical_pair_id>`; residues 0–1 held-out, 2–9 training; mates remain paired.
- Public short-read scope: established seed-11 approximately 2 Gb paired inputs, not the full datasets. Plant 6,671,740 source pairs → 5,336,938 train + 1,334,802 held-out; animal 6,659,067 → 5,328,722 + 1,330,345. All source/output gzip and SHA256 checks passed.
- Long-read mapping for R1: Flye-bundled minimap2 `-x map-ont -t 4`; exactly two Racon rounds with `-w 500 -q 10.0 -e 0.3 -m 3 -x -5 -g -4 -t 4`; no `-u`, `--no-trimming`, or CUDA; round two remaps to round one.
- Held-out evaluation mapper: the pinned minimap2 binary and exact command will be recorded before evaluation; held-out reads are never used for polishing, mask construction, or tuning.
- Callability: the exact command, mapping/base-quality thresholds, and BED intersection will be recorded before the mask is frozen; a missing or empty mask blocks all animal arms.
- Indel/homopolymer metrics: one pinned caller/normalization command and version will be recorded before evaluation; reference disagreement is proxy evidence only and read-backed evidence is primary.
- Polypolish and bcftools: executable paths, versions/container digests, full commands, training-read inputs, fixed Polypolish insert-filter defaults, and fixed bcftools depth/filter policy must be recorded before arm execution.

## Runtime preflight record (2026-08-13)

- Flye: `/home/iris-hp/miniconda3/envs/flye/bin/flye`, version `2.9.6-b1802`.
- Flye-bundled minimap2: `/home/iris-hp/miniconda3/envs/flye/bin/flye-minimap2`, version `2.24-r1155-dirty`.
- Racon authority for M4: BioContainers build `1.4.20--hd03093a_2`, digest `sha256:738d48f...5cb72`; local matching flat Mamba runtime `/home/iris-hp/miniconda3/envs/racon_compat/bin/racon`, executable SHA256 `c0f23e...64a`. Two fixed rounds use `-w 500 -q 10.0 -e 0.3 -m 3 -x -5 -g -4 -t 4`.
- Racon execution preflight: the default 1.5.0 binary terminated with `Illegal instruction` after the first minimap2 mapping on animal B0. A separate flat mamba environment `/home/iris-hp/miniconda3/envs/racon_compat` with Racon `1.4.20` (conda-forge/bioconda, no defaults) passed the same command and produced both two-round R1 candidates; the runtime identity and checksums are recorded in `MANIFEST.sha256`.
- Held-out mapper registration: the same Flye-bundled minimap2 binary, `-x sr -t 4`, with output PAF/SAM retained; no held-out reads are used before final evaluation.
- Training callability registration: `/home/iris-hp/miniconda3/envs/agrvate/bin/samtools` 1.20 with Flye-bundled minimap2 2.24; mapped primary reads use `flye-minimap2 -ax sr --sam-hit-only -t 4 | samtools view -F 0x904 -q 20 | samtools sort`, and callable positions use `samtools depth -aa -q 20 -Q 20` at depth `>=1`. This is intersected with the non-repeat, unique Flye/Raven/M2-anchor projection after 500-bp boundary trimming. Any empty result blocks animal arms.
- Animal mask prior result (invalidated): `contig_1:0-3004`, SHA256 `94948cc7170c9ae51cef59a1b6903df707df67612d8ce960122cb9217a588be8`. Review found that the generation path hard-coded `contig_1`, omitted other high-confidence collinear segments, and did not implement all pre-registered uniqueness/repeat/junction/liftover exclusions. It MUST NOT be used for ranking or arm execution.
- Animal mask replacement: `contig_1:500-2441`, `contig_3:515-3800`, and `contig_3:4839-10305` (10,692 bp total), BED SHA256 `468f82...f6b0`. It excludes repeat `contig_2`, the 39-bp multiply projected overlap, unanchored sequence, and 500-bp junction flanks. The retained pieces are local sequence-evaluation blocks only: Raven/anchor global query order and cross-block adjacency are not interpreted and cannot support topology. The validation/evidence Owner approved this limited use on 2026-08-13.
- bcftools: BioContainers build `1.21--h8b25389_0`, digest `sha256:969314...6027`; local matching `/home/iris-hp/miniconda3/envs/agrvate/bin/bcftools`, executable SHA256 `4ee4bb...9121`. The bactopia copy is unusable because its `libcrypto.so.1.0.0` dependency is missing.
- Polypolish: BioContainers build `0.7.1--hec9b1f2_0`, digest `sha256:729c4f...aa5d`; local matching `/home/iris-hp/miniconda3/envs/polypolish/bin/polypolish`, executable SHA256 `de46b9...7622`. Paired inputs are the frozen 80% training split.
- Container provenance: all four immutable amd64/Linux digests were independently resolved by `skopeo inspect`. Local Docker remained blocked before pull by Snap transient-scope DBus isolation. The authoritative PR #21 workflow executed every pinned image successfully on head `476ab56`: Racon, BWA, Polypolish, and bcftools all passed in [run 31689611580](https://github.com/enlopedfsf/organelle-auth/actions/runs/31689611580).
- Public short-read platform correction: ENA identifies SRR38978846 as Illumina HiSeq 2500 and SRR27841063 as Illumina HiSeq 2000. The registry now lists Illumina as an upstream-supported platform for BWA-MEM, Polypolish, and bcftools while keeping `project_validated_platforms=[]`; this M4 run is the project evaluation, not prior validation.
- Method preflight correction: current upstream Polypolish guidance recommends the paired insert filter after separate `bwa mem -a` mappings, so the fixed default filter is now part of every P arm. bcftools documents a default 250-read `mpileup` ceiling and a separate high-depth indel ceiling, while `consensus` applies variants already present in the VCF without allele-fraction logic. Every C arm therefore uses nonbinding `-d/-L 20000000` ceilings and the pre-registered training-only `QUAL>=30`, depth `>=10`, ALT-fraction `>=0.8` filter before consensus. These corrections were frozen before any arm executed.
- Indel/homopolymer metrics: final candidates will be normalized against the held-out read-backed callset using the pinned bcftools/normalization toolchain; homopolymer discordance is counted only where held-out reads are callable and support the alternate run-length.

## Non-decision invariants

All produced candidates must carry `status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE`. CycloneSEQ remains `PENDING_REAL_DATA`; PMAT2 and IDENTIFY/DECISION routing are unchanged.

## Audit policy

Large FASTQ/BAM/intermediate files remain outside Git. Their fixed paths and SHA256 values are recorded in `MANIFEST.sha256`; this report and all lightweight manifests are committed. `nf-test` uses property assertions rather than exact hashes for non-deterministic assemblies.

## Corrective freeze review (2026-08-13)

The earlier `FROZEN` declaration was withdrawn before any arm ran. Review identified four material defects: full short-read datasets were used without an explicit override of the established approximately 2 Gb default; the split implementation did not provide complete source/atomicity/EOF evidence; the animal mask hard-coded `contig_1` and omitted `contig_3`; and runtime claims did not match the binaries actually used. The old full-data splits and old 3,004-bp mask remain on disk as invalidated historical evidence but are absent from the authoritative freeze checklist and manifest. No historical output was deleted.

Corrections completed:

- Reused the already validated seed-11 approximately 2 Gb paired files for both taxa. Full gzip tests, read counts, byte sizes, source/output SHA256 values, and public-evaluation classification are recorded in lightweight JSON manifests.
- Added a tested atomic splitter with explicit mate-EOF checking, pair-ID matching, deterministic gzip headers, source hashes, exclusive assignment audit, script hash, and four passing unit tests.
- Freshly reproduced plant and animal R1 in new `backbones-v2` directories; both final SHA256 values exactly match the earlier two-round outputs.
- Rebuilt the animal mask using non-repeat Flye contigs, exactly-one local Raven/M2-anchor target projections, and training-only callability. The replacement is 10,692 bp rather than the invalid 3,004-bp hard-coded mask; it is expressly a local sequence core, not adjacency or topology evidence.
- Confirmed by ENA metadata that short/long runs share BioSample `SAMN60565143` (plant) and `SAMN39735897` (animal). These remain same-source public engineering evaluations, not independent biological transfer validation.
- Resolved matching immutable BioContainers digests by Quay API and `skopeo inspect` for Racon, BWA, Polypolish, and bcftools. The local Snap Docker probe remains infrastructure-blocked, while authoritative CI executed all four pinned containers successfully on PR #21 head `476ab56`.
- The validation/evidence Owner explicitly approved BED SHA256 `468f82bd65353bc89b28d94b5cc795e9216ae338ce7fde2c86e969bba9a9f6b0` on 2026-08-13, solely for animal six-arm local sequence ranking. The signed record is `evidence/animal-core-mask/animal-core.approval.json`; global order, adjacency, repeat copy number, circularity, and complete topology remain prohibited interpretations.
- Rebuilt `MANIFEST.sha256` in standard two-column `sha256sum -c` format; all 47 registered local objects passed, including the separate Owner-approval record.

Current honest state before execution was: B0/R1, paired splits, fixed arm protocols, and the Owner-approved animal local-core mask were frozen; all four pinned-container execution probes passed authoritative CI. The execution and evaluation results are recorded below.

## Twelve-arm execution result (2026-08-13)

The standalone `m4_hybrid.nf` evaluator ran in the fixed locations below. It is not imported by
`main.nf` or `workflows/organelleauth.nf`, so no candidate can reach IDENTIFY or DECISION.

- Output: `/home/iris-hp/Project/organelle-auth-ci-fix/runs/output/m4-hybrid-backbone-and-polish/matrix-v1`
- Work/cache: `/home/iris-hp/Project/organelle-auth-ci-fix/runs/work/m4-hybrid-backbone-and-polish/matrix-v1`
- Trace/report/timeline: `matrix-v1/run-metadata/`
- Execution audit: 80/80 tasks `COMPLETED`, all exit 0; PMAT2, IDENTIFY, and DECISION invocation counts are zero.
- Exact matrix: B0, R1, P0, C0, R1P1, and R1C1 for each of plant and animal; no additional arm or result-driven round was run.

### Uniform held-out comparison

| Taxon | Arm | callable core bp | residual unsupported loci | evaluable HP discordances | core concordance | SNV / indel |
|---|---:|---:|---:|---:|---:|---:|
| plant | B0 | 134,324 | 231 | 224 | 0.996330 | 1 / 230 |
| plant | R1 | 120,796 | 103 | 68 | 0.997955 | 14 / 89 |
| plant | P0 | 107,186 | 2 | 2 | 0.999963 | 0 / 2 |
| plant | C0 | 137,114 | 11 | 10 | 0.999803 | 0 / 11 |
| plant | R1P1 | 106,968 | 1 | 1 | 0.999981 | 0 / 1 |
| plant | R1C1 | 120,814 | 3 | 2 | 0.999917 | 0 / 3 |
| animal | B0 | 10,494 | 4 | 4 | 0.999238 | 0 / 4 |
| animal | R1 | 10,494 | 2 | 2 | 0.999619 | 0 / 2 |
| animal | P0 | 10,494 | 0 | 0 | 1.000000 | 0 / 0 |
| animal | C0 | 10,494 | 0 | 0 | 1.000000 | 0 / 0 |
| animal | R1P1 | 10,494 | 0 | 0 | 1.000000 | 0 / 0 |
| animal | R1C1 | 10,494 | 0 | 0 | 1.000000 | 0 / 0 |

The table is generated from `evidence/results/six-arm-comparison.tsv`; all underlying normalized
held-out records are in `heldout-residual-ledger.tsv`. These are read-backed experimental metrics,
not reference truth and not production acceptance thresholds.

### Pre-registered dominance result

- **Plant:** R1P1 is the sole numeric winner under the exact pre-registered rule: 1 residual and
  1 evaluable homopolymer discordance are each strictly lower than every other arm, and its core
  concordance does not regress from B0. This is recorded as
  `NUMERIC_DOMINANT_UNDER_PREREGISTERED_RULE`, while the machine state remains
  `INCONCLUSIVE / CANDIDATE / NOT_APPLICABLE`.
- **Animal:** P0, C0, R1P1, and R1C1 tie at 0/0/1.0, so no arm is strictly better than every
  competitor. The pre-registered result is `CONDITIONAL`, not a post-hoc winner.
- **Plant callability caveat:** callable bases range from 106,968 to 137,114 across arms. In
  particular, P arms lose MAPQ20 callability in the IR/repeat-labelled interval and some flanking
  sequence. Callability was not registered as a ranking metric, so no post-hoc threshold was added
  and the numeric R1P1 result is reported unchanged; it must not be generalized into a production
  preference until transfer data or a separately pre-registered common-callability analysis exists.

### Route edit evidence and applicability

| Taxon | P0 edits | C0 edits | R1P1 edits | R1C1 edits |
|---|---:|---:|---:|---:|
| plant | 382 | 242 | 230 | 109 |
| animal | 6 | 5 | 2 | 2 |

Each short-read route has a per-base introduced-edit ledger with input base, proposed allele,
depth/support evidence, ambiguity semantics, region, and filtering reason. Polypolish retained
multi-mapping evidence and inferred the expected `fr` orientation. Matching pair counts were
434,547/434,713 for plant P0/R1P1 and 14,250/14,228 for animal P0/R1P1; insert ranges were
45–643 bp across the four P arms. The two animal R1-derived routes produce identical biological
sequence content (canonical sequence SHA256
`3f7a1680f0d89fb414c2f0c824fc4310df3bbac2b4923253791b8558085cab77`) despite different FASTA
wrapping, providing independent-tool agreement for the evaluable sequence but not for topology.

### Region and junction interpretation

- Plant B0 has 21 residuals in the archived M3 IR-gap-closure interval and 210 in the remaining
  labelled sequence; R1P1 has one residual in the labelled flank and none callable in that IR
  interval. The absent IR residual count is not a topology or IR-copy-number result because P-arm
  callability in the interval is substantially lower.
- Animal ranking uses only the Owner-approved 10,692-bp B0 core translated into each candidate.
  Polishing removes all held-out residuals within the 10,494 callable bases. Edits and residuals
  outside the mask remain `NOT_EVALUABLE` and cannot rank arms.
- No M4 arm makes a new junction, adjacency, repeat-copy, or circularity claim. The junction audit
  is therefore `NOT_APPLICABLE_NO_NEW_JUNCTION_CLAIM`; the inherited plant and animal topologies
  both remain `INCONCLUSIVE`.

### Resources and retained artifacts

The full run took approximately 9.5 minutes from first to last task submission on this workstation.
The slowest individual task was BWA-MEM at 409 seconds; maximum observed RSS was approximately
829 MB in Polypolish. The fixed result tree is approximately 127 MB and the resumable Nextflow work
cache approximately 29 GB. Large BAM/work intermediates remain outside Git. Lightweight results,
ledgers, candidate checksums, raw trace rows, and `RESULT-MANIFEST.sha256` are committed under
`evidence/results/`; every manifest entry passes `sha256sum -c`.

## Verification status

- Real-data one-taxon smoke: PASS, including Polypolish, bcftools filtering/consensus, mask
  liftover, held-out mapping/calling, and metric generation.
- Full matrix: PASS, 80/80 tasks completed, 12/12 metrics present.
- Python targeted tests: PASS (evidence parsing, mask liftover, core-only metrics, dominance/tie
  handling).
- `openspec validate --all --strict`: PASS (10/10) after implementation, before final archive.
- Local `nf-test`: `INFRASTRUCTURE_BLOCKED`; both the direct and one proxy retry failed before test
  execution on the remote plugin index (file lookup failure, then connection timeout). The
  repository-owned workflow test and structural `-stub-run` exist; CI remains authoritative for
  this gate.
- Local `nf-core pipelines lint`: `INFRASTRUCTURE_BLOCKED` before lint assertions because this
  workstation's nf-core 4.1.0 installation calls an absent `prek` executable while normalizing
  `modules.json`. The partial formatting-only mutation was inspected and restored; CI remains the
  authoritative lint gate and no `--fix` operation was used.

## Final scientific and governance statement

Plant R1P1 is the pre-registered numeric leader on this public engineering dataset, with an explicit
callability caveat. Animal short-read polishing is beneficial in the frozen core, but four routes
tie and remain conditional. Neither result promotes a reference, changes topology, enters
authentication, or resolves CycloneSEQ transfer. Every candidate remains
`status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE`; CycloneSEQ remains
`PENDING_REAL_DATA`, and PMAT2 remains gated by Issue #10.
