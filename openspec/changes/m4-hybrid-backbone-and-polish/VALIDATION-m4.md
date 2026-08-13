# M4 Hybrid Backbone and Polish — Execution Validation

## State

`apply=APPROVED`; `planning_validation=PASS`; `freeze_gate=IN_PROGRESS`; `12-arm_execution=NOT_STARTED`.

No arm may run until the three freeze artifacts below are present, non-empty, checksum-recorded, and listed in the signed freeze manifest.

## Freeze checklist

| Artifact | Required evidence | Status |
|---|---|---|
| Plant/animal B0 and R1 backbone FASTA | absolute path, non-empty check, SHA256, producing command and tool versions | PENDING |
| Per-taxon train/held-out paired FASTQs | deterministic pair-preserving split, counts, source checksums, output checksums, manifest SHA256 | IN_PROGRESS |
| Animal core-mask BED | Flye/Raven single-copy collinear intervals intersected with training-read callability; BED SHA256; owner | IN_PROGRESS |

## Registered execution parameters

- Paired split: canonical first whitespace-delimited read token, strip `@` and terminal `/1` or `/2`; SHA256 of `m4-hybrid-v1\t<canonical_pair_id>`; residues 0–1 held-out, 2–9 training; mates remain paired.
- Long-read mapping for R1: Flye-bundled minimap2 `-x map-ont -t 4`; exactly two Racon rounds with `-w 500 -q 10.0 -e 0.3 -m 3 -x -5 -g -4 -t 4`; no `-u`, `--no-trimming`, or CUDA; round two remaps to round one.
- Held-out evaluation mapper: the pinned minimap2 binary and exact command will be recorded before evaluation; held-out reads are never used for polishing, mask construction, or tuning.
- Callability: the exact command, mapping/base-quality thresholds, and BED intersection will be recorded before the mask is frozen; a missing or empty mask blocks all animal arms.
- Indel/homopolymer metrics: one pinned caller/normalization command and version will be recorded before evaluation; reference disagreement is proxy evidence only and read-backed evidence is primary.
- Polypolish and bcftools: executable paths, versions/container digests, full commands, and training-read inputs must be recorded before arm execution.

## Non-decision invariants

All produced candidates must carry `status=INCONCLUSIVE`, `assembly_grade=CANDIDATE`, and `decision=NOT_APPLICABLE`. CycloneSEQ remains `PENDING_REAL_DATA`; PMAT2 and IDENTIFY/DECISION routing are unchanged.

## Audit policy

Large FASTQ/BAM/intermediate files remain outside Git. Their fixed paths and SHA256 values are recorded in `MANIFEST.sha256`; this report and all lightweight manifests are committed. `nf-test` uses property assertions rather than exact hashes for non-deterministic assemblies.
