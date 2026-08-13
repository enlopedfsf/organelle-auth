# M4 Hybrid Backbone and Polish — Execution Validation

## State

`apply=APPROVED`; `planning_validation=PASS`; `freeze_gate=IN_PROGRESS`; `12-arm_execution=NOT_STARTED`.

No arm may run until the three freeze artifacts below are present, non-empty, checksum-recorded, and listed in the signed freeze manifest.

## Freeze checklist

| Artifact | Required evidence | Status |
|---|---|---|
| Plant/animal B0 and R1 backbone FASTA | absolute path, non-empty check, SHA256, producing command and tool versions | FROZEN_LOCAL |
| Per-taxon train/held-out paired FASTQs | deterministic pair-preserving split, counts, source checksums, output checksums, manifest SHA256 | FROZEN_LOCAL |
| Animal core-mask BED | Flye/Raven/M2-anchor unique projection intersected with training-read callability; BED SHA256; owner | CANDIDATE_PENDING_OWNER_REVIEW |

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
- Animal mask replacement candidate: `contig_1:500-2441`, `contig_3:515-3800`, and `contig_3:4839-10305` (10,692 bp total), BED SHA256 `468f82...f6b0`. It excludes repeat `contig_2`, the 39-bp multiply projected overlap, unanchored sequence, and 500-bp junction flanks. The retained pieces are local sequence-evaluation blocks only: Raven/anchor global query order and cross-block adjacency are not interpreted and cannot support topology. It remains pending validation/evidence-owner review and cannot yet authorize arm execution.
- bcftools: BioContainers build `1.21--h8b25389_0`, digest `sha256:969314...6027`; local matching `/home/iris-hp/miniconda3/envs/agrvate/bin/bcftools`, executable SHA256 `4ee4bb...9121`. The bactopia copy is unusable because its `libcrypto.so.1.0.0` dependency is missing.
- Polypolish: BioContainers build `0.7.1--hec9b1f2_0`, digest `sha256:729c4f...aa5d`; local matching `/home/iris-hp/miniconda3/envs/polypolish/bin/polypolish`, executable SHA256 `de46b9...7622`. Paired inputs are the frozen 80% training split.
- Container provenance: all four immutable amd64/Linux digests were independently resolved by `skopeo inspect`. Local Docker execution was blocked before pull by Snap transient-scope DBus isolation; therefore container execution probes are `PENDING_CI`, and the freeze gate remains `IN_PROGRESS` until CI executes the pinned images.
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
- Resolved matching immutable BioContainers digests by Quay API and `skopeo inspect` for Racon, BWA, Polypolish, and bcftools. The local Snap Docker probe is infrastructure-blocked before image execution, so CI must still execute the pinned containers.
- Rebuilt `MANIFEST.sha256` in standard two-column `sha256sum -c` format; all 46 registered local objects passed.

Current honest state: B0/R1 and split artifacts are locally frozen; the mask is an unsigned owner-review candidate; container execution is `PENDING_CI`; twelve-arm execution remains `NOT_STARTED`.
