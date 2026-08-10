# VALIDATION-plant-lr (M3 apply-stage record)

## Scope and platform

This is an ONT-only method exercise using public `SRR38978847` (`SRR38978847-long.fastq.gz`)
and the paired M1 short-read anchor `SRR38978846_{1,2}.fastq.gz`. It is not CycloneSEQ evidence.
PMAT2 remains `EXPERIMENTAL`; no output is connected to IDENTIFY or DECISION_ENGINE.

## Input integrity

The pipeline requires non-empty files, gzip validation, and FASTQ record validation before launch.
The local files are non-empty (R1 2.1G, R2 2.2G, ONT 15G); full validation is performed by the
pilot before PMAT2 consumes the stream. Reference: `corydalis-test-0.1/PZ405204.1`.

## Method contract

- NanoPlot descriptive QC before/after filtering.
- filtlong is the selected filter; no scientific threshold is invented when the policy is null.
- PMAT2 version is pinned to `2.1.5` from the upstream release; invocation is `PMAT autoMito -t ont -x 0`.
- Runtime provisioned locally: NextDenovo 2.5.2, Canu 2.3, BLAST 2.17.0, R 4.x, Apptainer 1.5.3.
- M1 IR gap is `PZ405204.1:96371..134285` (1-based inclusive), copied from archived M1 validation.
- Homopolymer records use maximal SR runs, fixed-alignment lifting, callable denominators,
  substitutions/indels, and run-length delta; the schema is reusable for CycloneSEQ.

## Results

| Metric | Result |
|---|---|
| PMAT2 runtime | `RUNNING` (started 2026-08-11 01:45 CST; log and PID under `/mnt/ssd_pool/home/iris-hp/zhongyao/corydalis_test/m3-pmat2-ont-v2.1.5/`) |
| PMAT2 assembly | `not_assessable` |
| IR gap closure | `not_assessable` (no assembly to align; no closure inferred) |
| LR/SR concordance | `not_assessable` |
| Homopolymer spectrum | schema ready; measured values pending assembly |
| T3 full real-data smoke | intentionally not a CI test; run only after runtime availability |

This is an honest blocked apply-stage record, not a pass. The Go/No-Go record therefore remains
`NO_GO` for production and `PENDING_REAL_DATA` for CycloneSEQ.
