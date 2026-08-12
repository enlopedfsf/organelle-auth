# Topology-resolution experiments (experimental appendix)

Date: 2026-08-12  
Platform: ONT  
Decision: `NOT_APPLICABLE`  
Formal topology state: unchanged, `INCONCLUSIVE`

This appendix is independent evidence for the exploratory change. It does not modify the
archived plant pilot, `VALIDATION-plant-lr.md`, IDENTIFY, or DECISION_ENGINE.

## Frozen input

The input was resolved from the historical M3 output tree and linked at:

`runs/input/corydalis/SRR38978847-M3-final-recruited.fastq.gz`

The source is `/home/iris-hp/corydalis_validation/out_lr_reference_first_v4/plant_long_read_evaluation/lr_extract_final/SRR38978847.final-recruited.fastq.gz`.

| Metric | Value |
|---|---:|
| Reads | 14,786 |
| Bases | 122,132,426 |
| SHA-256 | `93f4fd3bc3969e5d4d3577870b32f4a63d99ddc57a325f84403d7f089531f3c8` |
| Source size | 132,373,641 bytes |

The input checksum was verified before starting any Flye task.

## Experiment A — Flye parameter grid

The initial six-point attempt was blocked during minimizer construction. Following the
documented disposition, the retry manifest in `runs/output/topology-resolution-experiments/grid/manifest.json`
contains only `(asm-coverage=200, min-overlap=5000)` and `(asm-coverage=unlimited, min-overlap=5000)`,
each with four Flye threads and an independent parameter-labelled directory. The complete
grid is deferred as an M4 candidate if this reduced retry also remains blocked.

| Combination | Result |
|---|---|
| reduced two-point retry | `GRID_BLOCKED_RUNTIME_TERMINATION` |

The initial Flye 2.9.3-b1797 attempt entered input reading and minimizer-index construction,
then the execution environment terminated the process before `assembly.fasta` or GFA output.
The archived formal control used Flye 2.9.6-b1802; the available runtime is therefore not
version-equivalent. This is an execution blocker, not evidence for or against circularity.
The reduced retry with four threads was also terminated during minimizer construction before
any assembly or GFA output. The available log is
`runs/output/topology-resolution-experiments/grid_retry/asm-200_overlap-5000/flye.log`.
No trustworthy memory peak was emitted, so a numeric resource requirement cannot be inferred;
the remaining full grid is deferred to M4 as planned.

## Experiment B — MAPQ-0 junction recount

Input alignment: `SRR38978847.reads_to_flye.paf`  
SHA-256: `5c7b69fcf42aa1b22c6e9fa0c7ba571f06b99f9e86db590b76d82df92a09f460`  
Flank rule: 500 bp at contig-1 end and contig-2 start; read identities deduplicated.

| Stratum | Junction support |
|---|---:|
| Existing high-quality-only record | 2 |
| MAPQ >= 20, recount | 2 |
| MAPQ-inclusive read identities | 587 |
| Copy-aware weighted support (two IR copies) | 293.5 |

Machine-readable outputs are `runs/output/topology-resolution-experiments/junction-recount.json`
and `.tsv`. The large increase after MAPQ inclusion demonstrates that IR multi-mapping is a
material confounder; it does not establish independent alignment support under the archived
`6.5 independent_alignment_support` definition. The recount therefore cannot revise the
formal `INCONCLUSIVE` topology state.

## Answers and status

1. **Does `asm-coverage` affect circularization?** Not yet answered: the six Flye assemblies
   were blocked by runtime termination before output. This question remains queued.
2. **Was junction evidence underestimated by MAPQ filtering?** Yes, the recount shows strong
   sensitivity to MAPQ inclusion, but most added support is copy-ambiguous; it is not a new
   independent-support qualification.

No archived file was edited. No ONT result entered a decision path. The reduced retry also
failed to produce an assembly, so A remains `BLOCKED` and the complete grid is an M4 candidate.
The observed scaling estimate is that `--asm-coverage 200` presents roughly four times the
selected-read working set of the successful 50x control (and unlimited presents the full ~610x
target depth); the current host cannot sustain minimizer construction at that scale. Exact RAM
must be measured on a larger host and is not inferred from the incomplete log.

The requested plant regression run was attempted with `nf-test test tests/default.nf.test`,
but the environment returned a plugin-repository network timeout after the stale cache was
moved aside. The stale cache is retained as `.nf-test.stale-20260812`; regression verification
remains pending in a clean workspace with the nf-test plugin available offline.
