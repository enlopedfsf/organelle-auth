# M4 Hybrid Backbone and Polish — Execution Validation

## State

`apply=APPROVED`; `planning_validation=PASS`; `freeze_gate=IN_PROGRESS`; `12-arm_execution=NOT_STARTED`.

No arm may run until the three freeze artifacts below are present, non-empty, checksum-recorded, and listed in the signed freeze manifest.

## Freeze checklist

| Artifact | Required evidence | Status |
|---|---|---|
| Plant/animal B0 and R1 backbone FASTA | absolute path, non-empty check, SHA256, producing command and tool versions | PENDING |
| Per-taxon train/held-out paired FASTQs | deterministic pair-preserving split, counts, source checksums, output checksums, manifest SHA256 | IN_PROGRESS |
| Animal core-mask BED | Flye/Raven single-copy collinear intervals intersected with training-read callability; BED SHA256; owner | FROZEN |

## Registered execution parameters

- Paired split: canonical first whitespace-delimited read token, strip `@` and terminal `/1` or `/2`; SHA256 of `m4-hybrid-v1\t<canonical_pair_id>`; residues 0–1 held-out, 2–9 training; mates remain paired.
- Long-read mapping for R1: Flye-bundled minimap2 `-x map-ont -t 4`; exactly two Racon rounds with `-w 500 -q 10.0 -e 0.3 -m 3 -x -5 -g -4 -t 4`; no `-u`, `--no-trimming`, or CUDA; round two remaps to round one.
- Held-out evaluation mapper: the pinned minimap2 binary and exact command will be recorded before evaluation; held-out reads are never used for polishing, mask construction, or tuning.
- Callability: the exact command, mapping/base-quality thresholds, and BED intersection will be recorded before the mask is frozen; a missing or empty mask blocks all animal arms.
- Indel/homopolymer metrics: one pinned caller/normalization command and version will be recorded before evaluation; reference disagreement is proxy evidence only and read-backed evidence is primary.
- Polypolish and bcftools: executable paths, versions/container digests, full commands, and training-read inputs must be recorded before arm execution.

## Runtime preflight record (2026-08-13)

- Flye: `/home/iris-hp/miniconda3/envs/flye/bin/flye`, version `2.9.6-b1802`.
- Flye-bundled minimap2: `/home/iris-hp/miniconda3/envs/flye/bin/flye-minimap2`, version `2.24-r1155-dirty`.
- Racon: `/home/iris-hp/miniconda3/envs/racon/bin/racon`, version `1.5.0`; two fixed rounds, `-w 500 -q 10.0 -e 0.3 -m 3 -x -5 -g -4 -t 4`.
- Racon execution preflight: the default 1.5.0 binary terminated with `Illegal instruction` after the first minimap2 mapping on animal B0. A separate flat mamba environment `/home/iris-hp/miniconda3/envs/racon_compat` with Racon `1.4.20` (conda-forge/bioconda, no defaults) passed the same command and produced both two-round R1 candidates; the runtime identity and checksums are recorded in `MANIFEST.sha256`.
- Held-out mapper registration: the same Flye-bundled minimap2 binary, `-x sr -t 4`, with output PAF/SAM retained; no held-out reads are used before final evaluation.
- Training callability registration: `/home/iris-hp/miniconda3/envs/bactopia/bin/samtools` 1.22.1; mapped training reads are retained with `minimap2 -ax sr -t 4`, and callable positions are defined before mask freeze as depth `>=1` at mapping quality `>=20` and base quality `>=20`, intersected with the single-copy Flye/Raven collinear BED. Any empty result blocks animal arms.
- Animal mask freeze result: B0/Flye coordinate frame `contig_1:0-3004` after single-copy Flye/Raven collinearity and full training-read callability intersection; merged BED SHA256 `94948cc7170c9ae51cef59a1b6903df707df67612d8ce960122cb9217a588be8`.
- bcftools: use `/home/iris-hp/miniconda3/envs/agrvate/bin/bcftools`, version `1.21`; the bactopia copy is unusable because its `libcrypto.so.1.0.0` dependency is missing. The working executable and environment identity must be checksum-recorded before C arms.
- Polypolish: `/home/iris-hp/miniconda3/envs/polypolish/bin/polypolish`, version `0.7.1`; paired short-read inputs are the frozen 80% training split. The executable/environment identity must be checksum-recorded before P arms.
- Indel/homopolymer metrics: final candidates will be normalized against the held-out read-backed callset using the pinned bcftools/normalization toolchain; homopolymer discordance is counted only where held-out reads are callable and support the alternate run-length.

## Non-decision invariants

All produced candidates must carry `status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE`. CycloneSEQ remains `PENDING_REAL_DATA`; PMAT2 and IDENTIFY/DECISION routing are unchanged.

## Audit policy

Large FASTQ/BAM/intermediate files remain outside Git. Their fixed paths and SHA256 values are recorded in `MANIFEST.sha256`; this report and all lightweight manifests are committed. `nf-test` uses property assertions rather than exact hashes for non-deterministic assemblies.
